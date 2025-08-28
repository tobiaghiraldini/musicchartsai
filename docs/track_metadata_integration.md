# Track Metadata Integration

## Overview

This document describes the implementation of track metadata fetching from the Soundcharts API, including both synchronous and asynchronous (Celery) approaches.

## Features Implemented

### 1. Celery Tasks for Background Processing

#### `fetch_track_metadata(track_uuid)`
- Fetches metadata for a single track from Soundcharts API
- Updates the track model with enhanced metadata fields
- Runs asynchronously in the background

#### `fetch_bulk_track_metadata(task_id)`
- Processes multiple tracks in bulk
- Updates progress tracking in the MetadataFetchTask model
- Handles errors gracefully and continues processing

#### `fetch_all_tracks_metadata()`
- Automatically identifies tracks that need metadata updates
- Creates bulk metadata fetch tasks for efficiency
- Considers tracks without metadata or older than 30 days

### 2. Admin Interface Enhancements

#### Track Changelist
- **Import from API button**: Imports tracks from Soundcharts API and automatically queues metadata fetch tasks
- **Fetch All Metadata button**: Creates bulk metadata fetch tasks for selected tracks
- **Bulk actions**: 
  - "Fetch metadata from Soundcharts API (Background)" - queues individual tasks
  - "Create bulk metadata fetch task" - creates a single bulk task

#### Track Change Form
- **Fetch Metadata from API button**: Fetches metadata synchronously for immediate feedback
- Enhanced fieldsets for better organization of metadata fields

### 3. Enhanced Track Model

The Track model now includes additional metadata fields:
- `slug`: Soundcharts track slug
- `release_date`: Track release date
- `duration`: Track duration in seconds
- `isrc`: International Standard Recording Code
- `label`: Record label
- `genre`: Primary genre
- `metadata_fetched_at`: Timestamp of last metadata fetch
- `audience_fetched_at`: Timestamp of last audience data fetch

### 4. MetadataFetchTask Model

Tracks the progress of metadata fetching operations:
- Task type (metadata, audience, bulk_metadata, bulk_audience)
- Status (pending, running, completed, failed, cancelled)
- Progress tracking (total, processed, successful, failed tracks)
- Celery task ID and error handling
- Timestamps for monitoring

## API Integration

### SoundchartsService Methods Used

- `get_song_metadata_enhanced(uuid)`: Fetches comprehensive track metadata
- Handles various response formats and error conditions
- Maps API response fields to model fields

### Data Mapping

The implementation maps the following API fields to model fields:
- `object.name` → `name`
- `object.slug` → `slug`
- `object.creditName` → `credit_name`
- `object.imageUrl` → `image_url`
- `object.releaseDate` → `release_date`
- `object.duration` → `duration`
- `object.isrc` → `isrc`
- `object.label.name` → `label`
- `object.genres[0].name` → `genre`

## Usage

### 1. Import Tracks from API

1. Navigate to Tracks admin changelist
2. Click "Import from API" button
3. Configure import parameters (limit, offset, artist UUID)
4. Fetch data and add tracks to database
5. Metadata fetch tasks are automatically queued

### 2. Fetch Metadata for Existing Tracks

#### Individual Tracks
1. Open track change form
2. Click "Fetch Metadata from API" button
3. Metadata is fetched synchronously and updated immediately

#### Bulk Operations
1. Select tracks in changelist
2. Use bulk actions to queue metadata fetch tasks
3. Monitor progress in MetadataFetchTask admin

### 3. Management Commands

```bash
# Fetch metadata for a specific track
python manage.py fetch_track_metadata --track-uuid <uuid>

# Create bulk metadata fetch task
python manage.py fetch_track_metadata --bulk

# Fetch metadata for all tracks that need it
python manage.py fetch_track_metadata --all

# Dry run to see what would be done
python manage.py fetch_track_metadata --bulk --dry-run
```

## Error Handling

- API failures are logged and tracked
- Individual track failures don't stop bulk operations
- Retry mechanisms can be implemented using the retry_count field
- Error messages are stored in the MetadataFetchTask model

## Monitoring and Debugging

### Admin Interface
- MetadataFetchTask admin provides real-time progress monitoring
- Visual progress bars and status indicators
- Detailed error messages and timestamps

### Logging
- Comprehensive logging at INFO, WARNING, and ERROR levels
- Task execution tracking
- API response logging for debugging

### Celery Integration
- Task IDs are stored for monitoring
- Progress updates in real-time
- Background processing for large datasets

## Future Enhancements

1. **Retry Logic**: Implement automatic retry for failed metadata fetches
2. **Rate Limiting**: Add API rate limiting to prevent overwhelming the Soundcharts API
3. **Incremental Updates**: Only fetch metadata for tracks that have changed
4. **Audience Data**: Extend to fetch track audience and demographic data
5. **Webhooks**: Implement webhooks for real-time metadata updates
6. **Scheduling**: Add periodic metadata refresh tasks

## Configuration

### Required Settings
- `SOUNDCHARTS_APP_ID`: Soundcharts application ID
- `SOUNDCHARTS_API_KEY`: Soundcharts API key
- `SOUNDCHARTS_API_URL`: Soundcharts API base URL

### Celery Configuration
- Ensure Celery worker is running for background tasks
- Configure result backend for task monitoring
- Set appropriate task timeouts and retry policies

## Testing

### Unit Tests
- Test individual task functions
- Mock API responses for testing
- Verify data mapping and error handling

### Integration Tests
- Test admin interface functionality
- Verify Celery task execution
- Test bulk operations with real data

### Manual Testing
- Use management commands for testing
- Verify admin interface functionality
- Monitor task progress in admin
