# Chart Sync System Documentation

## Overview

The Chart Sync System is a comprehensive solution for automatically synchronizing chart rankings from the Soundcharts API. It provides scheduled, automated chart data fetching with proper error handling, retry mechanisms, and detailed execution tracking.

## Enhanced Features

### Immediate vs Scheduled Sync

When adding a chart to the sync schedule, users can choose between:

1. **Scheduled Sync** (default): Chart will sync according to its frequency schedule
2. **Immediate Sync**: Chart will start syncing immediately when added to schedule

The immediate sync option triggers a one-time sync that includes all historical data based on the chart's frequency.

### Complete Historical Data Sync

The system now intelligently syncs all missing chart rankings based on the chart's frequency:

- **Daily Charts**: Syncs one ranking for each day
- **Weekly Charts**: Syncs one ranking for each week  
- **Monthly Charts**: Syncs one ranking for each month

Historical sync can be enabled/disabled per schedule and will:
- Go back up to 1 year to find missing data
- Identify gaps in existing rankings
- Create specific sync tasks for missing periods
- Ensure complete data consistency

### Track Metadata Integration

During chart sync, the system automatically:

1. **Fetches Track Metadata**: For all new tracks found in chart rankings
2. **Updates Existing Tracks**: If track information has changed
3. **Queues Metadata Tasks**: Uses existing bulk metadata fetch system
4. **Tracks Metadata Age**: Only fetches metadata if older than 30 days

This ensures all songs in chart rankings have complete metadata.

### On-Demand Audience Data Fetching

Audience data is now fetched on-demand when accessing song audience views:

1. **Automatic Detection**: System checks if audience data is stale or missing
2. **Background Fetching**: Triggers audience fetch task in background
3. **Multi-Platform Support**: Fetches audience data for all supported platforms
4. **Smart Caching**: Only fetches if data is older than 7 days

This approach optimizes performance by not fetching audience data during chart sync.

### Core Components

1. **Models**
   - `ChartSyncSchedule`: Manages sync schedules for individual charts
   - `ChartSyncExecution`: Tracks individual sync execution attempts

2. **Admin Interface**
   - Chart admin with sync status and management buttons
   - Dedicated sync schedule admin interface
   - Execution history and monitoring

3. **Celery Tasks**
   - `sync_chart_rankings_task`: Main sync task for individual charts
   - `process_scheduled_chart_syncs`: Periodic task to process due schedules

4. **API Endpoints**
   - RESTful API for managing sync schedules
   - Status monitoring and manual trigger endpoints

## Models

### ChartSyncSchedule

Manages scheduled chart synchronization tasks.

**Fields:**
- `chart`: Foreign key to Chart model (unique constraint)
- `is_active`: Boolean flag to enable/disable sync
- `sync_frequency`: How often to sync (daily, weekly, monthly, custom)
- `custom_interval_hours`: Custom interval in hours (for custom frequency)
- `last_sync_at`: Timestamp of last successful sync
- `next_sync_at`: When the next sync should occur
- `total_executions`: Total number of sync attempts
- `successful_executions`: Number of successful syncs
- `failed_executions`: Number of failed syncs
- `sync_immediately`: Whether to start sync immediately when schedule is created
- `sync_historical_data`: Whether to sync all historical data based on chart frequency
- `fetch_track_metadata`: Whether to fetch track metadata during chart sync
- `created_by`: User who created the schedule
- `created_at`, `updated_at`: Timestamps

**Key Methods:**
- `calculate_next_sync()`: Calculates next sync time based on frequency
- `success_rate`: Property returning success rate as percentage
- `is_overdue`: Property indicating if sync is overdue

### ChartSyncExecution

Tracks individual chart sync execution attempts.

**Fields:**
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

The Chart admin interface has been enhanced with:

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

## Celery Tasks

### Automatic Task Execution
The system includes multiple mechanisms to ensure scheduled tasks are executed:

1. **Celery Beat Configuration** (Primary Method)
   - Configured in `config/settings.py` with `CELERY_BEAT_SCHEDULE`
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

### Configuration Details

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

### sync_chart_rankings_task

Main task for syncing chart rankings.

**Parameters:**
- `schedule_id`: ID of the ChartSyncSchedule
- `execution_id`: ID of the ChartSyncExecution

**Process:**
1. Retrieves schedule and execution records
2. Determines missing ranking periods based on chart frequency
3. Fetches rankings from Soundcharts API for each missing period
4. Processes and stores chart rankings and track data
5. Updates execution record with results
6. Handles retries on failure (max 3 retries)

**Concurrency Limits:**
- Max 2 concurrent chart sync tasks
- Max 2 concurrent metadata/audience tasks
- Configurable via Celery settings

### process_scheduled_chart_syncs

Periodic task to process due sync schedules.

**Process:**
1. Finds all active schedules where `next_sync_at <= now`
2. Creates execution records for each due schedule
3. Queues individual sync tasks
4. Updates next sync times

**Scheduling:**
- **Automatically scheduled** via Celery Beat every 5 minutes
- Can also be run manually via Django management command
- Ensures continuous monitoring of due schedules

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

## Conclusion

The Chart Sync System provides a robust, scalable solution for automatically synchronizing chart data from the Soundcharts API. With comprehensive error handling, monitoring, and management capabilities, it ensures reliable data synchronization while providing administrators with full visibility and control over the sync process.

The system is designed to be extensible and maintainable, with clear separation of concerns and comprehensive documentation. Regular monitoring and maintenance will ensure optimal performance and reliability.
