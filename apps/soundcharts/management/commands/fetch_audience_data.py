from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.soundcharts.audience_processor import AudienceDataProcessor
from apps.soundcharts.models import Track, Platform
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch and process SoundCharts audience time-series data for tracks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--track-uuid',
            type=str,
            help='Specific track UUID to process'
        )
        parser.add_argument(
            '--platform',
            type=str,
            help='Specific platform slug to process (e.g., spotify, apple_music)'
        )
        parser.add_argument(
            '--force-refresh',
            action='store_true',
            help='Force refresh of existing data'
        )
        parser.add_argument(
            '--all-tracks',
            action='store_true',
            help='Process all tracks in the database'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Limit number of tracks to process (default: 100)'
        )

    def handle(self, *args, **options):
        processor = AudienceDataProcessor()
        
        if options['track_uuid']:
            # Process specific track
            self._process_single_track(processor, options)
        elif options['all_tracks']:
            # Process all tracks
            self._process_all_tracks(processor, options)
        else:
            # Process tracks that haven't been updated recently
            self._process_stale_tracks(processor, options)

    def _process_single_track(self, processor, options):
        """Process a single track"""
        track_uuid = options['track_uuid']
        platform = options['platform'] or 'spotify'
        force_refresh = options['force_refresh']
        
        try:
            track = Track.objects.get(uuid=track_uuid)
            self.stdout.write(f"Processing track: {track.name} ({track_uuid}) on {platform}")
            
            result = processor.process_and_store_audience_data(
                track_uuid, 
                platform, 
                force_refresh
            )
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully processed {track.name} on {platform}: "
                        f"{result['records_created']} created, "
                        f"{result['records_updated']} updated"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to process {track.name} on {platform}: {result['error']}"
                    )
                )
                
        except Track.DoesNotExist:
            raise CommandError(f"Track with UUID {track_uuid} not found")
        except Exception as e:
            raise CommandError(f"Error processing track {track_uuid}: {e}")

    def _process_all_tracks(self, processor, options):
        """Process all tracks in the database"""
        limit = options['limit']
        platform = options['platform'] or 'spotify'
        force_refresh = options['force_refresh']
        
        tracks = Track.objects.all()[:limit]
        total_tracks = tracks.count()
        
        self.stdout.write(f"Processing {total_tracks} tracks on {platform}")
        
        track_platform_pairs = [(track.uuid, platform) for track in tracks]
        
        result = processor.bulk_process_audience_data(track_platform_pairs, force_refresh)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Bulk processing completed: "
                f"{result['successful']} successful, "
                f"{result['failed']} failed, "
                f"{result['total_records_created']} records created, "
                f"{result['total_records_updated']} records updated"
            )
        )
        
        if result['errors']:
            self.stdout.write(self.style.WARNING("Errors encountered:"))
            for error in result['errors']:
                self.stdout.write(f"  {error['track_uuid']} on {error['platform_slug']}: {error['error']}")

    def _process_stale_tracks(self, processor, options):
        """Process tracks that haven't been updated recently"""
        limit = options['limit']
        platform = options['platform'] or 'spotify'
        
        # Get tracks that haven't been updated in the last 7 days
        week_ago = timezone.now() - timezone.timedelta(days=7)
        
        stale_tracks = Track.objects.filter(
            audience_fetched_at__lt=week_ago
        ).exclude(
            audience_fetched_at__isnull=True
        )[:limit]
        
        total_stale = stale_tracks.count()
        
        if total_stale == 0:
            self.stdout.write("No stale tracks found. All tracks are up to date.")
            return
        
        self.stdout.write(f"Found {total_stale} stale tracks to update on {platform}")
        
        track_platform_pairs = [(track.uuid, platform) for track in stale_tracks]
        
        result = processor.bulk_process_audience_data(track_platform_pairs, force_refresh=False)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Stale tracks processing completed: "
                f"{result['successful']} successful, "
                f"{result['failed']} failed, "
                f"{result['total_records_created']} records created, "
                f"{result['total_records_updated']} records updated"
            )
        )
