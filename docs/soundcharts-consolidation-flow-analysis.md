# Soundcharts Data Flow Consolidation - Analysis & Proposed Solutions

**Date:** 2025-01-26  
**Status:** Analysis Complete - Ready for Implementation

## Executive Summary

This document analyzes the current manual flow for fetching artist music analytics data and proposes an automated, consolidated solution using existing Celery background tasks.

## Current Problem

### Current Manual Flow
1. **Fetch Chart Rankings** → Creates tracks in ChartRankingEntry records
2. **Fetch Track Metadata** → Manually click buttons to fetch metadata for each track
3. **Fetch Artist Metadata** → Manually click buttons for each artist extracted from tracks
4. **Fetch Track Audience** → Manually fetch audience data for tracks (YouTube, Shazam, Spotify, Airplay)
5. **Fetch Artist Audience** → Manually fetch audience data for artists
6. **View Analytics** → Only then can users see complete artist analytics

### Problems
- **Missing Automation**: No automatic cascade from chart sync to metadata to audience data
- **Incomplete Data**: Important tracks may be forgotten if not manually selected
- **Inconsistent State**: Artist list may not reflect all artists found in charts
- **Manual Bottleneck**: Too many manual steps required
- **No Prioritization**: All tracks treated equally, no automation for key tracks

### Current Architecture

```
┌─────────────────┐
│  Chart Sync     │ (Automatic via ChartSyncSchedule)
│  (Task Running) │
└──────┬──────────┘
       │ Creates tracks with minimal data
       ↓
┌──────────────────────┐
│  Track Created       │ (name, uuid, slug, credit_name, image_url)
│  - NO artists linked │
│  - NO metadata       │
│  - NO audience data  │
└──────┬───────────────┘
       │
       ↓ Manual Action Required
┌──────────────────────┐
│  Fetch Track Metadata│ (Manual button click)
│  - Extracts artists   │
│  - Links to tracks    │
│  - Fetches full metadata │
└──────┬───────────────┘
       │
       ↓ Manual Action Required
┌──────────────────────┐
│  Fetch Artist Metadata│ (Manual button click per artist)
│  - Updates artist details │
└──────┬───────────────┘
       │
       ↓ Manual Action Required
┌──────────────────────┐
│  Fetch Track Audience│ (Manual button click)
│  - YouTube, Shazam    │
│  - Spotify, Airplay   │
└──────┬───────────────┘
       │
       ↓ Manual Action Required
┌──────────────────────┐
│  Fetch Artist Audience│ (Manual button click)
│  - YouTube, Shazam    │
│  - Spotify, Airplay   │
└───────────────────────┘
```

## Root Cause Analysis

### What Exists
✅ Chart sync system with Celery tasks  
✅ Track metadata fetching (single + bulk)  
✅ Artist metadata fetching  
✅ Audience data fetching (tracks + artists)  
✅ Task tracking and progress monitoring  

### What's Missing
❌ Automatic cascade from chart sync → metadata → audience  
❌ Automatic artist extraction and metadata fetching  
❌ Automatic audience fetching after metadata  
❌ Prioritized task queuing for key platforms  

### Critical Flow Gaps

1. **Track → Artist Relationship:**
   - Chart rankings create tracks with minimal data
   - Artists are NOT extracted from chart rankings
   - Artists are ONLY extracted when track metadata is fetched
   - But track metadata is never automatically fetched after chart sync

2. **Artist Discovery:**
   - Artists appear in tracks via credit_name in chart rankings
   - But artists table is never populated automatically
   - Relies entirely on manual metadata fetch for tracks

3. **Data Completeness:**
   - Artist analytics requires:
     - Tracks with metadata (artists, genres, etc.)
     - Artist metadata (biography, genres, etc.)
     - Track audience data (for track breakdown)
     - Artist audience data (for overall analytics)
   - Currently, NONE of this is automatic

## Proposed Solutions

### Solution 1: Automated Cascade Flow (Recommended)

**Architecture:**
```
Chart Sync Complete
    ↓
Trigger: Automatically fetch track metadata for new tracks
    ↓
Extract artists from track metadata
    ↓
Trigger: Automatically fetch artist metadata for new artists
    ↓
Trigger: Automatically fetch track audience for key platforms
    ↓
Trigger: Automatically fetch artist audience for key platforms
    ↓
Complete data ready for analytics
```

**Implementation Steps:**

#### Phase 1: Track Metadata Automation
- After chart sync completes, automatically queue metadata fetch for new/updated tracks
- Extract artists from track metadata and link them
- Update track with full metadata

#### Phase 2: Artist Metadata Automation  
- After track metadata fetch completes, check for new artists
- Automatically queue artist metadata fetch for new artists
- Update artist records

#### Phase 3: Audience Data Automation
- After metadata fetch completes, automatically queue audience data fetch
- Priority platforms: Spotify, YouTube, Shazam, Airplay
- Fetch track audience → fetch artist audience

**Code Changes Needed:**

1. **Update `_process_ranking_entries` in `apps/soundcharts/tasks.py`:**
   ```python
   # Add automatic metadata fetch for new tracks
   if track_created:
       # Queue metadata fetch immediately
       fetch_track_metadata.delay(track.uuid)
   ```

2. **Create new task: `sync_artists_from_tracks`:**
   - After track metadata is fetched, extract artists
   - Check if artists need metadata update
   - Queue artist metadata fetch if needed

3. **Create new task: `sync_audience_for_tracks`:**
   - After track metadata is fetched, queue audience fetch
   - For key platforms: spotify, youtube, shazam, airplay

4. **Create new task: `sync_audience_for_artists`:**
   - After artist metadata is fetched, queue artist audience fetch
   - For key platforms: spotify, youtube, shazam, airplay

#### Configuration Options
- Add to `ChartSyncSchedule` model:
  - `auto_fetch_metadata` (boolean, default=True)
  - `auto_fetch_audience` (boolean, default=True)
  - `priority_platforms` (JSON array of platform slugs)
  - `metadata_delay_seconds` (integer, default=0)
  - `audience_delay_seconds` (integer, default=0)

### Solution 2: Periodic Batch Processing (Alternative)

**Architecture:**
- Run periodic task every hour/day
- Find tracks/artists missing metadata or audience data
- Process in batches with rate limiting
- Retry failed items

**Pros:**
- Simpler to implement
- More resilient to API rate limits
- Better for large backlogs

**Cons:**
- Delays between data appearing and being complete
- Not real-time

## Implementation Plan

### Phase 1: Immediate (Auto-Track Metadata)
**Goal:** Automatically fetch metadata for tracks after chart sync

**Changes:**
1. Modify `_queue_track_metadata_tasks()` to be automatic in chart sync
2. Update `_process_ranking_entries()` to always enable metadata fetch
3. Add configuration options to `ChartSyncSchedule`

**Estimated Effort:** 2-3 hours

### Phase 2: Next (Auto-Artist Metadata)
**Goal:** Automatically fetch metadata for artists extracted from tracks

**Changes:**
1. Create new task `sync_artist_metadata_after_track_sync()`
2. Hook into track metadata completion
3. Check for new artists and queue metadata fetch

**Estimated Effort:** 2-3 hours

### Phase 3: Audience Automation
**Goal:** Automatically fetch audience data for tracks and artists

**Changes:**
1. Create new task `sync_track_audience_after_metadata()`
2. Create new task `sync_artist_audience_after_metadata()`
3. Configure priority platforms
4. Add rate limiting

**Estimated Effort:** 3-4 hours

### Phase 4: Optimization & Monitoring
**Goal:** Add smart queuing, priority handling, monitoring

**Changes:**
1. Priority queue for high-importance data
2. Rate limiting configuration
3. Progress monitoring dashboard
4. Error alerting

**Estimated Effort:** 4-5 hours

## Technical Details

### Existing Code to Reuse

**Tasks:**
- `fetch_track_metadata(task, track_uuid)` - Single track metadata
- `fetch_bulk_track_metadata(task, task_id)` - Bulk track metadata  
- `fetch_track_audience_data(task, track_uuid, platforms)` - Track audience
- `sync_chart_rankings_task(task, schedule_id, execution_id)` - Chart sync

**Functions:**
- `_queue_track_metadata_tasks(track_uuids)` - Queue metadata fetch
- `Artist.create_from_soundcharts(artist_data)` - Create artist from API data
- `TrackAdmin.fetch_metadata_api()` - Fetch and process track metadata

### New Code Needed

**New Tasks:**
```python
@shared_task
def sync_artists_after_track_metadata(track_uuid):
    """After track metadata is fetched, sync all its artists"""

@shared_task  
def sync_audience_for_track(track_uuid, platforms):
    """Fetch audience data for track on specified platforms"""

@shared_task
def sync_audience_for_artist(artist_uuid, platforms):
    """Fetch audience data for artist on specified platforms"""

@shared_task
def cascade_data_sync_after_chart_sync(execution_id):
    """Cascade metadata and audience sync after chart sync completes"""
```

**Configuration Model Updates:**
```python
class ChartSyncSchedule(models.Model):
    # Add new fields:
    auto_fetch_track_metadata = models.BooleanField(default=True)
    auto_fetch_artist_metadata = models.BooleanField(default=True)
    auto_fetch_audience = models.BooleanField(default=True)
    priority_platforms = models.JSONField(default=list)
    metadata_delay_seconds = models.IntegerField(default=0)
    audience_delay_seconds = models.IntegerField(default=60)
```

## Benefits

### Immediate
- ✅ Complete automation of data flow
- ✅ No manual button clicking required
- ✅ Artists list automatically consistent with charts
- ✅ All necessary data automatically populated

### Long-term
- ✅ Scalable to handle large chart volumes
- ✅ Resilient to API failures with retries
- ✅ Configurable per chart schedule
- ✅ Monitoring and alerting built-in

## Risks & Mitigation

### API Rate Limits
**Risk:** Too many API calls could hit rate limits  
**Mitigation:** Add configurable delays, batch processing, exponential backoff

### Performance Impact
**Risk:** Heavy background task processing could slow system  
**Mitigation:** Use Celery priorities, resource pools, off-peak processing

### Data Inconsistency
**Risk:** Partial data if process fails mid-way  
**Mitigation:** Transaction safety, atomic operations, retry logic

### Costs
**Risk:** More API calls = more Soundcharts costs  
**Mitigation:** Configurable fetch frequencies, smart caching, selective fetching

## Next Steps

1. Review and approve this proposal
2. Start with Phase 1 (Track Metadata Automation)
3. Implement Phase 1 and test with one chart
4. Roll out to all active charts
5. Proceed to Phase 2, 3, 4 in sequence

## Open Questions

1. Should this be enabled by default for all charts, or opt-in?
2. What should be the default priority platforms?
3. Should we add a "force refresh" option to re-fetch data?
4. How should we handle rate limiting configuration?

