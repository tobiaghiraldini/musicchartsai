import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from .models import Track, MetadataFetchTask
from .service import SoundchartsService

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def fetch_track_metadata(self, track_uuid):
    """
    Fetch metadata for a single track from Soundcharts API
    """
    try:
        logger.info(f"Starting metadata fetch for track {track_uuid}")
        
        # Get the track
        try:
            track = Track.objects.get(uuid=track_uuid)
        except Track.DoesNotExist:
            logger.error(f"Track with UUID {track_uuid} not found")
            return False
        
        # Fetch metadata from API
        service = SoundchartsService()
        metadata = service.get_song_metadata_enhanced(track_uuid)
        logger.info(f"Metadata: {metadata}")
        if not metadata:
            logger.error(f"Failed to fetch metadata for track {track_uuid}")
            return False
        
        # Update track with metadata
        with transaction.atomic():
            if "object" in metadata:
                track_data = metadata["object"]
                
                # Update basic fields
                if "name" in track_data:
                    track.name = track_data["name"]
                if "slug" in track_data:
                    track.slug = track_data["slug"]
                if "creditName" in track_data:
                    track.credit_name = track_data["creditName"]
                if "imageUrl" in track_data:
                    track.image_url = track_data["imageUrl"]
                
                # Update enhanced metadata fields
                if "releaseDate" in track_data and track_data["releaseDate"]:
                    try:
                        from datetime import datetime
                        release_date = datetime.strptime(track_data["releaseDate"], "%Y-%m-%d").date()
                        track.release_date = release_date
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid release date format for track {track_uuid}: {track_data['releaseDate']}")
                
                if "duration" in track_data:
                    track.duration = track_data["duration"]
                if "isrc" in track_data:
                    track.isrc = track_data["isrc"]
                if "label" in track_data and track_data["label"]:
                    track.label = track_data["label"]["name"] if isinstance(track_data["label"], dict) else track_data["label"]
                if "genres" in track_data and track_data["genres"]:
                    # Take the first genre as primary
                    if isinstance(track_data["genres"], list) and len(track_data["genres"]) > 0:
                        genre = track_data["genres"][0]
                        if isinstance(genre, dict) and "name" in genre:
                            track.genre = genre["name"]
                        elif isinstance(genre, str):
                            track.genre = genre
                
                # Update metadata fetch timestamp
                track.metadata_fetched_at = timezone.now()
                track.save()
                
                logger.info(f"Successfully updated metadata for track {track_uuid}")
                return True
            else:
                logger.error(f"Invalid metadata format for track {track_uuid}")
                return False
                
    except Exception as e:
        logger.error(f"Error fetching metadata for track {track_uuid}: {str(e)}")
        return False


@shared_task(bind=True)
def fetch_bulk_track_metadata(self, task_id):
    """
    Fetch metadata for multiple tracks in bulk
    """
    try:
        logger.info(f"Starting bulk metadata fetch task {task_id}")
        
        # Get the task record
        try:
            task = MetadataFetchTask.objects.get(id=task_id)
        except MetadataFetchTask.DoesNotExist:
            logger.error(f"MetadataFetchTask {task_id} not found")
            return False
        
        # Update task status
        task.status = 'running'
        task.started_at = timezone.now()
        task.celery_task_id = self.request.id
        task.save()
        
        service = SoundchartsService()
        success_count = 0
        failed_count = 0
        
        for track_uuid in task.track_uuids:
            try:
                # Check if track still exists
                try:
                    track = Track.objects.get(uuid=track_uuid)
                except Track.DoesNotExist:
                    logger.warning(f"Track {track_uuid} no longer exists, skipping")
                    failed_count += 1
                    continue
                
                # Fetch metadata
                metadata = service.get_song_metadata_enhanced(track_uuid)
                
                if metadata and "object" in metadata:
                    track_data = metadata["object"]
                    
                    # Update track with metadata
                    with transaction.atomic():
                        if "name" in track_data:
                            track.name = track_data["name"]
                        if "slug" in track_data:
                            track.slug = track_data["slug"]
                        if "creditName" in track_data:
                            track.credit_name = track_data["creditName"]
                        if "imageUrl" in track_data:
                            track.image_url = track_data["imageUrl"]
                        
                        # Update enhanced metadata fields
                        if "releaseDate" in track_data and track_data["releaseDate"]:
                            try:
                                from datetime import datetime
                                release_date = datetime.strptime(track_data["releaseDate"], "%Y-%m-%d").date()
                                track.release_date = release_date
                            except (ValueError, TypeError):
                                pass
                        
                        if "duration" in track_data:
                            track.duration = track_data["duration"]
                        if "isrc" in track_data:
                            track.isrc = track_data["isrc"]
                        if "label" in track_data and track_data["label"]:
                            track.label = track_data["label"]["name"] if isinstance(track_data["label"], dict) else track_data["label"]
                        if "genres" in track_data and track_data["genres"]:
                            if isinstance(track_data["genres"], list) and len(track_data["genres"]) > 0:
                                genre = track_data["genres"][0]
                                if isinstance(genre, dict) and "name" in genre:
                                    track.genre = genre["name"]
                                elif isinstance(genre, str):
                                    track.genre = genre
                        
                        track.metadata_fetched_at = timezone.now()
                        track.save()
                        
                        success_count += 1
                        logger.debug(f"Successfully updated metadata for track {track_uuid}")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to fetch metadata for track {track_uuid}")
                
                # Update progress
                task.processed_tracks += 1
                task.successful_tracks = success_count
                task.failed_tracks = failed_count
                task.save()
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing track {track_uuid}: {str(e)}")
                task.processed_tracks += 1
                task.failed_tracks = failed_count
                task.save()
        
        # Update final task status
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.successful_tracks = success_count
        task.failed_tracks = failed_count
        task.save()
        
        logger.info(f"Bulk metadata fetch task {task_id} completed. Success: {success_count}, Failed: {failed_count}")
        return True
        
    except Exception as e:
        logger.error(f"Error in bulk metadata fetch task {task_id}: {str(e)}")
        
        # Update task status to failed
        try:
            task = MetadataFetchTask.objects.get(id=task_id)
            task.status = 'failed'
            task.error_message = str(e)
            task.completed_at = timezone.now()
            task.save()
        except MetadataFetchTask.DoesNotExist:
            pass
        
        return False


@shared_task(bind=True)
def fetch_all_tracks_metadata(self):
    """
    Fetch metadata for all tracks that don't have metadata or haven't been updated recently
    """
    try:
        logger.info("Starting bulk metadata fetch for all tracks")
        
        # Get tracks that need metadata update (either no metadata or older than 30 days)
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=30)
        
        tracks_to_update = Track.objects.filter(
            Q(metadata_fetched_at__isnull=True) |
            Q(metadata_fetched_at__lt=cutoff_date)
        )
        
        if not tracks_to_update.exists():
            logger.info("No tracks need metadata update")
            return True
        
        # Create a bulk metadata fetch task
        track_uuids = list(tracks_to_update.values_list('uuid', flat=True))
        
        task = MetadataFetchTask.objects.create(
            task_type='bulk_metadata',
            status='pending',
            track_uuids=track_uuids,
            total_tracks=len(track_uuids),
            celery_task_id=self.request.id
        )
        
        logger.info(f"Created bulk metadata fetch task {task.id} for {len(track_uuids)} tracks")
        
        # Start the bulk fetch task
        fetch_bulk_track_metadata.delay(task.id)
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating bulk metadata fetch task: {str(e)}")
        return False
