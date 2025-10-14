import os
import uuid
import json
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
        
        # Get the latest analysis and report with defensive check for race conditions
        analysis = song.analyses.filter(analysis_type='full').first()
        report = None
        has_report = False
        report_pending = False
        
        if analysis:
            try:
                # Try to access the report - this will raise DoesNotExist if not ready
                report = analysis.report
                has_report = True
            except AnalysisReport.DoesNotExist:
                # Report doesn't exist yet
                has_report = False
                # Check if we're waiting for report (analyzed status but no report)
                if analysis.status == 'analyzed':
                    report_pending = True
                    logger.warning(f"Analysis {analysis.id} marked as analyzed but report not yet created (race condition)")
        
        context = {
            'song': song,
            'analysis': analysis,
            'report': report,
            'has_report': has_report,
            'report_pending': report_pending,
        }
        return render(request, 'acrcloud/song_detail.html', context)


@method_decorator(login_required, name='dispatch')
class AnalysisReportView(View):
    """
    View for displaying detailed analysis report
    """
    def get(self, request, analysis_id):
        analysis = get_object_or_404(Analysis, id=analysis_id, song__user=request.user)
        
        # Check if analysis is complete
        if analysis.status == 'processing':
            messages.info(request, 'Analysis is still in progress. Please wait a moment.')
            return redirect('acrcloud:song_detail', song_id=str(analysis.song.id))
        
        try:
            report = analysis.report
        except AnalysisReport.DoesNotExist:
            # Report not created yet (race condition)
            if analysis.status == 'analyzed':
                messages.warning(request, 'Report is being generated. Please refresh in a moment.')
            else:
                messages.error(request, 'Analysis report is not available.')
            return redirect('acrcloud:song_detail', song_id=str(analysis.song.id))
        
        context = {
            'analysis': analysis,
            'report': report,
        }
        return render(request, 'acrcloud/analysis_report.html', context)


@method_decorator(login_required, name='dispatch')
class PatternMatchingReportView(View):
    """
    View for displaying detailed pattern matching report
    """
    def get(self, request, analysis_id):
        analysis = get_object_or_404(Analysis, id=analysis_id, song__user=request.user)
        
        # Get counts by match type
        music_matches_count = analysis.track_matches.filter(match_type='music').count()
        cover_matches_count = analysis.track_matches.filter(match_type='cover').count()
        
        context = {
            'analysis': analysis,
            'music_matches_count': music_matches_count,
            'cover_matches_count': cover_matches_count,
        }
        return render(request, 'acrcloud/pattern_matching_report.html', context)


@method_decorator(login_required, name='dispatch')
class EnhancedAnalysisReportView(View):
    """
    View for displaying enhanced analysis report with all fingerprint details
    """
    def get(self, request, analysis_id):
        analysis = get_object_or_404(Analysis, id=analysis_id, song__user=request.user)
        
        # Check if analysis is complete
        if analysis.status == 'processing':
            messages.info(request, 'Analysis is still in progress. Please wait a moment.')
            return redirect('acrcloud:song_detail', song_id=str(analysis.song.id))
        
        # Get all track matches ordered by score (highest first)
        track_matches = analysis.track_matches.all().order_by('-score')
        
        # Get counts by match type
        music_matches_count = analysis.track_matches.filter(match_type='music').count()
        cover_matches_count = analysis.track_matches.filter(match_type='cover').count()
        
        context = {
            'analysis': analysis,
            'track_matches': track_matches,
            'music_matches_count': music_matches_count,
            'cover_matches_count': cover_matches_count,
        }
        return render(request, 'acrcloud/enhanced_analysis_report.html', context)


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
class ACRCloudWebhookView(View):
    """
    Webhook endpoint to receive ACRCloud file scanning completion callbacks
    """
    def post(self, request):
        try:
            # Get client information
            source_ip = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Log the incoming webhook
            logger.info(f"ACRCloud webhook received from {source_ip} - Content-Type: {request.content_type}")
            
            # Parse webhook payload
            if request.content_type == 'application/json':
                payload = json.loads(request.body.decode('utf-8'))
            else:
                payload = dict(request.POST)
            
            logger.info(f"Webhook payload: {payload}")
            
            # Extract file information from webhook
            file_id = payload.get('file_id') or payload.get('id')
            # ACRCloud sends 'state' field: 0=processing, 1=completed, 2=failed
            state = payload.get('state')
            status = payload.get('status')  # Keep for backward compatibility
            
            # Map state to status for processing logic
            if state is not None:
                if state == 1:
                    status = 'completed'
                elif state == 2:
                    status = 'failed'
                elif state == 0:
                    status = 'processing'
            
            # Log webhook call
            from .models import WebhookLog
            webhook_log = WebhookLog.objects.create(
                file_id=file_id or 'unknown',
                status=status or 'unknown',
                payload=payload,
                source_ip=source_ip,
                user_agent=user_agent
            )
            
            if not file_id:
                error_msg = "No file_id in webhook payload"
                logger.error(error_msg)
                webhook_log.error_message = error_msg
                webhook_log.save()
                return JsonResponse({'error': 'Missing file_id'}, status=400)
            
            logger.info(f"Processing webhook for file_id: {file_id}, status: {status}")
            
            # Find the corresponding analysis record
            try:
                analysis = Analysis.objects.get(acrcloud_file_id=file_id, status='processing')
                logger.info(f"Found analysis record: {analysis.id}")
            except Analysis.DoesNotExist:
                logger.error(f"No processing analysis found for file_id: {file_id}")
                return JsonResponse({'error': 'Analysis not found'}, status=404)
            except Analysis.MultipleObjectsReturned:
                logger.error(f"Multiple analyses found for file_id: {file_id}")
                analysis = Analysis.objects.filter(acrcloud_file_id=file_id, status='processing').first()
            
            # Process the webhook based on status
            if status == 'completed' or status == 'success':
                # File processing completed, retrieve results
                from .tasks import process_acrcloud_webhook_task
                
                # Pass webhook data directly to avoid additional API calls
                webhook_results = payload.get('results', {})
                if webhook_results:
                    logger.info(f"Processing webhook with provided results data")
                    process_acrcloud_webhook_task.delay(str(analysis.id), file_id, webhook_results)
                else:
                    logger.info(f"No results in webhook, will fetch from API")
                    process_acrcloud_webhook_task.delay(str(analysis.id), file_id)
                
                logger.info(f"Queued webhook processing task for analysis: {analysis.id}")
                return JsonResponse({'status': 'success', 'message': 'Webhook processed'})
                
            elif status == 'failed' or status == 'error':
                # File processing failed
                analysis.status = 'failed'
                analysis.song.status = 'failed'
                analysis.save()
                analysis.song.save()
                
                logger.error(f"ACRCloud processing failed for file_id: {file_id}")
                return JsonResponse({'status': 'success', 'message': 'Failure recorded'})
            
            else:
                # Unknown status, log and continue
                logger.warning(f"Unknown webhook status: {status} for file_id: {file_id}")
                return JsonResponse({'status': 'success', 'message': 'Status noted'})
                
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Webhook processing failed'}, status=500)
    
    def get_client_ip(self, request):
        """Get the client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get(self, request):
        # Health check endpoint
        return JsonResponse({'status': 'webhook_ready', 'message': 'ACRCloud webhook endpoint is active'})


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