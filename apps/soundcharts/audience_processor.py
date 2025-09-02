from datetime import datetime
from django.utils import timezone
from django.db import transaction
from .models import Track, Platform, TrackAudienceTimeSeries
from .service import SoundchartsService
import logging

logger = logging.getLogger(__name__)


class AudienceDataProcessor:
    """
    Processes and stores SoundCharts audience time-series data
    """
    
    def __init__(self):
        self.service = SoundchartsService()
    
    def process_and_store_audience_data(self, track_uuid, platform_slug, force_refresh=False):
        """
        Fetch, process, and store audience time-series data for a track on a specific platform
        
        Args:
            track_uuid (str): SoundCharts track UUID
            platform_slug (str): Platform slug (e.g., 'spotify', 'apple_music')
            force_refresh (bool): If True, refresh existing data
            
        Returns:
            dict: Processing results with counts and status
        """
        try:
            # Get or create platform
            platform, created = Platform.objects.get_or_create(
                slug=platform_slug,
                defaults={
                    'name': platform_slug.title(),
                    'platform_type': 'streaming',
                    'audience_metric_name': 'Listeners',
                    'platform_identifier': platform_slug
                }
            )
            
            # Get track
            try:
                track = Track.objects.get(uuid=track_uuid)
            except Track.DoesNotExist:
                logger.error(f"Track with UUID {track_uuid} not found")
                return {
                    'success': False,
                    'error': f"Track with UUID {track_uuid} not found",
                    'records_created': 0,
                    'records_updated': 0
                }
            
            # Check if we need to refresh data
            if not force_refresh:
                latest_record = TrackAudienceTimeSeries.objects.filter(
                    track=track, 
                    platform=platform
                ).first()
                
                if latest_record and (timezone.now() - latest_record.fetched_at).days < 1:
                    logger.info(f"Recent data exists for {track.name} on {platform.name}, skipping fetch")
                    return {
                        'success': True,
                        'message': 'Recent data exists, skipping fetch',
                        'records_created': 0,
                        'records_updated': 0
                    }
            
            # Fetch data from API
            api_data = self.service.get_song_audience_for_platform(track_uuid, platform_slug)
            if not api_data:
                logger.error(f"Failed to fetch audience data for {track_uuid} on {platform_slug}")
                return {
                    'success': False,
                    'error': 'Failed to fetch data from API',
                    'records_created': 0,
                    'records_updated': 0
                }
            
            # Process and store the data
            result = self._process_api_response(track, platform, api_data)
            
            # Update track's audience fetched timestamp
            track.audience_fetched_at = timezone.now()
            track.save(update_fields=['audience_fetched_at'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing audience data for {track_uuid} on {platform_slug}: {e}")
            return {
                'success': False,
                'error': str(e),
                'records_created': 0,
                'records_updated': 0
            }
    
    def _process_api_response(self, track, platform, api_data):
        """
        Process the API response and store time-series data
        
        Args:
            track (Track): Track instance
            platform (Platform): Platform instance
            api_data (dict): Raw API response
            
        Returns:
            dict: Processing results
        """
        records_created = 0
        records_updated = 0
        
        try:
            with transaction.atomic():
                # Extract items from API response
                items = api_data.get('items', [])
                
                for item in items:
                    date_str = item.get('date')
                    plots = item.get('plots', [])
                    
                    if not date_str or not plots:
                        continue
                    
                    # Parse date (handle both ISO format and other formats)
                    try:
                        if 'T' in date_str:
                            # ISO format: "2025-08-28T00:00:00+00:00"
                            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                        else:
                            # Simple date format: "2025-08-28"
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError as e:
                        logger.warning(f"Could not parse date {date_str}: {e}")
                        continue
                    
                    # Process each plot (platform-specific data)
                    for plot in plots:
                        platform_identifier = plot.get('identifier', '')
                        audience_value = plot.get('value')
                        
                        if audience_value is None:
                            continue
                        
                        # Create or update the time-series record
                        record, created = TrackAudienceTimeSeries.objects.update_or_create(
                            track=track,
                            platform=platform,
                            date=date_obj,
                            defaults={
                                'audience_value': audience_value,
                                'platform_identifier': platform_identifier,
                                'api_data': item,  # Store the raw item data
                                'fetched_at': timezone.now()
                            }
                        )
                        
                        if created:
                            records_created += 1
                        else:
                            records_updated += 1
                
                logger.info(f"Processed {len(items)} items for {track.name} on {platform.name}")
                
        except Exception as e:
            logger.error(f"Error in transaction for {track.name} on {platform.name}: {e}")
            raise
        
        return {
            'success': True,
            'records_created': records_created,
            'records_updated': records_updated,
            'total_items_processed': len(api_data.get('items', []))
        }
    
    def bulk_process_audience_data(self, track_platform_pairs, force_refresh=False):
        """
        Process audience data for multiple track-platform combinations
        
        Args:
            track_platform_pairs (list): List of tuples (track_uuid, platform_slug)
            force_refresh (bool): If True, refresh existing data
            
        Returns:
            dict: Bulk processing results
        """
        results = {
            'total_pairs': len(track_platform_pairs),
            'successful': 0,
            'failed': 0,
            'total_records_created': 0,
            'total_records_updated': 0,
            'errors': []
        }
        
        for track_uuid, platform_slug in track_platform_pairs:
            try:
                result = self.process_and_store_audience_data(track_uuid, platform_slug, force_refresh)
                
                if result['success']:
                    results['successful'] += 1
                    results['total_records_created'] += result['records_created']
                    results['total_records_updated'] += result['records_updated']
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'track_uuid': track_uuid,
                        'platform_slug': platform_slug,
                        'error': result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'track_uuid': track_uuid,
                    'platform_slug': platform_slug,
                    'error': str(e)
                })
        
        return results
