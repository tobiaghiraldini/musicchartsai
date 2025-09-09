# Artist-Track Relationships

## Overview

The Track model now supports comprehensive artist relationships that align with the SoundCharts API data structure. This allows for proper handling of multiple artists per track and maintains data integrity.

## Key Features

### Multiple Artist Support
- **Many-to-Many Relationship**: Tracks can have multiple artists
- **Primary Artist**: One artist designated as the main artist
- **SoundCharts Integration**: Direct mapping to SoundCharts artist data structure

### Artist Data Structure
The system handles SoundCharts artist data in this format:
```json
{
  "artists": [
    {
      "uuid": "11e81bcc-9c1c-ce38-b96b-a0369fe50396",
      "slug": "billie-eilish",
      "name": "Billie Eilish",
      "appUrl": "https://app.soundcharts.com/app/artist/billie-eilish/overview",
      "imageUrl": "https://assets.soundcharts.com/artist/c/1/c/11e81bcc-9c1c-ce38-b96b-a0369fe50396.jpg"
    }
  ]
}
```

## Model Relationships

### Track Model Fields
- `artists`: ManyToManyField to all associated artists
- `primary_artist`: ForeignKey to the main artist (first artist from API)

### Artist Model Enhancements
- `create_from_soundcharts()`: Class method to create/update artists from API data
- UUID-based identification for reliable artist matching
- Automatic field updates when artist data changes

## Usage Examples

### Creating Artists from SoundCharts Data
```python
artist_data = {
    "uuid": "11e81bcc-9c1c-ce38-b96b-a0369fe50396",
    "slug": "billie-eilish",
    "name": "Billie Eilish",
    "appUrl": "https://app.soundcharts.com/app/artist/billie-eilish/overview",
    "imageUrl": "https://assets.soundcharts.com/artist/c/1/c/11e81bcc-9c1c-ce38-b96b-a0369fe50396.jpg"
}

artist = Artist.create_from_soundcharts(artist_data)
```

### Track Artist Management
```python
# Add multiple artists to track
track.artists.set([artist1, artist2, artist3])
track.primary_artist = artist1

# Query tracks by artist
billie_tracks = artist1.tracks.all()
billie_primary_tracks = artist1.primary_tracks.all()
```

### Complex Queries
```python
# Get all tracks by a specific artist in a specific genre
alternative_tracks = Genre.objects.get(name="alternative").tracks.all()
billie_alternative_tracks = alternative_tracks.filter(artists=artist1)

# Get all artists for tracks in a specific genre
alternative_artists = Artist.objects.filter(tracks__genres__name="alternative").distinct()
```

## Admin Interface

### Track Admin Updates
- **List Display**: Shows `primary_artist` in the track list
- **Filters**: Added `artists` and `primary_artist` filters
- **Fieldsets**: Updated to include both `primary_artist` and `artists` fields

### Artist Management
- Artists are automatically created/updated when track metadata is fetched
- UUID-based identification prevents duplicates
- All SoundCharts artist fields are preserved

## Data Processing

### Automatic Artist Creation
When track metadata is fetched:
1. **Parse Artists Array**: Extract artist data from SoundCharts API response
2. **Create/Update Artists**: Use `Artist.create_from_soundcharts()` for each artist
3. **Link to Track**: Set ManyToManyField and primary artist
4. **Preserve Relationships**: Maintain existing artist-track connections

### Error Handling
- **Missing Data**: Skips artists without required UUID or name
- **Duplicate Prevention**: UUID-based matching prevents duplicate artists
- **Data Integrity**: Maintains referential integrity across relationships

## Benefits

1. **Complete Artist Coverage**: All artists from SoundCharts API are preserved
2. **Flexible Querying**: Support for both individual and multiple artist queries
3. **Primary Artist Support**: Easy access to main artist for display purposes
4. **Data Consistency**: UUID-based identification ensures reliable matching
5. **Admin Friendly**: Clear organization in Django admin interface

## Migration Notes

### Database Changes
- Added `artists` ManyToManyField to Track model
- Added `primary_artist` ForeignKey to Track model
- No changes to existing Artist model structure

### Backward Compatibility
- All existing functionality preserved
- Enhanced with comprehensive artist support
- Better alignment with SoundCharts API structure

## Future Enhancements

- **Artist Metadata**: Rich artist information from SoundCharts API
- **Artist Analytics**: Track artist popularity and trends
- **Collaboration Tracking**: Identify frequent artist collaborations
- **Artist Charts**: Generate artist-specific performance metrics
