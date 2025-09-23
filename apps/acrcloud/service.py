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


