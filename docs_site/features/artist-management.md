# Artist Management

Complete artist functionality for the Soundcharts integration, including search, metadata management, audience analytics, and bidirectional track linking.

## Overview

The Artist Management system provides:

- **Artist Search** with Soundcharts API integration
- **Artist List** with table layout and status tracking
- **Artist Details** with ApexCharts audience analytics
- **Bidirectional Linking** between artists and tracks
- **Admin Interface** with enhanced controls
- **API Integration** with corrected endpoints

## Features

### Artist Search

Search and import artists from Soundcharts API.

#### Search Interface

- **Autocomplete Search**: Search by artist name
- **Real-time Results**: Instant API search results
- **Import Functionality**: Save artists to database
- **Action Buttons**: 
  - 🟢 Save to Database
  - 🔵 Fetch Metadata
  - 🟣 Fetch Audience Data

#### Workflow

1. Navigate to **Artist Search** (`/soundcharts/artists/search/`)
2. Enter artist name in search box
3. View results in table format
4. Click action buttons to:
   - Save artist to database
   - Fetch metadata from API
   - Fetch audience data from API

### Artist List

View all stored artists with comprehensive status tracking.

#### Table Layout

| Column | Description |
|--------|-------------|
| **Artist** | Artist name and image |
| **Country** | Country of origin |
| **Career Stage** | Career stage classification |
| **Status** | Metadata and audience status |
| **Actions** | View details button |

#### Status Indicators

- **Metadata Status**: Shows when metadata was fetched
- **Audience Status**: Shows when audience data was fetched
- **Status Colors**: Color-coded status indicators

#### Features

- **Responsive Design**: Works on all devices
- **Status Tracking**: Visual indicators for data completeness
- **Quick Access**: View details with one click
- **Search and Filter**: Search and filter capabilities

### Artist Detail Page

Comprehensive artist information and analytics.

#### Artist Information Card

- **Artist Image**: Full artist photo
- **Name and Country**: Display name and country
- **Career Stage**: Current career stage
- **Biography**: Full artist biography
- **Metadata Info**: Last metadata fetch timestamp

#### Audience Analytics

**ApexCharts Integration** provides interactive charts:

- **30-Day Trends**: Historical audience data
- **Multi-Platform**: Spotify, YouTube, Instagram, TikTok
- **Interactive Zoom**: Zoom and pan functionality
- **Color-Coded**: Platform-specific colors
- **Dark Mode**: Full dark mode support

#### Platform-Specific Charts

Each platform displays:

- **Streaming Platforms**: Monthly listeners (Spotify, YouTube)
- **Social Platforms**: Follower counts (Instagram, TikTok)
- **Time Series**: 30-day historical data
- **Growth Trends**: Visual trend indicators

#### Related Tracks

- **Track Links**: Links to related track pages
- **Track List**: Shows all tracks by artist
- **Bidirectional Navigation**: Navigate tracks ↔ artists

### Artist-Track Linking

Bidirectional navigation between artists and tracks.

#### Track → Artist Links

- **Song Detail Pages**: Link to artist pages
- **Track Cards**: Show artist information
- **Navigation**: Quick access to artist data

#### Artist → Track Links

- **Artist Detail Pages**: Show related tracks
- **Track List**: All tracks by artist
- **Navigation**: Quick access to track data

#### Benefits

- **Complete Data**: Access artist data from track pages
- **Track Data**: Access track data from artist pages
- **Seamless Navigation**: Intuitive user experience

## Admin Interface

### Enhanced Admin Features

#### Metadata Management

**"Fetch Metadata from API" Button**:
- Fetches complete artist metadata
- Updates artist record with latest data
- Stores fetch timestamp
- Error handling and logging

**Metadata Includes**:
- Artist name and display name
- Biography and description
- Country and career stage
- Image URLs and thumbnails
- Metadata timestamps

#### Audience Management

**"Fetch Audience Data from API" Button**:
- Select platform from dropdown
- Fetches audience time-series data
- Processes and stores data
- Updates audience timestamp

**Platform Support**:
- Spotify: Monthly listeners
- YouTube: Monthly listeners
- Instagram: Followers
- TikTok: Followers

#### Form Validation

- **UUID Validation**: Ensures valid Soundcharts UUIDs
- **Error Handling**: Graceful error messages
- **Success Feedback**: Confirmation messages

## API Integration

### Corrected Endpoints

#### Search Artists

```python
GET /api/v2.37/artist/search
```

- **Fixed Limit**: Changed from 100 to 20 results
- **Autocomplete**: Fast search results
- **Query Parameters**: Name search

#### Get Artist Metadata

```python
GET /api/v2.37/artist/{uuid}
```

- **Complete Profile**: Full artist information
- **Metadata Fields**: All artist details
- **Image URLs**: High-quality images

#### Get Audience Data

```python
GET /api/v2/artist/{uuid}/streaming/{platform}
GET /api/v2.37/artist/{uuid}/social/{platform}/followers/
```

- **Corrected URLs**: Fixed API endpoints
- **Platform Support**: Streaming and social
- **Time Series**: Historical data support

## Data Models

### Artist Model

```python
class Artist(models.Model):
    uuid = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=2, blank=True)
    career_stage = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    bio = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    thumbnail_url = models.URLField(blank=True)
    metadata_fetched_at = models.DateTimeField(null=True)
    audience_fetched_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### ArtistAudience Model

```python
class ArtistAudience(models.Model):
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    platform = models.CharField(max_length=50)
    metric_type = models.CharField(max_length=50)
    audience_count = models.BigIntegerField(default=0)
    recorded_at = models.DateTimeField()
```

### ArtistAudienceTimeSeries Model

```python
class ArtistAudienceTimeSeries(models.Model):
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    platform = models.CharField(max_length=50)
    metric_type = models.CharField(max_length=50)
    value = models.BigIntegerField(default=0)
    date = models.DateField()
    
    class Meta:
        unique_together = [['artist', 'platform', 'metric_type', 'date']]
```

## Usage Workflows

### Adding a New Artist

1. Navigate to **Artist Search**
2. Search for artist name
3. Click **🟢 Save to Database**
4. Click **🔵 Fetch Metadata** to get full details
5. Click **🟣 Fetch Audience** to get audience data

### Viewing Artist Analytics

1. Navigate to **Artist List**
2. Click **View Details** on desired artist
3. View artist information card
4. Explore audience charts per platform
5. Review related tracks

### Fetching Audience Data

1. Open artist in admin interface
2. Select platform from dropdown
3. Click **"Fetch Audience Data from API"**
4. Wait for completion
5. View updated timestamp
6. Check audience charts on detail page

## Troubleshooting

### Artist Not Found

- Verify artist exists in Soundcharts
- Check spelling of artist name
- Review search parameters

### Metadata Fetch Fails

- Verify API credentials
- Check network connectivity
- Review error logs
- Ensure valid UUID

### Audience Data Missing

- Verify platform is supported
- Check date range has data
- Ensure API credentials are valid
- Review fetch timestamp

### Linking Issues

- Verify track has credit_name
- Check artist exists in database
- Review database relationships
- Clear cache if needed

## Related Documentation

- [Analytics](analytics.md)
- [Soundcharts Integration](soundcharts-integration.md)
- [API Reference](../../api/overview.md)

