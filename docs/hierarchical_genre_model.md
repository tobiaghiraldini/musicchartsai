# Hierarchical Genre Model

## Overview

The Genre model has been redesigned to support hierarchical relationships that align with the SoundCharts API data structure. This allows for better organization and querying of genre data.

## Key Features

### Hierarchical Structure
- **Root Genres**: Top-level genres (e.g., "electronic", "rock", "alternative")
- **Subgenres**: Child genres that belong to a root genre (e.g., "house", "techno" under "electronic")
- **Self-referencing**: Uses Django's `ForeignKey` to `self` to create parent-child relationships

### SoundCharts Integration
- **API Alignment**: Directly maps to SoundCharts genre data structure:
  ```json
  {
    "root": "electronic",
    "sub": ["house", "techno", "ambient"]
  }
  ```
- **Automatic Creation**: `Genre.create_from_soundcharts()` method handles API data processing
- **Preservation**: Maintains original SoundCharts root genre names

## Model Fields

### Core Fields
- `name`: Genre name (e.g., "electronic", "house")
- `slug`: URL-friendly identifier (auto-generated)
- `uuid`: SoundCharts UUID (optional)

### Hierarchical Fields
- `parent`: ForeignKey to parent genre (null for root genres)
- `level`: Hierarchy level (0=root, 1=sub)
- `soundcharts_root`: Original root genre name from API

### Metadata Fields
- `description`: Optional genre description
- `created_at`, `updated_at`: Timestamps

## Track Integration

### Genre Relationships
- `genres`: ManyToManyField to all associated genres
- `primary_genre`: ForeignKey to the main genre (first root genre from API)

### Benefits
- **Flexible Querying**: Can query by root genres, subgenres, or both
- **Primary Genre**: Easy access to the main genre for display
- **Complete Coverage**: All genres from API are preserved

## Usage Examples

### Creating Genres from SoundCharts Data
```python
genre_data = {
    "root": "electronic",
    "sub": ["house", "techno", "ambient"]
}

root_genre, subgenres = Genre.create_from_soundcharts(genre_data)
```

### Querying Genres
```python
# Get all root genres
root_genres = Genre.get_root_genres()

# Get all subgenres of electronic
electronic = Genre.objects.get(name="electronic")
subgenres = electronic.get_all_subgenres()

# Check if genre is root or subgenre
if electronic.is_root:
    print("This is a root genre")
```

### Track Genre Management
```python
# Add genres to track
track.genres.set([electronic, house])
track.primary_genre = electronic

# Query tracks by genre
electronic_tracks = electronic.tracks.all()
```

## Admin Interface

### Track Admin Updates
- **List Display**: Shows `primary_genre` instead of old `genre` field
- **Filters**: Added `genres` filter for ManyToManyField
- **Fieldsets**: Updated to include both `primary_genre` and `genres` fields

### Genre Admin Features
- **Hierarchical Display**: Shows parent-child relationships
- **Slug Generation**: Automatic slug creation from genre names
- **SoundCharts Integration**: Preserves original API data

## Migration Notes

### Data Migration
- Old `genre` field removed from Track model
- New `genres` ManyToManyField and `primary_genre` ForeignKey added
- Existing genre data needs to be migrated (if any)

### Backward Compatibility
- All existing functionality preserved
- Enhanced with hierarchical capabilities
- Better alignment with SoundCharts API structure

## Benefits

1. **API Alignment**: Direct mapping to SoundCharts genre structure
2. **Flexible Querying**: Support for both root and subgenre queries
3. **Data Preservation**: No loss of genre information from API
4. **Scalability**: Easy to add more hierarchy levels if needed
5. **Admin Friendly**: Better organization in Django admin interface

## Future Enhancements

- **Multi-level Hierarchy**: Support for deeper genre hierarchies
- **Genre Descriptions**: Rich descriptions for each genre
- **Genre Analytics**: Track genre popularity and trends
- **API Sync**: Automatic genre updates from SoundCharts API
