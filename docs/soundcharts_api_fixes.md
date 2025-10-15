# Soundcharts API Fixes - October 2025

## Summary

Fixed two critical issues with the Soundcharts API integration based on official [API documentation](https://doc.api.soundcharts.com).

## Issues Fixed

### 1. Artist Search - Limit Parameter Exceeds API Maximum ✅

**Issue:** Artist search was failing with `400 Bad Request`

**Root Cause:**
- Service was requesting `limit=100` results
- Soundcharts API has a **maximum of 20 results per request**
- Reference: [Search artist by name](https://doc.api.soundcharts.com/documentation/reference/search/search-artist-by-name)

**Fix:**
```python
# Before (WRONG):
def search_artists(self, q, limit=100, offset=0):

# After (CORRECT):
def search_artists(self, q, limit=20, offset=0):
    params = {"limit": min(limit, 20), "offset": offset}  # Enforce max
```

**Files Modified:**
- `apps/soundcharts/service.py` - Line 164

**Test Result:**
```bash
✅ Search for "busta rhymes" now returns 20 results successfully
```

---

### 2. Artist Audience - Wrong Endpoint URL ✅

**Issue:** Artist audience fetch was failing with `400 Bad Request`

**Root Cause:**
- Service was using: `/api/v2/artist/{uuid}/audience/{platform}/report/{date}` ❌
- Correct endpoint: `/api/v2/artist/{uuid}/audience/{platform}` ✅
- The `/report/{date}` part is for a **different endpoint** (audience reports with demographics)
- Reference: [Get audience](https://doc.api.soundcharts.com/documentation/reference/artist/get-audience)

**Fix:**
```python
# Before (WRONG):
url = f"{self.api_url}/api/v2/artist/{uuid}/audience/{platform}/report/{date}"

# After (CORRECT):
url = f"{self.api_url}/api/v2/artist/{uuid}/audience/{platform}"
# Optional query params: startDate, endDate (format YYYY-MM-DD)
```

**Response Structure Change:**
```python
# Expected (from docs):
{
    "related": {
        "artist": {...},
        "platform": "spotify",
        "lastCrawlDate": "..."
    },
    "items": [  # NOT "plots"!
        {"date": "2025-10-15T00:00:00+00:00", "followerCount": 3150182, ...}
    ],
    "page": {"offset": 0, "limit": 100, "total": 112}
}
```

**Files Modified:**
1. `apps/soundcharts/service.py`:
   - Updated `get_artist_audience_for_platform()` method
   - Changed signature from `date='latest'` to `start_date=None, end_date=None`
   - Uses query parameters instead of path parameters

2. `apps/soundcharts/admin_views/artist_admin.py`:
   - Updated `_process_artist_audience_data()` to handle correct response structure
   - Changed from checking `"object"` to `"items"`
   - Changed from `plots` to `items` array
   - Updated date parsing to handle ISO format timestamps

3. `apps/soundcharts/templates/admin/soundcharts/artist/change_form.html`:
   - Removed unused date selector
   - Added common social platforms to dropdown
   - Added helper text: "Returns latest 90 days of follower/like counts"

**Test Result:**
```bash
✅ Busta Rhymes (UUID: 11e81bc9-c011-e434-b2f8-a0369fe50396)
   Platform: Spotify
   Latest Follower Count: 3,150,182
   Time-series data points: 112 (90 days)
```

---

## API Endpoints Reference

### Search Artists
```
GET /api/v2/artist/search/{term}
Query params: limit (max 20), offset
Returns: Artist collection
```

### Get Artist Metadata
```
GET /api/v2.9/artist/{uuid}
Returns: Full artist details
```

### Get Artist Audience (Time-Series)
```
GET /api/v2/artist/{uuid}/audience/{platform}
Query params (optional): startDate, endDate (YYYY-MM-DD, max 90 days)
Returns: Follower/like counts over time
```

### Get Artist Audience Report (Demographics) - Different Endpoint!
```
GET /api/v2/artist/{uuid}/audience/{platform}/report/{date}
Returns: Age, gender, geographic demographics for a specific date
Note: This is a DIFFERENT endpoint with DIFFERENT response structure
```

## Available Platforms

According to [Get audience documentation](https://doc.api.soundcharts.com/documentation/reference/artist/get-audience), supported platforms include:

- `spotify` - Follower count
- `instagram` - Follower count, following count, post count
- `youtube` - Subscriber count, view count
- `tiktok` - Follower count, like count, post count
- `facebook` - Like count
- `twitter` (X) - Follower count, like count, post count
- `soundcloud` - Follower count, like count, post count
- `mixcloud`, `patreon`, `triller`, `weibo` - Various metrics

## Data Stored

The artist audience fetch now correctly stores:

### ArtistAudienceTimeSeries Model
- `artist` - ForeignKey to Artist
- `platform` - ForeignKey to Platform
- `date` - Date of measurement
- `audience_value` - Follower/like/view count
- `api_data` - Raw item data
- `fetched_at` - Timestamp

### What's NOT Stored
- Demographics (age, gender) - requires different endpoint
- Geographic data (countries, cities) - requires different endpoint
- These are available via `/audience/{platform}/report/{date}` endpoint (not implemented yet)

## Testing

### Test Artist Search
```bash
cd /path/to/project
source venv/bin/activate
python manage.py shell -c "
from apps.soundcharts.service import SoundchartsService
service = SoundchartsService()
results = service.search_artists('taylor swift', limit=20)
print(f'Found: {len(results)} artists')
"
```

### Test Artist Audience
```bash
python manage.py shell -c "
from apps.soundcharts.service import SoundchartsService
service = SoundchartsService()
data = service.get_artist_audience_for_platform(
    '11e81bcc-9c1c-ce38-b96b-a0369fe50396',  # Billie Eilish
    platform='spotify'
)
print(f'Data points: {len(data.get(\"items\", []))}')
"
```

### Test in Django Admin
1. Navigate to **Artists** in Django admin
2. Open an artist with a UUID (e.g., search and import "Billie Eilish")
3. Click **"Fetch Metadata from API"** - should work ✅
4. Select a platform (e.g., Spotify)
5. Click **"Fetch Audience Data from API"** - should work ✅
6. Check **Artist Audience Time Series** to see stored data

## Comparison: Audience vs Audience Report Endpoints

| Feature | `/audience/{platform}` | `/audience/{platform}/report/{date}` |
|---------|------------------------|--------------------------------------|
| **Purpose** | Time-series follower counts | Demographics for a specific date |
| **Returns** | 90 days of data points | Single date snapshot |
| **Data** | followerCount, likeCount, viewCount | age groups, gender %, countries, cities |
| **Date param** | Query string (optional) | Path parameter (required) |
| **Response** | `items` array | `object` with demographics |
| **Implemented** | ✅ Yes | ❌ Not yet |

## Future Enhancements

To get demographic data (age, gender, location), implement:

```python
def get_artist_audience_report(self, uuid, platform="spotify", date="latest"):
    """
    Get demographic audience data for a specific date.
    Endpoint: GET /api/v2/artist/{uuid}/audience/{platform}/report/{date}
    """
    url = f"{self.api_url}/api/v2/artist/{uuid}/audience/{platform}/report/{date}"
    # Returns: age groups, gender percentages, top countries/cities
```

This would populate the `ArtistAudience` model with demographic fields.

## Lessons Learned

1. **Always check API documentation** - Don't assume endpoint structures
2. **Respect API limits** - Soundcharts has strict limits (20 results max for search)
3. **Verify response structure** - The actual response may differ from expectations
4. **Different endpoints for different data** - Audience counts vs demographics are separate endpoints

## Related Documentation

- [Soundcharts API Documentation](https://doc.api.soundcharts.com)
- [Artist UUID Validation](artist_uuid_validation.md)
- [Artist Audience Integration](artist_audience_integration.md)
- [Artist Admin Form Validation Fix](artist_audience_form_validation_fix.md)

