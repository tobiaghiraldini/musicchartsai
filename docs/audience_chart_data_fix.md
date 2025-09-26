# Audience Chart Data Verification and Fix

## Issue Identified

The audience line charts were showing older datetime data points instead of the most recent ones. This was caused by an incorrect data ordering logic in the `TrackAudienceTimeSeries.get_chart_data()` method.

## Root Cause

In `apps/soundcharts/models.py`, the `get_chart_data()` method had the following problematic logic:

```python
# Order first, then apply limit
queryset = queryset.order_by('date')  # Orders by date ASCENDING (oldest first)

if limit:
    queryset = queryset[:limit]  # Takes first N records (oldest)
```

**The Problem:**
- Data was ordered by `'date'` (ascending), meaning oldest dates first
- When `limit=30` was applied, it took the first 30 records, which were the **oldest** 30 records
- The frontend calls `/soundcharts/audience/chart/${trackUuid}/${platformSlug}/?limit=30`
- Users saw the oldest 30 data points instead of the most recent 30

## Solution Implemented

Fixed the data ordering logic to:

1. **First**: Order by `'-date'` (descending) to get most recent records first
2. **Second**: Apply the limit to get the most recent N records
3. **Third**: Reorder by `'date'` (ascending) for proper chart display (oldest to newest)

```python
# Order by date descending to get most recent records first
queryset = queryset.order_by('-date')

if limit:
    queryset = queryset[:limit]

# Reorder by date ascending for proper chart display (oldest to newest)
queryset = queryset.order_by('date')
```

## Files Modified

- `apps/soundcharts/models.py` - Fixed `TrackAudienceTimeSeries.get_chart_data()` method
- `debug_audience_charts.py` - Created debugging script for verification

## Verification

Use the debugging script to verify the fix:

```bash
# Test all tracks with audience data
python debug_audience_charts.py

# Test a specific track
python debug_audience_charts.py <track_uuid>
```

The script will:
- Show total data points available
- Display latest and oldest dates in the database
- Show what the chart data method returns
- Verify that chart data shows the most recent records
- Check that the limit is working correctly

## Expected Behavior After Fix

- Charts will show the most recent 30 data points (when limit=30)
- Chart dates will match the latest dates visible in the admin interface
- Data will be properly ordered from oldest to newest for smooth line chart display
- No more discrepancies between admin view and chart data

## Testing Recommendations

1. **Before testing**: Note the latest dates visible in the admin interface for tracks with audience data
2. **After fix**: Check that the charts show the same latest dates
3. **Verify**: Use the debug script to confirm data consistency
4. **Test edge cases**: Tracks with fewer than 30 data points should show all available data

## Related Code

- **Frontend**: `templates/soundcharts/song_audience_detail.html` - Calls API with `limit=30`
- **API**: `apps/soundcharts/views.py` - `AudienceChartView._get_single_platform_data()`
- **Model**: `apps/soundcharts/models.py` - `TrackAudienceTimeSeries.get_chart_data()`
- **URL**: `/soundcharts/audience/chart/<track_uuid>/<platform_slug>/?limit=30`
