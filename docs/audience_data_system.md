# Audience Data System Documentation

## Overview

The Audience Data System is designed to store, process, and retrieve time-series audience data for tracks across different platforms. This system enables the creation of audience line charts with dates on the X-axis and audience values on the Y-axis, supporting both single-platform and multi-platform comparison views.

## Architecture

### Core Components

1. **TrackAudienceTimeSeries Model** - Stores time-series audience data
2. **Enhanced Platform Model** - Includes platform metadata and audience metrics
3. **AudienceDataProcessor** - Processes API responses and stores data
4. **AudienceChartView** - Provides chart-ready data via API endpoints
5. **Management Commands** - CLI tools for data processing

### Data Flow

```
SoundCharts API → AudienceDataProcessor → TrackAudienceTimeSeries → AudienceChartView → Frontend Charts
```

## Models

### TrackAudienceTimeSeries

The core model for storing time-series audience data:

```python
class TrackAudienceTimeSeries(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    date = models.DateField()
    audience_value = models.BigIntegerField()
    platform_identifier = models.CharField(max_length=255)
    fetched_at = models.DateTimeField(auto_now_add=True)
    api_data = models.JSONField(default=dict)
```

**Key Features:**
- Unique constraint on (track, platform, date)
- Optimized indexes for efficient queries
- Built-in methods for chart data retrieval
- Automatic data formatting for display

### Enhanced Platform Model

Extended platform model with audience-specific metadata:

```python
class Platform(models.Model):
    # ... existing fields ...
    platform_type = models.CharField(choices=[
        ('streaming', 'Streaming'),
        ('social', 'Social Media'),
        ('radio', 'Radio'),
        ('tv', 'TV'),
        ('other', 'Other'),
    ])
    audience_metric_name = models.CharField(default="Listeners")
    platform_identifier = models.CharField(blank=True)
```

## API Endpoints

### Get Chart Data

**Single Platform:**
```
GET /soundcharts/audience/chart/{track_uuid}/{platform_slug}/
```

**Multi-Platform Comparison:**
```
GET /soundcharts/audience/chart/{track_uuid}/
```

**Query Parameters:**
- `start_date`: Filter data from this date (YYYY-MM-DD)
- `end_date`: Filter data until this date (YYYY-MM-DD)
- `limit`: Maximum number of data points to return

### Refresh Audience Data

**Manual Refresh:**
```
POST /soundcharts/audience/refresh/{track_uuid}/{platform_slug}/
```

## Data Processing

### AudienceDataProcessor

The main class for processing and storing audience data:

```python
processor = AudienceDataProcessor()

# Process single track-platform combination
result = processor.process_and_store_audience_data(
    track_uuid="7d534228-5165-11e9-9375-549f35161576",
    platform_slug="spotify",
    force_refresh=False
)

# Bulk processing
track_platform_pairs = [
    ("uuid1", "spotify"),
    ("uuid2", "apple_music")
]
results = processor.bulk_process_audience_data(track_platform_pairs)
```

### Management Commands

**Process specific track:**
```bash
python manage.py fetch_audience_data --track-uuid 7d534228-5165-11e9-9375-549f35161576 --platform spotify
```

**Process all tracks:**
```bash
python manage.py fetch_audience_data --all-tracks --platform spotify --limit 50
```

**Process stale tracks:**
```bash
python manage.py fetch_audience_data --limit 100
```

## Chart Data Format

### Single Platform Response

```json
{
  "success": true,
  "track": {
    "name": "bad guy",
    "credit_name": "Billie Eilish",
    "uuid": "7d534228-5165-11e9-9375-549f35161576"
  },
  "platform": {
    "name": "Spotify",
    "slug": "spotify",
    "metric_name": "Listeners"
  },
  "chart_data": {
    "labels": ["2025-07-21", "2025-07-22", "2025-07-23"],
    "datasets": [{
      "label": "bad guy on Spotify",
      "data": [2763701395, 2764225348, 2764759050],
      "borderColor": "#3b82f6",
      "backgroundColor": "rgba(59, 130, 246, 0.1)",
      "tension": 0.1
    }]
  }
}
```

### Multi-Platform Response

```json
{
  "success": true,
  "track": { ... },
  "platforms": [
    {
      "name": "Spotify",
      "slug": "spotify",
      "metric_name": "Listeners"
    },
    {
      "name": "Apple Music",
      "slug": "apple_music",
      "metric_name": "Listeners"
    }
  ],
  "chart_data": {
    "labels": ["2025-07-21", "2025-07-22", "2025-07-23"],
    "datasets": [
      {
        "label": "bad guy on Spotify",
        "data": [2763701395, 2764225348, 2764759050],
        "borderColor": "#3b82f6",
        "backgroundColor": "rgba(59, 130, 246, 0.1)"
      },
      {
        "label": "bad guy on Apple Music",
        "data": [1500000, 1550000, 1600000],
        "borderColor": "#ef4444",
        "backgroundColor": "rgba(239, 68, 68, 0.1)"
      }
    ]
  }
}
```

## Usage Examples

### Frontend Integration

**Chart.js Example:**
```javascript
// Fetch chart data
fetch('/soundcharts/audience/chart/7d534228-5165-11e9-9375-549f35161576/spotify/')
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      const ctx = document.getElementById('audienceChart').getContext('2d');
      new Chart(ctx, {
        type: 'line',
        data: data.chart_data,
        options: {
          responsive: true,
          scales: {
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: data.platform.metric_name
              }
            },
            x: {
              title: {
                display: true,
                text: 'Date'
              }
            }
          }
        }
      });
    }
  });
```

### Backend Data Retrieval

**Using Model Methods:**
```python
from soundcharts.models import Track, Platform

# Get track and platform
track = Track.objects.get(uuid="7d534228-5165-11e9-9375-549f35161576")
platform = Platform.objects.get(slug="spotify")

# Get chart data
chart_data = track.get_audience_chart_data(platform, limit=30)

# Get multi-platform comparison
platforms = Platform.objects.filter(slug__in=["spotify", "apple_music"])
comparison_data = track.get_platform_audience_comparison(platforms, limit=30)
```

## Data Management

### Storage Considerations

- **Data Retention**: Consider implementing data retention policies for old time-series data
- **Indexing**: The model includes optimized indexes for common query patterns
- **Partitioning**: For large datasets, consider date-based table partitioning

### Performance Optimization

- **Caching**: Implement Redis caching for frequently accessed chart data
- **Batch Processing**: Use bulk operations for large data imports
- **Query Optimization**: Leverage the built-in model methods for efficient data retrieval

## Error Handling

### Common Error Scenarios

1. **Track Not Found**: Returns 404 with descriptive error message
2. **Platform Not Found**: Returns 404 with platform identification
3. **API Failures**: Logs errors and returns appropriate HTTP status codes
4. **Data Processing Errors**: Transaction rollback with detailed error logging

### Monitoring

- All API calls are logged with appropriate log levels
- Failed data processing attempts are tracked
- Performance metrics are available through Django's built-in monitoring

## Future Enhancements

### Planned Features

1. **Real-time Updates**: WebSocket support for live audience data
2. **Advanced Analytics**: Trend analysis and prediction models
3. **Data Export**: CSV/Excel export functionality
4. **Custom Date Ranges**: Flexible date filtering options
5. **Platform Aggregation**: Combined metrics across multiple platforms

### Integration Opportunities

1. **Celery Tasks**: Background processing for large datasets
2. **Redis Caching**: Improved performance for chart data
3. **Elasticsearch**: Advanced search and analytics capabilities
4. **Data Warehousing**: Long-term data storage and analysis

## Troubleshooting

### Common Issues

1. **Migration Errors**: Ensure all migrations are applied before using new features
2. **API Rate Limits**: Monitor SoundCharts API usage and implement rate limiting
3. **Data Inconsistencies**: Use the `force_refresh` option to resolve data issues
4. **Performance Issues**: Check database indexes and query optimization

### Debug Tools

- Django Debug Toolbar for query analysis
- Custom management commands for data validation
- Comprehensive logging for troubleshooting
- Test suite for functionality verification
