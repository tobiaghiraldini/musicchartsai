"""
Test the platform creation fix to ensure no duplicate key errors
"""
from django.core.management.base import BaseCommand
from apps.acrcloud.models import Analysis
from apps.acrcloud.service import ACRCloudMetadataProcessor
from apps.soundcharts.models import Platform
from django.core.files.base import ContentFile


class Command(BaseCommand):
    help = 'Test platform creation robustness'

    def add_arguments(self, parser):
        parser.add_argument('--create-test-platforms', action='store_true', help='Create test platforms first')

    def handle(self, *args, **options):
        # Create test platforms if requested
        if options['create_test_platforms']:
            self.stdout.write("Creating test platforms...")
            test_platforms = ['spotify', 'deezer', 'youtube']
            
            for platform_name in test_platforms:
                platform, created = Platform.objects.get_or_create(
                    slug=platform_name,
                    defaults={
                        'name': platform_name.title(),
                        'platform_identifier': platform_name,
                        'platform_type': 'streaming'
                    }
                )
                if created:
                    self.stdout.write(f"  Created: {platform_name}")
                else:
                    self.stdout.write(f"  Already exists: {platform_name}")
        
        # Get or create test analysis
        analysis = Analysis.objects.filter(status='analyzed').first()
        if not analysis:
            self.stdout.write(self.style.ERROR("No analyzed analysis found. Run test_webhook_processing first."))
            return
        
        self.stdout.write(f"Testing with analysis: {analysis.id}")
        
        # Test external metadata with platforms that might already exist
        test_metadata = {
            'spotify': {
                'track': {'id': 'test_spotify_track'},
                'artists': [{'id': 'test_spotify_artist'}],
                'album': {'id': 'test_spotify_album'}
            },
            'deezer': {
                'track': {'id': 'test_deezer_track'},
                'artists': [{'id': 'test_deezer_artist'}],
                'album': {'id': 'test_deezer_album'}
            },
            'youtube': {
                'vid': 'test_youtube_video'
            }
        }
        
        # Test the platform creation
        processor = ACRCloudMetadataProcessor()
        
        try:
            # Get the track from the analysis
            track = analysis.track_matches.first().track
            if not track:
                self.stdout.write(self.style.ERROR("No track found in analysis"))
                return
            
            self.stdout.write(f"Testing platform creation for track: {track.name}")
            
            # Test platform mapping creation
            processor._create_platform_mappings(track, test_metadata)
            
            self.stdout.write(self.style.SUCCESS("✅ Platform creation test passed - no duplicate key errors"))
            
            # Show created platforms
            platforms = Platform.objects.filter(slug__in=['spotify', 'deezer', 'youtube'])
            self.stdout.write(f"Platforms in database: {list(platforms.values_list('slug', flat=True))}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Platform creation test failed: {str(e)}"))
            import traceback
            traceback.print_exc()
