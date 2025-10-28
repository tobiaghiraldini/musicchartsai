# Music Analytics

The Music Analytics feature provides comprehensive insights into artist performance across multiple platforms with detailed audience metrics and track-level breakdowns.

## Overview

Music Analytics allows you to:

- **Search artists** with autocomplete functionality
- **Select multiple platforms** (Spotify, YouTube, Instagram, TikTok, etc.)
- **Choose date ranges** for historical analysis
- **Filter by country** for geo-specific insights
- **View aggregated metrics** per platform
- **Explore track-level data** with detailed breakdowns
- **Export results** to Excel format

## Features

### Artist-Level Aggregation (Phase 1)

Artist-level metrics provide platform-level insights:

#### Per-Platform Summary Cards

Each platform displays six key metrics:

| Metric | Description | Use Case |
|--------|-------------|----------|
| **Start Value** | Audience count at period start | Baseline measurement |
| **End Value** | Audience count at period end | Current state |
| **Difference** | Net change (growth/decline) | Trend analysis |
| **Period Average** | Average daily audience count | **Primary metric** |
| **Peak Value** | Highest audience count in period | Best performance day |
| **Data Points** | Number of days with data | Data completeness |

#### Metrics Explained

**Period Average** (Primary Metric)
- Answer: "How much did Artist X do in Month Y?"
- Formula: `SUM(all values) / number of days`
- Example: "8.5M average monthly listeners in September"

**Difference** (Growth Indicator)
- Shows audience change during period
- Green = Growth, Red = Decline
- Example: "+700K growth during September"

**Peak** (Best Performance)
- Highest audience count in the period
- Identifies best-performing days
- Example: "9.5M peak listeners on Sept 25"

### Track-Level Breakdown (Phase 2)

Expand artist rows to view detailed track performance:

#### Track Metrics

| Metric | Description |
|--------|-------------|
| **Track Name** | Song title |
| **Total Streams** | Total stream count for the period |
| **Average Daily Streams** | Average streams per day |
| **Peak Streams** | Highest daily stream count |
| **Best Chart Position** | Best ranking achieved |
| **Weeks on Chart** | Duration on charts |

#### Features

- **Top Track Badge**: Highlights best-performing track
- **Stream Aggregation**: Shows total streams across all tracks
- **Lazy Loading**: Track data loads on demand
- **Client-Side Caching**: Reduces API calls

## Usage

### Step 1: Access Analytics

Navigate to **Music Analytics** from the sidebar.

### Step 2: Fill Search Form

1. **Select Artist(s)** using autocomplete search
2. **Choose Platform(s)** by checking boxes
3. **Set Date Range** (start and end dates)
4. **Optionally Filter by Country**

### Step 3: Analyze Metrics

Click **"Analyze Metrics"** to fetch data.

### Step 4: View Results

- **Summary Cards**: Per-platform aggregated metrics
- **Artist × Platform Table**: Detailed breakdown

### Step 5: Explore Track Data

Click an artist row to expand and view track-level data.

### Step 6: Export Results

Click **"Export to Excel"** to download a multi-sheet workbook.

## Data Sources

### Artist-Level Data

Fetched from **SoundCharts API**:

- **Streaming Platforms**: Monthly listeners (Spotify, YouTube, Deezer)
- **Social Platforms**: Follower counts (Instagram, TikTok, Twitter)

### Track-Level Data

Fetched from **Local Database**:

- Chart ranking history
- Stream counts from charts
- Position and ranking data

## Platform Support

### Streaming Platforms

- **Spotify**: Monthly listeners
- **YouTube**: Monthly listeners  
- **Deezer**: Monthly listeners
- **Apple Music**: Monthly listeners

### Social Platforms

- **Instagram**: Follower counts
- **TikTok**: Follower counts
- **Twitter**: Follower counts

## Export Functionality

### Excel Export Format

The export generates a multi-sheet Excel workbook:

**Sheet 1: Overview**
- Platform summary cards
- Artist × Platform breakdown
- Metrics and calculations

**Additional Sheets**
- One sheet per artist × platform combination
- Track-level detail data
- Stream counts and positions

### Export Includes

- All metrics from summary cards
- Aggregate calculations
- Track-level stream data
- Date ranges and filters applied
- Timestamp of export

## Technical Architecture

### Frontend

- **View**: `/analytics/`
- **AJAX Communication**: Real-time data fetching
- **Charts**: Interactive visualizations (Phase 3 future)

### Backend

- **Service**: `analytics_service.py`
- **API Integration**: SoundCharts API calls
- **Data Processing**: Aggregation and calculation
- **Export**: Excel generation with `openpyxl`

### Data Flow

```
User Input → AJAX POST → Backend Processing
                                      ↓
                        Fetch from SoundCharts API
                                      ↓
                        Fetch from Local Database
                                      ↓
                        Aggregate and Calculate
                                      ↓
                            Return JSON Response
                                      ↓
                    Frontend Rendering (Cards + Table)
```

## Performance

- **Lazy Loading**: Track data loads on demand
- **Client-Side Caching**: Reduces API calls
- **Efficient Queries**: Optimized database queries
- **Async Processing**: Background data fetching

## Troubleshooting

### No Data Available

- Verify artist exists in database
- Check date range contains data
- Ensure platform has audience data
- Review API credentials

### Export Fails

- Check file size limits
- Verify `openpyxl` is installed
- Ensure write permissions

### Platform Data Missing

- Verify platform support
- Check API configuration
- Review data availability in SoundCharts

## Future Enhancements

### Planned Features

- Interactive charts and visualizations
- Historical trend analysis
- Comparison mode (artist vs artist)
- Automated reporting
- Custom metric calculations
- Real-time data updates

## Related Documentation

- [Artist Management](artist-management.md)
- [Soundcharts Integration](soundcharts-integration.md)
- [API Reference](../../api/overview.md)

