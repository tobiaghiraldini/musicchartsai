"""
Management command to test mock analysis
"""
from django.core.management.base import BaseCommand
from apps.acrcloud.models import Song
from apps.acrcloud.mock_tasks import mock_analyze_song_task


class Command(BaseCommand):
    help = 'Test mock analysis on uploaded songs'
    
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
        if options['song_id']:
            # Analyze specific song
            song_id = options['song_id']
            try:
                song = Song.objects.get(id=song_id)
                self.stdout.write(f"Starting mock analysis for song: {song}")
                result = mock_analyze_song_task.delay(song_id)
                self.stdout.write(
                    self.style.SUCCESS(f'Mock analysis queued with task ID: {result.id}')
                )
            except Song.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Song with ID {song_id} not found')
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
            
            for song in uploaded_songs:
                self.stdout.write(f"Starting mock analysis for: {song}")
                result = mock_analyze_song_task.delay(str(song.id))
                self.stdout.write(f"  - Task ID: {result.id}")
            
            self.stdout.write(
                self.style.SUCCESS(f'Queued {uploaded_songs.count()} mock analysis tasks')
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
            self.stdout.write("  python manage.py test_mock_analysis --song-id <ID>")
            self.stdout.write("  python manage.py test_mock_analysis --all")
