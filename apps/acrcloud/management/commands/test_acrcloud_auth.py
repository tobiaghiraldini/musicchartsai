"""
Management command to test ACRCloud authentication
"""
from django.core.management.base import BaseCommand
from apps.acrcloud.service import ACRCloudService
import urllib.request
import json


class Command(BaseCommand):
    help = 'Test ACRCloud authentication and API access'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-upload',
            action='store_true',
            help='Test file upload after authentication',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🔍 Testing ACRCloud Authentication...")
        self.stdout.write("=" * 50)
        
        try:
            service = ACRCloudService()
            self.stdout.write(f"✅ Service initialized with config: {service.config.name}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Service initialization failed: {str(e)}"))
            return
        
        # Test 1: Console API Authentication
        self.stdout.write("\n1. Testing Console API Authentication...")
        try:
            url = f'{service.config.base_url}/api/fs-containers'
            req = urllib.request.Request(url, headers={
                'Authorization': f'Bearer {service.config.bearer_token}',
                'Accept': 'application/json'
            })
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                response = json.loads(resp.read().decode('utf-8'))
                self.stdout.write(self.style.SUCCESS("✅ Console API: SUCCESS"))
                self.stdout.write(f"   Response: {response}")
                
        except urllib.error.HTTPError as e:
            self.stdout.write(self.style.ERROR(f"❌ Console API: HTTP {e.code} - {e.reason}"))
            response_body = e.read().decode()
            self.stdout.write(f"   Response: {response_body}")
            
            if e.code == 403:
                self.stdout.write(self.style.WARNING("\n🔧 SOLUTION:"))
                self.stdout.write("   You need a Console API Bearer Token, not Project API credentials.")
                self.stdout.write("   Go to ACRCloud Console → API Keys → Console API")
                self.stdout.write("   Generate a new Bearer Token with File Scanning permissions.")
                self.stdout.write("   Update your ACRCloudConfig with the new Bearer Token.")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Console API: {str(e)}"))
        
        # Test 2: File Scanning API
        self.stdout.write("\n2. Testing File Scanning API...")
        try:
            url = f'{service.config.base_url}/api/fs-containers/{service.config.container_id}/files'
            req = urllib.request.Request(url, headers={
                'Authorization': f'Bearer {service.config.bearer_token}',
                'Accept': 'application/json'
            })
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                response = json.loads(resp.read().decode('utf-8'))
                self.stdout.write(self.style.SUCCESS("✅ File Scanning API: SUCCESS"))
                self.stdout.write(f"   Response: {response}")
                
        except urllib.error.HTTPError as e:
            self.stdout.write(self.style.ERROR(f"❌ File Scanning API: HTTP {e.code} - {e.reason}"))
            response_body = e.read().decode()
            self.stdout.write(f"   Response: {response_body}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ File Scanning API: {str(e)}"))
        
        # Test 3: Identification API
        self.stdout.write("\n3. Testing Identification API...")
        try:
            url = f'https://{service.config.identify_host}/v1/identify'
            req = urllib.request.Request(url, method='POST', headers={
                'Content-Type': 'application/octet-stream'
            })
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                self.stdout.write(self.style.SUCCESS("✅ Identification API: SUCCESS (host reachable)"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Identification API: {str(e)}"))
        
        # Test 4: File Upload (if requested)
        if options['test_upload']:
            self.stdout.write("\n4. Testing File Upload...")
            try:
                from apps.acrcloud.models import Song
                from django.core.files.base import ContentFile
                
                # Create test song
                song = Song()
                song.user_id = 1
                song.title = 'Auth Test Song'
                song.artist = 'Auth Test Artist'
                song.original_filename = 'auth_test.mp3'
                song.file_size = 1024
                song.audio_file.save('auth_test.mp3', ContentFile(b'fake audio data'))
                song.save()
                
                # Test upload
                file_id = service.upload_file_for_scanning(song.audio_file)
                self.stdout.write(self.style.SUCCESS(f"✅ File Upload: SUCCESS"))
                self.stdout.write(f"   File ID: {file_id}")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ File Upload: {str(e)}"))
        
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("🎯 Next Steps:")
        self.stdout.write("1. If Console API fails (403), get Console API Bearer Token from ACRCloud Console")
        self.stdout.write("2. Update ACRCloudConfig with the new Bearer Token")
        self.stdout.write("3. Run this command again to verify")
        self.stdout.write("4. Use --test-upload to test complete file upload flow")
