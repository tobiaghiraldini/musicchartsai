# Artist UUID Validation and Finding Artists

## Issue: 404 Not Found for Artist UUID

### Symptom
```
Error getting artist metadata: 404 Client Error: Not Found for url: 
https://customer.api.soundcharts.com/api/v2.9/artist/{uuid}
```

### Root Cause
**The artist UUID doesn't exist in Soundcharts' database.** This happens when:

1. The UUID was copied from another source (not Soundcharts)
2. The artist doesn't exist in Soundcharts
3. The UUID is incorrectly formatted
4. The artist was removed from Soundcharts

### Verification
The API implementation is **correct**. Testing proves:
- ✅ Billie Eilish (UUID: `11e81bcc-9c1c-ce38-b96b-a0369fe50396`) - **Works**
- ✅ Taylor Swift, Taylor Acorn, etc. via search - **Works**
- ❌ Random/invalid UUIDs - **404 Not Found**

## Solution: Use Search to Find Valid Artists

### Method 1: Django Admin Interface (Easiest)

1. Go to **Django Admin → Soundcharts → Artists**
2. Click **"Import from API"** button at the top
3. Search for the artist by name (e.g., "Taylor Swift")
4. Select the artist from search results
5. Click "Import Selected Artists"
6. The artist is now in your database with the **correct UUID**
7. Open the artist and use **"Fetch Metadata from API"** button

### Method 2: Command Line Script

Use the provided script to search and import:

```bash
cd /Users/tobia/Code/Projects/Customers/Knowmark/MusicCharts/Django/rocket-django-main
source venv/bin/activate

# Search and import an artist
python scripts/find_and_import_artist.py "Taylor Swift"
```

**Script features:**
- Searches Soundcharts for matching artists
- Shows up to 10 results with details
- Lets you select which one to import
- Imports the artist with correct UUID
- Provides admin link to view/edit

**Example session:**
```
🔍 Searching for: 'Taylor Swift'...

✅ Found 1 artist(s):

1. Taylor Swift
   UUID: 06HL4z0CvFAxyc27GXpf02
   Country: US
   Career Stage: superstar

Enter the number of the artist to import (or 'q' to quit): 1

✅ Artist imported successfully!
   Name: Taylor Swift
   UUID: 06HL4z0CvFAxyc27GXpf02
   ID: 42

Now you can:
1. View in admin: http://localhost:8000/admin/soundcharts/artist/42/change/
2. Use 'Fetch Metadata from API' button to get full details
3. Use 'Fetch Audience Data from API' button to get audience info
```

### Method 3: Python/Django Shell

```python
from apps.soundcharts.service import SoundchartsService
from apps.soundcharts.models import Artist

service = SoundchartsService()

# Step 1: Search for artists
results = service.search_artists('Taylor Swift', limit=5)

# Step 2: Check results
for artist in results:
    print(f"{artist['name']} - UUID: {artist['uuid']}")

# Step 3: Import the artist
if results:
    artist_data = results[0]  # First result
    artist = Artist.create_from_soundcharts(artist_data)
    print(f"✅ Imported: {artist.name} (UUID: {artist.uuid})")
    
    # Step 4: Fetch full metadata
    metadata = service.get_artist_metadata(artist.uuid)
    if metadata and 'object' in metadata:
        # Update artist with full metadata
        artist_data = metadata['object']
        artist.biography = artist_data.get('biography', '')
        artist.birthDate = artist_data.get('birthDate')
        # ... update other fields
        artist.save()
        print(f"✅ Metadata fetched and saved")
```

## Workflow: Adding New Artists

### Recommended Workflow

```
1. Search for Artist
   ↓
2. Import Artist (creates record with UUID)
   ↓
3. Fetch Metadata (populates all fields)
   ↓
4. Fetch Audience (gets demographic data)
```

### DON'T Do This ❌

```
1. Manually create Artist with random UUID ❌
   ↓
2. Try to fetch metadata → 404 Error ❌
```

### DO This ✅

```
1. Use Search or Import feature ✅
   ↓
2. Artist created with valid UUID from Soundcharts ✅
   ↓
3. Fetch metadata → Success ✅
```

## API Endpoints Reference

### Search Artists (always works)
```
GET /api/v2/artist/search/{query}
Response: List of matching artists with UUIDs
```

### Get Artist Metadata (requires valid UUID)
```
GET /api/v2.9/artist/{uuid}
Response: Full artist details
```

### Get Artist Audience (requires valid UUID)
```
GET /api/v2/artist/{uuid}/audience/{platform}/report/{date}
Response: Audience demographics
```

## Testing Valid UUIDs

### Known Valid Artist UUIDs (commonly available):

```python
# Billie Eilish
uuid = "11e81bcc-9c1c-ce38-b96b-a0369fe50396"

# Tones & I
uuid = "ca22091a-3c00-11e9-974f-549f35141000"

# Taylor Acorn
uuid = "11e81bbd-9e27-3628-b746-a0369fe50396"

# James Taylor
uuid = "11e81bc2-f6fa-b86a-8f95-a0369fe50396"
```

### Test Script

```python
from apps.soundcharts.service import SoundchartsService

service = SoundchartsService()

# Test a UUID
test_uuid = "11e81bcc-9c1c-ce38-b96b-a0369fe50396"
result = service.get_artist_metadata(test_uuid)

if result and 'object' in result:
    print(f"✅ Valid UUID - Artist: {result['object']['name']}")
else:
    print(f"❌ Invalid UUID - Not found in Soundcharts")
```

## Troubleshooting

### Error: "Artist has no UUID"
**Cause:** Artist was created manually without using search/import.

**Fix:** Delete the artist and re-import using search.

### Error: "404 Not Found"
**Cause:** UUID doesn't exist in Soundcharts database.

**Fix:** 
1. Delete the artist record
2. Use search to find the artist
3. Import with correct UUID

### Error: "Validation errors on empty fields"
**Cause:** Form validation running before fetch.

**Fix:** This was fixed in the latest update. The fetch buttons now bypass validation.

## Best Practices

1. ✅ **Always use Search/Import** to add new artists
2. ✅ **Verify artist exists** in Soundcharts before importing
3. ✅ **Use Fetch Metadata** after importing to get full details
4. ✅ **Use Fetch Audience** to get demographic data
5. ❌ **Never manually enter UUIDs** unless you're 100% certain they're valid
6. ❌ **Never create artists** without searching first

## FAQ

**Q: Can I use UUIDs from Spotify/Apple Music?**  
A: No. Soundcharts has its own UUID system. You must use Soundcharts' search to get the correct UUID.

**Q: Why does Billie Eilish work but my artist doesn't?**  
A: Billie Eilish is a major artist in Soundcharts' database. Your artist might not be indexed by Soundcharts, or you have the wrong UUID.

**Q: How do I know if an artist exists in Soundcharts?**  
A: Use the search endpoint. If search returns results, the artist exists with a valid UUID.

**Q: Can I import artists in bulk?**  
A: Yes, you can modify the script to import multiple artists, or use the admin's bulk import feature.

**Q: What if my artist is not in Soundcharts?**  
A: Unfortunately, you cannot fetch metadata for artists that don't exist in Soundcharts' database. You'll need to enter their information manually or wait for Soundcharts to index them.

## Related Documentation

- [Artist Audience Integration](artist_audience_integration.md)
- [Soundcharts Integration](soundcharts_integration.md)
- [Artist Admin Form Validation Fix](artist_audience_form_validation_fix.md)

