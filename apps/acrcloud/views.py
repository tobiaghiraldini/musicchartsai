import os
import uuid
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.models import Q
from django.conf import settings
from .models import Song, Analysis, AnalysisReport
from .tasks import analyze_song_task
from .forms import SongUploadForm

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class UploadAudioView(View):
    """
    View for uploading audio files with FilePond integration
    """
    def get(self, request):
        form = SongUploadForm()
        return render(request, 'acrcloud/upload_audio.html', {'form': form})
    
    def post(self, request):
        # Debug logging
        logger.info(f"Upload form submission - POST data: {list(request.POST.keys())}")
        logger.info(f"Upload form submission - FILES data: {list(request.FILES.keys())}")
        
        # Check if we have an uploaded file path from FilePond
        uploaded_file_path = request.POST.get('uploaded_file_path')
        logger.info(f"Uploaded file path from form: {uploaded_file_path}")
        
        if uploaded_file_path:
            # Handle FilePond upload
            return self._handle_filepond_upload(request, uploaded_file_path)
        else:
            # Handle regular form upload (fallback)
            return self._handle_regular_upload(request)
    
    def _handle_filepond_upload(self, request, uploaded_file_path):
        """Handle song creation from FilePond uploaded file"""
        try:
            logger.info(f"Processing FilePond upload: {uploaded_file_path}")
            
            # Check if the temp file exists
            if not default_storage.exists(uploaded_file_path):
                logger.error(f"Temp file not found: {uploaded_file_path}")
                messages.error(request, 'Uploaded file not found. Please try uploading again.')
                return redirect('acrcloud:upload_audio')
            
            # Get the temp file
            temp_file = default_storage.open(uploaded_file_path, 'rb')
            file_content = temp_file.read()
            temp_file.close()
            
            logger.info(f"Read temp file, size: {len(file_content)} bytes")
            
            # Extract original filename from the uploaded path
            temp_filename = os.path.basename(uploaded_file_path)
            if '_' in temp_filename:
                original_filename = temp_filename.split('_', 1)[1]
            else:
                original_filename = temp_filename
            
            logger.info(f"Original filename: {original_filename}")
            
            # Create song instance
            song = Song()
            song.user = request.user
            song.title = request.POST.get('title', '').strip()
            song.artist = request.POST.get('artist', '').strip()
            song.original_filename = original_filename
            song.file_size = len(file_content)
            
            logger.info(f"Creating song: title='{song.title}', artist='{song.artist}', filename='{song.original_filename}'")
            
            # Save the file to the proper location
            song.audio_file.save(
                original_filename,
                ContentFile(file_content),
                save=False
            )
            
            # Save the song
            song.save()
            
            logger.info(f"Song saved with ID: {song.id}")
            
            # Clean up temp file
            try:
                default_storage.delete(uploaded_file_path)
                logger.info(f"Temp file deleted: {uploaded_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete temp file: {cleanup_error}")
            
            # Start analysis task
            logger.info(f"Starting analysis task for song: {song.id}")
            analyze_song_task.delay(str(song.id))
            
            messages.success(request, f'Song "{song.title or song.original_filename}" uploaded successfully. Analysis in progress.')
            return redirect('acrcloud:song_detail', song_id=str(song.id))
            
        except Exception as e:
            logger.error(f"Error handling FilePond upload: {str(e)}", exc_info=True)
            messages.error(request, f'Error processing uploaded file: {str(e)}')
            return redirect('acrcloud:upload_audio')
    
    def _handle_regular_upload(self, request):
        """Handle regular form upload (fallback)"""
        form = SongUploadForm(request.POST, request.FILES)
        if form.is_valid():
            song = form.save(commit=False)
            song.user = request.user
            song.original_filename = song.audio_file.name
            song.file_size = song.audio_file.size
            song.save()
            
            # Start analysis task
            analyze_song_task.delay(str(song.id))
            
            messages.success(request, f'Song "{song.title or song.original_filename}" uploaded successfully. Analysis in progress.')
            return redirect('acrcloud:song_detail', song_id=str(song.id))
        
        return render(request, 'acrcloud/upload_audio.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class ViewAudiosView(View):
    """
    View for viewing uploaded audio files
    """
    def get(self, request):
        songs = Song.objects.filter(user=request.user).order_by('-created_at')
        
        # Filter by status if provided
        status_filter = request.GET.get('status')
        if status_filter:
            songs = songs.filter(status=status_filter)
        
        # Search functionality
        search_query = request.GET.get('search')
        if search_query:
            songs = songs.filter(
                Q(title__icontains=search_query) |
                Q(artist__icontains=search_query) |
                Q(original_filename__icontains=search_query)
            )
        
        context = {
            'songs': songs,
            'status_filter': status_filter,
            'search_query': search_query,
        }
        return render(request, 'acrcloud/view_audios.html', context)


@method_decorator(login_required, name='dispatch')
class SongDetailView(View):
    """
    View for displaying song details and analysis report
    """
    def get(self, request, song_id):
        song = get_object_or_404(Song, id=song_id, user=request.user)
        
        # Get the latest analysis and report
        analysis = song.analyses.filter(analysis_type='full').first()
        report = analysis.report if analysis else None
        
        context = {
            'song': song,
            'analysis': analysis,
            'report': report,
        }
        return render(request, 'acrcloud/song_detail.html', context)


@method_decorator(login_required, name='dispatch')
class AnalysisReportView(View):
    """
    View for displaying detailed analysis report
    """
    def get(self, request, analysis_id):
        analysis = get_object_or_404(Analysis, id=analysis_id, song__user=request.user)
        
        try:
            report = analysis.report
        except AnalysisReport.DoesNotExist:
            report = None
        
        context = {
            'analysis': analysis,
            'report': report,
        }
        return render(request, 'acrcloud/analysis_report.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class FilePondUploadView(View):
    """
    API endpoint for FilePond file uploads
    """
    def post(self, request):
        try:
            # Debug: Log all request data
            logger.info(f"FilePond upload request - Method: {request.method}")
            logger.info(f"Content-Type: {request.content_type}")
            logger.info(f"FILES keys: {list(request.FILES.keys())}")
            logger.info(f"POST keys: {list(request.POST.keys())}")
            
            # FilePond sends files with different field names, let's check all possible names
            file = None
            possible_field_names = ['filepond', 'file']
            
            # Add the first available file key if any
            if request.FILES:
                possible_field_names.append(list(request.FILES.keys())[0])
            
            for field_name in possible_field_names:
                if field_name and field_name in request.FILES:
                    file = request.FILES[field_name]
                    logger.info(f"Found file in field: {field_name}")
                    break
            
            if not file:
                error_msg = f"No file found in request.FILES. Available fields: {list(request.FILES.keys())}, Content-Type: {request.content_type}"
                logger.error(error_msg)
                return JsonResponse({'error': 'No file provided', 'debug': error_msg}, status=400)
            
            logger.info(f"Received file: {file.name}, size: {file.size}, content_type: {file.content_type}")
            
            # Validate file type - be more flexible with content types
            allowed_types = [
                'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/wave', 
                'audio/mp4', 'audio/m4a', 'audio/flac', 'audio/aac',
                'audio/x-wav', 'audio/x-m4a', 'application/octet-stream'
            ]
            
            # Also check file extension as fallback
            allowed_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.aac']
            file_extension = os.path.splitext(file.name.lower())[1]
            
            if file.content_type not in allowed_types and file_extension not in allowed_extensions:
                logger.error(f"Invalid file type: {file.content_type}, extension: {file_extension}")
                return JsonResponse({'error': f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}'}, status=400)
            
            # Validate file size (max 50MB)
            max_size = 50 * 1024 * 1024  # 50MB
            if file.size > max_size:
                logger.error(f"File too large: {file.size} bytes")
                return JsonResponse({'error': f'File too large. Maximum size: {max_size // (1024 * 1024)}MB'}, status=400)
            
            # Create temp directory if it doesn't exist
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Save file temporarily with unique name to avoid conflicts
            unique_filename = f"{uuid.uuid4()}_{file.name}"
            file_path = default_storage.save(f'temp/{unique_filename}', ContentFile(file.read()))
            
            logger.info(f"File saved successfully: {file_path}")
            return JsonResponse({'file_id': file_path})
            
        except Exception as e:
            logger.error(f"FilePond upload error: {str(e)}", exc_info=True)
            return JsonResponse({'error': f'Upload failed: {str(e)}'}, status=500)
    
    def delete(self, request):
        try:
            file_id = request.body.decode('utf-8')
            if default_storage.exists(file_id):
                default_storage.delete(file_id)
            return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f"FilePond delete error: {str(e)}")
            return JsonResponse({'error': 'Delete failed'}, status=500)


@method_decorator(login_required, name='dispatch')
class RetryAnalysisView(View):
    """
    View to retry failed analysis
    """
    def post(self, request, song_id):
        song = get_object_or_404(Song, id=song_id, user=request.user)
        
        if song.status == 'failed':
            song.status = 'uploaded'
            song.save()
            
            # Start analysis task
            analyze_song_task.delay(str(song.id))
            
            messages.success(request, 'Analysis restarted successfully.')
        else:
            messages.warning(request, 'Analysis can only be retried for failed songs.')
        
        return redirect('acrcloud:song_detail', song_id=str(song.id))


@method_decorator(login_required, name='dispatch')
class DeleteSongView(View):
    """
    View to delete a song and its analysis data
    """
    def post(self, request, song_id):
        song = get_object_or_404(Song, id=song_id, user=request.user)
        
        # Delete the audio file
        if song.audio_file:
            try:
                song.audio_file.delete(save=False)
            except Exception as e:
                logger.error(f"Failed to delete audio file: {str(e)}")
        
        # Delete the song (this will cascade to analyses and reports)
        song.delete()
        
        messages.success(request, 'Song deleted successfully.')
        return redirect('acrcloud:view_audios')


@method_decorator(login_required, name='dispatch')
class AnalysisStatusView(View):
    """
    API endpoint to check analysis status
    """
    def get(self, request, song_id):
        song = get_object_or_404(Song, id=song_id, user=request.user)
        
        analysis = song.analyses.filter(analysis_type='full').first()
        
        data = {
            'song_id': str(song.id),
            'status': song.status,
            'has_analysis': analysis is not None,
            'has_report': analysis and hasattr(analysis, 'report'),
        }
        
        if analysis and hasattr(analysis, 'report'):
            report = analysis.report
            data.update({
                'risk_level': report.risk_level,
                'match_type': report.match_type,
                'confidence_score': report.confidence_score,
                'fraud_detected': report.is_fraud_detected(),
            })
        
        return JsonResponse(data)


@method_decorator(csrf_exempt, name='dispatch')
class TestUploadView(View):
    """
    Simple test endpoint to debug upload issues
    """
    def post(self, request):
        return JsonResponse({
            'method': request.method,
            'content_type': request.content_type,
            'files_keys': list(request.FILES.keys()),
            'post_keys': list(request.POST.keys()),
            'files_count': len(request.FILES),
            'success': True
        })
    
    def get(self, request):
        return JsonResponse({'message': 'Test endpoint is working', 'method': 'GET'})