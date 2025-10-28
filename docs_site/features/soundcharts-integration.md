# Soundcharts Integration

The Soundcharts integration provides automated chart synchronization, data cascading, and comprehensive music analytics.

## Overview

The Soundcharts integration enables:

- **Automated Chart Sync**: Scheduled chart ranking retrieval
- **Cascade Data Flow**: Automatic metadata and audience data fetching
- **Track Management**: Complete track lifecycle management
- **Artist Management**: Artist metadata and audience tracking
- **Audience Analytics**: Time-series audience data analysis
- **Multi-Platform Support**: Spotify, YouTube, Instagram, TikTok, and more

## Architecture

### Data Flow

```
Chart Sync (Automatic)
    ↓
Creates Tracks (minimal data)
    ↓
Auto-Queue: Track Metadata Fetch
    ↓
Extract Artists & Genres
Link to Tracks
    ↓
Auto-Queue: Artist Metadata Fetch
    ↓
Fetch Full Artist Metadata
    ↓
Auto-Queue: Track Audience Fetch
Auto-Queue: Artist Audience Fetch
    ↓
Complete Analytics Data Available
```

### Components

#### Chart Sync System

- **Scheduled Tasks**: Celery Beat scheduling
- **Chart Ranking**: Fetches chart rankings from API
- **Track Creation**: Automatically creates track records
- **Status Tracking**: Monitors sync health and status

#### Cascade Flow

- **Automatic Triggering**: No manual intervention required
- **Sequential Processing**: Metadata → Audience
- **Error Handling**: Comprehensive retry mechanisms
- **Status Monitoring**: Real-time progress tracking

#### API Integration

- **Soundcharts API**: Secure API communication
- **Authentication**: API key-based authentication
- **Rate Limiting**: Respects API rate limits
- **Error Recovery**: Automatic retry on failures

## Features

### Automated Chart Sync

The system automatically fetches chart rankings and creates tracks.

#### Configuration

In the admin interface:

1. **Create Chart Sync Schedule**
2. **Configure Settings**:
   - Chart selection
   - Schedule (daily, weekly, etc.)
   - Auto-fetch options
   - Cascade triggers

#### Chart Sync Process

1. **Schedule Triggered**: Celery Beat starts sync
2. **Fetch Rankings**: Calls Soundcharts API
3. **Create Tracks**: Creates track records
4. **Store Data**: Saves rankings to database
5. **Trigger Cascade**: If enabled, starts metadata fetch

### Cascade Data Flow

The cascade system automatically fetches data in sequence.

#### Cascade Steps

1. **Track Metadata**
   - Fetches full track information
   - Extracts artists
   - Extracts genres
   - Links relationships

2. **Artist Metadata**
   - Fetches artist details
   - Updates artist records
   - Stores metadata timestamps

3. **Track Audience**
   - Fetches platform-specific data
   - Stores time-series data
   - Updates audience metrics

4. **Artist Audience**
   - Fetches platform-specific data
   - Stores time-series data
   - Updates audience metrics

#### Platform Configuration

**Track Audience Platforms** (default):
- Spotify
- YouTube
- Shazam
- Airplay

**Artist Audience Platforms** (default):
- Spotify
- YouTube
- Instagram
- TikTok

#### Manual Triggers

You can manually trigger cascade flow:

1. Navigate to chart admin
2. Click **"Trigger Cascade Data Fetch"**
3. System queues all cascade tasks
4. Monitor progress in admin

### Track Management

Complete track lifecycle management.

#### Track Creation

Tracks are created automatically during chart sync.

**Initial Data** (minimal):
- Track name
- UUID
- Slug
- Credit name
- Image URL

#### Track Metadata Fetch

Fetches complete track information.

**Includes**:
- Full metadata
- Artist relationships
- Genre relationships
- Image URLs
- Production details

#### Track Audience Data

Fetches platform-specific audience data.

**Metrics**:
- Stream counts
- Listener counts
- Chart positions
- Time-series data

### Artist Management

Complete artist management integration.

#### Artist Extraction

Artists are automatically extracted from tracks.

**Process**:
1. Fetch track metadata
2. Parse credit names
3. Extract artist UUIDs
4. Create artist records
5. Link to tracks

#### Artist Metadata Fetch

Fetches comprehensive artist information.

**Includes**:
- Name and display name
- Biography
- Career stage
- Country
- Image URLs

#### Artist Audience Data

Fetches audience analytics for artists.

**Platforms**:
- Streaming: Monthly listeners
- Social: Follower counts
- Historical: Time-series data

### Audience Analytics

Time-series audience data analysis.

#### Data Points

Each data point contains:
- **Platform**: Spotify, YouTube, etc.
- **Metric Type**: Listeners, followers, etc.
- **Value**: Audience count
- **Date**: Measurement date

#### Data Processing

- **Time Series**: Sequential data storage
- **Aggregation**: Calculated metrics
- **Charts**: Visual representation
- **Export**: Excel export capability

## Configuration

### Chart Sync Schedule

Configure chart synchronization:

```python
# In admin interface
ChartSyncSchedule:
    chart: Spotify Top 50
    schedule: Daily at 2 AM
    fetch_track_metadata: True
    auto_trigger_cascade: True
```

### Cascade Settings

Control cascade behavior:

```python
# Track metadata triggers
fetch_track_metadata:
    auto_extract_artists: True
    auto_extract_genres: True
    trigger_artist_metadata: True
    trigger_audience_fetch: True

# Platform selection
track_audience_platforms: ['spotify', 'youtube', 'shazam', 'airplay']
artist_audience_platforms: ['spotify', 'youtube', 'instagram', 'tiktok']
```

## API Endpoints

### Soundcharts API

#### Chart Rankings

```
GET /api/v2.37/chart/{chart_id}/ranking
```

#### Track Metadata

```
GET /api/v2.37/track/{uuid}
```

#### Artist Metadata

```
GET /api/v2.37/artist/{uuid}
```

#### Audience Data

```
GET /api/v2/artist/{uuid}/streaming/{platform}
GET /api/v2.37/artist/{uuid}/social/{platform}/followers/
GET /api/v2/track/{uuid}/streaming/{platform}
```

### Internal API

#### Trigger Cascade

```
POST /admin/soundcharts/chart/{id}/trigger-cascade/
```

#### Check Status

```
GET /admin/soundcharts/chart/{id}/status/
```

## Monitoring

### Health Checks

Monitor chart sync health:

- **Last Sync**: Last successful sync time
- **Success Rate**: Percentage of successful syncs
- **Error Count**: Number of failures
- **Status**: Current sync status

### Task Status

Monitor Celery task progress:

- **Task ID**: Unique task identifier
- **Status**: Pending, processing, complete, failed
- **Progress**: Percentage complete
- **Logs**: Task execution logs

### Admin Dashboard

View comprehensive metrics:

- **Charts**: Total number of charts
- **Tracks**: Total number of tracks
- **Artists**: Total number of artists
- **Status**: System health indicators

## Troubleshooting

### Chart Sync Fails

**Possible Causes**:
- Invalid API credentials
- Network connectivity issues
- API rate limits exceeded
- Invalid chart configuration

**Solutions**:
- Verify API credentials
- Check network connection
- Review rate limits
- Validate chart settings

### Cascade Stops

**Possible Causes**:
- Task queue full
- Error in previous step
- Missing data dependencies
- Resource exhaustion

**Solutions**:
- Check task queue status
- Review error logs
- Verify data completeness
- Monitor resource usage

### Missing Data

**Possible Causes**:
- Chart sync not completed
- Metadata not fetched
- Audience data not available
- Platform-specific issues

**Solutions**:
- Trigger manual sync
- Manually fetch metadata
- Check platform availability
- Review data completeness

## Best Practices

### Configuration

1. **Enable Auto-Cascade**: Always enable cascade triggers
2. **Monitor Health**: Regularly check sync status
3. **Schedule Appropriately**: Don't sync too frequently
4. **Handle Errors**: Set up error notifications

### Data Management

1. **Regular Backups**: Backup database regularly
2. **Clean Old Data**: Archive old chart rankings
3. **Monitor Storage**: Track database growth
4. **Optimize Queries**: Monitor query performance

### API Usage

1. **Respect Limits**: Don't exceed rate limits
2. **Cache Responses**: Cache API responses
3. **Handle Errors**: Implement retry logic
4. **Monitor Usage**: Track API consumption

## Related Documentation

- [Chart Management](chart-management.md)
- [Artist Management](artist-management.md)
- [Background Tasks](background-tasks.md)
- [API Reference](../../api/overview.md)
