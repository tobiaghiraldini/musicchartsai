# Data Models and Relationships

## Overview

This document provides a comprehensive overview of the data models and relationships implemented in MusicChartsAI, including the enhanced models for tracks, artists, genres, and their integrations with external APIs.

## Core Models

### Track Model

The Track model serves as the central entity for music data, with comprehensive metadata support and API integrations.

#### Key Fields

**Basic Information**:
- `name`: Track title
- `slug`: URL-friendly identifier
- `uuid`: SoundCharts UUID for API integration
- `credit_name`: Artist credit name
- `image_url`: Track artwork URL

**Metadata Fields**:
- `release_date`: Track release date
- `duration`: Track duration in seconds
- `isrc`: International Standard Recording Code
- `label`: Record label
- `metadata_fetched_at`: Timestamp of last metadata fetch
- `audience_fetched_at`: Timestamp of last audience data fetch

**Relationships**:
- `artists`: ManyToManyField to all associated artists
- `primary_artist`: ForeignKey to the main artist
- `genres`: ManyToManyField to all associated genres
- `primary_genre`: ForeignKey to the main genre
- `album`: ForeignKey to the album (if applicable)

#### Usage Examples

```python
# Create track with metadata
track = Track.objects.create(
    name="bad guy",
    uuid="11e81bcc-9c1c-ce38-b96b-a0369fe50396",
    credit_name="Billie Eilish",
    release_date="2019-03-29",
    duration=194,
    isrc="USRC11900595"
)

# Add artists and genres
track.artists.set([billie_eilish])
track.primary_artist = billie_eilish
track.genres.set([electronic, alternative])
track.primary_genre = electronic
```

### Artist Model

Enhanced artist model with SoundCharts API integration and relationship management.

#### Key Features

**SoundCharts Integration**:
- `uuid`: SoundCharts UUID for reliable identification
- `slug`: URL-friendly identifier
- `app_url`: SoundCharts application URL
- `image_url`: Artist image URL

**Relationship Management**:
- `create_from_soundcharts()`: Class method for API data processing
- Automatic field updates when artist data changes
- UUID-based identification prevents duplicates

#### Usage Examples

```python
# Create artist from SoundCharts data
artist_data = {
    "uuid": "11e81bcc-9c1c-ce38-b96b-a0369fe50396",
    "slug": "billie-eilish",
    "name": "Billie Eilish",
    "appUrl": "https://app.soundcharts.com/app/artist/billie-eilish/overview",
    "imageUrl": "https://assets.soundcharts.com/artist/c/1/c/11e81bcc-9c1c-ce38-b96b-a0369fe50396.jpg"
}

artist = Artist.create_from_soundcharts(artist_data)

# Query tracks by artist
billie_tracks = artist.tracks.all()
billie_primary_tracks = artist.primary_tracks.all()
```

### Genre Model (Hierarchical)

The Genre model supports hierarchical relationships that align with the SoundCharts API data structure.

#### Key Features

**Hierarchical Structure**:
- `parent`: ForeignKey to parent genre (null for root genres)
- `level`: Hierarchy level (0=root, 1=sub)
- `soundcharts_root`: Original root genre name from API

**SoundCharts Integration**:
- Direct mapping to SoundCharts genre data structure
- `create_from_soundcharts()` method handles API data processing
- Preservation of original SoundCharts root genre names

#### Usage Examples

```python
# Create genres from SoundCharts data
genre_data = {
    "root": "electronic",
    "sub": ["house", "techno", "ambient"]
}

root_genre, subgenres = Genre.create_from_soundcharts(genre_data)

# Query genres
root_genres = Genre.get_root_genres()
electronic = Genre.objects.get(name="electronic")
subgenres = electronic.get_all_subgenres()

# Check hierarchy
if electronic.is_root:
    print("This is a root genre")
```

## API Integration Models

### ChartSyncSchedule Model

Manages automated chart synchronization schedules.

#### Key Fields

- `chart`: ForeignKey to Chart model
- `is_active`: Boolean flag for schedule activation
- `sync_frequency`: Frequency of synchronization (daily, weekly, monthly)
- `last_sync_at`: Timestamp of last successful sync
- `next_sync_at`: Timestamp of next scheduled sync
- `total_executions`: Count of total sync executions
- `successful_executions`: Count of successful syncs

#### Usage Examples

```python
# Create sync schedule
schedule = ChartSyncSchedule.objects.create(
    chart=spotify_chart,
    sync_frequency='daily',
    is_active=True
)

# Get active schedules
active_schedules = ChartSyncSchedule.objects.filter(is_active=True)
```

### ChartSyncExecution Model

Tracks individual chart synchronization executions.

#### Key Fields

- `schedule`: ForeignKey to ChartSyncSchedule
- `status`: Execution status (pending, running, completed, failed)
- `started_at`: Execution start timestamp
- `completed_at`: Execution completion timestamp
- `total_entries`: Total entries processed
- `successful_entries`: Successfully processed entries
- `failed_entries`: Failed entries
- `error_message`: Error details if execution failed

### MetadataFetchTask Model

Tracks metadata fetching operations for tracks and artists.

#### Key Fields

- `task_type`: Type of task (metadata, audience, bulk_metadata, bulk_audience)
- `status`: Task status (pending, running, completed, failed, cancelled)
- `progress`: Progress tracking (total, processed, successful, failed)
- `celery_task_id`: Celery task identifier
- `error_message`: Error details if task failed
- `created_at`, `updated_at`: Timestamps

## Data Processing and Integration

### Track Metadata Integration

#### Celery Tasks

**`fetch_track_metadata(track_uuid)`**:
- Fetches metadata for a single track from SoundCharts API
- Updates the track model with enhanced metadata fields
- Runs asynchronously in the background

**`fetch_bulk_track_metadata(task_id)`**:
- Processes multiple tracks in bulk
- Updates progress tracking in the MetadataFetchTask model
- Handles errors gracefully and continues processing

**`fetch_all_tracks_metadata()`**:
- Automatically identifies tracks that need metadata updates
- Creates bulk metadata fetch tasks for efficiency
- Considers tracks without metadata or older than 30 days

#### Data Mapping

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

### Artist-Track Relationships

#### Multiple Artist Support

- **Many-to-Many Relationship**: Tracks can have multiple artists
- **Primary Artist**: One artist designated as the main artist
- **SoundCharts Integration**: Direct mapping to SoundCharts artist data structure

#### Data Processing

When track metadata is fetched:
1. **Parse Artists Array**: Extract artist data from SoundCharts API response
2. **Create/Update Artists**: Use `Artist.create_from_soundcharts()` for each artist
3. **Link to Track**: Set ManyToManyField and primary artist
4. **Preserve Relationships**: Maintain existing artist-track connections

### Hierarchical Genre Processing

#### API Data Structure

SoundCharts genre data format:
```json
{
  "genres": [
    {
      "root": "electronic",
      "sub": ["house", "techno", "ambient"]
    }
  ]
}
```

#### Processing Logic

1. **Root Genre Creation**: Create root genre if it doesn't exist
2. **Subgenre Creation**: Create subgenres with proper parent relationships
3. **Track Association**: Link tracks to appropriate genres
4. **Primary Genre**: Set primary genre to root genre

## Admin Interface Enhancements

### Track Admin Updates

**List Display**: Shows `primary_artist` and `primary_genre` in the track list
**Filters**: Added `artists`, `primary_artist`, `genres`, and `primary_genre` filters
**Fieldsets**: Updated to include both relationship fields and individual fields
**Actions**: Bulk actions for metadata fetching and API synchronization

### Artist Management

- Artists are automatically created/updated when track metadata is fetched
- UUID-based identification prevents duplicates
- All SoundCharts artist fields are preserved
- Comprehensive artist-track relationship management

### Genre Management

- Hierarchical display shows parent-child relationships
- Automatic slug generation from genre names
- SoundCharts integration preserves original API data
- Support for both root and subgenre queries

## Database Optimization

### Indexing Strategy

**Track Model Indexes**:
```python
class Meta:
    indexes = [
        models.Index(fields=['uuid']),
        models.Index(fields=['primary_artist']),
        models.Index(fields=['primary_genre']),
        models.Index(fields=['metadata_fetched_at']),
        models.Index(fields=['audience_fetched_at']),
    ]
```

**Artist Model Indexes**:
```python
class Meta:
    indexes = [
        models.Index(fields=['uuid']),
        models.Index(fields=['slug']),
    ]
```

**Genre Model Indexes**:
```python
class Meta:
    indexes = [
        models.Index(fields=['parent']),
        models.Index(fields=['level']),
        models.Index(fields=['soundcharts_root']),
    ]
```

### Query Optimization

**Efficient Queries**:
```python
# Use select_related for foreign keys
tracks = Track.objects.select_related('primary_artist', 'primary_genre')

# Use prefetch_related for many-to-many
tracks = Track.objects.prefetch_related('artists', 'genres')

# Combined optimization
tracks = Track.objects.select_related('primary_artist', 'primary_genre').prefetch_related('artists', 'genres')
```

## Management Commands

### Track Metadata Commands

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

### Chart Sync Commands

```bash
# Sync specific chart
python manage.py sync_chart_rankings --chart-id <id>

# Sync all active charts
python manage.py sync_chart_rankings --all

# Create sync schedule
python manage.py create_sync_schedule --chart-id <id> --frequency daily
```

## Error Handling and Monitoring

### Error Handling

- API failures are logged and tracked
- Individual track failures don't stop bulk operations
- Retry mechanisms using the retry_count field
- Error messages are stored in task models

### Monitoring

**Admin Interface**:
- Real-time progress monitoring in MetadataFetchTask admin
- Visual progress bars and status indicators
- Detailed error messages and timestamps

**Logging**:
- Comprehensive logging at INFO, WARNING, and ERROR levels
- Task execution tracking
- API response logging for debugging

**Celery Integration**:
- Task IDs are stored for monitoring
- Progress updates in real-time
- Background processing for large datasets

## Future Enhancements

### Planned Features

1. **Retry Logic**: Implement automatic retry for failed metadata fetches
2. **Rate Limiting**: Add API rate limiting to prevent overwhelming external APIs
3. **Incremental Updates**: Only fetch metadata for tracks that have changed
4. **Webhooks**: Implement webhooks for real-time metadata updates
5. **Scheduling**: Add periodic metadata refresh tasks
6. **Analytics**: Track genre popularity and trends
7. **Collaboration Tracking**: Identify frequent artist collaborations

### Performance Improvements

1. **Caching**: Implement Redis caching for frequently accessed data
2. **Database Optimization**: Add more indexes for common query patterns
3. **Batch Processing**: Optimize bulk operations for large datasets
4. **Connection Pooling**: Implement database connection pooling

## Configuration

### Required Settings

```python
# SoundCharts API Configuration
SOUNDCHARTS_APP_ID = 'your_app_id'
SOUNDCHARTS_API_KEY = 'your_api_key'
SOUNDCHARTS_API_URL = 'your_api_url'

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'musiccharts_db',
        # ... other database settings
    }
}
```

### Celery Configuration

- Ensure Celery worker is running for background tasks
- Configure result backend for task monitoring
- Set appropriate task timeouts and retry policies

## Testing

### Unit Tests

- Test individual model methods and properties
- Mock API responses for testing
- Verify data mapping and error handling
- Test relationship queries and optimizations

### Integration Tests

- Test admin interface functionality
- Verify Celery task execution
- Test bulk operations with real data
- Test API integration and data processing

### Manual Testing

- Use management commands for testing
- Verify admin interface functionality
- Monitor task progress in admin
- Test data consistency and relationships

## Conclusion

The data models and relationships in MusicChartsAI provide a robust foundation for music data management, with comprehensive API integrations, hierarchical data structures, and efficient querying capabilities. The system is designed for scalability, maintainability, and performance, with extensive monitoring and error handling capabilities.
