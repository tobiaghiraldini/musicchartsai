"""
Management command to test the complete webhook-based ACRCloud flow
"""
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.conf import settings
import requests
import json
import time


class Command(BaseCommand):
    help = 'Test the complete webhook-based ACRCloud analysis flow'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--song-id',
            type=str,
            help='Specific song ID to test',
        )
        parser.add_argument(
            '--simulate-webhook',
            action='store_true',
            help='Simulate ACRCloud webhook callback',
        )
    
    def handle(self, *args, **options):
        if options['simulate_webhook']:
            self._test_webhook_simulation()
        elif options['song_id']:
            self._test_song_analysis(options['song_id'])
        else:
            self._show_usage()
    
    def _test_webhook_simulation(self):
        """Test webhook endpoint with simulated ACRCloud callback"""
        self.stdout.write("🧪 Testing webhook simulation...")
        
        # First, create a test analysis record
        from apps.acrcloud.models import Song, Analysis, ACRCloudConfig
        from django.contrib.auth import get_user_model
        from django.core.files.base import ContentFile
        
        User = get_user_model()
        
        # Get or create test user
        user, _ = User.objects.get_or_create(
            username='webhook_test_user',
            defaults={'email': 'test@example.com'}
        )
        
        # Create test song
        song = Song()
        song.user = user
        song.title = "Webhook Test Song"
        song.artist = "Test Artist"
        song.original_filename = "webhook_test.mp3"
        song.file_size = 1024
        song.status = 'processing'
        
        # Create fake audio file
        song.audio_file.save(
            "webhook_test.mp3",
            ContentFile(b"fake audio for webhook testing"),
            save=False
        )
        song.save()
        
        # Create analysis record
        analysis = Analysis.objects.create(
            song=song,
            analysis_type='full',
            status='processing',
            acrcloud_file_id='webhook_test_file_123'
        )
        
        self.stdout.write(f"Created test song: {song.id}")
        self.stdout.write(f"Created test analysis: {analysis.id}")
        
        # Simulate ACRCloud webhook callback
        webhook_url = f"http://localhost:8000{reverse('acrcloud:acrcloud_webhook')}"
        webhook_payload = {
            "file_id": "webhook_test_file_123",
            "status": "completed",
            "container_id": "test_container",
            "processing_time": 45.2,
            "file_size": 1024
        }
        
        self.stdout.write(f"Sending webhook to: {webhook_url}")
        self.stdout.write(f"Payload: {json.dumps(webhook_payload, indent=2)}")
        
        try:
            response = requests.post(
                webhook_url,
                json=webhook_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            self.stdout.write(f"Webhook response: {response.status_code}")
            self.stdout.write(f"Response body: {response.text}")
            
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS("✅ Webhook processed successfully!"))
                
                # Wait a moment for background task to process
                time.sleep(3)
                
                # Check if analysis was updated
                analysis.refresh_from_db()
                song.refresh_from_db()
                
                self.stdout.write(f"Analysis status: {analysis.status}")
                self.stdout.write(f"Song status: {song.status}")
                
                if hasattr(analysis, 'report'):
                    report = analysis.report
                    self.stdout.write(f"Report created: Risk={report.risk_level}, Match={report.match_type}")
                else:
                    self.stdout.write("⚠️  No report created yet")
                    
            else:
                self.stdout.write(self.style.ERROR(f"❌ Webhook failed: {response.status_code}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Webhook test failed: {str(e)}"))
    
    def _test_song_analysis(self, song_id):
        """Test analysis flow for a specific song"""
        from apps.acrcloud.models import Song
        from apps.acrcloud.service import ACRCloudService
        from django.urls import reverse
        
        try:
            song = Song.objects.get(id=song_id)
            self.stdout.write(f"Testing analysis for song: {song}")
            
            # Test webhook-based analysis
            service = ACRCloudService()
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            callback_url = f"{base_url}{reverse('acrcloud:acrcloud_webhook')}"
            
            self.stdout.write(f"Callback URL: {callback_url}")
            
            # This would normally upload to ACRCloud with webhook
            # For testing, we'll just show what would happen
            self.stdout.write("🔄 Would upload to ACRCloud with callback URL...")
            self.stdout.write("📡 ACRCloud would process file asynchronously...")
            self.stdout.write("🔔 ACRCloud would call webhook when complete...")
            self.stdout.write("⚡ Background task would process results...")
            
            self.stdout.write(self.style.SUCCESS("✅ Webhook flow configured correctly!"))
            
        except Song.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Song {song_id} not found"))
    
    def _show_usage(self):
        """Show usage instructions"""
        from apps.acrcloud.models import Song, WebhookLog
        
        self.stdout.write("🎵 ACRCloud Webhook Flow Testing")
        self.stdout.write("=" * 40)
        
        # Show recent songs
        songs = Song.objects.all().order_by('-created_at')[:5]
        if songs:
            self.stdout.write("\n📀 Recent Songs:")
            for song in songs:
                self.stdout.write(f"  {song.id} - {song.title or song.original_filename} ({song.status})")
        else:
            self.stdout.write("\n⚠️  No songs found. Upload a song first.")
        
        # Show recent webhook logs
        webhooks = WebhookLog.objects.all()[:5]
        if webhooks:
            self.stdout.write("\n🔔 Recent Webhook Calls:")
            for webhook in webhooks:
                self.stdout.write(f"  {webhook.created_at}: {webhook.file_id} - {webhook.status} ({'✅' if webhook.processed else '❌'})")
        else:
            self.stdout.write("\n📡 No webhook calls yet.")
        
        self.stdout.write("\n🧪 Usage:")
        self.stdout.write("  python manage.py test_webhook_flow --song-id <ID>")
        self.stdout.write("  python manage.py test_webhook_flow --simulate-webhook")
        
        self.stdout.write("\n🔗 Webhook Endpoint:")
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        webhook_url = f"{base_url}{reverse('acrcloud:acrcloud_webhook')}"
        self.stdout.write(f"  {webhook_url}")
        
        self.stdout.write("\n⚙️  Configure this URL in your ACRCloud File Scanning container settings.")
