# Chart Management

## Overview

The Chart Management system provides comprehensive tools for managing music charts, including automated synchronization, health monitoring, performance tracking, and advanced admin interfaces. The system ensures reliable data collection from multiple music platforms while providing detailed insights into chart performance and data quality.

## Features

### Core Functionality
- **Automated Sync Scheduling**: Intelligent scheduling based on chart frequency
- **Health Monitoring**: Real-time chart update status and performance tracking
- **Error Handling**: Comprehensive retry mechanisms with exponential backoff
- **Performance Metrics**: Detailed sync success rates, timing, and data quality metrics
- **Admin Interface**: Enhanced navigation and management tools
- **Historical Data Sync**: Complete historical data synchronization with gap detection

### Advanced Features
- **Track Metadata Integration**: Automatic track metadata fetching during sync
- **On-Demand Audience Data**: Smart audience data fetching when needed
- **Multi-Platform Support**: Unified management across all music platforms
- **Execution Tracking**: Detailed execution history and performance analytics
- **Native Admin Tables**: Professional admin interface with sorting and filtering

## Chart Sync System

### Enhanced Sync Features

#### Immediate vs Scheduled Sync
When adding a chart to the sync schedule, users can choose between:

1. **Scheduled Sync** (default): Chart syncs according to its frequency schedule
2. **Immediate Sync**: Chart starts syncing immediately with all historical data

#### Complete Historical Data Sync

The system intelligently syncs all missing chart rankings based on chart frequency:

- **Daily Charts**: Syncs one ranking for each day
- **Weekly Charts**: Syncs one ranking for each week  
- **Monthly Charts**: Syncs one ranking for each month

Historical sync features:
- Goes back up to 1 year to find missing data
- Identifies gaps in existing rankings
- Creates specific sync tasks for missing periods
- Ensures complete data consistency

#### Track Metadata Integration

During chart sync, the system automatically:

1. **Fetches Track Metadata**: For all new tracks found in chart rankings
2. **Updates Existing Tracks**: If track information has changed
3. **Queues Metadata Tasks**: Uses existing bulk metadata fetch system
4. **Tracks Metadata Age**: Only fetches metadata if older than 30 days

#### On-Demand Audience Data Fetching

Audience data is fetched on-demand when accessing song audience views:

1. **Automatic Detection**: System checks if audience data is stale or missing
2. **Background Fetching**: Triggers audience fetch task in background
3. **Multi-Platform Support**: Fetches audience data for all supported platforms
4. **Smart Caching**: Only fetches if data is older than 7 days

## Architecture

### Core Models

#### ChartSyncSchedule
Manages scheduled chart synchronization tasks.

**Key Fields:**
- `chart`: Foreign key to Chart model (unique constraint)
- `is_active`: Boolean flag to enable/disable sync
- `sync_frequency`: How often to sync (daily, weekly, monthly, custom)
- `custom_interval_hours`: Custom interval in hours
- `last_sync_at`: Timestamp of last successful sync
- `next_sync_at`: When the next sync should occur
- `total_executions`: Total number of sync attempts
- `successful_executions`: Number of successful syncs
- `failed_executions`: Number of failed syncs
- `sync_immediately`: Whether to start sync immediately
- `sync_historical_data`: Whether to sync all historical data
- `fetch_track_metadata`: Whether to fetch track metadata during sync

**Key Methods:**
- `calculate_next_sync()`: Calculates next sync time based on frequency
- `success_rate`: Property returning success rate as percentage
- `is_overdue`: Property indicating if sync is overdue

#### ChartSyncExecution
Tracks individual chart sync execution attempts.

**Key Fields:**
- `schedule`: Foreign key to ChartSyncSchedule
- `status`: Execution status (pending, running, completed, failed, cancelled)
- `started_at`: When execution started
- `completed_at`: When execution completed
- `error_message`: Error details if failed
- `rankings_created`: Number of chart rankings created
- `rankings_updated`: Number of chart rankings updated
- `tracks_created`: Number of tracks created
- `tracks_updated`: Number of tracks updated
- `celery_task_id`: Celery task identifier
- `retry_count`: Number of retry attempts
- `max_retries`: Maximum retries allowed

**Key Methods:**
- `mark_completed()`: Mark execution as completed with results
- `mark_failed()`: Mark execution as failed with error message
- `duration`: Property returning execution duration in seconds

## Admin Interface

### Chart Admin Enhancements

The Chart admin interface includes:

1. **Sync Status Column**: Shows current sync status for each chart
   - ✅ Active: Chart is actively syncing
   - ⚠ Overdue: Chart sync is overdue
   - ⏸ Inactive: Chart sync is paused
   - Not Scheduled: Chart is not in sync schedule

2. **Sync Actions**: Bulk actions for managing sync schedules
   - Add to Sync Schedule
   - Remove from Sync Schedule
   - Trigger Manual Sync

3. **Quick Links**: Direct links to manage sync schedules

### Chart Sync Schedule Admin

Dedicated admin interface for managing sync schedules:

**List View Features:**
- Chart name and platform
- Sync frequency and status
- Last sync and next sync times
- Success rate with color coding
- Overdue status indicators
- Total execution counts

**Detail View Features:**
- Complete schedule configuration
- Execution history inline
- Statistics and performance metrics
- Error tracking and debugging

**Actions:**
- Activate/Deactivate schedules
- Trigger manual syncs
- Bulk operations

### Chart Ranking Admin Dashboard

#### Native Admin Table Implementation

A proxy model `ChartRankingEntrySummary` provides a native Django admin table:

**Features:**
- **Native Django admin styling**: Uses built-in admin templates and CSS
- **Custom list display**: Shows position, track info, trend, weeks, streams, and previous position
- **Filtering by ranking**: Automatically filters entries for a specific chart ranking
- **Enhanced summary information**: Shows comprehensive chart metadata
- **Entry statistics**: Displays counts of new entries, moving up/down, and no change
- **Smart pagination**: Shows up to 100 entries per page
- **Read-only access**: Entries are managed through the import process

**Key Benefits:**
- Native look and feel matching other Django admin tables
- Built-in sorting, filtering, and search functionality
- Consistent styling with the overall admin interface
- Better performance using Django's optimized admin queryset handling
- Comprehensive information display with chart metadata

## Celery Task Integration

### Automatic Task Execution

The system includes multiple mechanisms to ensure scheduled tasks are executed:

1. **Celery Beat Configuration** (Primary Method)
   - Configured with `CELERY_BEAT_SCHEDULE`
   - Runs `process_scheduled_chart_syncs` every 5 minutes
   - Automatically finds and processes due schedules

2. **Django Management Command** (Backup Method)
   - Command: `python manage.py process_chart_syncs`
   - Can be run manually or via cron
   - Useful for debugging or manual execution

3. **Model-Level Scheduling** (Automatic Setup)
   - When a new `ChartSyncSchedule` is created, it ensures the periodic task is scheduled
   - Prevents missing periodic task configuration

### Starting the System

To run the complete chart sync system:

```bash
# Terminal 1: Start Celery Worker
celery -A config worker -l info

# Terminal 2: Start Celery Beat (for periodic tasks)
celery -A config beat -l info

# Terminal 3: Start Django (if not already running)
python manage.py runserver
```

### Task Configuration

**Celery Beat Schedule:**
```python
CELERY_BEAT_SCHEDULE = {
    'process-chart-sync-schedules': {
        'task': 'apps.soundcharts.tasks.process_scheduled_chart_syncs',
        'schedule': 300.0,  # Run every 5 minutes
    },
}
```

**Task Flow:**
1. Celery Beat runs `process_scheduled_chart_syncs` every 5 minutes
2. Task queries for active schedules where `next_sync_at <= now`
3. For each due schedule, creates a `ChartSyncExecution` record
4. Queues `sync_chart_rankings_task` with the execution ID
5. Updates execution status and Celery task ID
6. Worker processes the sync task asynchronously

## API Endpoints

### Chart Sync Schedules

**GET /api/sync/schedules/**
- Returns all chart sync schedules
- Includes chart details, status, and statistics

**POST /api/sync/schedules/**
- Creates a new sync schedule
- Requires `chart_id` in request body
- Optional: `is_active`, `sync_frequency`, `custom_interval_hours`

### Chart Sync Schedule Detail

**GET /api/sync/schedules/{schedule_id}/**
- Returns detailed schedule information
- Includes recent execution history

**PUT /api/sync/schedules/{schedule_id}/**
- Updates schedule configuration
- Supports partial updates

**DELETE /api/sync/schedules/{schedule_id}/**
- Removes sync schedule

### Chart Sync Trigger

**POST /api/sync/trigger/**
- Triggers manual sync for a chart
- Requires `chart_id` in request body
- Returns execution details

### Chart Sync Status

**GET /api/sync/status/{chart_id}/**
- Returns sync status for a specific chart
- Includes schedule details and latest execution

## Configuration

### Sync Frequency Options

1. **Daily**: Syncs every 24 hours
2. **Weekly**: Syncs every 7 days
3. **Monthly**: Syncs every 30 days
4. **Custom**: Syncs at custom interval (in hours)

### Automatic Frequency Detection

When creating a sync schedule, the system automatically detects the chart's frequency:
- If chart frequency is 'daily', 'weekly', or 'monthly', it uses that
- Otherwise, defaults to 'weekly'
- Users can override the detected frequency

### Missing Data Detection

The system intelligently detects missing ranking periods:
- Analyzes existing chart rankings
- Identifies gaps based on chart frequency
- Creates specific sync tasks for missing periods
- Ensures data consistency

## Error Handling

### Retry Mechanism

- Automatic retries on task failure (max 3 attempts)
- Exponential backoff between retries
- Detailed error logging and tracking

### Error Tracking

- Failed executions are logged with error messages
- Error statistics are maintained per schedule
- Admin interface shows error details for debugging

### Graceful Degradation

- Individual chart failures don't affect other charts
- Partial failures are tracked and reported
- System continues processing other schedules

## Monitoring and Reporting

### Success Metrics

- Success rate per schedule
- Total executions and success counts
- Average execution duration
- Data freshness indicators

### Alert System

- Overdue sync detection
- Failed execution alerts
- Performance degradation warnings

### Admin Notifications

- Django admin messages for batch operations
- Success/failure notifications
- Progress updates for long-running operations

## Usage Examples

### Adding a Chart to Sync Schedule

```python
# Via Admin Interface
1. Go to Charts admin
2. Select chart(s) to sync
3. Choose "Add to Sync Schedule" action
4. Configure sync frequency if needed

# Via API
POST /api/sync/schedules/
{
    "chart_id": 123,
    "sync_frequency": "weekly",
    "is_active": true
}
```

### Triggering Manual Sync

```python
# Via Admin Interface
1. Go to Charts admin
2. Select chart(s) to sync
3. Choose "Trigger Manual Sync" action

# Via API
POST /api/sync/trigger/
{
    "chart_id": 123
}
```

### Monitoring Sync Status

```python
# Via Admin Interface
1. Go to Chart Sync Schedules admin
2. View schedule list with status indicators
3. Click on individual schedules for details

# Via API
GET /api/sync/status/123/
```

## Best Practices

### Schedule Management

1. **Start with Weekly**: Begin with weekly syncs for most charts
2. **Monitor Performance**: Watch success rates and adjust frequency
3. **Handle Failures**: Investigate failed syncs promptly
4. **Regular Cleanup**: Remove inactive schedules periodically

### Performance Optimization

1. **Batch Operations**: Use bulk actions when possible
2. **Monitor Concurrency**: Ensure Celery workers can handle load
3. **Database Maintenance**: Regular cleanup of old execution records
4. **API Rate Limits**: Respect Soundcharts API limits

### Troubleshooting

1. **Check Logs**: Review Celery and Django logs for errors
2. **Verify API Keys**: Ensure Soundcharts API credentials are valid
3. **Monitor Celery**: Check Celery worker status and queue
4. **Database Health**: Monitor database performance and connections

## Future Enhancements

### Planned Features

1. **Subscription-based Access**: Different sync limits per user subscription
2. **Advanced Scheduling**: Cron-like scheduling expressions
3. **Data Retention**: Configurable retention periods for execution history
4. **Webhook Integration**: Real-time notifications for sync events
5. **Analytics Dashboard**: Advanced reporting and analytics

### Scalability Considerations

1. **Horizontal Scaling**: Support for multiple Celery workers
2. **Database Optimization**: Indexing and query optimization
3. **Caching**: Redis-based caching for frequently accessed data
4. **Load Balancing**: Distribution of sync tasks across workers

## Security Considerations

### Access Control

- Admin-only access to sync management
- Staff member requirement for API endpoints
- Future: Subscription-based access control

### Data Protection

- Secure API key storage
- Encrypted communication with Soundcharts API
- Audit logging for all sync operations

### Rate Limiting

- Built-in concurrency limits
- API rate limit respect
- Graceful handling of quota exceeded errors

## Implementation Status

### ✅ Completed Features

- **Core Models**: ChartSyncSchedule and ChartSyncExecution
- **Admin Interface**: Enhanced chart admin with sync management
- **Celery Integration**: Automated task processing and scheduling
- **API Endpoints**: RESTful API for sync management
- **Error Handling**: Comprehensive retry mechanisms and error tracking
- **Monitoring**: Performance metrics and health monitoring
- **Historical Sync**: Complete historical data synchronization
- **Track Integration**: Automatic track metadata fetching
- **Native Admin Tables**: Professional admin interface

### 🎯 Production Ready

The Chart Management system is production-ready with:
- Complete feature implementation
- Robust error handling and monitoring
- Security best practices
- Performance optimization
- Comprehensive documentation
- Testing and debugging tools

## Support and Documentation

For technical support or questions about Chart Management:

1. Check the troubleshooting section for common issues
2. Review error logs and monitoring data
3. Use debug tools for performance analysis
4. Contact system administrator for assistance
5. Submit issue reports for bug tracking
