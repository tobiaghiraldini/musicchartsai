"""
Celery tasks for ACRCloud analysis
"""
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Song, Analysis, AnalysisReport
from .service import ACRCloudService
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def analyze_song_task(self, song_id: str, config_name: str = None):
    """
    Celery task to analyze a song using ACRCloud
    
    Args:
        song_id: UUID of the Song model
        config_name: Name of ACRCloudConfig to use
        
    Returns:
        Dict with analysis results
    """
    try:
        logger.info(f"Starting analysis for song {song_id}")
        
        # Initialize ACRCloud service
        service = ACRCloudService(config_name=config_name)
        
        # Build callback URL for webhook
        from django.urls import reverse
        from django.conf import settings
        
        # Get the base URL for webhooks
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        callback_url = f"{base_url}{reverse('acrcloud:acrcloud_webhook')}"
        
        logger.info(f"Using webhook callback URL: {callback_url}")
        
        # Start analysis with webhook callback
        result = service.analyze_song(song_id, callback_url=callback_url)
        
        if result['success']:
            logger.info(f"Analysis completed successfully for song {song_id}")
            
            # Send notification email if configured
            if hasattr(settings, 'ACRCLOUD_NOTIFICATION_EMAIL'):
                send_analysis_complete_notification.delay(song_id, result['analysis_id'])
            
            return result
        else:
            logger.error(f"Analysis failed for song {song_id}: {result['error']}")
            raise Exception(result['error'])
            
    except Exception as exc:
        logger.error(f"Analysis task failed for song {song_id}: {str(exc)}")
        
        # Update song status to failed
        try:
            song = Song.objects.get(id=song_id)
            song.status = 'failed'
            song.save()
        except Song.DoesNotExist:
            logger.error(f"Song {song_id} not found when updating status")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying analysis task for song {song_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        else:
            logger.error(f"Max retries exceeded for song {song_id}")
            raise exc


@shared_task
def send_analysis_complete_notification(song_id: str, analysis_id: str):
    """
    Send email notification when analysis is complete
    
    Args:
        song_id: UUID of the Song model
        analysis_id: UUID of the Analysis model
    """
    try:
        song = Song.objects.get(id=song_id)
        analysis = Analysis.objects.get(id=analysis_id)
        
        # Get the report if it exists
        try:
            report = analysis.report
            fraud_detected = report.is_fraud_detected()
            risk_level = report.get_risk_level_display()
        except AnalysisReport.DoesNotExist:
            fraud_detected = False
            risk_level = "Unknown"
        
        subject = f"Music Analysis Complete - {song.title or song.original_filename}"
        
        message = f"""
        Analysis completed for: {song.title or song.original_filename}
        Artist: {song.artist or 'Unknown'}
        
        Risk Level: {risk_level}
        Fraud Detected: {'Yes' if fraud_detected else 'No'}
        
        You can view the detailed report in your dashboard.
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[song.user.email],
            fail_silently=False,
        )
        
        logger.info(f"Notification sent for song {song_id}")
        
    except Exception as e:
        logger.error(f"Failed to send notification for song {song_id}: {str(e)}")


@shared_task
def cleanup_old_analyses(days_old: int = 30):
    """
    Clean up old analysis data to save storage
    
    Args:
        days_old: Number of days after which to clean up data
    """
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days_old)
    
    # Delete old analyses and their related data
    old_analyses = Analysis.objects.filter(created_at__lt=cutoff_date)
    count = old_analyses.count()
    
    for analysis in old_analyses:
        # Delete the audio file
        if analysis.song.audio_file:
            try:
                analysis.song.audio_file.delete(save=False)
            except Exception as e:
                logger.error(f"Failed to delete audio file for song {analysis.song.id}: {str(e)}")
        
        # Delete the song and related data
        analysis.song.delete()
    
    logger.info(f"Cleaned up {count} old analyses")
    return f"Cleaned up {count} old analyses"


@shared_task
def batch_analyze_songs(song_ids: list, config_name: str = None):
    """
    Analyze multiple songs in batch
    
    Args:
        song_ids: List of song UUIDs
        config_name: Name of ACRCloudConfig to use
    """
    results = []
    
    for song_id in song_ids:
        try:
            result = analyze_song_task.delay(song_id, config_name)
            results.append({
                'song_id': song_id,
                'task_id': result.id,
                'status': 'queued'
            })
        except Exception as e:
            logger.error(f"Failed to queue analysis for song {song_id}: {str(e)}")
            results.append({
                'song_id': song_id,
                'task_id': None,
                'status': 'failed',
                'error': str(e)
            })
    
    logger.info(f"Queued {len(song_ids)} songs for analysis")
    return results


@shared_task
def process_acrcloud_webhook_task(analysis_id: str, file_id: str):
    """
    Process ACRCloud webhook callback and retrieve analysis results
    
    Args:
        analysis_id: UUID of the Analysis model
        file_id: ACRCloud file ID
    """
    try:
        from .models import Analysis
        from .service import ACRCloudService
        
        logger.info(f"Processing ACRCloud webhook for analysis {analysis_id}, file {file_id}")
        
        # Get the analysis record
        analysis = Analysis.objects.get(id=analysis_id)
        song = analysis.song
        
        # Initialize ACRCloud service
        service = ACRCloudService()
        
        # Retrieve the file scanning results
        file_results = service.get_file_scanning_results(file_id)
        logger.info(f"Retrieved file scanning results for {file_id}")
        
        # Also get identification results for additional analysis
        identify_results = service.identify_audio(song.audio_file, top_n=10)
        logger.info(f"Retrieved identification results for song {song.id}")
        
        # Combine results
        combined_results = {
            'file_scanning': file_results,
            'identification': identify_results
        }
        
        # Update analysis with results
        analysis.raw_response = combined_results
        analysis.status = 'analyzed'
        analysis.completed_at = timezone.now()
        analysis.save()
        
        # Process results and create report
        report_data = service._process_analysis_results(combined_results)
        
        # Create AnalysisReport
        from .models import AnalysisReport
        AnalysisReport.objects.create(
            analysis=analysis,
            **report_data
        )
        
        # Process metadata and create/update Soundcharts models
        from .service import ACRCloudMetadataProcessor
        metadata_processor = ACRCloudMetadataProcessor()
        metadata_processor.process_webhook_results(analysis, combined_results)
        
        # Update song status
        song.status = 'analyzed'
        song.save()
        
        logger.info(f"Webhook processing completed successfully for analysis {analysis_id}")
        
        # Send notification email if configured
        from django.conf import settings
        if hasattr(settings, 'ACRCLOUD_NOTIFICATION_EMAIL'):
            send_analysis_complete_notification.delay(str(song.id), analysis_id)
        
        return {
            'success': True,
            'analysis_id': analysis_id,
            'file_id': file_id
        }
        
    except Exception as e:
        logger.error(f"Webhook processing failed for analysis {analysis_id}: {str(e)}", exc_info=True)
        
        # Update analysis and song status to failed
        try:
            analysis = Analysis.objects.get(id=analysis_id)
            analysis.status = 'failed'
            analysis.song.status = 'failed'
            analysis.save()
            analysis.song.save()
        except Analysis.DoesNotExist:
            logger.error(f"Analysis {analysis_id} not found when updating failure status")
        
        raise e


@shared_task
def retry_failed_analyses():
    """
    Retry failed analyses that might have failed due to temporary issues
    """
    failed_songs = Song.objects.filter(status='failed')
    retry_count = 0
    
    for song in failed_songs:
        try:
            # Reset status and retry
            song.status = 'uploaded'
            song.save()
            
            # Queue for analysis
            analyze_song_task.delay(str(song.id))
            retry_count += 1
            
        except Exception as e:
            logger.error(f"Failed to retry analysis for song {song.id}: {str(e)}")
    
    logger.info(f"Retried {retry_count} failed analyses")
    return f"Retried {retry_count} failed analyses"
