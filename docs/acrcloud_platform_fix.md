# ACRCloud Platform Creation Fix

## Problem

The ACRCloud webhook processing was failing with a duplicate key constraint error:

```
duplicate key value violates unique constraint "soundcharts_platform_slug_4ff76fab_uniq"
DETAIL: Key (slug)=(deezer) already exists.
```

## Root Cause

The issue was in the `_create_platform_mappings` method in `apps/acrcloud/service.py`. The code was using `get_or_create` with `platform_identifier` as the lookup field, but trying to create platforms with `slug` values that might already exist:

```python
# PROBLEMATIC CODE
platform, created = Platform.objects.get_or_create(
    platform_identifier=platform_name,  # Lookup by platform_identifier
    defaults={
        'name': platform_name.title(),
        'slug': platform_name.lower(),  # But slug might already exist!
        'platform_type': 'streaming'
    }
)
```

This caused issues when:
1. A platform with `slug='deezer'` already existed
2. But had a different `platform_identifier` 
3. The code would try to create a new platform with the same slug
4. Violating the unique constraint on the `slug` field

## Solution

### 1. Fixed Platform Lookup Strategy

Changed the lookup field from `platform_identifier` to `slug` since `slug` has the unique constraint:

```python
# FIXED CODE
platform_slug = platform_name.lower()
platform, created = Platform.objects.get_or_create(
    slug=platform_slug,  # Use slug as the unique identifier
    defaults={
        'name': platform_name.title(),
        'platform_identifier': platform_name,
        'platform_type': 'streaming'
    }
)
```

### 2. Added Error Handling and Logging

Added comprehensive error handling to all metadata creation methods:

- `_create_platform_mappings()` - Platform creation
- `_create_or_update_artists()` - Artist creation  
- `_create_or_update_album()` - Album creation
- `_create_or_update_genres()` - Genre creation

Each method now:
- Wraps database operations in try-catch blocks
- Logs success/failure messages
- Continues processing other items if one fails
- Prevents the entire webhook processing from failing due to one duplicate

### 3. Enhanced Logging

Added detailed logging to track:
- When new platforms/artists/albums/genres are created
- When existing ones are reused
- When errors occur during creation
- Platform mapping creation success/failure

## Testing

Created test command `test_platform_creation.py` to verify:
- Platform creation works with existing platforms
- No duplicate key constraint errors occur
- Error handling works correctly
- End-to-end webhook processing succeeds

## Impact

- ✅ **Fixed duplicate key constraint errors** in production
- ✅ **Made webhook processing more robust** - individual failures don't crash the entire process
- ✅ **Added comprehensive logging** for better debugging
- ✅ **Maintained backward compatibility** - existing platforms continue to work
- ✅ **Improved error resilience** - system continues processing even if some metadata creation fails

## Files Modified

- `apps/acrcloud/service.py` - Fixed platform creation logic and added error handling
- `apps/acrcloud/management/commands/test_platform_creation.py` - New test command

The fix ensures that ACRCloud webhook processing is robust and won't fail due to duplicate platform creation attempts.
