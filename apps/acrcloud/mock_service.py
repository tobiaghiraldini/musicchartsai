"""
Mock ACRCloud service for testing without real API credentials
"""
import time
import random
from django.utils import timezone
from .models import Analysis, AnalysisReport


class MockACRCloudService:
    """Mock service for testing ACRCloud integration without real API"""
    
    def analyze_song(self, song_id: str) -> dict:
        """Mock analysis that simulates ACRCloud processing"""
        from .models import Song
        
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            raise ValueError(f"Song with ID {song_id} not found")
        
        # Update song status
        song.status = 'processing'
        song.save()
        
        # Simulate processing time
        time.sleep(2)
        
        # Create mock analysis results
        mock_results = {
            'file_scanning': {
                'id': f'mock_file_{song_id[:8]}',
                'results': {
                    'music': [
                        {
                            'result': {
                                'acrid': f'mock_acrid_{random.randint(1000, 9999)}',
                                'title': 'Similar Song Title',
                                'artists': [{'name': 'Similar Artist'}],
                                'album': {'name': 'Similar Album'},
                                'score': random.randint(20, 95),
                                'similarity': random.random(),
                                'isrc': 'MOCK123456789',
                                'duration_ms': 180000,
                                'play_offset_ms': 0,
                                'match_type': 'fingerprint',
                                'risk': 'low' if random.random() > 0.3 else 'medium'
                            }
                        }
                    ] if random.random() > 0.5 else [],
                    'cover_songs': [
                        {
                            'result': {
                                'acrid': f'mock_cover_{random.randint(1000, 9999)}',
                                'title': 'Original Song Title',
                                'artists': [{'name': 'Original Artist'}],
                                'album': {'name': 'Original Album'},
                                'score': random.randint(60, 85),
                                'similarity': random.random() * 0.8 + 0.2,
                                'isrc': 'ORIG123456789',
                                'duration_ms': 175000,
                                'play_offset_ms': 5000,
                                'match_type': 'cover',
                                'risk': 'medium'
                            }
                        }
                    ] if random.random() > 0.7 else []
                }
            },
            'identification': {
                'metadata': {
                    'music': [
                        {
                            'acrid': f'mock_id_{random.randint(1000, 9999)}',
                            'title': 'Identified Song',
                            'artists': [{'name': 'Identified Artist'}],
                            'score': random.randint(30, 90),
                            'similarity': random.random(),
                        }
                    ] if random.random() > 0.6 else []
                }
            }
        }
        
        # Create analysis record
        analysis = Analysis.objects.create(
            song=song,
            analysis_type='full',
            status='analyzed',
            acrcloud_file_id=f'mock_file_{song_id[:8]}',
            raw_response=mock_results,
            completed_at=timezone.now()
        )
        
        # Process results and create report
        report_data = self._create_mock_report(mock_results)
        
        # Create AnalysisReport
        AnalysisReport.objects.create(
            analysis=analysis,
            **report_data
        )
        
        # Update song status
        song.status = 'analyzed'
        song.save()
        
        return {
            'success': True,
            'analysis_id': str(analysis.id),
            'file_id': f'mock_file_{song_id[:8]}',
            'results': mock_results
        }
    
    def _create_mock_report(self, results: dict) -> dict:
        """Create mock analysis report"""
        file_scanning = results.get('file_scanning', {})
        file_results = file_scanning.get('results', {})
        
        music_matches = file_results.get('music', [])
        cover_matches = file_results.get('cover_songs', [])
        
        # Determine risk level based on mock results
        if music_matches and music_matches[0]['result']['score'] > 80:
            risk_level = 'high'
            match_type = 'exact'
            confidence = music_matches[0]['result']['score']
        elif cover_matches and cover_matches[0]['result']['score'] > 70:
            risk_level = 'medium'
            match_type = 'cover'
            confidence = cover_matches[0]['result']['score']
        elif music_matches or cover_matches:
            risk_level = 'low'
            match_type = 'similar'
            confidence = 50
        else:
            risk_level = 'low'
            match_type = 'no_match'
            confidence = 0
        
        return {
            'risk_level': risk_level,
            'match_type': match_type,
            'confidence_score': confidence,
            'fingerprint_matches': [m['result'] for m in music_matches],
            'cover_matches': [m['result'] for m in cover_matches],
            'lyrics_matches': [],
            'fingerprint_score': music_matches[0]['result']['score'] if music_matches else None,
            'fingerprint_similarity': music_matches[0]['result']['similarity'] if music_matches else None,
            'cover_score': cover_matches[0]['result']['score'] if cover_matches else None,
            'cover_similarity': cover_matches[0]['result']['similarity'] if cover_matches else None,
            'detected_genre': random.choice(['Pop', 'Rock', 'Hip-Hop', 'Electronic', 'Classical']),
            'detected_language': 'en',
            'isrc_code': music_matches[0]['result']['isrc'] if music_matches else None,
            'summary': f'Mock analysis completed. Match type: {match_type}, Risk: {risk_level}',
            'recommendations': f'This is a mock analysis. In production, this would contain real ACRCloud recommendations.'
        }
