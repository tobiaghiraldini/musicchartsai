# Chart Cascade Button Implementation

**Date:** 2025-01-26  
**Status:** ✅ Complete

## What Was Added

A new button in the Chart admin change view that allows manually triggering the cascade data flow for charts that aren't part of a scheduled sync.

## User Need

When a chart is not part of a sync schedule, there was no way to:
1. Fetch track metadata for all tracks in the chart
2. Extract and fetch artist metadata
3. Fetch audience data for tracks and artists

This button provides that capability.

## Implementation

### 1. API Endpoint (`trigger_cascade_api`)
- Added URL route: `soundcharts_chart_trigger_cascade`
- Gets all unique tracks from the chart's rankings
- Creates a bulk metadata fetch task
- Triggers the cascade automatically

### 2. Admin View Enhancement
- Added `change_view` override to pass context flag
- Added button via template with AJAX functionality

### 3. Template Enhancement
- Added cascade trigger button in `change_form.html`
- Button shows loading state during processing
- AJAX call to the API endpoint
- User-friendly success/error alerts

## Usage

1. Go to Chart admin → Edit any chart
2. Click "Trigger Cascade Data Fetch" button
3. Confirm the action
4. Background tasks will automatically:
   - Fetch track metadata
   - Extract and link artists
   - Fetch artist metadata
   - Fetch track audience data (Spotify, YouTube, Shazam, Airplay)
   - Fetch artist audience data (Spotify, YouTube, Instagram, TikTok)

## Technical Details

### Endpoint
```
POST /admin/soundcharts/chart/<chart_id>/trigger-cascade/
```

### Response
```json
{
    "success": true,
    "message": "Triggered cascade data fetch for X tracks from 'Chart Name'",
    "task_id": 123,
    "tracks_count": X
}
```

### Task Chain
```
User clicks button
    ↓
trigger_cascade_api() creates MetadataFetchTask
    ↓
fetch_bulk_track_metadata.delay(task.id)
    ↓
For each track:
    - Fetch metadata (extract artists/genres)
    - sync_artists_after_track_metadata.delay()
    - sync_track_audience.delay()
    ↓
For each artist:
    - sync_artist_metadata_bulk.delay()
    - sync_artist_audience.delay()
    ↓
All data complete
```

## Code Changes

### `apps/soundcharts/admin_views/chart_admin.py`
- Added `trigger_cascade_api()` method
- Added `change_view()` override
- Added URL route in `get_urls()`
- Added `messages` import

### `apps/soundcharts/templates/admin/soundcharts/chart/change_form.html`
- Added cascade trigger button
- Added AJAX JavaScript function
- Added loading state handling

## Benefits

✅ **Manual trigger for unscheduled charts**  
✅ **Same automated flow as scheduled charts**  
✅ **Background processing (non-blocking)**  
✅ **Visual feedback (loading state, success/error alerts)**  
✅ **Complete cascade** (metadata → artists → audience)

