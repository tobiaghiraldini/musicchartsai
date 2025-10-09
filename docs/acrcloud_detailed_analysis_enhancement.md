# ACRCloud Detailed Analysis Enhancement

## Overview
This document outlines the enhancements needed to display comprehensive fingerprint analysis, pattern matching data, and lyrics analysis from ACRCloud, similar to what's shown in the PDF "Dettagli Brano Analizzato.pdf".

## Current State

### What We Already Have
1. **Models:**
   - `ACRCloudTrackMatch`: Stores individual matches with `raw_data` JSONField containing pattern matching details
   - `AnalysisReport`: Stores summary-level data (fingerprint_matches, cover_matches, lyrics_matches)
   - `Analysis`: Links songs to their ACRCloud analysis results

2. **Data Being Captured:**
   - Basic match info: title, artists, album, ISRC
   - Score and played_duration
   - Pattern matching data in `raw_data` field:
     - offset, type, score, similarity, distance
     - pattern_matching, risk, match_type, result_from
     - Time offsets: db_begin/end, sample_begin/end
     - time_skew, frequency_skew

3. **Current Display:**
   - `pattern_matching_report.html`: Shows some pattern matching data in a table
   - `analysis_report.html`: Shows limited match information (title, artists, score only)

## What's Missing (Based on ACRCloud API and PDF)

### 1. Comprehensive Fingerprint Values Display
For each match, we need to show:
- **Score**: Overall match confidence (0-100)
- **Similarity**: Audio similarity metric (0-1 or 0-100)
- **Distance**: Distance metric from ACRCloud
- **Pattern Matching**: Pattern matching percentage
- **Risk**: Fraud risk score
- **Match Type**: Type of match (exact, cover, similar)
- **Result From**: Which ACRCloud engine found this (fingerprint=1, cover=2, etc.)

### 2. Time/Offset Analysis
For each match, show:
- **Play Offset (ms)**: Where in the reference track the match starts
- **DB Begin/End Time Offset (ms)**: Database track time range
- **Sample Begin/End Time Offset (ms)**: Uploaded sample time range
- **Played Duration (seconds)**: How long the match segment is
- **Time Skew**: Temporal distortion factor
- **Frequency Skew**: Pitch/frequency distortion factor

### 3. Lyrics Analysis
Currently not implemented but available from ACRCloud:
- Lyrics matches if available
- Lyrics similarity scores
- Language detection

### 4. External Metadata
For each match, show:
- **Platform IDs**: Spotify, Deezer, YouTube, Apple Music IDs
- **ISRC, UPC**: Standard music identifiers
- **MusicBrainz ID**: For cross-referencing
- **Label**: Record label information
- **Release Date**: Track release date

### 5. Visual Representation
Need to add:
- Timeline visualization showing match offsets
- Score distribution charts
- Risk level indicators
- Pattern matching heat maps

## Proposed Enhancements

### Phase 1: Enhanced Data Display (Immediate)

#### 1.1 Create Detailed Match Card Component
Create a reusable component that displays all fingerprint data for a single match:

**Template: `templates/acrcloud/components/match_detail_card.html`**
- Show all fingerprint values (score, similarity, distance, pattern_matching, risk)
- Display time offset information in milliseconds and seconds
- Show external IDs and platform links
- Color-code risk levels
- Display time skew and frequency skew if available

#### 1.2 Enhanced Analysis Report Template
Update `analysis_report.html` to:
- Display comprehensive match details using the new card component
- Show ALL matches, not just top 5
- Group by match type (music/fingerprint, cover, lyrics)
- Add expandable sections for detailed fingerprint values
- Include time offset visualization

#### 1.3 Create Dedicated Fingerprint Analysis View
New template: `templates/acrcloud/fingerprint_analysis.html`
- Dedicated page for deep-dive fingerprint analysis
- Table with ALL fingerprint columns visible
- Sortable by score, similarity, risk, etc.
- Filterable by match type
- Export to CSV functionality

### Phase 2: Lyrics Analysis Integration (Next)

#### 2.1 Service Enhancement
Update `service.py` to capture lyrics analysis:
- Check for lyrics data in ACRCloud responses
- Store in `AnalysisReport.lyrics_matches`
- Extract lyrics similarity scores
- Detect language from lyrics

#### 2.2 Display Lyrics Matches
- Add lyrics matches section to analysis report
- Show lyrics similarity scores
- Display language detection results
- Link to original lyrics source if available

### Phase 3: Data Enrichment (Future)

#### 3.1 Platform Links
- Generate clickable links to Spotify, Deezer, YouTube
- Show album artwork from platforms
- Display streaming statistics if available

#### 3.2 Visualizations
- Timeline showing match segments
- Score distribution histogram
- Risk level gauge chart
- Pattern matching visualization

### Phase 4: Advanced Features (Future)

#### 4.1 Comparison View
- Side-by-side comparison of uploaded track vs. matched tracks
- Waveform comparison if possible
- Highlight matching segments

#### 4.2 Export and Reporting
- PDF report generation with all fingerprint data
- CSV export of all matches
- API endpoint for programmatic access

## Implementation Details

### Template Structure

```
templates/acrcloud/
├── components/
│   ├── match_detail_card.html          [NEW] - Detailed match card with all fingerprint values
│   ├── fingerprint_values_table.html   [NEW] - Table showing all fingerprint metrics
│   ├── time_offset_display.html        [NEW] - Time offset visualization
│   └── platform_links.html             [NEW] - Platform ID links
├── analysis_report.html                [ENHANCE] - Add comprehensive match details
├── fingerprint_analysis.html           [NEW] - Dedicated fingerprint analysis page
├── pattern_matching_report.html        [ENHANCE] - Add missing fingerprint columns
└── song_detail.html                    [KEEP AS IS]
```

### Views Enhancement

Add new view: `FingerprintAnalysisView`
- URL: `/acrcloud/analysis/<uuid:analysis_id>/fingerprints/`
- Show comprehensive fingerprint data table
- Provide filtering and sorting
- Include export functionality

### Service Enhancement

Update `ACRCloudMetadataProcessor._extract_pattern_matching_data()`:
```python
def _extract_pattern_matching_data(self, match_data: dict, track_info: dict) -> dict:
    """Extract ALL pattern matching and fingerprint analysis data"""
    pattern_data = {
        # Basic match info
        'offset': match_data.get('offset', 0),
        'played_duration': match_data.get('played_duration', 0),
        'type': match_data.get('type', 'unknown'),
        
        # Fingerprint scores
        'score': track_info.get('score', 0),
        'similarity': track_info.get('similarity', 0),
        'distance': track_info.get('distance', 0),
        'pattern_matching': track_info.get('pattern_matching', 0),
        'risk': track_info.get('risk', 0),
        
        # Match metadata
        'match_type': track_info.get('match_type', 'unknown'),
        'result_from': track_info.get('result_from', 0),
        
        # Duration info
        'duration_ms': track_info.get('duration_ms', 0),
        
        # Time offsets (DB = database track)
        'db_begin_time_offset_ms': track_info.get('db_begin_time_offset_ms', 0),
        'db_end_time_offset_ms': track_info.get('db_end_time_offset_ms', 0),
        
        # Time offsets (Sample = uploaded track)
        'sample_begin_time_offset_ms': track_info.get('sample_begin_time_offset_ms', 0),
        'sample_end_time_offset_ms': track_info.get('sample_end_time_offset_ms', 0),
        
        # Play offset
        'play_offset_ms': track_info.get('play_offset_ms', 0),
        
        # Skew analysis
        'time_skew': track_info.get('time_skew'),
        'frequency_skew': track_info.get('frequency_skew'),
        
        # External IDs
        'external_ids': track_info.get('external_ids', {}),
        
        # Metadata
        'label': track_info.get('label', ''),
        'release_date': track_info.get('release_date', ''),
    }
    
    return pattern_data
```

### Model Enhancement (Optional)

Consider adding explicit fields to `ACRCloudTrackMatch` for frequently accessed values:
```python
class ACRCloudTrackMatch(models.Model):
    # ... existing fields ...
    
    # Fingerprint metrics (for easier querying)
    similarity = models.FloatField(null=True, blank=True, help_text="Similarity score (0-1)")
    distance = models.FloatField(null=True, blank=True, help_text="Distance metric")
    pattern_matching_score = models.FloatField(null=True, blank=True, help_text="Pattern matching %")
    risk_score = models.IntegerField(null=True, blank=True, help_text="Risk score (0-100)")
    
    # Time offsets (for easier querying and display)
    db_begin_ms = models.IntegerField(null=True, blank=True)
    db_end_ms = models.IntegerField(null=True, blank=True)
    sample_begin_ms = models.IntegerField(null=True, blank=True)
    sample_end_ms = models.IntegerField(null=True, blank=True)
    play_offset_ms = models.IntegerField(null=True, blank=True)
    
    # Skew analysis
    time_skew = models.FloatField(null=True, blank=True)
    frequency_skew = models.FloatField(null=True, blank=True)
```

## Data Fields Reference

### ACRCloud File Scanning Response Structure
```json
{
  "results": {
    "music": [
      {
        "offset": 0.0,
        "played_duration": 180.5,
        "type": "music",
        "result": {
          "acrid": "...",
          "title": "Song Title",
          "artists": [{"name": "Artist Name"}],
          "album": {"name": "Album Name"},
          "label": "Record Label",
          "isrc": "USRC12345678",
          "external_ids": {
            "isrc": "USRC12345678",
            "upc": "123456789012"
          },
          "external_metadata": {
            "spotify": {
              "track": {"id": "spotify_track_id"},
              "artists": [{"id": "spotify_artist_id"}],
              "album": {"id": "spotify_album_id"}
            },
            "deezer": {...},
            "youtube": {"vid": "youtube_video_id"}
          },
          "score": 95,
          "similarity": 0.95,
          "distance": 0.05,
          "pattern_matching": 95,
          "risk": 90,
          "match_type": "exact",
          "result_from": 1,
          "duration_ms": 180000,
          "db_begin_time_offset_ms": 0,
          "db_end_time_offset_ms": 180000,
          "sample_begin_time_offset_ms": 0,
          "sample_end_time_offset_ms": 180000,
          "play_offset_ms": 0,
          "time_skew": 1.0,
          "frequency_skew": 1.0
        }
      }
    ],
    "cover_songs": [...],
    "lyrics": [...]
  }
}
```

### Fingerprint Values Explanation

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `score` | int | 0-100 | Overall confidence score of the match |
| `similarity` | float | 0-1 | Audio similarity metric (sometimes 0-100) |
| `distance` | float | 0-1+ | Distance metric (lower = more similar) |
| `pattern_matching` | int | 0-100 | Pattern matching percentage |
| `risk` | int | 0-100 | Fraud/duplicate risk score (higher = more risk) |
| `match_type` | string | - | Type: exact, cover, similar |
| `result_from` | int | 1-3 | 1=fingerprint, 2=cover, 3=both |
| `play_offset_ms` | int | ms | Where match starts in reference track |
| `db_begin_time_offset_ms` | int | ms | Database track segment start |
| `db_end_time_offset_ms` | int | ms | Database track segment end |
| `sample_begin_time_offset_ms` | int | ms | Uploaded sample segment start |
| `sample_end_time_offset_ms` | int | ms | Uploaded sample segment end |
| `time_skew` | float | ~0.9-1.1 | Temporal distortion (1.0 = no distortion) |
| `frequency_skew` | float | ~0.9-1.1 | Pitch distortion (1.0 = no distortion) |

## Priority Implementation Order

### Immediate (This Week)
1. ✅ Create detailed match card component showing all fingerprint values
2. ✅ Update `analysis_report.html` to use new component
3. ✅ Add time offset display in milliseconds and seconds
4. ✅ Show external IDs and ISRC/UPC codes

### Short-term (Next Week)
1. ⬜ Create dedicated fingerprint analysis table view
2. ⬜ Add sorting and filtering capabilities
3. ⬜ Implement CSV export
4. ⬜ Add lyrics analysis integration

### Medium-term (Next Sprint)
1. ⬜ Add visualizations (timeline, charts)
2. ⬜ Create platform links (Spotify, Deezer, YouTube)
3. ⬜ Add comparison view
4. ⬜ Implement PDF report generation

## Questions for Clarification

1. **PDF Content**: Since I cannot read the PDF directly, can you confirm which specific fingerprint values are most important to display prominently?

2. **Lyrics Analysis**: Is lyrics analysis a priority? ACRCloud supports it but it may not always return results.

3. **Display Format**: Do you prefer:
   - A table view with all columns (like the pattern_matching_report.html)?
   - Card-based layout with expandable details?
   - Both options available?

4. **Data Completeness**: Are there specific ACRCloud response fields that are currently missing from our capture process?

5. **Export Format**: What format do you need for exports? CSV, JSON, PDF, or multiple formats?

## Next Steps

1. Review this proposal and confirm priorities
2. Check if the PDF shows additional data fields not covered here
3. Decide on immediate implementation tasks
4. Start with Phase 1.1 and 1.2 (enhanced display components)

## Notes

- All data is already being captured in the `raw_data` JSONField
- Main work is enhancing the display templates
- May need to add some convenience fields to models for easier querying
- Service layer is already extracting pattern matching data correctly
