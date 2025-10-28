import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from .models import Track, Artist, MetadataFetchTask, ChartSyncSchedule, ChartSyncExecution, Chart, ChartRanking, ChartRankingEntry, Platform, TrackAudienceTimeSeries, ArtistAudienceTimeSeries
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
                # Process genres (extract hierarchical genres)
                if "genres" in track_data and track_data["genres"]:
                    from .models import Genre
                    track.genres.clear()
                    track_genres = []
                    primary_genre = None
                    
                    if isinstance(track_data["genres"], list) and len(track_data["genres"]) > 0:
                        for genre_data in track_data["genres"]:
                            if isinstance(genre_data, dict) and "root" in genre_data:
                                result = Genre.create_from_soundcharts(genre_data)
                                if result:
                                    root_genre, subgenres = result
                                    track_genres.append(root_genre)
                                    track_genres.extend(subgenres)
                                    
                                    if primary_genre is None:
                                        primary_genre = root_genre
                    
                    if track_genres:
                        track.genres.set(track_genres)
                        track.primary_genre = primary_genre
                
                # Process artists (extract artists from track metadata)
                if "artists" in track_data and track_data["artists"]:
                    track.artists.clear()
                    track_artists = []
                    primary_artist = None
                    
                    if isinstance(track_data["artists"], list) and len(track_data["artists"]) > 0:
                        for artist_data in track_data["artists"]:
                            if isinstance(artist_data, dict) and "uuid" in artist_data and "name" in artist_data:
                                artist = Artist.create_from_soundcharts(artist_data)
                                if artist:
                                    track_artists.append(artist)
                                    
                                    if primary_artist is None:
                                        primary_artist = artist
                    
                    if track_artists:
                        track.artists.set(track_artists)
                        track.primary_artist = primary_artist
                
                # Update metadata fetch timestamp
                track.metadata_fetched_at = timezone.now()
                track.save()
                
                logger.info(f"Successfully updated metadata for track {track_uuid}")
                
                # Cascade: After track metadata is fetched, sync artists
                sync_artists_after_track_metadata.delay(track_uuid)
                
                # Cascade: After track metadata is fetched, fetch audience
                sync_track_audience.delay(track_uuid)
                
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
                    
                    # Process genres (extract hierarchical genres)
                    if "genres" in track_data and track_data["genres"]:
                        from .models import Genre
                        track.genres.clear()
                        track_genres = []
                        primary_genre = None
                        
                        if isinstance(track_data["genres"], list) and len(track_data["genres"]) > 0:
                            for genre_data in track_data["genres"]:
                                if isinstance(genre_data, dict) and "root" in genre_data:
                                    result = Genre.create_from_soundcharts(genre_data)
                                    if result:
                                        root_genre, subgenres = result
                                        track_genres.append(root_genre)
                                        track_genres.extend(subgenres)
                                        
                                        if primary_genre is None:
                                            primary_genre = root_genre
                        
                        if track_genres:
                            track.genres.set(track_genres)
                            track.primary_genre = primary_genre
                    
                    # Process artists (extract artists from track metadata)
                    if "artists" in track_data and track_data["artists"]:
                        track.artists.clear()
                        track_artists = []
                        primary_artist = None
                        
                        if isinstance(track_data["artists"], list) and len(track_data["artists"]) > 0:
                            for artist_data in track_data["artists"]:
                                if isinstance(artist_data, dict) and "uuid" in artist_data and "name" in artist_data:
                                    artist = Artist.create_from_soundcharts(artist_data)
                                    if artist:
                                        track_artists.append(artist)
                                        
                                        if primary_artist is None:
                                            primary_artist = artist
                        
                        if track_artists:
                            track.artists.set(track_artists)
                            track.primary_artist = primary_artist
                        
                        track.metadata_fetched_at = timezone.now()
                        track.save()
                        
                        success_count += 1
                        logger.debug(f"Successfully updated metadata for track {track_uuid}")
                        
                        # Cascade: After track metadata is fetched, sync artists
                        sync_artists_after_track_metadata.delay(track_uuid)
                        
                        # Cascade: After track metadata is fetched, fetch audience
                        sync_track_audience.delay(track_uuid)
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


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_chart_rankings_task(self, schedule_id, execution_id):
    """
    Sync chart rankings for a specific chart schedule
    This task handles fetching chart rankings from Soundcharts API and storing them
    """
    try:
        logger.info(f"Starting chart sync task for schedule {schedule_id}, execution {execution_id}")
        
        # Get the execution record
        try:
            execution = ChartSyncExecution.objects.get(id=execution_id)
            schedule = execution.schedule
            chart = schedule.chart
        except ChartSyncExecution.DoesNotExist:
            logger.error(f"ChartSyncExecution {execution_id} not found")
            return False
        
        # Update execution status
        execution.status = 'running'
        execution.celery_task_id = self.request.id
        execution.save()
        
        service = SoundchartsService()
        rankings_created = 0
        rankings_updated = 0
        tracks_created = 0
        tracks_updated = 0
        
        # Determine what rankings to fetch based on chart frequency
        missing_periods = _get_missing_ranking_periods(chart, schedule.sync_historical_data)
        
        for period_start, period_end in missing_periods:
            try:
                logger.info(f"Fetching rankings for {chart.name} from {period_start} to {period_end}")
                
                # Fetch rankings from API
                rankings_data = service.get_song_ranking_for_date(
                    chart.slug, 
                    period_start
                )
                
                if rankings_data and 'items' in rankings_data:
                    items_count = len(rankings_data['items'])
                    logger.info(f"API returned {items_count} items for {chart.name} on {period_start}")
                    
                    # Check if API has any items - only process if there's actual data
                    if items_count == 0:
                        logger.warning(f"API returned empty results for {chart.name} on {period_start} - skipping (no data available)")
                        # Don't create ranking record for dates with no data (like manual import behavior)
                        continue
                    
                    # Process the ranking data
                    ranking, created = _process_chart_ranking(
                        chart, 
                        rankings_data, 
                        period_start
                    )
                    
                    if created:
                        rankings_created += 1
                        logger.info(f"Created new ranking {ranking.id} for {chart.name}")
                    else:
                        rankings_updated += 1
                        logger.info(f"Updated existing ranking {ranking.id} for {chart.name}")
                    
                    # Process tracks and entries
                    track_stats = _process_ranking_entries(ranking, rankings_data['items'], schedule.fetch_track_metadata)
                    tracks_created += track_stats.get('created', 0)
                    tracks_updated += track_stats.get('updated', 0)
                    entries_created = track_stats.get('entries_created', 0)
                    
                    logger.info(f"Successfully processed ranking for {chart.name} on {period_start}: {entries_created} entries created")
                else:
                    logger.warning(f"No ranking data found for {chart.name} on {period_start}")
                
            except Exception as e:
                logger.error(f"Error processing ranking for {chart.name} on {period_start}: {str(e)}")
                continue
        
        # Mark execution as completed
        execution.mark_completed(
            rankings_created=rankings_created,
            rankings_updated=rankings_updated,
            tracks_created=tracks_created,
            tracks_updated=tracks_updated
        )
        
        logger.info(f"Chart sync task completed for {chart.name}. Rankings: {rankings_created} created, {rankings_updated} updated")
        return True
        
    except Exception as e:
        logger.error(f"Error in chart sync task for schedule {schedule_id}: {str(e)}")
        
        # Mark execution as failed
        try:
            execution = ChartSyncExecution.objects.get(id=execution_id)
            execution.mark_failed(str(e))
        except ChartSyncExecution.DoesNotExist:
            pass
        
        # Retry if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying chart sync task for schedule {schedule_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return False


@shared_task(bind=True)
def process_scheduled_chart_syncs(self):
    """
    Process all active chart sync schedules that are due for sync
    This is a periodic task that should be run regularly (e.g., every hour)
    """
    try:
        logger.info("Starting scheduled chart sync processing")
        
        # Get all active schedules that are due for sync
        from django.utils import timezone
        now = timezone.now()
        
        due_schedules = ChartSyncSchedule.objects.filter(
            is_active=True,
            next_sync_at__lte=now
        )
        
        if not due_schedules.exists():
            logger.info("No chart sync schedules are due")
            return True
        
        logger.info(f"Found {due_schedules.count()} chart sync schedules due for processing")
        
        # Process each due schedule
        processed_count = 0
        for schedule in due_schedules:
            try:
                # Create execution record
                execution = ChartSyncExecution.objects.create(
                    schedule=schedule,
                    status='pending'
                )
                
                # Queue the sync task
                task = sync_chart_rankings_task.delay(schedule.id, execution.id)
                execution.celery_task_id = task.id
                execution.status = 'running'
                execution.save()
                
                processed_count += 1
                logger.info(f"Queued sync task for chart {schedule.chart.name}")
                
            except Exception as e:
                logger.error(f"Error queuing sync task for chart {schedule.chart.name}: {str(e)}")
                continue
        
        logger.info(f"Successfully queued {processed_count} chart sync tasks")
        return True
        
    except Exception as e:
        logger.error(f"Error in scheduled chart sync processing: {str(e)}")
        return False


def _get_missing_ranking_periods(chart, sync_historical_data=True):
    """
    Determine what ranking dates are missing for a chart based on its frequency.
    First checks API for 'latest' to get the actual latest available ranking date,
    then calculates missing periods based on that date.
    Returns a list of (date, None) tuples representing dates to fetch.
    """
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    missing_periods = []
    
    # Get existing rankings dates for this chart
    existing_ranking_dates = set(
        ChartRanking.objects.filter(chart=chart)
        .values_list('ranking_date__date', flat=True)
    )
    
    # Determine frequency interval
    if chart.frequency.lower() == 'daily':
        interval = timedelta(days=1)
        # For daily charts, check last 3 periods
        periods_to_check = 3
    elif chart.frequency.lower() == 'weekly':
        interval = timedelta(weeks=1)
        # For weekly charts, check last 3-4 weeks
        periods_to_check = 4 if sync_historical_data else 2
    elif chart.frequency.lower() == 'monthly':
        interval = timedelta(days=30)
        # For monthly charts, check last 3 months
        periods_to_check = 3 if sync_historical_data else 1
    else:
        # Default to weekly
        interval = timedelta(weeks=1)
        periods_to_check = 4 if sync_historical_data else 2
    
    # First, check the API for the latest available ranking date
    service = SoundchartsService()
    logger.info(f"Checking API for latest available ranking for {chart.name}")
    
    try:
        latest_data = service.get_song_ranking_for_date(chart.slug, 'latest')
        
        if latest_data and 'related' in latest_data and 'date' in latest_data['related']:
            # Parse the latest ranking date from the API
            latest_date_str = latest_data['related']['date']
            latest_date = timezone.datetime.fromisoformat(latest_date_str.replace('+00:00', '+0000').replace('Z', '+0000'))
            if latest_date.tzinfo is None:
                latest_date = timezone.make_aware(latest_date)
            
            logger.info(f"Latest available ranking for {chart.name} is from: {latest_date.date()}")
            
            # Use the latest available date as the reference point
            check_date = latest_date
        else:
            # Fallback to today if we can't get the latest date
            logger.warning(f"Could not determine latest ranking date for {chart.name}, using today as reference")
            check_date = timezone.now()
    except Exception as e:
        logger.warning(f"Error checking latest ranking for {chart.name}: {e}, using today as reference")
        check_date = timezone.now()
    
    # Now check for missing periods starting from the latest available date
    for i in range(periods_to_check):
        if check_date.date() not in existing_ranking_dates:
            missing_periods.append((check_date, None))
            logger.info(f"Will check for ranking data for {chart.name} on: {check_date.date()}")
        
        # Move back by the chart's frequency interval
        check_date -= interval
    
    if not missing_periods:
        logger.info(f"No missing rankings found for {chart.name}")
    else:
        logger.info(f"Found {len(missing_periods)} missing ranking(s) for {chart.name}")
    
    return missing_periods


def _process_chart_ranking(chart, rankings_data, ranking_date):
    """
    Process chart ranking data and create/update ChartRanking record.
    Uses the exact same approach as the manual import for consistency.
    """
    try:
        # Parse ranking_date if it's a string
        from django.utils import timezone
        if isinstance(ranking_date, str):
            ranking_date = timezone.datetime.fromisoformat(ranking_date)
        
        # Use the exact same approach as manual import
        ranking, created = ChartRanking.objects.get_or_create(
            chart=chart,
            ranking_date=ranking_date,
            defaults={
                "total_entries": len(rankings_data.get('items', [])),
                "api_version": rankings_data.get('version', 'v2.14'),
            },
        )
        
        if created:
            logger.info(f"Created new ranking for {chart.name} on {ranking_date}")
        else:
            # Update existing ranking if data has changed
            updated = False
            if ranking.total_entries != len(rankings_data.get('items', [])):
                ranking.total_entries = len(rankings_data.get('items', []))
                updated = True
            if rankings_data.get('version') and ranking.api_version != rankings_data['version']:
                ranking.api_version = rankings_data['version']
                updated = True
            if updated:
                ranking.save()
                logger.info(f"Updated existing ranking for {chart.name} on {ranking_date}")
            else:
                logger.info(f"Ranking already exists for {chart.name} on {ranking_date}, no changes needed")
        
        return ranking, created
        
    except Exception as e:
        logger.error(f"Error processing chart ranking: {str(e)}")
        raise


def _process_ranking_entries(ranking, items_data, fetch_track_metadata=True):
    """
    Process ranking entries and create/update Track and ChartRankingEntry records
    """
    tracks_created = 0
    tracks_updated = 0
    entries_created = 0
    
    try:
        # Clear existing entries for this ranking
        existing_count = ranking.entries.count()
        if existing_count > 0:
            logger.info(f"Deleting {existing_count} existing entries for ranking {ranking.id}")
            ranking.entries.all().delete()
        
        # Collect track UUIDs for metadata fetching
        track_uuids_for_metadata = []
        
        for item_data in items_data:
            try:
                # Extract song data from API response
                # API structure: { "song": { "uuid": "...", "name": "..." }, "position": 1, ... }
                song_data = item_data.get('song', {})
                track_uuid = song_data.get('uuid')
                
                if not track_uuid:
                    logger.warning(f"Skipping entry with no track UUID: {item_data}")
                    continue
                
                # Extract track information from nested song object
                track_name = song_data.get('name', '')
                track_slug = song_data.get('slug', '')
                credit_name = song_data.get('creditName', '')
                image_url = song_data.get('imageUrl', '')
                
                # Get or create track
                track, track_created = Track.objects.get_or_create(
                    uuid=track_uuid,
                    defaults={
                        'name': track_name,
                        'slug': track_slug,
                        'credit_name': credit_name,
                        'image_url': image_url,
                    }
                )
                
                if track_created:
                    tracks_created += 1
                    logger.info(f"Created new track: {track_name} ({track_uuid})")
                    # Add to metadata fetch queue if enabled
                    if fetch_track_metadata:
                        track_uuids_for_metadata.append(track_uuid)
                else:
                    # Update existing track if needed
                    updated = False
                    if track_name and track.name != track_name:
                        track.name = track_name
                        updated = True
                    if track_slug and track.slug != track_slug:
                        track.slug = track_slug
                        updated = True
                    if credit_name and track.credit_name != credit_name:
                        track.credit_name = credit_name
                        updated = True
                    if image_url and track.image_url != image_url:
                        track.image_url = image_url
                        updated = True
                    
                    if updated:
                        track.save()
                        tracks_updated += 1
                        # Add to metadata fetch queue if enabled and metadata is stale
                        if fetch_track_metadata and _should_fetch_track_metadata(track):
                            track_uuids_for_metadata.append(track_uuid)
                
                # Extract position data - API uses different field names
                position = item_data.get('position', 0)
                old_position = item_data.get('oldPosition')  # API uses 'oldPosition' not 'previousPosition'
                position_evolution = item_data.get('positionEvolution')  # API uses 'positionEvolution' not 'positionChange'
                time_on_chart = item_data.get('timeOnChart')  # API uses 'timeOnChart' not 'weeksOnChart'
                
                # Extract entry date from API (format: "2025-06-22T12:00:00+00:00")
                entry_date_str = item_data.get('entryDate')
                entry_date = None
                if entry_date_str:
                    try:
                        from datetime import datetime
                        entry_date = datetime.fromisoformat(entry_date_str.replace('Z', '+00:00'))
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not parse entry date '{entry_date_str}': {e}")
                
                # Create ranking entry
                entry = ChartRankingEntry.objects.create(
                    ranking=ranking,
                    track=track,
                    position=position,
                    previous_position=old_position,
                    position_change=position_evolution,
                    weeks_on_chart=time_on_chart,
                    entry_date=entry_date,
                    api_data=item_data,
                )
                entries_created += 1
                logger.debug(f"Created ranking entry: Position {position} - {track_name}")
                
            except Exception as e:
                logger.error(f"Error processing ranking entry: {str(e)}")
                logger.error(f"Item data: {item_data}")
                continue
        
        # Log summary
        logger.info(f"Created {entries_created} ranking entries for ranking {ranking.id}")
        logger.info(f"Track stats - Created: {tracks_created}, Updated: {tracks_updated}")
        
        # Queue metadata fetch tasks if enabled
        if fetch_track_metadata and track_uuids_for_metadata:
            _queue_track_metadata_tasks(track_uuids_for_metadata)
        
        return {
            'created': tracks_created,
            'updated': tracks_updated,
            'entries_created': entries_created
        }
        
    except Exception as e:
        logger.error(f"Error processing ranking entries: {str(e)}")
        raise


def _should_fetch_track_metadata(track):
    """
    Determine if track metadata should be fetched
    """
    from datetime import timedelta
    from django.utils import timezone
    
    # Fetch if no metadata has been fetched
    if not track.metadata_fetched_at:
        return True
    
    # Fetch if metadata is older than 30 days
    cutoff_date = timezone.now() - timedelta(days=30)
    return track.metadata_fetched_at < cutoff_date


def _queue_track_metadata_tasks(track_uuids):
    """
    Queue track metadata fetch tasks
    """
    try:
        # Create a bulk metadata fetch task
        from .models import MetadataFetchTask
        
        task = MetadataFetchTask.objects.create(
            task_type='bulk_metadata',
            status='pending',
            track_uuids=track_uuids,
            total_tracks=len(track_uuids),
        )
        
        # Queue the bulk fetch task
        fetch_bulk_track_metadata.delay(task.id)
        
        logger.info(f"Queued metadata fetch for {len(track_uuids)} tracks")
        
    except Exception as e:
        logger.error(f"Error queuing track metadata tasks: {str(e)}")


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def fetch_track_audience_data(self, track_uuid, platforms=None):
    """
    Fetch audience data for a track from Soundcharts API
    This task is triggered when accessing the song audience view
    """
    try:
        logger.info(f"Starting audience data fetch for track {track_uuid}")
        
        # Get the track
        try:
            track = Track.objects.get(uuid=track_uuid)
        except Track.DoesNotExist:
            logger.error(f"Track with UUID {track_uuid} not found")
            return False
        
        service = SoundchartsService()
        
        # Get platforms to fetch audience data for
        if platforms is None:
            # Get all platforms that support audience data
            platforms = Platform.objects.filter(
                platform_type='audience'
            ).values_list('platform_identifier', flat=True)
        
        audience_data_fetched = 0
        
        for platform_identifier in platforms:
            try:
                logger.info(f"Fetching audience data for track {track_uuid} on platform {platform_identifier}")
                
                # Fetch audience data from API
                audience_data = service.get_song_audience_for_platform(track_uuid, platform_identifier)
                
                if audience_data:
                    # Process and store audience data
                    _process_audience_data(track, platform_identifier, audience_data)
                    audience_data_fetched += 1
                    logger.info(f"Successfully fetched audience data for track {track_uuid} on platform {platform_identifier}")
                else:
                    logger.warning(f"No audience data found for track {track_uuid} on platform {platform_identifier}")
                
            except Exception as e:
                logger.error(f"Error fetching audience data for track {track_uuid} on platform {platform_identifier}: {str(e)}")
                continue
        
        # Update track audience fetch timestamp
        track.audience_fetched_at = timezone.now()
        track.save()
        
        logger.info(f"Audience data fetch completed for track {track_uuid}. Platforms: {audience_data_fetched}")
        return True
        
    except Exception as e:
        logger.error(f"Error fetching audience data for track {track_uuid}: {str(e)}")
        
        # Retry if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying audience data fetch for track {track_uuid} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return False


def _process_audience_data(track, platform_identifier, audience_data):
    """
    Process and store audience data for a track
    """
    try:
        # Get the platform
        try:
            platform = Platform.objects.get(platform_identifier=platform_identifier)
        except Platform.DoesNotExist:
            logger.warning(f"Platform {platform_identifier} not found")
            return
        
        # Process audience data based on API response structure
        if isinstance(audience_data, list):
            # Handle list of audience data points
            for data_point in audience_data:
                _create_audience_timeseries_entry(track, platform, data_point)
        elif isinstance(audience_data, dict):
            # Handle single audience data point
            _create_audience_timeseries_entry(track, platform, audience_data)
        
    except Exception as e:
        logger.error(f"Error processing audience data for track {track.uuid}: {str(e)}")


def _create_audience_timeseries_entry(track, platform, data_point):
    """
    Create a TrackAudienceTimeSeries entry from API data
    """
    try:
        from datetime import datetime
        
        # Extract date and audience value from data point
        date_str = data_point.get('date') or data_point.get('timestamp')
        audience_value = data_point.get('audience') or data_point.get('value') or data_point.get('listeners')
        
        if not date_str or not audience_value:
            logger.warning(f"Incomplete audience data point: {data_point}")
            return
        
        # Parse date
        try:
            if isinstance(date_str, str):
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
                    try:
                        date = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    logger.warning(f"Could not parse date: {date_str}")
                    return
            else:
                date = date_str
        except Exception as e:
            logger.warning(f"Error parsing date {date_str}: {str(e)}")
            return
        
        # Create or update audience timeseries entry
        audience_entry, created = TrackAudienceTimeSeries.objects.get_or_create(
            track=track,
            platform=platform,
            date=date,
            defaults={
                'audience_value': int(audience_value),
                'api_data': data_point,
            }
        )
        
        if not created:
            # Update existing entry if audience value has changed
            if audience_entry.audience_value != int(audience_value):
                audience_entry.audience_value = int(audience_value)
                audience_entry.api_data = data_point
                audience_entry.save()
        
    except Exception as e:
        logger.error(f"Error creating audience timeseries entry: {str(e)}")


# ============================================
# CASCADE DATA FLOW TASKS
# ============================================

@shared_task(bind=True)
def sync_artists_after_track_metadata(self, track_uuid):
    """
    Cascade: After track metadata is fetched, extract and sync artist metadata
    Called automatically after track metadata fetch completes
    """
    try:
        logger.info(f"Processing artist cascade for track {track_uuid}")
        
        # Get the track
        try:
            track = Track.objects.get(uuid=track_uuid)
        except Track.DoesNotExist:
            logger.error(f"Track {track_uuid} not found")
            return False
        
        # Check if track has artists
        if not track.artists.exists():
            logger.info(f"Track {track_uuid} has no artists, skipping cascade")
            return True
        
        # Get all artists for this track
        artists = track.artists.all()
        logger.info(f"Track {track.name} has {artists.count()} artist(s)")
        
        # Check which artists need metadata updates
        artists_to_sync = []
        for artist in artists:
            if _should_fetch_artist_metadata(artist):
                artists_to_sync.append(artist.uuid)
        
        if artists_to_sync:
            logger.info(f"Queueing metadata fetch for {len(artists_to_sync)} artist(s)")
            sync_artist_metadata_bulk.delay(artists_to_sync)
        else:
            logger.info("All artists already have up-to-date metadata")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in artist cascade for track {track_uuid}: {str(e)}")
        return False


@shared_task(bind=True)
def sync_artist_metadata_bulk(self, artist_uuids):
    """
    Fetch metadata for multiple artists in bulk
    """
    try:
        logger.info(f"Starting bulk artist metadata fetch for {len(artist_uuids)} artists")
        
        service = SoundchartsService()
        success_count = 0
        failed_count = 0
        
        for artist_uuid in artist_uuids:
            try:
                # Get the artist
                artist = Artist.objects.get(uuid=artist_uuid)
                
                # Fetch metadata
                metadata = service.get_artist_metadata(artist_uuid)
                
                if metadata and "object" in metadata:
                    artist_data = metadata["object"]
                    
                    # Update artist with metadata
                    if "name" in artist_data:
                        artist.name = artist_data["name"]
                    if "slug" in artist_data:
                        artist.slug = artist_data["slug"]
                    if "appUrl" in artist_data:
                        artist.appUrl = artist_data["appUrl"]
                    if "imageUrl" in artist_data:
                        artist.imageUrl = artist_data["imageUrl"]
                    if "biography" in artist_data:
                        artist.biography = artist_data["biography"]
                    if "isni" in artist_data:
                        artist.isni = artist_data["isni"]
                    if "ipi" in artist_data:
                        artist.ipi = artist_data["ipi"]
                    if "gender" in artist_data:
                        artist.gender = artist_data["gender"]
                    if "type" in artist_data:
                        artist.type = artist_data["type"]
                    if "careerStage" in artist_data:
                        artist.careerStage = artist_data["careerStage"]
                    if "cityName" in artist_data:
                        artist.cityName = artist_data["cityName"]
                    if "countryCode" in artist_data:
                        artist.countryCode = artist_data["countryCode"]
                    
                    # Update metadata fetch timestamp
                    artist.metadata_fetched_at = timezone.now()
                    artist.save()
                    
                    success_count += 1
                    logger.debug(f"Successfully updated artist {artist.name}")
                    
                    # After artist metadata is fetched, cascade to audience data
                    sync_artist_audience.delay(artist_uuid)
                else:
                    failed_count += 1
                    logger.warning(f"Failed to fetch metadata for artist {artist_uuid}")
                    
            except Artist.DoesNotExist:
                failed_count += 1
                logger.warning(f"Artist {artist_uuid} not found")
            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing artist {artist_uuid}: {str(e)}")
        
        logger.info(f"Bulk artist metadata fetch complete. Success: {success_count}, Failed: {failed_count}")
        return True
        
    except Exception as e:
        logger.error(f"Error in bulk artist metadata fetch: {str(e)}")
        return False


@shared_task(bind=True)
def sync_track_audience(self, track_uuid, platforms=None):
    """
    Cascade: Fetch audience data for a track after metadata is fetched
    Platforms to fetch: spotify, youtube, shazam, airplay
    """
    try:
        logger.info(f"Starting audience fetch for track {track_uuid}")
        
        # Get the track
        try:
            track = Track.objects.get(uuid=track_uuid)
        except Track.DoesNotExist:
            logger.error(f"Track {track_uuid} not found")
            return False
        
        # Default platforms if not specified
        if platforms is None:
            platforms = ['spotify', 'youtube', 'shazam', 'airplay']
        
        # Fetch audience data for each platform
        from .audience_processor import AudienceDataProcessor
        processor = AudienceDataProcessor()
        
        for platform_slug in platforms:
            try:
                logger.info(f"Fetching audience data for track {track.name} on {platform_slug}")
                
                result = processor.process_and_store_audience_data(
                    track.uuid,
                    platform_slug,
                    force_refresh=False
                )
                
                if result.get('success'):
                    logger.info(f"Successfully fetched audience data for track {track.name} on {platform_slug}")
                else:
                    logger.warning(f"Failed to fetch audience data for track {track.name} on {platform_slug}: {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error fetching audience data for track {track.name} on {platform_slug}: {str(e)}")
                continue
        
        # Update track audience fetch timestamp
        track.audience_fetched_at = timezone.now()
        track.save()
        
        logger.info(f"Completed audience fetch for track {track.uuid}")
        return True
        
    except Exception as e:
        logger.error(f"Error in track audience cascade for track {track_uuid}: {str(e)}")
        return False


@shared_task(bind=True)
def sync_artist_audience(self, artist_uuid, platforms=None):
    """
    Cascade: Fetch audience data for an artist after metadata is fetched
    Platforms to fetch: spotify, youtube, instagram, tiktok
    """
    try:
        logger.info(f"Starting audience fetch for artist {artist_uuid}")
        
        # Get the artist
        try:
            artist = Artist.objects.get(uuid=artist_uuid)
        except Artist.DoesNotExist:
            logger.error(f"Artist {artist_uuid} not found")
            return False
        
        # Default platforms if not specified
        if platforms is None:
            platforms = ['spotify', 'youtube', 'instagram', 'tiktok']
        
        # Fetch audience data for each platform
        service = SoundchartsService()
        
        for platform_slug in platforms:
            try:
                logger.info(f"Fetching audience data for artist {artist.name} on {platform_slug}")
                
                audience_data = service.get_artist_audience_for_platform(
                    artist.uuid,
                    platform=platform_slug
                )
                
                if audience_data and "items" in audience_data:
                    # Process and store audience data
                    records_created, records_updated = _process_artist_audience_timeseries(
                        artist, platform_slug, audience_data
                    )
                    logger.info(f"Stored audience data for artist {artist.name} on {platform_slug}: {records_created} created, {records_updated} updated")
                else:
                    logger.warning(f"No audience data returned for artist {artist.name} on {platform_slug}")
                    
            except Exception as e:
                logger.error(f"Error fetching audience data for artist {artist.name} on {platform_slug}: {str(e)}")
                continue
        
        # Update artist audience fetch timestamp
        artist.audience_fetched_at = timezone.now()
        artist.save()
        
        logger.info(f"Completed audience fetch for artist {artist.uuid}")
        return True
        
    except Exception as e:
        logger.error(f"Error in artist audience cascade for artist {artist_uuid}: {str(e)}")
        return False


def _should_fetch_artist_metadata(artist):
    """
    Determine if artist metadata should be fetched
    """
    from datetime import timedelta
    
    # Fetch if no metadata has been fetched
    if not artist.metadata_fetched_at:
        return True
    
    # Fetch if metadata is older than 30 days
    cutoff_date = timezone.now() - timedelta(days=30)
    return artist.metadata_fetched_at < cutoff_date


def _process_artist_audience_timeseries(artist, platform_slug, audience_data):
    """
    Process and store artist audience time series data
    Returns (records_created, records_updated)
    """
    from .models import Platform, ArtistAudienceTimeSeries
    from datetime import datetime
    
    try:
        # Get the platform
        platform = Platform.objects.filter(slug=platform_slug).first()
        if not platform:
            logger.warning(f"Platform {platform_slug} not found")
            return 0, 0
        
        items = audience_data.get('items', [])
        
        if not items:
            return 0, 0
        
        records_created = 0
        records_updated = 0
        
        for item in items:
            item_date_str = item.get('date')
            if not item_date_str:
                continue
            
            try:
                # Parse date (format: YYYY-MM-DDTHH:MM:SS+00:00 or YYYY-MM-DD)
                if 'T' in item_date_str:
                    item_date = datetime.fromisoformat(item_date_str.replace('Z', '+00:00')).date()
                else:
                    item_date = datetime.strptime(item_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse item date '{item_date_str}': {e}")
                continue
            
            # Get the metric value (followerCount, likeCount, or viewCount)
            audience_value = (item.get('followerCount') or 
                            item.get('likeCount') or 
                            item.get('viewCount'))
            if audience_value is None:
                continue
            
            # Create or update ArtistAudienceTimeSeries record
            ts_record, created = ArtistAudienceTimeSeries.objects.update_or_create(
                artist=artist,
                platform=platform,
                date=item_date,
                defaults={
                    'audience_value': audience_value,
                    'platform_identifier': '',  # Not provided in this endpoint
                    'api_data': item,
                    'fetched_at': timezone.now()
                }
            )
            
            if created:
                records_created += 1
            else:
                records_updated += 1
        
        return records_created, records_updated
        
    except Exception as e:
        logger.error(f"Error processing artist audience timeseries: {e}")
        return 0, 0
