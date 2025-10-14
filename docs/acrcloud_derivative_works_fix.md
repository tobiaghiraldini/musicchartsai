# ACRCloud Derivative Works Detection - Data Format Fix

## Summary
Fixed webhook processor to handle new data format from ACRCloud when derivative works detection is enabled.

## Date
October 14, 2025

## Problem
After enabling derivative works detection in ACRCloud, the webhook processor was failing with:
```
AttributeError: 'list' object has no attribute 'get'
```

The error occurred because ACRCloud now returns certain fields as empty lists `[]` instead of empty dictionaries `{}` when data is not available.

## Root Cause Analysis

### Changed Fields
When derivative works detection is enabled, ACRCloud can return these fields as either:
- **Empty list `[]`** when no data is available
- **Dictionary `{}`** when data exists

Affected fields:
1. `external_metadata` - Platform metadata (Spotify, Deezer, YouTube, etc.)
2. `external_ids` - External identifiers (ISRC, UPC, etc.)

### New Fields with Derivative Works Detection
The webhook now includes additional fingerprint analysis fields:
- `engine_type` - Detection engine used (1, 2, or 3)
- `time_skew` - Temporal distortion detection
- `frequency_skew` - Pitch/frequency distortion detection
- `file_duration` - Duration of the analyzed file

## Solution Implemented

### 1. Data Normalization Helper Methods
Added two helper methods to `apps/acrcloud/service.py`:

```python
def _normalize_external_metadata(self, external_metadata):
    """Normalize external_metadata to always return a dict."""
    if isinstance(external_metadata, list):
        return {}
    return external_metadata if isinstance(external_metadata, dict) else {}

def _normalize_external_data(self, data):
    """Normalize any external data field to always return a dict."""
    if isinstance(data, list):
        return {}
    return data if isinstance(data, dict) else {}
```

### 2. Updated Track Creation/Update Logic
Modified `_create_or_update_track()` method in `apps/acrcloud/service.py`:

**Before:**
```python
isrc = track_info.get('external_ids', {}).get('isrc')
musicbrainz_id = track_info.get('external_metadata', {}).get('musicbrainz', {})...
```

**After:**
```python
external_ids = self._normalize_external_data(track_info.get('external_ids', {}))
external_meta = self._normalize_external_metadata(track_info.get('external_metadata', {}))

isrc = external_ids.get('isrc')
musicbrainz_id = external_meta.get('musicbrainz', {})...
```

### 3. Enhanced Pattern Matching Data Extraction
Updated `_extract_pattern_matching_data()` to capture derivative works detection fields:

```python
# Extract derivative works detection fields from match_data
if 'engine_type' in match_data:
    pattern_data['engine_type'] = match_data['engine_type']
if 'time_skew' in match_data:
    pattern_data['time_skew'] = match_data['time_skew']
if 'frequency_skew' in match_data:
    pattern_data['frequency_skew'] = match_data['frequency_skew']
if 'file_duration' in match_data:
    pattern_data['file_duration'] = match_data['file_duration']
```

### 4. Handle Missing ACRCloud IDs
Some derivative works matches don't have an `acrid` field. Updated to handle this:

```python
acrcloud_id=track_info.get('acrid') or '',  # Provide default empty string
```

### 5. Model Enhancement
Added property methods to `ACRCloudTrackMatch` model for easy access to stored data:

```python
@property
def track_info(self):
    """Get track info from raw_data"""
    return self.raw_data.get('track_info', {})

@property
def engine_type(self):
    """Get engine type used for detection"""
    return self.match_data.get('engine_type')

@property
def time_skew(self):
    """Get time skew value"""
    return self.match_data.get('time_skew')

@property
def frequency_skew(self):
    """Get frequency skew value"""
    return self.match_data.get('frequency_skew')
```

## Template Mapping

### Enhanced Analysis Report Template
Location: `templates/acrcloud/components/match_detail_card.html`

Fields correctly mapped:
- ✅ `match.raw_data.pattern_matching.time_skew` (lines 206-217)
- ✅ `match.raw_data.pattern_matching.frequency_skew` (lines 220-232)
- ✅ All time offset fields (db_begin, db_end, sample_begin, sample_end)
- ✅ Play offset, duration, score, similarity, distance, risk

### Pattern Matching Report Template
Location: `templates/acrcloud/pattern_matching_report.html`

Table columns correctly mapped:
- ✅ **Time Skew** column (line 321-326): `match.raw_data.pattern_matching.time_skew`
- ✅ **Frequency Skew** column (line 328-333): `match.raw_data.pattern_matching.frequency_skew`
- ✅ **Similarity** column (line 286-291): `match.raw_data.pattern_matching.similarity`
- ✅ **Distance** column (line 293-298): `match.raw_data.pattern_matching.distance`
- ✅ **Pattern %** column (line 300-305): `match.raw_data.pattern_matching.pattern_matching`
- ✅ **Risk** column (line 307-314): `match.raw_data.pattern_matching.risk`

## Testing Results

Processed sample webhook with 77 music matches and 14 cover songs:
- ✅ All matches processed successfully
- ✅ No AttributeError exceptions
- ✅ external_metadata and external_ids correctly normalized
- ✅ Missing acrid fields handled gracefully
- ✅ Derivative works detection fields captured:
  - 77/77 music matches have time_skew data
  - 77/77 music matches have frequency_skew data
  - 91/91 total matches have engine_type data

## Files Modified

1. **apps/acrcloud/service.py**
   - Added `_normalize_external_metadata()` method
   - Added `_normalize_external_data()` method
   - Updated `_create_or_update_track()` to use normalization
   - Enhanced `_extract_pattern_matching_data()` to capture derivative works fields
   - Added handling for missing `acrid` values

2. **apps/acrcloud/models.py**
   - Added property methods to `ACRCloudTrackMatch` for easier data access
   - Properties: `track_info`, `match_data`, `pattern_matching`, `engine_type`, `time_skew`, `frequency_skew`, `match_type_detail`

## Backward Compatibility

✅ The fix maintains backward compatibility:
- Old webhook format (dict only) continues to work
- New webhook format (with lists) is now supported
- Templates work with both old and new data
- Fallback logic ensures missing fields don't cause errors

## Data Structure Examples

### Before (without derivative works detection):
```json
{
  "external_metadata": {
    "spotify": {...},
    "deezer": {...}
  },
  "external_ids": {
    "isrc": "...",
    "upc": "..."
  }
}
```

### After (with derivative works detection):
```json
{
  "engine_type": "1",
  "time_skew": -0.006,
  "frequency_skew": 0,
  "file_duration": 223,
  "result": {
    "external_metadata": [],  // Can be empty list!
    "external_ids": {
      "isrc": "..."
    }
  }
}
```

## Next Steps

1. ✅ Monitor production webhooks to ensure no errors
2. Consider adding engine_type, time_skew, and frequency_skew as dedicated model fields in future for better querying
3. Add admin interface filters for derivative works detection fields
4. Create visualizations for skew analysis in future iterations

