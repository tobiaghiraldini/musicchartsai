"""
ACRCloud Service Integration
Provides services for file scanning, identification, and fraud detection
"""
import json
import hmac
import hashlib
import base64
import time
import urllib.request
import logging
import uuid
from datetime import datetime
from urllib.parse import urlencode
from typing import Dict, Any, List, Optional
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
from .models import ACRCloudConfig, Analysis, AnalysisReport

logger = logging.getLogger(__name__)


class ACRCloudService:
    """Service class for ACRCloud API integration"""
    
    def __init__(self, config_name: str = None, use_mock: bool = None):
        """
        Initialize ACRCloud service with configuration
        
        Args:
            config_name: Name of ACRCloudConfig to use. If None, uses active config.
            use_mock: Whether to use mock service. If None, checks settings.
        """
        if use_mock is None:
            from django.conf import settings
            use_mock = getattr(settings, 'ACRCLOUD_USE_MOCK', False)
        
        if use_mock:
            from .mock_service import MockACRCloudService
            self.mock_service = MockACRCloudService()
            self.config = None
            return
        
        if config_name:
            self.config = ACRCloudConfig.objects.get(name=config_name, is_active=True)
        else:
            self.config = ACRCloudConfig.objects.filter(is_active=True).first()
        
        if not self.config:
            raise ValueError("No active ACRCloud configuration found")
    
    def _sign_string(self, string_to_sign: str, secret: str) -> str:
        """Sign a string using HMAC-SHA1"""
        dig = hmac.new(
            bytes(secret, 'utf-8'), 
            bytes(string_to_sign, 'utf-8'), 
            digestmod=hashlib.sha1
        ).digest()
        return base64.b64encode(dig).decode('utf-8')
    
    def _http_get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make authenticated GET request to ACRCloud API"""
        if params:
            url = url + ("&" if "?" in url else "?") + urlencode(params)
        
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {self.config.bearer_token}",
            "Accept": "application/json"
        })
        
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    
    def _http_post_json(self, url: str, data: bytes, content_type: str = "application/octet-stream") -> Dict[str, Any]:
        """Make authenticated POST request to ACRCloud API"""
        http_date = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
        string_to_sign = f"POST\n/v1/identify\n{http_date}\n{content_type}\nx-amz-acrcloud-1"
        sig = self._sign_string(string_to_sign, self.config.identify_access_secret)
        
        req = urllib.request.Request(url, data=data, method="POST", headers={
            "Content-Type": content_type,
            "Date": http_date,
            "Authorization": f"ACS {self.config.identify_access_key}:{sig}",
            "x-amz-acrcloud-1": "1"
        })
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    
    def upload_file_for_scanning(self, audio_file: UploadedFile, callback_url: str = None) -> str:
        """
        Upload file to ACRCloud for file scanning with webhook callback
        
        Args:
            audio_file: Django UploadedFile object
            callback_url: URL for ACRCloud to call when processing is complete
            
        Returns:
            File ID from ACRCloud
        """
        # Read file content
        audio_file.seek(0)
        file_content = audio_file.read()
        
        # Upload to ACRCloud File Scanning
        upload_url = f"{self.config.base_url}/api/fs-containers/{self.config.container_id}/files"
        
        # Create multipart form data with callback URL
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = []
        
        # Add file
        body.append(f'--{boundary}'.encode())
        body.append(b'Content-Disposition: form-data; name="file"; filename="' + audio_file.name.encode() + b'"')
        body.append(b'Content-Type: audio/mpeg')
        body.append(b'')
        body.append(file_content)
        
        # Add data_type (required by ACRCloud API)
        body.append(f'--{boundary}'.encode())
        body.append(b'Content-Disposition: form-data; name="data_type"')
        body.append(b'')
        body.append(b'audio')
        
        # Add callback URL if provided
        if callback_url:
            body.append(f'--{boundary}'.encode())
            body.append(b'Content-Disposition: form-data; name="notification_url"')
            body.append(b'')
            body.append(callback_url.encode())
        
        # Add metadata (optional)
        body.append(f'--{boundary}'.encode())
        body.append(b'Content-Disposition: form-data; name="metadata"')
        body.append(b'')
        body.append(json.dumps({
            'title': getattr(audio_file, 'title', ''),
            'artist': getattr(audio_file, 'artist', ''),
            'filename': audio_file.name
        }).encode())
        
        body.append(f'--{boundary}--'.encode())
        body.append(b'')
        
        data = b'\r\n'.join(body)
        
        req = urllib.request.Request(upload_url, data=data, method="POST", headers={
            "Authorization": f"Bearer {self.config.bearer_token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(data))
        })
        
        with urllib.request.urlopen(req, timeout=120) as resp:
            response = json.loads(resp.read().decode("utf-8"))
            logger.info(f"File uploaded to ACRCloud: {response}")
            # Extract file ID from the response structure
            if "data" in response and "id" in response["data"]:
                return response["data"]["id"]
            return response.get("id")
    
    def get_file_scanning_results(self, file_id: str) -> Dict[str, Any]:
        """
        Get file scanning results from ACRCloud
        
        Args:
            file_id: ACRCloud file ID
            
        Returns:
            File scanning results
        """
        url = f"{self.config.base_url}/api/fs-containers/{self.config.container_id}/files/{file_id}"
        return self._http_get_json(url)
    
    def identify_audio(self, audio_file: UploadedFile, data_type: str = "audio", top_n: int = 5) -> Dict[str, Any]:
        """
        Identify audio using ACRCloud Identification API
        
        Args:
            audio_file: Django UploadedFile object
            data_type: Type of data (audio, fingerprint, etc.)
            top_n: Number of top results to return
            
        Returns:
            Identification results
        """
        # Read file content
        audio_file.seek(0)
        file_content = audio_file.read()
        
        # Call identification API
        url = f"https://{self.config.identify_host}/v1/identify?data_type={data_type}&top_n={top_n}"
        return self._http_post_json(url, file_content)
    
    def analyze_song(self, song_id: str, callback_url: str = None) -> Dict[str, Any]:
        """
        Start comprehensive analysis on a song using webhook-based processing
        
        Args:
            song_id: UUID of the Song model
            callback_url: Webhook URL for ACRCloud to call when processing is complete
            
        Returns:
            Analysis initiation results
        """
        from .models import Song
        
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            raise ValueError(f"Song with ID {song_id} not found")
        
        # Check if we should use mock service
        if hasattr(self, 'mock_service'):
            logger.info("Using mock ACRCloud service for analysis")
            return self.mock_service.analyze_song(song_id, callback_url)
        
        # Update song status
        song.status = 'processing'
        song.save()
        
        try:
            # 1. Upload file to ACRCloud File Scanning with webhook callback
            file_id = self.upload_file_for_scanning(song.audio_file, callback_url)
            logger.info(f"File uploaded to ACRCloud with ID: {file_id}")
            
            # 2. Create Analysis record in 'processing' status
            analysis = Analysis.objects.create(
                song=song,
                analysis_type='full',
                status='processing',
                acrcloud_file_id=file_id,
                raw_response={'upload_response': {'file_id': file_id, 'callback_url': callback_url}}
            )
            
            logger.info(f"Analysis record created: {analysis.id}")
            
            # 3. Run immediate identification analysis (this is synchronous)
            try:
                identify_results = self.identify_audio(song.audio_file, top_n=10)
                logger.info(f"Identification analysis completed for song {song_id}")
                
                # Store identification results in the analysis
                current_response = analysis.raw_response or {}
                current_response['identification'] = identify_results
                analysis.raw_response = current_response
                analysis.save()
                
            except Exception as identify_error:
                logger.warning(f"Identification analysis failed: {identify_error}")
                # Continue without identification results
            
            # File scanning results will be processed via webhook when ACRCloud completes processing
            
            return {
                'success': True,
                'analysis_id': str(analysis.id),
                'file_id': file_id,
                'status': 'processing',
                'message': 'File uploaded to ACRCloud. Analysis will complete via webhook.'
            }
            
        except Exception as e:
            # Update song status to failed
            song.status = 'failed'
            song.save()
            
            logger.error(f"Analysis initiation failed for song {song_id}: {str(e)}")
            
            return {
                'success': False,
                'error': str(e),
                'status': 'failed'
            }
    
    def _create_analysis_report(self, song, file_id: str, results: Dict[str, Any]) -> Analysis:
        """
        Create analysis and report from ACRCloud results
        
        Args:
            song: Song model instance
            file_id: ACRCloud file ID
            results: Analysis results from ACRCloud
            
        Returns:
            Analysis model instance
        """
        # Create Analysis record
        analysis = Analysis.objects.create(
            song=song,
            analysis_type='full',
            status='analyzed',
            acrcloud_file_id=file_id,
            raw_response=results,
            completed_at=timezone.now()
        )
        
        # Process results and create report
        report_data = self._process_analysis_results(results)
        
        # Create AnalysisReport
        AnalysisReport.objects.create(
            analysis=analysis,
            **report_data
        )
        
        return analysis
    
    def _process_analysis_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process ACRCloud results and extract relevant data for fraud detection
        
        Args:
            results: Raw results from ACRCloud
            
        Returns:
            Processed data for AnalysisReport
        """
        report_data = {
            'risk_level': 'low',
            'match_type': 'no_match',
            'confidence_score': 0.0,
            'fingerprint_matches': [],
            'cover_matches': [],
            'lyrics_matches': [],
            'summary': '',
            'recommendations': ''
        }
        
        # Process file scanning results
        file_scanning = results.get('file_scanning', {})
        if file_scanning:
            file_results = file_scanning.get('results', {})
            
            # Process music/fingerprint matches
            music_matches = file_results.get('music', [])
            if music_matches:
                report_data['fingerprint_matches'] = self._process_music_matches(music_matches)
                report_data['fingerprint_score'] = max([m.get('score', 0) for m in music_matches], default=0)
                report_data['fingerprint_similarity'] = max([m.get('similarity', 0) for m in music_matches], default=0)
            
            # Process cover song matches
            cover_matches = file_results.get('cover_songs', [])
            if cover_matches:
                report_data['cover_matches'] = self._process_cover_matches(cover_matches)
                report_data['cover_score'] = max([m.get('score', 0) for m in cover_matches], default=0)
                report_data['cover_similarity'] = max([m.get('similarity', 0) for m in cover_matches], default=0)
        
        # Process identification results
        identification = results.get('identification', {})
        if identification:
            metadata = identification.get('metadata', {})
            music_results = metadata.get('music', [])
            if music_results:
                # Merge with fingerprint results or use as additional data
                if not report_data['fingerprint_matches']:
                    report_data['fingerprint_matches'] = self._process_identification_matches(music_results)
        
        # Determine risk level and match type
        report_data.update(self._assess_fraud_risk(report_data))
        
        # Generate summary and recommendations
        report_data['summary'] = self._generate_summary(report_data)
        report_data['recommendations'] = self._generate_recommendations(report_data)
        
        return report_data
    
    def _process_music_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process music/fingerprint matches"""
        processed = []
        for match in matches:
            result = match.get('result', {})
            processed.append({
                'acrid': result.get('acrid'),
                'title': result.get('title'),
                'artists': [a.get('name') for a in result.get('artists', [])],
                'album': result.get('album', {}).get('name') if result.get('album') else None,
                'score': result.get('score'),
                'similarity': result.get('similarity'),
                'isrc': result.get('isrc'),
                'duration_ms': result.get('duration_ms'),
                'play_offset_ms': result.get('play_offset_ms'),
                'match_type': result.get('match_type'),
                'risk': result.get('risk')
            })
        return processed
    
    def _process_cover_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process cover song matches"""
        processed = []
        for match in matches:
            result = match.get('result', {})
            processed.append({
                'acrid': result.get('acrid'),
                'title': result.get('title'),
                'artists': [a.get('name') for a in result.get('artists', [])],
                'album': result.get('album', {}).get('name') if result.get('album') else None,
                'score': result.get('score'),
                'similarity': result.get('similarity'),
                'isrc': result.get('isrc'),
                'duration_ms': result.get('duration_ms'),
                'play_offset_ms': result.get('play_offset_ms'),
                'match_type': result.get('match_type'),
                'risk': result.get('risk')
            })
        return processed
    
    def _process_identification_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process identification API matches"""
        processed = []
        for match in matches:
            processed.append({
                'acrid': match.get('acrid'),
                'title': match.get('title'),
                'artists': [a.get('name') for a in match.get('artists', [])],
                'album': match.get('album', {}).get('name') if match.get('album') else None,
                'score': match.get('score'),
                'similarity': match.get('similarity'),
                'isrc': match.get('isrc'),
                'duration_ms': match.get('duration_ms'),
                'play_offset_ms': match.get('play_offset_ms'),
                'match_type': match.get('match_type'),
                'risk': match.get('risk')
            })
        return processed
    
    def _assess_fraud_risk(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess fraud risk based on analysis results"""
        fingerprint_score = report_data.get('fingerprint_score', 0)
        cover_score = report_data.get('cover_score', 0)
        fingerprint_similarity = report_data.get('fingerprint_similarity', 0)
        cover_similarity = report_data.get('cover_similarity', 0)
        
        # Determine match type and risk level
        if fingerprint_score > 80 or fingerprint_similarity > 0.8:
            return {
                'match_type': 'exact',
                'risk_level': 'high',
                'confidence_score': max(fingerprint_score, fingerprint_similarity * 100)
            }
        elif cover_score > 70 or cover_similarity > 0.7:
            return {
                'match_type': 'cover',
                'risk_level': 'medium',
                'confidence_score': max(cover_score, cover_similarity * 100)
            }
        elif fingerprint_score > 50 or cover_score > 50:
            return {
                'match_type': 'similar',
                'risk_level': 'medium',
                'confidence_score': max(fingerprint_score, cover_score)
            }
        else:
            return {
                'match_type': 'no_match',
                'risk_level': 'low',
                'confidence_score': 0
            }
    
    def _generate_summary(self, report_data: Dict[str, Any]) -> str:
        """Generate analysis summary"""
        match_type = report_data.get('match_type', 'no_match')
        risk_level = report_data.get('risk_level', 'low')
        confidence = report_data.get('confidence_score', 0)
        
        if match_type == 'exact':
            return f"Exact match detected with {confidence:.1f}% confidence. This appears to be a duplicate of an existing song."
        elif match_type == 'cover':
            return f"Cover song detected with {confidence:.1f}% confidence. This appears to be a cover version of an existing song."
        elif match_type == 'similar':
            return f"Similar song detected with {confidence:.1f}% confidence. This song shows similarities to existing content."
        else:
            return "No significant matches found. This appears to be original content."
    
    def _generate_recommendations(self, report_data: Dict[str, Any]) -> str:
        """Generate recommendations based on analysis"""
        match_type = report_data.get('match_type', 'no_match')
        risk_level = report_data.get('risk_level', 'low')
        
        if match_type == 'exact':
            return "RECOMMENDATION: This song appears to be a duplicate. Consider removing or investigating the source."
        elif match_type == 'cover':
            return "RECOMMENDATION: This is a cover song. Ensure proper licensing and attribution are in place."
        elif match_type == 'similar':
            return "RECOMMENDATION: Similar content detected. Review for potential copyright issues."
        else:
            return "RECOMMENDATION: No issues detected. Content appears to be original."


class ACRCloudMetadataProcessor:
    """Process ACRCloud webhook data and create/update Soundcharts models"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_webhook_results(self, analysis: 'Analysis', webhook_data: dict):
        """Process webhook results and create metadata models"""
        
        results = webhook_data.get('results', {})
        
        # Process music matches
        music_matches = results.get('music', [])
        for match_data in music_matches:
            self._process_music_match(analysis, match_data)
        
        # Process cover song matches
        cover_matches = results.get('cover_songs', [])
        for match_data in cover_matches:
            self._process_cover_match(analysis, match_data)
    
    def _process_music_match(self, analysis: 'Analysis', match_data: dict):
        """Process a music match and create/update models"""
        
        # Extract track information
        track_info = match_data.get('result', {})
        
        # Create or update Track
        track = self._create_or_update_track(track_info, match_data)
        
        # Create ACRCloud match record
        from .models import ACRCloudTrackMatch
        ACRCloudTrackMatch.objects.create(
            analysis=analysis,
            match_type='music',
            acrcloud_id=track_info.get('acrid'),
            score=match_data.get('score', 0),
            offset=match_data.get('offset', 0),
            played_duration=match_data.get('played_duration', 0),
            track=track,
            raw_data=match_data
        )
    
    def _process_cover_match(self, analysis: 'Analysis', match_data: dict):
        """Process a cover song match and create/update models"""
        
        # Extract track information
        track_info = match_data.get('result', {})
        
        # Create or update Track
        track = self._create_or_update_track(track_info, match_data)
        
        # Create ACRCloud match record
        from .models import ACRCloudTrackMatch
        ACRCloudTrackMatch.objects.create(
            analysis=analysis,
            match_type='cover',
            acrcloud_id=track_info.get('acrid'),
            score=match_data.get('score', 0),
            offset=match_data.get('offset', 0),
            played_duration=match_data.get('played_duration', 0),
            track=track,
            raw_data=match_data
        )
    
    def _create_or_update_track(self, track_info: dict, match_data: dict):
        """Create or update Track model from ACRCloud data"""
        
        from apps.soundcharts.models import Track, Artist, Album, Genre
        from django.utils import timezone
        from datetime import datetime
        
        # Try to find existing track by ISRC
        isrc = track_info.get('external_ids', {}).get('isrc')
        track = None
        
        if isrc:
            track = Track.objects.filter(isrc=isrc).first()
        
        if not track:
            # Create new track
            track = Track.objects.create(
                name=track_info.get('title', ''),
                uuid=str(uuid.uuid4()),  # Generate new UUID
                isrc=isrc,
                duration=int(track_info.get('duration_ms', 0) / 1000) if track_info.get('duration_ms') else None,
                release_date=self._parse_date(track_info.get('release_date')),
                label=track_info.get('label', ''),
                acrcloud_id=track_info.get('acrid'),
                acrcloud_score=match_data.get('score'),
                acrcloud_analyzed_at=timezone.now(),
                upc=track_info.get('external_ids', {}).get('upc'),
                musicbrainz_id=track_info.get('external_metadata', {}).get('musicbrainz', {}).get('track', {}).get('id'),
                platform_ids=self._extract_platform_ids(track_info.get('external_metadata', {}))
            )
        else:
            # Update existing track with ACRCloud data
            track.acrcloud_id = track_info.get('acrid')
            track.acrcloud_score = match_data.get('score')
            track.acrcloud_analyzed_at = timezone.now()
            track.upc = track_info.get('external_ids', {}).get('upc')
            track.musicbrainz_id = track_info.get('external_metadata', {}).get('musicbrainz', {}).get('track', {}).get('id')
            track.platform_ids = self._extract_platform_ids(track_info.get('external_metadata', {}))
            track.save()
        
        # Create/update artists
        self._create_or_update_artists(track, track_info.get('artists', []))
        
        # Create/update album
        self._create_or_update_album(track, track_info.get('album', {}))
        
        # Create/update genres
        self._create_or_update_genres(track, track_info.get('genres', []))
        
        # Create platform mappings
        self._create_platform_mappings(track, track_info.get('external_metadata', {}))
        
        return track
    
    def _create_or_update_artists(self, track, artists_data: list):
        """Create or update Artist models from ACRCloud data"""
        
        from apps.soundcharts.models import Artist
        
        for artist_data in artists_data:
            artist_name = artist_data.get('name', '')
            if not artist_name:
                continue
            
            # Try to find existing artist by name
            artist = Artist.objects.filter(name__iexact=artist_name).first()
            
            if not artist:
                # Create new artist
                artist = Artist.objects.create(
                    uuid=str(uuid.uuid4()),
                    name=artist_name,
                    slug=artist_name.lower().replace(' ', '-'),
                    appUrl='',
                    imageUrl='',
                    countryCode='',
                    platform_ids=self._extract_artist_platform_ids(artist_data)
                )
            
            # Add artist to track if not already associated
            if artist not in track.artists.all():
                track.artists.add(artist)
    
    def _create_or_update_album(self, track, album_data: dict):
        """Create or update Album model from ACRCloud data"""
        
        from apps.soundcharts.models import Album
        
        album_name = album_data.get('name', '')
        if not album_name:
            return
        
        # Try to find existing album by name
        album = Album.objects.filter(name__iexact=album_name).first()
        
        if not album:
            # Create new album
            album = Album.objects.create(
                uuid=str(uuid.uuid4()),
                name=album_name,
                platform_ids=self._extract_album_platform_ids(album_data)
            )
    
    def _create_or_update_genres(self, track, genres_data: list):
        """Create or update Genre models from ACRCloud data"""
        
        from apps.soundcharts.models import Genre
        
        for genre_data in genres_data:
            genre_name = genre_data.get('name', '')
            if not genre_name:
                continue
            
            # Try to find existing genre by name
            genre = Genre.objects.filter(name__iexact=genre_name).first()
            
            if not genre:
                # Create new genre
                genre = Genre.objects.create(
                    name=genre_name,
                    slug=genre_name.lower().replace(' ', '-'),
                    level=0  # Assume root level for ACRCloud genres
                )
            
            # Add genre to track if not already associated
            if genre not in track.genres.all():
                track.genres.add(genre)
    
    def _create_platform_mappings(self, track, external_metadata: dict):
        """Create platform mappings from external metadata"""
        
        from apps.soundcharts.models import Platform
        from .models import PlatformTrackMapping
        
        for platform_name, data in external_metadata.items():
            if platform_name == 'musicbrainz':
                continue  # Skip MusicBrainz as it's not a streaming platform
            
            # Get or create platform
            platform, created = Platform.objects.get_or_create(
                platform_identifier=platform_name,
                defaults={
                    'name': platform_name.title(),
                    'slug': platform_name.lower(),
                    'platform_type': 'streaming'
                }
            )
            
            # Extract platform-specific IDs
            track_id = None
            artist_id = None
            album_id = None
            
            if platform_name == 'spotify' and 'track' in data:
                track_id = data['track'].get('id')
                artist_id = data.get('artists', [{}])[0].get('id')
                album_id = data.get('album', {}).get('id')
            elif platform_name == 'deezer' and 'track' in data:
                track_id = data['track'].get('id')
                artist_id = data.get('artists', [{}])[0].get('id')
                album_id = data.get('album', {}).get('id')
            elif platform_name == 'youtube':
                track_id = data.get('vid')
            
            if track_id:
                # Create platform mapping
                PlatformTrackMapping.objects.get_or_create(
                    track=track,
                    platform=platform,
                    platform_track_id=track_id,
                    defaults={
                        'platform_artist_id': artist_id or '',
                        'platform_album_id': album_id or ''
                    }
                )
    
    def _extract_platform_ids(self, external_metadata: dict) -> dict:
        """Extract platform-specific IDs from external metadata"""
        platform_ids = {}
        
        for platform, data in external_metadata.items():
            if platform == 'spotify' and 'track' in data:
                platform_ids['spotify_track_id'] = data['track'].get('id')
                platform_ids['spotify_artist_id'] = data.get('artists', [{}])[0].get('id')
                platform_ids['spotify_album_id'] = data.get('album', {}).get('id')
            elif platform == 'deezer' and 'track' in data:
                platform_ids['deezer_track_id'] = data['track'].get('id')
                platform_ids['deezer_artist_id'] = data.get('artists', [{}])[0].get('id')
                platform_ids['deezer_album_id'] = data.get('album', {}).get('id')
            elif platform == 'youtube':
                platform_ids['youtube_video_id'] = data.get('vid')
        
        return platform_ids
    
    def _extract_artist_platform_ids(self, artist_data: dict) -> dict:
        """Extract platform-specific IDs for artist"""
        # This would be populated from external_metadata if available
        return {}
    
    def _extract_album_platform_ids(self, album_data: dict) -> dict:
        """Extract platform-specific IDs for album"""
        # This would be populated from external_metadata if available
        return {}
    
    def _parse_date(self, date_str: str):
        """Parse date string to Date object"""
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None


