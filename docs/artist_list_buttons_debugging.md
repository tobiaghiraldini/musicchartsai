# Artist List Buttons - Debugging Guide

## Issue
The fetch metadata and fetch audience buttons in the artist list show spinning loader but don't complete the API calls.

## Debugging Steps

### 1. Open Browser Console
1. Navigate to `/soundcharts/artists/`
2. Open Developer Tools (F12 or Right-click → Inspect)
3. Go to Console tab
4. Look for these messages:

**Expected on page load:**
```
CSRF Token available: Yes
CSRF Token length: 64 (or similar)
```

**Expected when clicking Metadata button:**
```
fetchMetadata called for UUID: 11e81bc9-c011-e434-b2f8-a0369fe50396
Fetching metadata from: /soundcharts/api/artists/fetch-metadata/
Request body: {uuid: "11e81bc9-c011-e434-b2f8-a0369fe50396"}
Response status: 200
Metadata fetch response: {success: true, message: "..."}
```

**Expected when clicking Audience button:**
```
fetchAudience called for UUID: 11e81bc9-c011-e434-b2f8-a0369fe50396
Fetching audience from: /soundcharts/api/artists/fetch-audience/
Request body: {uuid: "11e81bc9-c011-e434-b2f8-a0369fe50396", platform: "spotify"}
Response status: 200
Audience fetch response: {success: true, message: "...", data: {...}}
```

### 2. Check Network Tab
1. Go to Network tab in Developer Tools
2. Filter by "XHR" or "Fetch"
3. Click a button
4. Look for the request:
   - URL: `/soundcharts/api/artists/fetch-metadata/` or `/fetch-audience/`
   - Method: POST
   - Status: Should be 200 (OK)
   - Response: JSON with `success: true`

### 3. Common Issues

#### Issue A: CSRF Token Missing
**Symptom:** 
```
Response status: 403
Error: Forbidden
```

**Solution:**
The CSRF token is now in the template. If still missing:
```html
<!-- Add at top of template -->
<meta name="csrf-token" content="{{ csrf_token }}">
```

#### Issue B: 404 Not Found
**Symptom:**
```
Response status: 404
Error: Not Found
```

**Solution:**
Check URL configuration. The URLs should be:
- `/soundcharts/api/artists/fetch-metadata/`
- `/soundcharts/api/artists/fetch-audience/`

Verify in `apps/soundcharts/urls.py`:
```python
path('api/artists/fetch-metadata/', ArtistMetadataFetchView.as_view(), name='artist_fetch_metadata'),
path('api/artists/fetch-audience/', ArtistAudienceFetchView.as_view(), name='artist_fetch_audience'),
```

And in `config/urls.py`:
```python
path("soundcharts/", include("apps.soundcharts.urls")),
```

#### Issue C: 500 Internal Server Error
**Symptom:**
```
Response status: 500
Error: Internal Server Error
```

**Solution:**
Check Django logs:
```bash
# In terminal where Django is running
# Look for Python errors/tracebacks
```

Check for:
- Missing imports in views.py
- Database errors
- API connection issues

#### Issue D: Artist Not Found in Database
**Symptom:**
```
Response status: 404
Response: {success: false, error: "Artist not found in database"}
```

**Solution:**
The artist needs to be in the database. Ensure:
1. Artist was saved from search results, OR
2. Artist was imported via admin, OR
3. Artist was created programmatically

#### Issue E: Invalid UUID
**Symptom:**
```
Response: {success: false, error: "Artist UUID is required"}
```

**Solution:**
The UUID is not being passed correctly. Check:
```javascript
// UUID should be passed to function
fetchMetadata('11e81bc9-c011-e434-b2f8-a0369fe50396')
```

### 4. Test API Directly

You can test the API endpoints directly with curl:

#### Test Metadata Fetch
```bash
curl -X POST http://localhost:8000/soundcharts/api/artists/fetch-metadata/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: your-csrf-token-here" \
  -d '{"uuid": "11e81bc9-c011-e434-b2f8-a0369fe50396"}'
```

#### Test Audience Fetch
```bash
curl -X POST http://localhost:8000/soundcharts/api/artists/fetch-audience/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: your-csrf-token-here" \
  -d '{"uuid": "11e81bc9-c011-e434-b2f8-a0369fe50396", "platform": "spotify"}'
```

### 5. Verify Database
Check if artist exists:
```bash
python manage.py shell -c "
from apps.soundcharts.models import Artist
artists = Artist.objects.all()
print(f'Total artists: {artists.count()}')
for a in artists[:5]:
    print(f'- {a.name} (UUID: {a.uuid})')
"
```

## Current Implementation

### URLs Configuration
```python
# apps/soundcharts/urls.py (lines 64-65)
path('api/artists/fetch-metadata/', ArtistMetadataFetchView.as_view(), name='artist_fetch_metadata'),
path('api/artists/fetch-audience/', ArtistAudienceFetchView.as_view(), name='artist_fetch_audience'),

# config/urls.py (line 33)
path("soundcharts/", include("apps.soundcharts.urls")),
```

### Full URLs
- Metadata: `http://localhost:8000/soundcharts/api/artists/fetch-metadata/`
- Audience: `http://localhost:8000/soundcharts/api/artists/fetch-audience/`

### JavaScript
```javascript
// templates/soundcharts/artist_list.html (lines 196-313)
function fetchMetadata(uuid) {
    // Calls: POST /soundcharts/api/artists/fetch-metadata/
    // Body: { uuid: "..." }
}

function fetchAudience(uuid) {
    // Calls: POST /soundcharts/api/artists/fetch-audience/
    // Body: { uuid: "...", platform: "spotify" }
}
```

### Views
```python
# apps/soundcharts/views.py (lines 1148-1210, 1212-1317)
class ArtistMetadataFetchView(View):
    def post(self, request):
        # Gets artist by UUID
        # Fetches metadata from Soundcharts API
        # Updates artist record
        # Returns JSON response

class ArtistAudienceFetchView(View):
    def post(self, request):
        # Gets artist by UUID
        # Fetches audience from Soundcharts API
        # Stores in ArtistAudienceTimeSeries
        # Returns JSON response
```

## Expected Behavior

### Successful Metadata Fetch
1. Button shows spinner
2. API call to `/soundcharts/api/artists/fetch-metadata/`
3. Soundcharts API returns artist data
4. Database updated
5. Button shows checkmark
6. Success notification appears
7. Page reloads after 1 second
8. Status badge shows "✓ Metadata"

### Successful Audience Fetch
1. Button shows spinner
2. API call to `/soundcharts/api/artists/fetch-audience/`
3. Soundcharts API returns 90 days of data
4. Records stored in ArtistAudienceTimeSeries
5. Button shows checkmark
6. Success notification appears
7. Page reloads after 1 second
8. Audience Data shows "✓ X platforms"

## What to Check

1. **Browser Console:** Any JavaScript errors?
2. **Network Tab:** Are requests being sent?
3. **Django Logs:** Any Python errors?
4. **Database:** Does artist exist?
5. **Soundcharts API:** Valid UUID?

## Quick Test

Open browser console and run:
```javascript
// Test if functions are defined
console.log(typeof fetchMetadata);  // Should be "function"
console.log(typeof fetchAudience);  // Should be "function"
console.log(typeof CSRF_TOKEN);     // Should be "string"

// Test manually
fetchMetadata('11e81bc9-c011-e434-b2f8-a0369fe50396');
```

Watch the console output to see where it fails.

## Next Steps

With the enhanced debugging in place:
1. Open `/soundcharts/artists/` in browser
2. Open Developer Console
3. Click a button
4. Review console output
5. Check Network tab for the request
6. Look at response details
7. Report any errors seen in console

The debugging logs will now show exactly where the process is failing!

