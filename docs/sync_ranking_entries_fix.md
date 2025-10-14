# Chart Sync Ranking Entries Fix

## Issue
The automated chart sync was creating `ChartRanking` records but NOT creating `ChartRankingEntry` records (the actual songs in the ranking). This made the rankings useless as they had no song data.

## Root Cause
The `_process_ranking_entries()` function in `apps/soundcharts/tasks.py` was using incorrect field names to extract data from the Soundcharts API response.

### API Response Structure
The Soundcharts API returns data in this format:
```json
{
  "items": [
    {
      "song": {
        "uuid": "...",
        "name": "...",
        "creditName": "...",
        "imageUrl": "..."
      },
      "position": 1,
      "oldPosition": 1,
      "positionEvolution": 0,
      "timeOnChart": 55
    }
  ]
}
```

### Incorrect Field Mapping (Before Fix)
The code was looking for fields at the wrong level:
- `item_data.get('uuid')` → **WRONG** (uuid is nested inside `song`)
- `item_data.get('name')` → **WRONG** (name is nested inside `song`)
- `item_data.get('previousPosition')` → **WRONG** (API uses `oldPosition`)
- `item_data.get('positionChange')` → **WRONG** (API uses `positionEvolution`)
- `item_data.get('weeksOnChart')` → **WRONG** (API uses `timeOnChart`)

Since `track_uuid` was always `None`, the function would skip to the next item without creating any entries.

### Correct Field Mapping (After Fix)
```python
# Extract song data from nested object
song_data = item_data.get('song', {})
track_uuid = song_data.get('uuid')
track_name = song_data.get('name', '')
credit_name = song_data.get('creditName', '')
image_url = song_data.get('imageUrl', '')

# Extract position data with correct field names
position = item_data.get('position', 0)
old_position = item_data.get('oldPosition')
position_evolution = item_data.get('positionEvolution')
time_on_chart = item_data.get('timeOnChart')
```

## Files Changed

### `apps/soundcharts/tasks.py`

1. **`_process_ranking_entries()` function (lines 535-608)**
   - Fixed field extraction to access nested `song` object
   - Corrected API field names: `oldPosition`, `positionEvolution`, `timeOnChart`
   - Added comprehensive logging for debugging
   - Added `entries_created` counter to track how many ranking entries are created

2. **`sync_chart_rankings_task()` function (lines 298-322)**
   - Enhanced logging to show API response details
   - Log number of items returned from API
   - Log number of entries created per ranking
   - Better error tracking

## How It Works Now

### Immediate Sync (Manual "Add to Sync")
1. User clicks "Add to Sync" button
2. Creates `ChartSyncSchedule` with `sync_immediately=True`
3. Model's `save()` triggers `_trigger_immediate_sync()`
4. Creates `ChartSyncExecution` and queues Celery task
5. Task fetches rankings from API
6. **Now correctly creates `ChartRanking` AND `ChartRankingEntry` records**

### Scheduled Sync
1. Periodic task `process_scheduled_chart_syncs` runs every 5 minutes
2. Finds schedules where `next_sync_at` has passed
3. Creates executions and queues sync tasks
4. **Now correctly creates both ranking and entry records**

## Verification

Check Celery logs for these messages:
```
INFO: API returned {N} items for {chart_name} on {date}
INFO: Created new track: {track_name} ({uuid})
INFO: Created ranking entry: Position {N} - {track_name}
INFO: Created {N} ranking entries for ranking {id}
INFO: Successfully processed ranking for {chart_name} on {date}: {N} entries created
```

## Testing
1. Click "Add to Sync" on a chart in admin
2. Check Celery logs to verify task execution
3. Verify `ChartRanking` record created in database
4. **Verify `ChartRankingEntry` records created (should match API items count)**
5. Check ranking entries in admin view - should now show songs

## Related Code
The manual import functionality in `apps/soundcharts/admin_views/chart_admin.py` (`store_rankings_api` method, lines 1954-2001) already had the correct field mapping. The automated sync task now matches this implementation.

