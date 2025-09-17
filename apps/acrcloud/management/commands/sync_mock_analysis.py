"""
Management command to run synchronous mock analysis (no Celery needed)
"""
from django.core.management.base import BaseCommand
from apps.acrcloud.models import Song
from apps.acrcloud.mock_service import MockACRCloudService


class Command(BaseCommand):
    help = 'Run synchronous mock analysis on uploaded songs (no Celery needed)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--song-id',
            type=str,
            help='Specific song ID to analyze',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Analyze all uploaded songs',
        )
    
    def handle(self, *args, **options):
        service = MockACRCloudService()
        
        if options['song_id']:
            # Analyze specific song
            song_id = options['song_id']
            try:
                song = Song.objects.get(id=song_id)
                self.stdout.write(f"Starting synchronous mock analysis for song: {song}")
                
                result = service.analyze_song(song_id)
                
                if result['success']:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Analysis completed successfully!')
                    )
                    self.stdout.write(f"Analysis ID: {result['analysis_id']}")
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Analysis failed: {result.get("error")}')
                    )
                    
            except Song.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Song with ID {song_id} not found')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error during analysis: {str(e)}')
                )
        
        elif options['all']:
            # Analyze all uploaded songs
            uploaded_songs = Song.objects.filter(status='uploaded')
            if not uploaded_songs.exists():
                self.stdout.write(
                    self.style.WARNING('No uploaded songs found')
                )
                return
            
            self.stdout.write(f"Found {uploaded_songs.count()} uploaded songs")
            success_count = 0
            
            for song in uploaded_songs:
                self.stdout.write(f"\nProcessing: {song}")
                try:
                    result = service.analyze_song(str(song.id))
                    if result['success']:
                        self.stdout.write(f"  ✅ Success - Analysis ID: {result['analysis_id']}")
                        success_count += 1
                    else:
                        self.stdout.write(f"  ❌ Failed: {result.get('error')}")
                except Exception as e:
                    self.stdout.write(f"  ❌ Error: {str(e)}")
            
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 Completed {success_count}/{uploaded_songs.count()} analyses')
            )
        
        else:
            # Show available songs
            songs = Song.objects.all().order_by('-created_at')[:10]
            if not songs.exists():
                self.stdout.write(
                    self.style.WARNING('No songs found. Upload a song first.')
                )
                return
            
            self.stdout.write("Recent songs:")
            for song in songs:
                status_color = {
                    'uploaded': self.style.HTTP_INFO,
                    'processing': self.style.WARNING,
                    'analyzed': self.style.SUCCESS,
                    'failed': self.style.ERROR
                }.get(song.status, self.style.HTTP_INFO)
                
                self.stdout.write(f"  {song.id} - {song} - {status_color(song.status)}")
            
            self.stdout.write("\nUsage:")
            self.stdout.write("  python manage.py sync_mock_analysis --song-id <ID>")
            self.stdout.write("  python manage.py sync_mock_analysis --all")
