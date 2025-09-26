# ACRCloud Metadata Integration Design

## Overview
This document outlines the implementation plan for storing rich metadata from ACRCloud webhooks, leveraging existing Soundcharts models and adding ACRCloud-specific analysis data.

## Current State Analysis

### Existing Soundcharts Models
- **Artist**: Comprehensive artist model with metadata, genres, biography
- **Track**: Track model with ISRC, duration, genres, artists, release info
- **Album**: Album model with metadata
- **Genre**: Hierarchical genre model (root/sub relationships)
- **Platform**: Platform model for streaming services

### ACRCloud Webhook Data Structure
```json
{
  "file_id": "5f33f69c-9af0-446b-8209-5ea0e6097cd4",
  "state": 1,
  "results": {
    "music": [{
      "title": "Everything Remains Raw",
      "artists": [{"name": "Busta Rhymes"}],
      "album": {"name": "The Coming"},
      "genres": [{"name": "Hip Hop"}, {"name": "East Coast"}],
      "external_ids": {
        "isrc": "USEE19900123",
        "upc": "0603497986774"
      },
      "external_metadata": {
        "spotify": {"track": {"id": "4M8SdMmrvx001Au6aZFchJ"}},
        "deezer": {"track": {"id": "3589946"}},
        "youtube": {"vid": "x3qbmQcimWE"},
        "musicbrainz": {"track": {"id": "bebc5a7a-5944-4e02-9e71-9debbf4f8d06"}}
      },
      "score": 99,
      "duration_ms": 220827,
      "release_date": "2007-11-27",
      "label": "Rhino/Elektra"
    }],
    "cover_songs": [...]
  }
}
```

## Proposed Implementation

### Option 1: Reuse Soundcharts Models (Recommended)

#### 1. Enhance Existing Models

**Track Model Enhancements:**
```python
# Add to apps/soundcharts/models.py
class Track(models.Model):
    # ... existing fields ...
    
    # ACRCloud specific fields
    acrcloud_id = models.CharField(max_length=255, blank=True, help_text="ACRCloud track identifier")
    acrcloud_score = models.IntegerField(null=True, blank=True, help_text="ACRCloud confidence score")
    acrcloud_analyzed_at = models.DateTimeField(null=True, blank=True, help_text="When ACRCloud analysis was performed")
    
    # Enhanced external IDs
    upc = models.CharField(max_length=255, blank=True, help_text="Universal Product Code")
    musicbrainz_id = models.CharField(max_length=255, blank=True, help_text="MusicBrainz track ID")
    
    # Platform-specific IDs (stored as JSON for flexibility)
    platform_ids = models.JSONField(default=dict, blank=True, help_text="Platform-specific track IDs")
```

**Artist Model Enhancements:**
```python
# Add to apps/soundcharts/models.py
class Artist(models.Model):
    # ... existing fields ...
    
    # ACRCloud specific fields
    acrcloud_id = models.CharField(max_length=255, blank=True, help_text="ACRCloud artist identifier")
    musicbrainz_id = models.CharField(max_length=255, blank=True, help_text="MusicBrainz artist ID")
    
    # Platform-specific IDs
    platform_ids = models.JSONField(default=dict, blank=True, help_text="Platform-specific artist IDs")
```

**Album Model Enhancements:**
```python
# Add to apps/soundcharts/models.py
class Album(models.Model):
    # ... existing fields ...
    
    # ACRCloud specific fields
    acrcloud_id = models.CharField(max_length=255, blank=True, help_text="ACRCloud album identifier")
    musicbrainz_id = models.CharField(max_length=255, blank=True, help_text="MusicBrainz album ID")
    
    # Platform-specific IDs
    platform_ids = models.JSONField(default=dict, blank=True, help_text="Platform-specific album IDs")
```

#### 2. Create ACRCloud-Specific Models

**ACRCloud Analysis Result:**
```python
# Add to apps/acrcloud/models.py
class ACRCloudTrackMatch(models.Model):
    """Store individual track matches from ACRCloud analysis"""
    
    MATCH_TYPE_CHOICES = [
        ('music', 'Music Match'),
        ('cover', 'Cover Song'),
        ('similar', 'Similar Song'),
    ]
    
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='track_matches')
    match_type = models.CharField(max_length=20, choices=MATCH_TYPE_CHOICES)
    
    # ACRCloud specific data
    acrcloud_id = models.CharField(max_length=255)
    score = models.IntegerField(help_text="ACRCloud confidence score")
    offset = models.FloatField(help_text="Match offset in seconds")
    played_duration = models.FloatField(help_text="Duration of matched segment")
    
    # Track reference (if we can match to existing Track)
    track = models.ForeignKey('soundcharts.Track', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Raw ACRCloud data
    raw_data = models.JSONField(help_text="Complete ACRCloud match data")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-score', 'offset']
        indexes = [
            models.Index(fields=['analysis', 'match_type']),
            models.Index(fields=['score']),
        ]
```

**Platform Track Mapping:**
```python
# Add to apps/soundcharts/models.py
class PlatformTrackMapping(models.Model):
    """Map tracks to platform-specific IDs"""
    
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='platform_mappings')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    
    # Platform-specific identifiers
    platform_track_id = models.CharField(max_length=255)
    platform_artist_id = models.CharField(max_length=255, blank=True)
    platform_album_id = models.CharField(max_length=255, blank=True)
    
    # Additional platform metadata
    platform_url = models.URLField(blank=True)
    platform_image_url = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['track', 'platform', 'platform_track_id']
        indexes = [
            models.Index(fields=['platform', 'platform_track_id']),
        ]
```

#### 3. Data Processing Service

**ACRCloud Metadata Processor:**
```python
# Add to apps/acrcloud/service.py
class ACRCloudMetadataProcessor:
    """Process ACRCloud webhook data and create/update Soundcharts models"""
    
    def process_webhook_results(self, analysis: Analysis, webhook_data: dict):
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
    
    def _process_music_match(self, analysis: Analysis, match_data: dict):
        """Process a music match and create/update models"""
        
        # Extract track information
        track_info = match_data.get('result', {})
        
        # Create or update Track
        track = self._create_or_update_track(track_info, match_data)
        
        # Create ACRCloud match record
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
    
    def _create_or_update_track(self, track_info: dict, match_data: dict):
        """Create or update Track model from ACRCloud data"""
        
        # Try to find existing track by ISRC
        isrc = track_info.get('external_ids', {}).get('isrc')
        track = None
        
        if isrc:
            track = Track.objects.filter(isrc=isrc).first()
        
        if not track:
            # Create new track
            track = Track.objects.create(
                name=track_info.get('title', ''),
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
        
        # Create/update artists
        self._create_or_update_artists(track, track_info.get('artists', []))
        
        # Create/update album
        self._create_or_update_album(track, track_info.get('album', {}))
        
        # Create/update genres
        self._create_or_update_genres(track, track_info.get('genres', []))
        
        # Create platform mappings
        self._create_platform_mappings(track, track_info.get('external_metadata', {}))
        
        return track
    
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
```

## Benefits of This Approach

1. **Unified Data Model**: Single source of truth for all music metadata
2. **Reuse Existing Infrastructure**: Leverage existing admin, APIs, and relationships
3. **Flexible Platform Support**: Easy to add new platforms via JSON fields
4. **Rich Analysis Data**: Preserve detailed ACRCloud analysis results
5. **Data Integrity**: Proper foreign key relationships and constraints
6. **Scalable**: Efficient queries and indexing

## Migration Strategy

1. **Phase 1**: Add new fields to existing models
2. **Phase 2**: Create new ACRCloud-specific models
3. **Phase 3**: Implement metadata processing service
4. **Phase 4**: Update webhook processing to use new service
5. **Phase 5**: Create admin interfaces for new models

## Database Schema Changes

### New Fields Added:
- `Track.acrcloud_id`, `Track.acrcloud_score`, `Track.acrcloud_analyzed_at`
- `Track.upc`, `Track.musicbrainz_id`, `Track.platform_ids`
- `Artist.acrcloud_id`, `Artist.musicbrainz_id`, `Artist.platform_ids`
- `Album.acrcloud_id`, `Album.musicbrainz_id`, `Album.platform_ids`

### New Models:
- `ACRCloudTrackMatch` - Individual track matches from analysis
- `PlatformTrackMapping` - Platform-specific track mappings

This approach maximizes code reuse while providing comprehensive metadata storage for ACRCloud analysis results.

