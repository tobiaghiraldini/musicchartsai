from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.models import Q
import json
import os
import mimetypes
from .models import Song, Analysis, AnalysisReport
from .tasks import analyze_song_task
from .forms import SongUploadForm
import logging

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
            if 'filepond' not in request.FILES:
                return JsonResponse({'error': 'No file provided'}, status=400)
            
            file = request.FILES['filepond']
            
            # Validate file type
            allowed_types = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/flac', 'audio/aac']
            if file.content_type not in allowed_types:
                return JsonResponse({'error': 'Invalid file type'}, status=400)
            
            # Validate file size (max 50MB)
            max_size = 50 * 1024 * 1024  # 50MB
            if file.size > max_size:
                return JsonResponse({'error': 'File too large'}, status=400)
            
            # Save file temporarily
            file_path = default_storage.save(f'temp/{file.name}', ContentFile(file.read()))
            
            return JsonResponse({'file_id': file_path})
            
        except Exception as e:
            logger.error(f"FilePond upload error: {str(e)}")
            return JsonResponse({'error': 'Upload failed'}, status=500)
    
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