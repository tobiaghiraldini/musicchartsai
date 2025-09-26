# Platform Duplicate Records Fix

## Problem Description

The track audience charts were failing with the error:
```
Internal Server Error: /soundcharts/audience/chart/98aca268-7180-4af0-b8e1-d51ff3bc3cf9/youtube/
Error in AudienceChartView: get() returned more than one Platform -- it returned 2!
```

This error occurred because there were duplicate `Platform` records with the same `slug` field, causing `Platform.objects.get(slug=platform_slug)` to fail when it expected exactly one result but found multiple.

## Root Cause Analysis

The issue was caused by duplicate Platform records created at different times:

1. **YouTube platforms**: 
   - ID 41: "YouTube" (created: 2025-08-27) - had 10 audience records
   - ID 43: "Youtube" (created: 2025-09-26) - had 0 audience records

2. **Spotify platforms**:
   - ID 38: "Spotify" (created: 2025-08-27) - had 578 audience records  
   - ID 45: "Spotify" (created: 2025-09-26) - had 0 audience records

3. **Deezer platforms**:
   - ID 28: "Deezer" (created: 2025-08-27) - had 0 audience records
   - ID 44: "Deezer" (created: 2025-09-26) - had 0 audience records

The duplicates were likely created by the `get_or_create()` method in the audience data processor when platform slugs were not consistently formatted.

## Solution Implemented

### 1. Data Cleanup
- Identified all duplicate Platform records by slug using Django ORM queries
- Deleted the newer duplicate platforms (IDs 43, 45, 44) that had no related audience data
- Kept the older platforms (IDs 41, 38, 28) that contained the actual data

### 2. Database Constraint
- Added `unique=True` constraint to the `Platform.slug` field in the model
- Created and applied migration `0020_add_unique_constraint_to_platform_slug.py`
- This prevents future duplicate platforms from being created

### 3. Code Changes
```python
# Before
slug = models.CharField(max_length=255)

# After  
slug = models.CharField(max_length=255, unique=True)
```

## Verification

After the fix:
- ✅ `Platform.objects.get(slug='youtube')` returns exactly one record
- ✅ `Platform.objects.get(slug='spotify')` returns exactly one record  
- ✅ `Platform.objects.get(slug='deezer')` returns exactly one record
- ✅ The specific failing URL `/soundcharts/audience/chart/98aca268-7180-4af0-b8e1-d51ff3bc3cf9/youtube/` now works correctly

## Prevention

The unique constraint on `Platform.slug` will prevent this issue from recurring. Any future attempts to create duplicate platforms with the same slug will result in a database integrity error, which should be handled gracefully in the application code.

## Related Files Modified

- `apps/soundcharts/models.py` - Added unique constraint to Platform.slug
- `apps/soundcharts/migrations/0020_add_unique_constraint_to_platform_slug.py` - Database migration
- Database cleanup via Django shell commands

## Testing

The fix was verified by:
1. Testing `Platform.objects.get()` calls for all affected slugs
2. Testing the specific URL pattern that was failing
3. Confirming no data loss occurred (older platforms with data were preserved)
4. Verifying the unique constraint works as expected
