# Song Detail Page with Audience Analytics Integration

## Overview
This document outlines the implementation plan to link each song in the dashboard rankings list to a dedicated audience analytics detail page for that song.

## Current State Analysis

### Existing Components
1. **Rankings Dashboard**: `/rankings/{ranking_id}/songs/` - Shows songs in a specific chart ranking
2. **Audience Analytics**: `/soundcharts/audience/dashboard/` - Shows all songs with audience data
3. **Individual Song Audience Data**: `/soundcharts/audience/chart/{track_uuid}/` - API endpoint for specific song audience data

### Data Models
- `Track`: Contains song information with UUID, name, credit_name, etc.
- `ChartRankingEntry`: Links tracks to chart positions
- `TrackAudienceTimeSeries`: Time-series audience data per platform
- `Platform`: Platform information (Spotify, Apple Music, etc.)

## Implementation Plan

### Phase 1: Create Song Detail View
1. **New URL Pattern**: `/songs/{track_uuid}/audience/`
2. **New View**: `SongAudienceDetailView` in `apps/soundcharts/views.py`
3. **Template**: `templates/soundcharts/song_audience_detail.html`

### Phase 2: Update Rankings Template
1. **Add Links**: Make song names clickable in `ranking_songs_table.html`
2. **Link Format**: Link to `/songs/{track.uuid}/audience/`

### Phase 3: Enhance Song Detail Page
1. **Song Information**: Display track metadata, artist info, genres
2. **Audience Charts**: Show audience performance across platforms
3. **Navigation**: Back to rankings, related songs
4. **Responsive Design**: Mobile-friendly layout

## Technical Implementation

### 1. URL Configuration
```python
# In apps/soundcharts/urls.py
path('songs/<str:track_uuid>/audience/', SongAudienceDetailView.as_view(), name='song_audience_detail'),
```

### 2. View Implementation
```python
class SongAudienceDetailView(View):
    def get(self, request, track_uuid):
        # Get track and audience data
        # Render template with song info and audience charts
```

### 3. Template Structure
- Song header with metadata
- Audience performance charts per platform
- Navigation breadcrumbs
- Related songs section

### 4. Frontend Integration
- Reuse existing audience chart components
- Responsive design with Tailwind CSS
- Dark mode support

## Success Criteria
1. ✅ Songs in rankings are clickable and link to detail pages
2. ✅ Detail pages show comprehensive audience analytics
3. ✅ Navigation is intuitive and consistent
4. ✅ Design is responsive and matches existing UI
5. ✅ Performance is optimized for large datasets

## Future Enhancements
- Add song comparison functionality
- Implement song search and filtering
- Add export capabilities for audience data
- Include social sharing features
