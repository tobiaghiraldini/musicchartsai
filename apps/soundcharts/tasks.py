import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from .models import Track, MetadataFetchTask, ChartSyncSchedule, ChartSyncExecution, Chart, ChartRanking, ChartRankingEntry
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
    Returns a list of (date, None) tuples representing dates to fetch.
    Historical data is limited to the last 3 days only to prevent excessive API calls.
    """
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    now = timezone.now()
    missing_periods = []
    
    # Get existing rankings dates for this chart
    existing_ranking_dates = set(
        ChartRanking.objects.filter(chart=chart)
        .values_list('ranking_date__date', flat=True)
    )
    
    # Determine frequency interval
    if chart.frequency.lower() == 'daily':
        interval = timedelta(days=1)
        # For daily charts, check last 3 days
        days_to_check = 3
    elif chart.frequency.lower() == 'weekly':
        interval = timedelta(weeks=1)
        # For weekly charts, check last 3 weeks
        days_to_check = 21 if sync_historical_data else 7
    elif chart.frequency.lower() == 'monthly':
        interval = timedelta(days=30)
        # For monthly charts, check last 3 months
        days_to_check = 90 if sync_historical_data else 30
    else:
        # Default to weekly
        interval = timedelta(weeks=1)
        days_to_check = 21 if sync_historical_data else 7
    
    # Always check today's ranking
    today = now.date()
    if today not in existing_ranking_dates:
        missing_periods.append((now, None))
        logger.info(f"Will fetch ranking for {chart.name} for today: {today}")
    
    # If sync_historical_data is enabled, check for missing historical data
    if sync_historical_data:
        check_date = now - timedelta(days=1)  # Start from yesterday
        end_date = now - timedelta(days=days_to_check)
        
        while check_date >= end_date:
            if check_date.date() not in existing_ranking_dates:
                missing_periods.append((check_date, None))
                logger.info(f"Will fetch ranking for {chart.name} for date: {check_date.date()}")
            
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
    Only creates a new ranking if one doesn't exist for the given date.
    """
    try:
        # Normalize ranking_date to just the date portion for comparison
        from django.utils import timezone
        if isinstance(ranking_date, str):
            ranking_date = timezone.datetime.fromisoformat(ranking_date)
        
        ranking_date_normalized = ranking_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Check if a ranking already exists for this chart and date
        existing_ranking = ChartRanking.objects.filter(
            chart=chart,
            ranking_date__date=ranking_date_normalized.date()
        ).first()
        
        if existing_ranking:
            # Ranking already exists for this date, skip creation but update if needed
            logger.info(f"Ranking already exists for {chart.name} on {ranking_date_normalized.date()}, skipping...")
            updated = False
            if existing_ranking.total_entries != len(rankings_data.get('items', [])):
                existing_ranking.total_entries = len(rankings_data.get('items', []))
                updated = True
            if rankings_data.get('version') and existing_ranking.api_version != rankings_data['version']:
                existing_ranking.api_version = rankings_data['version']
                updated = True
            if updated:
                existing_ranking.save()
                logger.info(f"Updated existing ranking for {chart.name} on {ranking_date_normalized.date()}")
            return existing_ranking, False
        
        # Create new ranking
        ranking = ChartRanking.objects.create(
            chart=chart,
            ranking_date=ranking_date_normalized,
            total_entries=len(rankings_data.get('items', [])),
            api_version=rankings_data.get('version', 'v2.14'),
        )
        logger.info(f"Created new ranking for {chart.name} on {ranking_date_normalized.date()}")
        
        return ranking, True
        
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
                
                # Create ranking entry
                entry = ChartRankingEntry.objects.create(
                    ranking=ranking,
                    track=track,
                    position=position,
                    previous_position=old_position,
                    position_change=position_evolution,
                    weeks_on_chart=time_on_chart,
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
