"""
Mock Celery tasks for testing ACRCloud analysis without real API credentials
"""
from celery import shared_task
from django.utils import timezone
import time
import random
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def mock_analyze_song_task(self, song_id: str):
    """
    Mock Celery task to test analysis flow without real ACRCloud API
    
    Args:
        song_id: UUID of the Song model
        
    Returns:
        Dict with mock analysis results
    """
    try:
        from .models import Song, Analysis, AnalysisReport
        from .mock_service import MockACRCloudService
        
        logger.info(f"Starting MOCK analysis for song {song_id}")
        
        # Initialize mock service
        service = MockACRCloudService()
        
        # Perform mock analysis
        result = service.analyze_song(song_id)
        
        if result['success']:
            logger.info(f"MOCK analysis completed successfully for song {song_id}")
            return result
        else:
            logger.error(f"MOCK analysis failed for song {song_id}: {result['error']}")
            raise Exception(result['error'])
            
    except Exception as exc:
        logger.error(f"MOCK analysis task failed for song {song_id}: {str(exc)}")
        
        # Update song status to failed
        try:
            from .models import Song
            song = Song.objects.get(id=song_id)
            song.status = 'failed'
            song.save()
        except Song.DoesNotExist:
            logger.error(f"Song {song_id} not found when updating status")
        
        raise exc
