"""
Test webhook processing with real webhook data
"""
import json
from django.core.management.base import BaseCommand
from apps.acrcloud.models import Analysis, Song
from apps.acrcloud.service import ACRCloudMetadataProcessor
from django.core.files.base import ContentFile


class Command(BaseCommand):
    help = 'Test webhook processing with real webhook data'

    def add_arguments(self, parser):
        parser.add_argument('--song-id', type=str, help='Song ID to test with')
        parser.add_argument('--create-test-song', action='store_true', help='Create a test song')

    def handle(self, *args, **options):
        # Load webhook data from file
        webhook_file = 'apps/acrcloud/webhook.json'
        
        try:
            with open(webhook_file, 'r') as f:
                webhook_content = f.read()
                # Extract Python dict from the file content
                dict_start = webhook_content.find('Webhook payload: ') + len('Webhook payload: ')
                dict_content = webhook_content[dict_start:].strip()
                # Use eval to parse Python dict (safe since it's our own data)
                webhook_data = eval(dict_content)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to load webhook data: {e}"))
            return

        self.stdout.write(f"Loaded webhook data with keys: {list(webhook_data.keys())}")
        
        # Get or create test song
        if options['create_test_song']:
            song = Song.objects.create(
                user_id=1,
                title='Test Webhook Song',
                artist='Test Artist',
                original_filename='test_webhook.mp3',
                file_size=1024,
                status='uploaded'
            )
            song.audio_file.save('test_webhook.mp3', ContentFile(b'fake audio data'))
            self.stdout.write(f"Created test song: {song.id}")
        elif options['song_id']:
            try:
                song = Song.objects.get(id=options['song_id'])
                self.stdout.write(f"Using existing song: {song.id} - {song.title}")
            except Song.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Song {options['song_id']} not found"))
                return
        else:
            # Use the most recent song
            song = Song.objects.filter(status='uploaded').first()
            if not song:
                self.stdout.write(self.style.ERROR("No uploaded songs found. Use --create-test-song"))
                return
            self.stdout.write(f"Using most recent song: {song.id} - {song.title}")

        # Create analysis record
        analysis = Analysis.objects.create(
            song=song,
            analysis_type='full',
            status='processing',
            acrcloud_file_id=webhook_data.get('file_id', 'test-file-id'),
            raw_response={'webhook_data': webhook_data}
        )
        
        self.stdout.write(f"Created analysis: {analysis.id}")

        # Process webhook data
        processor = ACRCloudMetadataProcessor()
        
        try:
            processor.process_webhook_results(analysis, webhook_data)
            self.stdout.write(self.style.SUCCESS("Webhook processing completed successfully"))
            
            # Show results
            matches = analysis.track_matches.all()
            self.stdout.write(f"Created {matches.count()} track matches:")
            
            for match in matches:
                self.stdout.write(f"  - {match.get_match_type_display()}: {match.acrcloud_id} (Score: {match.score})")
                
                # Show pattern matching data
                if 'pattern_matching' in match.raw_data:
                    pattern = match.raw_data['pattern_matching']
                    self.stdout.write(f"    Pattern matching: offset={pattern.get('offset')}, duration={pattern.get('played_duration')}")
                    self.stdout.write(f"    Score: {pattern.get('score')}, Similarity: {pattern.get('similarity')}")
                    self.stdout.write(f"    Risk: {pattern.get('risk')}, Match Type: {pattern.get('match_type')}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Webhook processing failed: {e}"))
            import traceback
            traceback.print_exc()
