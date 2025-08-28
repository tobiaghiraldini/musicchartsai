from django.core.management.base import BaseCommand
from django.utils import timezone
from soundcharts.models import Track, MetadataFetchTask
from soundcharts.tasks import fetch_track_metadata, fetch_bulk_track_metadata, fetch_all_tracks_metadata


class Command(BaseCommand):
    help = 'Fetch track metadata from Soundcharts API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--track-uuid',
            type=str,
            help='UUID of a specific track to fetch metadata for'
        )
        parser.add_argument(
            '--bulk',
            action='store_true',
            help='Create a bulk metadata fetch task for all tracks'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Fetch metadata for all tracks that need it'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it'
        )

    def handle(self, *args, **options):
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No actual changes will be made'))
        
        if options['track_uuid']:
            self.fetch_single_track(options['track_uuid'], options['dry_run'])
        elif options['bulk']:
            self.create_bulk_task(options['dry_run'])
        elif options['all']:
            self.fetch_all_tracks(options['dry_run'])
        else:
            self.stdout.write(self.style.ERROR('Please specify one of: --track-uuid, --bulk, or --all'))
            self.stdout.write('Use --help for more information')

    def fetch_single_track(self, track_uuid, dry_run):
        """Fetch metadata for a single track"""
        try:
            track = Track.objects.get(uuid=track_uuid)
            self.stdout.write(f"Found track: {track.name} (UUID: {track_uuid})")
            
            if dry_run:
                self.stdout.write(f"Would fetch metadata for track: {track.name}")
                return
            
            # Use Celery task
            task = fetch_track_metadata.delay(track_uuid)
            self.stdout.write(
                self.style.SUCCESS(f"Metadata fetch queued for track '{track.name}' (Task ID: {task.id})")
            )
            
        except Track.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Track with UUID {track_uuid} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))

    def create_bulk_task(self, dry_run):
        """Create a bulk metadata fetch task"""
        tracks = Track.objects.all()
        track_uuids = list(tracks.values_list('uuid', flat=True))
        
        if not track_uuids:
            self.stdout.write(self.style.WARNING("No tracks found in database"))
            return
        
        self.stdout.write(f"Found {len(track_uuids)} tracks")
        
        if dry_run:
            self.stdout.write(f"Would create bulk metadata fetch task for {len(track_uuids)} tracks")
            return
        
        try:
            # Create the task record
            task = MetadataFetchTask.objects.create(
                task_type='bulk_metadata',
                status='pending',
                track_uuids=track_uuids,
                total_tracks=len(track_uuids)
            )
            
            # Start the bulk fetch task
            fetch_bulk_track_metadata.delay(task.id)
            
            self.stdout.write(
                self.style.SUCCESS(f"Created bulk metadata fetch task (ID: {task.id}) for {len(track_uuids)} tracks")
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating bulk metadata task: {str(e)}"))

    def fetch_all_tracks(self, dry_run):
        """Fetch metadata for all tracks that need it"""
        if dry_run:
            self.stdout.write("Would fetch metadata for all tracks that need it")
            return
        
        try:
            task = fetch_all_tracks_metadata.delay()
            self.stdout.write(
                self.style.SUCCESS(f"Bulk metadata fetch task queued (Task ID: {task.id})")
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
