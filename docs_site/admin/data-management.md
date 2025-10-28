# Data Management

Complete guide to managing charts, tracks, rankings, artists, and all data in the MusicChartsAI admin interface.

## Overview

The admin interface provides comprehensive data management capabilities for:

- **Chart Data**: Managing charts, rankings, and entries
- **Track Data**: Managing track metadata and audience data
- **Artist Data**: Managing artists and their metadata
- **Genre Data**: Managing genre hierarchies
- **Platform Data**: Managing platform configurations
- **Import Templates**: Consistent import workflows

## Chart Management

### Chart Rankings Dashboard

The Chart Rankings dashboard provides a native Django admin interface for viewing chart ranking entries.

#### Features

- **Native Admin Table**: Consistent Django admin styling
- **Custom List Display**: Position, track info, trend, weeks, streams
- **Filtering**: Filter by ranking automatically
- **Summary Information**: Chart metadata display
- **Entry Statistics**: New entries, moving up/down, no change
- **Smart Pagination**: Up to 100 entries per page

#### Accessing the Dashboard

1. Navigate to a **ChartRanking** in admin
2. Click **"View Entries in Admin Table"**
3. Opens native admin table with all entries

#### Direct URL Access

```
/admin/soundcharts/chartrankingentrysummary/?ranking_id={ranking_id}
```

### Chart Sync System

Scheduled chart synchronization with automated data fetching.

#### Configuration

1. **Create Chart Sync Schedule**:
   - Select chart
   - Set frequency (daily, weekly, monthly)
   - Enable auto-fetch options
   - Configure cascade triggers

2. **Monitor Sync Status**:
   - Last sync time
   - Success rate
   - Error count
   - Next scheduled sync

#### Manual Triggers

**Sync Now Button**:
- Manually trigger chart sync
- Immediate sync execution
- Progress tracking
- Error handling

**Cascade Trigger Button**:
- Manually trigger cascade data flow
- Fetches metadata and audience data
- Processes all cascade steps
- Status monitoring

### Chart Entry Management

View and manage chart ranking entries.

#### Entry Display

- **Position**: Current ranking position
- **Track Info**: Name and artist
- **Trend**: Position change indicator
- **Weeks**: Weeks on chart
- **Streams**: Stream count
- **Previous Position**: Historical position

#### Entry Statistics

- **New Entries**: Count of new songs
- **Moving Up**: Count of songs moving up
- **Moving Down**: Count of songs moving down
- **No Change**: Count of songs with same position

## Track Management

### Track Admin Interface

Enhanced track management with metadata and audience data.

#### Track List View

- **Search**: Search by name, UUID, or artist
- **Filters**: Platform, genre, label
- **Actions**: Bulk metadata fetch, bulk audience fetch
- **Status Indicators**: Metadata and audience status

#### Track Detail View

- **Metadata**: Complete track information
- **Artists**: Linked artists with roles
- **Genres**: Linked genres
- **Charts**: Chart appearances
- **Audience Data**: Platform-specific audience metrics

### Track Metadata Management

Fetch and manage track metadata from Soundcharts API.

#### Individual Track Fetch

1. Open track in admin
2. Click **"Fetch Metadata from API"**
3. System fetches metadata
4. Updates track record
5. Links artists and genres

#### Bulk Track Fetch

1. Select multiple tracks in list
2. Choose **"Fetch Metadata"** from actions
3. System processes tracks in background
4. Monitor progress in task list
5. Review results

#### Metadata Fields

- **Name**: Track title
- **Slug**: URL-friendly identifier
- **Credit Name**: Display name
- **Image URL**: Track image
- **Release Date**: Release date
- **Duration**: Track length
- **ISRC**: International Standard Recording Code
- **Label**: Record label
- **Genre**: Musical genre

### Track Audience Data

Fetch and manage track audience data.

#### Audience Platforms

- **Spotify**: Monthly listeners
- **YouTube**: Monthly listeners
- **Shazam**: Shazam count
- **Airplay**: Airplay counts

#### Fetching Audience Data

1. Open track in admin
2. Select platform from dropdown
3. Click **"Fetch Audience Data"**
4. System fetches time-series data
5. Stores data in database

#### Audience Data Display

- **Time Series**: Historical data points
- **Charts**: Visual representations
- **Export**: Export to Excel/CSV

## Artist Management

### Artist Admin Interface

Manage artists and their metadata.

#### Artist List View

- **Search**: Search by name or UUID
- **Filters**: Country, career stage
- **Status**: Metadata and audience status
- **Actions**: Fetch metadata, fetch audience

#### Artist Detail View

- **Metadata**: Complete artist information
- **Tracks**: Linked tracks
- **Audience**: Audience analytics
- **Charts**: Chart appearances

### Artist Metadata Management

Fetch and manage artist metadata.

#### Fetching Metadata

1. Open artist in admin
2. Click **"Fetch Metadata from API"**
3. System fetches metadata
4. Updates artist record
5. Stores timestamp

#### Metadata Fields

- **Name**: Artist name
- **Display Name**: Display name
- **Country**: Country code
- **Career Stage**: Career stage
- **Biography**: Artist bio
- **Image URLs**: Artist images

### Artist Audience Data

Fetch and manage artist audience data.

#### Audience Platforms

- **Spotify**: Monthly listeners
- **YouTube**: Monthly listeners
- **Instagram**: Followers
- **TikTok**: Followers

#### Fetching Audience Data

1. Open artist in admin
2. Select platform from dropdown
3. Click **"Fetch Audience Data"**
4. System fetches time-series data
5. Processes and stores data

## Genre Management

### Hierarchical Genre System

Manage genre hierarchies with parent-child relationships.

#### Root Genres

- Electronic
- Pop
- Rock
- Hip-Hop
- And more...

#### Subgenres

Each root genre can have multiple subgenres:
- Electronic → House, Techno, Ambient
- Pop → Pop Rock, Pop Dance, Pop Ballad

### Genre Admin Interface

- **Tree View**: Hierarchical display
- **Search**: Search by name
- **Filters**: Parent genre
- **Actions**: Create, edit, delete

## Platform Management

### Platform Configuration

Configure platforms for track and artist data.

#### Platform Settings

- **Name**: Platform name
- **Slug**: Platform identifier
- **Type**: Streaming or social
- **Icon**: Platform icon
- **Color**: Platform color

#### Platform Types

**Streaming Platforms**:
- Spotify
- YouTube
- Apple Music
- Deezer

**Social Platforms**:
- Instagram
- TikTok
- Twitter

## Import Templates

### Consistent Import Workflows

All import operations use consistent templates.

#### Template Features

- **Django Admin Module**: Native admin integration
- **Consistent Styling**: Unified design
- **Alert System**: Success/error feedback
- **Progress Tracking**: Real-time progress
- **Error Handling**: Comprehensive error messages

#### Import Types

- **Chart Sync**: Chart ranking import
- **Track Metadata**: Track metadata import
- **Artist Metadata**: Artist metadata import
- **Audience Data**: Audience data import

## Best Practices

### Data Quality

1. **Regular Sync**: Enable automatic chart sync
2. **Monitor Status**: Check sync health regularly
3. **Handle Errors**: Review and fix sync errors
4. **Data Validation**: Verify data completeness

### Performance

1. **Bulk Operations**: Use bulk actions when possible
2. **Background Processing**: Enable Celery for heavy operations
3. **Monitor Resources**: Track resource usage
4. **Optimize Queries**: Use efficient queries

### Maintenance

1. **Backup Data**: Regular database backups
2. **Clean Old Data**: Archive old chart rankings
3. **Monitor Storage**: Track database growth
4. **Update API Keys**: Keep API credentials current

## Troubleshooting

### Sync Failures

- Check API credentials
- Verify network connectivity
- Review error logs
- Check API rate limits

### Missing Data

- Trigger manual sync
- Fetch metadata manually
- Check data availability
- Review import logs

### Performance Issues

- Check Celery worker status
- Monitor database performance
- Review query optimization
- Check resource usage

## Related Documentation

- [Task Monitoring](task-monitoring.md)
- [Dashboard Overview](dashboard-overview.md)
- [Chart Management](../../features/chart-management.md)
- [Soundcharts Integration](../../features/soundcharts-integration.md)
