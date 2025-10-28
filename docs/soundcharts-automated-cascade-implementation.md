# Soundcharts Automated Cascade Flow - Implementation Complete

**Date:** 2025-01-26  
**Status:** ✅ Implemented and Ready for Testing

## What Was Implemented

The automated cascade flow for Soundcharts data has been fully implemented in `apps/soundcharts/tasks.py`. The system now automatically:

1. **Chart Sync** → Creates tracks automatically
2. **Track Metadata Fetch** → Extracts artists, genres, and links them to tracks
3. **Artist Metadata Sync** → Fetches full metadata for all artists
4. **Track Audience Data** → Fetches audience data for tracks on key platforms
5. **Artist Audience Data** → Fetches audience data for artists on key platforms

## Changes Made

### 1. Added Missing Imports
```python
from .models import Track, Artist, MetadataFetchTask, ChartSyncSchedule, ChartSyncExecution, 
    Chart, ChartRanking, ChartRankingEntry, Platform, TrackAudienceTimeSeries, ArtistAudienceTimeSeries
```

### 2. Enhanced `fetch_track_metadata` (Single Track)
- Now properly extracts and links genres (hierarchical)
- Now properly extracts and links artists
- Triggers cascade: `sync_artists_after_track_metadata.delay()`
- Triggers cascade: `sync_track_audience.delay()`

### 3. Enhanced `fetch_bulk_track_metadata` (Bulk)
- Already had proper genre/artist extraction
- Now triggers cascade tasks after each successful fetch

### 4. New Cascade Tasks (Already Implemented)

#### `sync_artists_after_track_metadata`
- Extracts artists from track
- Checks which artists need metadata updates
- Queues `sync_artist_metadata_bulk` for new/stale artists

#### `sync_artist_metadata_bulk`
- Fetches metadata for multiple artists
- After successful fetch, triggers `sync_artist_audience.delay()` for each artist

#### `sync_track_audience`
- Fetches audience data for track on: spotify, youtube, shazam, airplay
- Uses `AudienceDataProcessor` for processing

#### `sync_artist_audience`
- Fetches audience data for artist on: spotify, youtube, instagram, tiktok
- Processes time-series data into `ArtistAudienceTimeSeries`

## Data Flow

```
Chart Sync Completes
    ↓
Tracks Created (minimal data)
    ↓
Auto Queue: fetch_track_metadata (bulk)
    ↓
For Each Track:
    - Fetch full metadata from API
    - Extract artists → Link to tracks
    - Extract genres → Link to tracks
    ↓
    Auto Queue: sync_artists_after_track_metadata
    ↓
    - Check which artists need metadata
    - Queue: sync_artist_metadata_bulk
    ↓
    Auto Queue: sync_track_audience
    ↓
    - Fetch audience for: spotify, youtube, shazam, airplay
    
For Each Artist:
    - Fetch full metadata from API
    - Update artist record
    ↓
    Auto Queue: sync_artist_audience
    ↓
    - Fetch audience for: spotify, youtube, instagram, tiktok
```

## Configuration

The cascade is controlled by the `ChartSyncSchedule.fetch_track_metadata` flag (default: `True`).

If this flag is enabled on a schedule:
- Chart sync will automatically trigger track metadata fetch
- Track metadata fetch will automatically cascade to artist/audience fetches

## Platform Configuration

**Track Audience Platforms (default):**
- spotify
- youtube
- shazam
- airplay

**Artist Audience Platforms (default):**
- spotify
- youtube
- instagram
- tiktok

These can be customized by passing a `platforms` parameter to the sync tasks.

## How It Works

### Automatic Triggering

When a chart sync completes:
1. New tracks are created with minimal data (name, uuid, slug, credit_name)
2. If `fetch_track_metadata=True`, tracks are queued for metadata fetch
3. Metadata fetch extracts artists and genres
4. Cascade tasks are automatically triggered

### Smart Sync Logic

The system uses `_should_fetch_artist_metadata()` to determine if artist metadata needs updating:
- Fetches if artist has no metadata (`metadata_fetched_at` is null)
- Fetches if metadata is older than 30 days

This prevents unnecessary API calls while keeping data fresh.

### Error Handling

Each cascade task includes:
- Try/catch blocks to handle API errors gracefully
- Logging for debugging and monitoring
- Failures in one track don't stop the entire batch

## Testing

To test the implementation:

1. **Run a chart sync:**
   - Go to admin → Chart Sync Schedules
   - Create or edit a schedule
   - Ensure `Fetch Track Metadata` is checked
   - Trigger sync manually or wait for scheduled time

2. **Monitor the cascade:**
   - Check Celery logs for cascade task execution
   - Look for: "Processing artist cascade", "Starting audience fetch"
   - Verify tracks get full metadata, artists, genres
   - Check that audience data is fetched

3. **Verify data completeness:**
   - Go to Tracks admin → Check tracks have artists and genres linked
   - Go to Artists admin → Check artists have full metadata
   - Check TrackAudienceTimeSeries and ArtistAudienceTimeSeries tables

## Benefits

✅ **Fully Automated** - No manual button clicking required  
✅ **Complete Data** - All necessary data fetched automatically  
✅ **Consistent State** - Artist list always consistent with charts  
✅ **Smart Syncing** - Only fetches stale data (30-day window)  
✅ **Scalable** - Handles large volumes via Celery

## What's Next

- [ ] Test with real chart sync
- [ ] Monitor for any rate limit issues
- [ ] Add rate limiting if needed
- [ ] Create monitoring dashboard
- [ ] Add configuration for custom platforms

## Notes

- The cascade is **asynchronous** - tasks run in background
- Tasks respect Celery retry policies
- API rate limits are not enforced by this code (consider adding if issues)
- Data freshness is controlled by 30-day cutoff (configurable in code)

