# Artist Dashboard Pages

## Overview

This document describes the frontend artist dashboard pages that mirror the track audience functionality. Users can search for artists, save them to the database, fetch metadata and audience data, and view audience analytics with ApexCharts.

## Pages Implemented

### 1. Artist Search Page
**URL:** `/soundcharts/artists/search/`  
**View:** `ArtistSearchView`  
**Template:** `templates/soundcharts/artist_search.html`

**Features:**
- Search artists by name via Soundcharts API
- Display results in a table with:
  - Artist image and name
  - UUID (truncated)
  - Country code
  - Career stage (with color-coded badges)
  - Genres
  - Action buttons

**Action Buttons (Icon buttons):**
1. **Save** (Green download icon)
   - Saves artist to database
   - Enables metadata and audience buttons
   - Shows checkmark when complete

2. **Fetch Metadata** (Blue info icon)
   - Disabled until artist is saved
   - Fetches full metadata from Soundcharts
   - Updates all artist fields
   - Shows checkmark when complete

3. **Fetch Audience** (Purple chart icon)
   - Disabled until artist is saved
   - Fetches Spotify audience data by default
   - Stores 90 days of time-series data
   - Shows checkmark when complete

**Technical Details:**
- Uses AJAX for all operations
- Real-time button state updates
- Loading spinners during operations
- Success/error notifications
- Maximum 20 results (Soundcharts API limit)

### 2. Artist List Page
**URL:** `/soundcharts/artists/`  
**View:** `ArtistListView`  
**Template:** `templates/soundcharts/artist_list.html`

**Features:**
- Grid layout of all stored artists
- Artist cards showing:
  - Artist image
  - Name and country
  - Career stage badge
  - Status badges (Metadata ✓, Audience ✓)
  - Platform count for artists with audience data
  - "View Details" button linking to detail page

**Layout:**
- Responsive grid (1-4 columns depending on screen size)
- Card-based design with hover effects
- Visual indicators for data availability
- Empty state with call-to-action

### 3. Artist Detail Page
**URL:** `/soundcharts/artists/{uuid}/`  
**View:** `ArtistDetailView`  
**Template:** `templates/soundcharts/artist_detail.html`

**Features:**
- **Artist Information Card:**
  - Large artist image
  - Name, country, career stage
  - Metadata (UUID, city, birth date)
  - Biography (if available)
  - Genres as badges

- **Audience Performance Section:**
  - Grid of platform cards (Spotify, Instagram, YouTube, etc.)
  - Each card shows:
    - Platform name and metric name
    - Latest audience value (formatted: 3.1M, 150K)
    - Latest date
    - ApexCharts line chart (30 days by default)
    - Data points count
  - Platform-specific colors for charts

- **Related Tracks Section:**
  - Shows up to 10 tracks by this artist
  - Track cards with image, name, artist
  - Links to track audience details

**ApexCharts Features:**
- Smooth area charts with gradients
- Platform-specific colors (Spotify green, YouTube red, etc.)
- Interactive zoom and pan
- Hover tooltips with formatted values
- Responsive design
- Dark mode support

## API Endpoints

### Artist Search
```
POST /soundcharts/api/artists/save/
Body: { "artist": {artistData} }
Response: { "success": true, "artist": {...} }
```

### Artist Metadata Fetch
```
POST /soundcharts/api/artists/fetch-metadata/
Body: { "uuid": "artist-uuid" }
Response: { "success": true, "message": "..." }
```

### Artist Audience Fetch
```
POST /soundcharts/api/artists/fetch-audience/
Body: { "uuid": "artist-uuid", "platform": "spotify" }
Response: { "success": true, "message": "...", "data": {...} }
```

### Artist Audience Chart Data
```
GET /soundcharts/artists/{uuid}/audience/chart/{platform}/?limit=30
Response: { "success": true, "chart_data": {...} }
```

## Views Implementation

### ArtistSearchView
```python
class ArtistSearchView(View):
    def get(self, request):
        # Renders search page
    
    def post(self, request):
        # Searches Soundcharts API
        # Returns JSON with artist results
```

### ArtistListView
```python
class ArtistListView(View):
    def get(self, request):
        # Fetches all stored artists
        # Includes audience data status
        # Renders artist list page
```

### ArtistDetailView
```python
class ArtistDetailView(View):
    def get(self, request, artist_uuid):
        # Gets artist by UUID
        # Fetches platform audience data
        # Gets related tracks
        # Renders detail page with charts
```

### ArtistAudienceChartView
```python
class ArtistAudienceChartView(View):
    def get(self, request, artist_uuid, platform_slug=None):
        # Returns time-series data for ApexCharts
        # Single platform or all platforms
        # Formatted as chart.js/ApexCharts compatible data
```

### ArtistSaveView
```python
class ArtistSaveView(View):
    def post(self, request):
        # Saves artist from search results to database
        # Uses Artist.create_from_soundcharts()
```

### ArtistMetadataFetchView
```python
class ArtistMetadataFetchView(View):
    def post(self, request):
        # Fetches full metadata from Soundcharts
        # Updates artist record
        # Sets metadata_fetched_at timestamp
```

### ArtistAudienceFetchView
```python
class ArtistAudienceFetchView(View):
    def post(self, request):
        # Fetches audience time-series data
        # Stores in ArtistAudienceTimeSeries model
        # Sets audience_fetched_at timestamp
```

## URL Patterns

```python
# Artist pages
path('artists/search/', ArtistSearchView.as_view(), name='artist_search'),
path('artists/', ArtistListView.as_view(), name='artist_list'),
path('artists/<str:artist_uuid>/', ArtistDetailView.as_view(), name='artist_detail'),

# Artist API endpoints
path('api/artists/save/', ArtistSaveView.as_view(), name='artist_save'),
path('api/artists/fetch-metadata/', ArtistMetadataFetchView.as_view(), name='artist_fetch_metadata'),
path('api/artists/fetch-audience/', ArtistAudienceFetchView.as_view(), name='artist_fetch_audience'),

# Artist audience chart data
path('artists/<str:artist_uuid>/audience/chart/', ArtistAudienceChartView.as_view(), name='artist_audience_chart_all'),
path('artists/<str:artist_uuid>/audience/chart/<str:platform_slug>/', ArtistAudienceChartView.as_view(), name='artist_audience_chart_single'),
```

## User Workflow

### Workflow 1: Add New Artist
```
1. Navigate to /soundcharts/artists/search/
2. Enter artist name (e.g., "Taylor Swift")
3. Click "Search"
4. Results appear in table
5. Click Save icon (green) → Artist saved to database
6. Click Metadata icon (blue) → Full metadata fetched
7. Click Audience icon (purple) → Audience data fetched
8. Navigate to artist list to see the saved artist
```

### Workflow 2: View Artist Details
```
1. Navigate to /soundcharts/artists/
2. Browse stored artists in grid view
3. Click "View Details" on an artist card
4. See artist information and audience charts
5. Charts automatically load with ApexCharts
6. View related tracks by this artist
```

## Frontend Components

### JavaScript Classes

**ArtistDetailChartsManager** (artist_detail.html)
- Manages ApexCharts instances for each platform
- Loads chart data via AJAX
- Handles empty states
- Supports dark mode
- Platform-specific colors

**Functions:**
- `searchArtists()` - Searches Soundcharts API
- `displayResults(artists)` - Renders results table
- `saveArtist(uuid)` - Saves artist to database
- `fetchMetadata(uuid)` - Fetches metadata
- `fetchAudience(uuid)` - Fetches audience data
- `getCareerStageColor(stage)` - Returns color class for badges

### Styling

Uses Tailwind CSS classes:
- Card-based layouts
- Responsive grids
- Dark mode support
- Hover effects and transitions
- Color-coded badges
- Loading spinners
- Status indicators

## Database Models Used

### Artist
- Stores artist metadata
- Tracks fetch timestamps
- Links to genres (ManyToMany)

### ArtistAudienceTimeSeries
- Stores follower/like counts over time
- One record per artist/platform/date
- Used for charting

### Platform
- Defines available platforms
- Stores audience metric names (Followers, Likes, etc.)

## Chart Configuration

### ApexCharts Options
```javascript
{
    chart: {
        type: 'area',
        height: 140,
        zoom: true,
        pan: true,
        animations: true
    },
    stroke: {
        curve: 'smooth',
        width: 3
    },
    fill: {
        type: 'gradient',
        gradient: { opacityFrom: 0.45, opacityTo: 0 }
    },
    markers: {
        size: 4,
        hover: { size: 6 }
    },
    xaxis: {
        type: 'datetime',
        labels: { format: 'MMM dd' }
    },
    tooltip: {
        enabled: true,
        y: { formatter: formatNumber }
    }
}
```

### Platform Colors
- Spotify: #1DB954 (green)
- YouTube: #FF0000 (red)
- Instagram: #E4405F (pink)
- TikTok: #000000 (black)
- Facebook: #1877F2 (blue)
- Twitter: #1DA1F2 (light blue)
- SoundCloud: #FF5500 (orange)
- Default: #1A56DB (blue)

## Responsive Design

### Breakpoints
- **Mobile** (< 768px): Single column
- **Tablet** (768px - 1024px): 2 columns
- **Desktop** (1024px - 1280px): 3 columns
- **Large Desktop** (> 1280px): 4 columns

### Components
- Search page table: Horizontal scroll on mobile
- Artist list: Responsive grid
- Artist detail: Stacked on mobile, side-by-side on desktop
- Charts: Always full-width within cards

## Error Handling

### User-Facing Errors
- "Search query is required" - Empty search
- "No artists found" - No results from API
- "Failed to save artist" - Database error
- "Artist not found in database" - UUID not in DB
- "No audience data available" - No time-series data

### Error Display
- Toast notifications (5 second auto-hide)
- Color-coded (red for errors, green for success)
- Clear error messages
- Console logging for debugging

## Performance Optimizations

1. **Prefetch Related Data:**
   - `prefetch_related('genres', 'audience_timeseries__platform')`

2. **Lazy Chart Loading:**
   - Charts load after page render
   - Async data fetching
   - Empty states during load

3. **Limited Data Points:**
   - Default limit of 30 days for charts
   - Configurable via URL parameter

4. **Efficient Queries:**
   - `select_related()` for foreign keys
   - `distinct()` for many-to-many
   - Indexed fields (date, platform, artist)

## Testing

### Test Artist Search
1. Go to `/soundcharts/artists/search/`
2. Search for "Billie Eilish"
3. Verify results appear
4. Click Save → Should save to database
5. Click Metadata → Should fetch and update
6. Click Audience → Should fetch Spotify data

### Test Artist List
1. Go to `/soundcharts/artists/`
2. Verify saved artists appear
3. Check status badges show correctly
4. Click "View Details" → Should navigate to detail page

### Test Artist Detail
1. Navigate to an artist with audience data
2. Verify charts load automatically
3. Check platform-specific colors
4. Hover over chart points → Tooltip should show
5. Check related tracks appear

## Files Created/Modified

### New Files
1. `templates/soundcharts/artist_search.html` - Search page
2. `templates/soundcharts/artist_list.html` - List page
3. `templates/soundcharts/artist_detail.html` - Detail page

### Modified Files
1. `apps/soundcharts/views.py`:
   - Added `ArtistSearchView`
   - Added `ArtistListView`
   - Added `ArtistDetailView`
   - Added `ArtistAudienceChartView`
   - Added `ArtistSaveView`
   - Added `ArtistMetadataFetchView`
   - Added `ArtistAudienceFetchView`

2. `apps/soundcharts/urls.py`:
   - Added artist page URLs
   - Added artist API endpoint URLs
   - Added artist audience chart URLs

3. `apps/soundcharts/models.py`:
   - Already had `ArtistAudienceTimeSeries` model with chart methods

## Comparison: Tracks vs Artists

| Feature | Tracks | Artists |
|---------|--------|---------|
| Search page | ✅ | ✅ |
| List page | ✅ | ✅ |
| Detail page | ✅ | ✅ |
| ApexCharts | ✅ | ✅ |
| Save from search | ✅ | ✅ |
| Fetch metadata | ✅ | ✅ |
| Fetch audience | ✅ | ✅ |
| Time-series model | `TrackAudienceTimeSeries` | `ArtistAudienceTimeSeries` |
| Chart colors | Platform-specific | Platform-specific |
| Related items | Related tracks | Related tracks by artist |

## Future Enhancements

### Potential Improvements
1. **Bulk Operations:**
   - Select multiple artists from search
   - Bulk save, metadata fetch, audience fetch
   - Progress bar for bulk operations

2. **Advanced Filters:**
   - Filter by career stage
   - Filter by country
   - Filter by genre
   - Sort by followers, growth, etc.

3. **Comparison View:**
   - Compare multiple artists
   - Side-by-side charts
   - Growth rate comparison

4. **Export Features:**
   - Export artist data to CSV/Excel
   - Export chart images
   - Generate reports

5. **Real-time Updates:**
   - WebSocket integration
   - Live audience updates
   - Push notifications for milestones

6. **Additional Platforms:**
   - Instagram Stories metrics
   - TikTok video counts
   - YouTube video stats
   - Social media engagement

## Navigation

Add to main navigation menu:

```html
<li>
  <a href="{% url 'soundcharts:artist_search' %}">
    Search Artists
  </a>
</li>
<li>
  <a href="{% url 'soundcharts:artist_list' %}">
    Stored Artists
  </a>
</li>
```

## Related Documentation

- [Artist Audience Integration](artist_audience_integration.md)
- [Soundcharts API Fixes](soundcharts_api_fixes.md)
- [Artist UUID Validation](artist_uuid_validation.md)
- [Song Audience Detail](song_detail_audience_integration.md)

