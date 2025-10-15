# Artist Audience and Metadata Integration

## Overview

This document describes the implementation of artist metadata and audience data fetching from the Soundcharts API, similar to the existing track functionality.

## Changes Implemented

### 1. Service Layer (apps/soundcharts/service.py)

The service methods were already present:
- `get_artist_metadata(uuid)` - Fetches artist metadata from `/api/v2.9/artist/{uuid}`
- `get_artist_audience_for_platform(uuid, platform="spotify", date='latest')` - Fetches artist audience data from `/api/v2/artist/{uuid}/audience/{platform}/report/{date}`

### 2. Model Updates (apps/soundcharts/models.py)

#### Artist Model Enhancements
Added tracking fields to the Artist model:
```python
# Metadata fetch tracking
metadata_fetched_at = models.DateTimeField(null=True, blank=True, help_text="When metadata was last fetched")
audience_fetched_at = models.DateTimeField(null=True, blank=True, help_text="When audience data was last fetched")
```

#### New Models: ArtistAudience and ArtistAudienceTimeSeries

**ArtistAudience Model:**
- Stores demographic and audience data for artists per platform
- Fields include:
  - Age demographics (13-17, 18-24, 25-34, 35-44, 45-54, 45-59, 55-64, 60-150, 65+)
  - Gender demographics (male, female percentages)
  - Geographic data (top countries, top cities)
  - Raw API data for future reference
  - Report date tracking
- Unique constraint: `artist`, `platform`, `report_date`

**ArtistAudienceTimeSeries Model:**
- Stores time-series audience data for trend analysis and charting
- Fields include:
  - Date of measurement
  - Audience value
  - Platform identifier
  - Raw API data
- Includes helper methods:
  - `get_chart_data()` - Returns formatted data for charting
  - `get_platform_comparison()` - Returns data for multi-platform comparison
  - `get_latest_audience()` - Returns most recent audience value
  - `formatted_audience_value` property - Returns human-readable format (e.g., "1.5M")

### 3. Admin Integration (apps/soundcharts/admin_views/artist_admin.py)

#### Enhanced ArtistAdmin Class

**Added Imports:**
```python
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, path
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from ..models import Artist, Genre, Platform, ArtistAudience, ArtistAudienceTimeSeries
```

**Updated response_change() Method:**
- Added `_fetch_audience` button handler
- Processes audience data for selected platform and date
- Updates `audience_fetched_at` timestamp on successful fetch
- Also updated `_fetch_metadata` to track `metadata_fetched_at`

**New Helper Method:**
```python
def _process_artist_audience_data(self, artist, platform_slug, audience_data)
```
- Parses and stores audience data from Soundcharts API
- Extracts age demographics, gender data, and geographic information
- Creates or updates ArtistAudience records
- Returns success/failure status

**Enhanced change_view() Method:**
- Simplified to only set context variables
- Passes `show_fetch_metadata_button` and `show_fetch_audience_button` flags
- Provides available platforms list for the dropdown

**New Custom URL Endpoint:**
```python
def get_urls(self):
    # Adds path for artist audience fetch API endpoint
    path("<int:object_id>/fetch-audience/", 
         self.admin_site.admin_view(self.fetch_audience_api),
         name="soundcharts_artist_fetch_audience")
```

**New API Endpoint:**
```python
@csrf_exempt
def fetch_audience_api(self, request, object_id)
```
- Handles AJAX requests for audience data fetching
- Accepts platform and date parameters
- Returns JSON response with success/error status

### 4. Template Updates (apps/soundcharts/templates/admin/soundcharts/artist/change_form.html)

Enhanced the artist change form template to include:

**Fetch Metadata Button:**
- Styled with green theme
- Appears when artist has a UUID

**Fetch Audience Button:**
- Styled with blue theme
- Includes platform selector dropdown
- Includes report date selector
- Submits via POST to trigger audience fetch

**Styling:**
- Added consistent button styling
- Flexbox layout for form controls
- Responsive design with proper spacing

### 5. Admin Registration (apps/soundcharts/admin.py)

Added admin registration for new models:

**ArtistAudienceAdmin:**
- List display: artist, platform, report_date, fetched_at
- Filters by platform, report_date, fetched_at
- Search by artist name and UUID

**ArtistAudienceTimeSeriesAdmin:**
- List display: artist, platform, date, formatted_audience_value, fetched_at
- Filters by platform and date
- Formatted audience value display

## Database Migration

To apply these changes, run:

```bash
cd /Users/tobia/Code/Projects/Customers/Knowmark/MusicCharts/Django/rocket-django-main
source venv/bin/activate
python manage.py makemigrations soundcharts
python manage.py migrate
```

## API Field Mapping

### Artist Metadata Fields Mapped:
- `name` → Artist.name
- `slug` → Artist.slug
- `appUrl` → Artist.appUrl
- `imageUrl` → Artist.imageUrl
- `biography` → Artist.biography
- `isni` → Artist.isni (International Standard Name Identifier)
- `ipi` → Artist.ipi (Interested Party Information)
- `gender` → Artist.gender
- `type` → Artist.type (e.g., "person", "band")
- `birthDate` → Artist.birthDate (with ISO format parsing)
- `careerStage` → Artist.careerStage
- `cityName` → Artist.cityName
- `countryCode` → Artist.countryCode
- `genres` → Artist.genres (ManyToMany relationship)

### Artist Audience Fields Mapped:
- `age` object → Individual age range fields
- `gender` object → Male/female percentage fields
- `topCountries` → JSON field
- `topCities` → JSON field
- `date` → report_date

## Usage

### In Django Admin:

1. **Fetch Metadata:**
   - Navigate to an Artist in the admin
   - Click "Fetch Metadata from API" button
   - System fetches and updates all metadata fields
   - Timestamp recorded in `metadata_fetched_at`

2. **Fetch Audience Data:**
   - Navigate to an Artist in the admin
   - Select desired platform (default: Spotify)
   - Select report date (default: Latest)
   - Click "Fetch Audience Data from API" button
   - System fetches and stores audience demographics
   - Timestamp recorded in `audience_fetched_at`

### Programmatically:

```python
from apps.soundcharts.service import SoundchartsService
from apps.soundcharts.models import Artist

service = SoundchartsService()

# Fetch artist metadata
metadata = service.get_artist_metadata(artist_uuid)

# Fetch artist audience for Spotify
audience_data = service.get_artist_audience_for_platform(
    artist_uuid, 
    platform="spotify",
    date="latest"
)

# Get latest audience from database
from apps.soundcharts.models import ArtistAudienceTimeSeries, Platform

artist = Artist.objects.get(uuid="some-uuid")
platform = Platform.objects.get(slug="spotify")
latest = ArtistAudienceTimeSeries.get_latest_audience(artist, platform)
print(f"Latest audience: {latest.formatted_audience_value}")
```

## Comparison with Soundcharts API Response

### Artist Metadata Response Structure:
```json
{
  "object": {
    "uuid": "...",
    "name": "...",
    "slug": "...",
    "appUrl": "...",
    "imageUrl": "...",
    "biography": "...",
    "isni": "...",
    "ipi": "...",
    "gender": "...",
    "type": "...",
    "birthDate": "...",
    "careerStage": "...",
    "cityName": "...",
    "countryCode": "...",
    "genres": [
      {"root": "...", "sub": ["..."]}
    ]
  }
}
```

### Artist Audience Response Structure:
```json
{
  "object": {
    "date": "2024-01-01",
    "age": {
      "13-17": 5,
      "18-24": 20,
      "25-34": 35,
      ...
    },
    "gender": {
      "male": 45,
      "female": 55
    },
    "topCountries": [...],
    "topCities": [...]
  }
}
```

## Model Field Completeness

All fields returned by the Soundcharts API are now supported in the Artist model:

✅ Basic Information (name, slug, uuid, appUrl, imageUrl)
✅ Biographical Data (biography, birthDate, gender, type)
✅ Location Data (cityName, countryCode)
✅ Career Information (careerStage)
✅ Identifiers (isni, ipi, acrcloud_id, musicbrainz_id)
✅ Relationships (genres - ManyToMany)
✅ Platform IDs (platform_ids - JSONField)
✅ Tracking Fields (metadata_fetched_at, audience_fetched_at)

## Future Enhancements

Potential improvements to consider:

1. **Bulk Operations:**
   - Add bulk metadata fetch for multiple artists
   - Add bulk audience fetch for multiple artists
   - Create background tasks using Celery

2. **Audience Visualization:**
   - Add chart views for audience trends
   - Platform comparison charts
   - Demographic distribution visualizations

3. **Historical Data:**
   - Schedule periodic audience data fetching
   - Track audience growth over time
   - Alert on significant changes

4. **Additional API Endpoints:**
   - Artist social media metrics
   - Artist streaming performance
   - Artist chart performance

## Related Documentation

- [Soundcharts Integration](soundcharts_integration.md)
- [Track Metadata Integration](track_metadata_integration.md)
- [Audience Data System](audience_data_system.md)

