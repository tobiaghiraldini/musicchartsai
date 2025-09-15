# Track Admin Alerts Implementation

## Overview
This document outlines the implementation of alert patterns for track admin actions, matching the same alert system used in chart admin for import actions.

## Requirements
- Add success/error alerts for track change view admin actions (import metadata, import audience)
- Add success/error alerts for track change list bulk actions (import all metadata)
- Use the same alert pattern as chart admin's "import song rankings from soundcharts" button

## Implementation Details

### 1. JavaScript Alert System
**File**: `static/assets/track-admin-alerts.js`

Created a dedicated JavaScript file that provides:
- `showTrackAlert(message, type)` - Displays alerts using Django admin patterns
- `hideTrackAlert()` - Removes existing alerts
- `fetchTrackMetadata(trackId)` - AJAX call for single track metadata fetch
- `fetchTrackAudience(trackId)` - AJAX call for single track audience fetch
- `fetchBulkMetadata()` - AJAX call for bulk metadata fetch

The alert system uses the same CSS classes and structure as the chart admin:
- `alert-success` for success messages
- `alert-danger` for error messages
- `alert-warning` for warning messages
- `alert-info` for info messages

### 2. Template Updates

#### Track Change Form Template
**File**: `apps/soundcharts/templates/admin/soundcharts/track/change_form.html`

Added:
- Link to `admin-import.css` for consistent styling
- Script tag to load `track-admin-alerts.js`
- Form submission is now handled via AJAX instead of traditional form submission

#### Track Change List Template
**File**: `apps/soundcharts/templates/admin/soundcharts/track/change_list.html`

Added:
- Link to `admin-import.css` for consistent styling
- Script tag to load `track-admin-alerts.js`
- Updated `createBulkMetadataTask()` function to use `showTrackAlert()` instead of `alert()`

### 3. Backend API Endpoints

#### Track Admin Views
**File**: `apps/soundcharts/admin_views/track_admin.py`

Added three new API endpoints:

1. **`/<int:object_id>/fetch-metadata/`** (POST)
   - Fetches metadata for a single track
   - Returns JSON response with success/error status
   - Updates track with fetched metadata synchronously

2. **`/<int:object_id>/fetch-audience/`** (POST)
   - Fetches audience data for a single track
   - Accepts platform and force_refresh parameters
   - Returns JSON response with success/error status

3. **`/bulk-fetch-metadata/`** (POST)
   - Starts bulk metadata fetch for selected tracks
   - Creates a MetadataFetchTask record
   - Returns JSON response with task information

### 4. URL Configuration
The custom URLs are added via the `get_urls()` method in `TrackAdmin` class:
- `soundcharts_track_fetch_metadata`
- `soundcharts_track_fetch_audience`
- `soundcharts_track_bulk_fetch_metadata`

### 5. Alert Behavior
- Alerts appear at the top of the content area
- Success alerts auto-hide after 5 seconds
- Error alerts remain visible until manually dismissed
- Alerts are removed before showing new ones
- Page reloads after successful operations to show updated data

## Usage

### Single Track Actions (Change View)
1. Navigate to a track's change view
2. Click "Fetch Metadata from API" or "Fetch Audience Data from API"
3. Alert will appear showing the result
4. Page will reload to show updated data

### Bulk Actions (Change List)
1. Navigate to the track change list
2. Select tracks using checkboxes
3. Click "Fetch All Metadata" button
4. Alert will appear showing the result
5. Page will reload to show updated data

## Technical Notes

### AJAX Implementation
- All import actions now use AJAX instead of form submission
- CSRF tokens are included in all requests
- Error handling is consistent across all endpoints
- Loading states are managed by the JavaScript

### Error Handling
- Network errors are caught and displayed as alerts
- API errors are returned as JSON and displayed as alerts
- Validation errors (e.g., missing UUID) are handled gracefully

### Backward Compatibility
- The old `response_change` method is kept but simplified
- Existing functionality continues to work
- New AJAX functionality is additive

## Testing
To test the implementation:
1. Go to a track's change view and test metadata/audience fetch buttons
2. Go to the track change list and test bulk metadata fetch
3. Verify alerts appear correctly for both success and error cases
4. Confirm page reloads show updated data after successful operations

## Troubleshooting
If the buttons are not working:
1. Check browser console for JavaScript errors
2. Verify the track-admin-alerts.js script is loading (look for "Track admin alerts script loaded" in console)
3. Check if buttons are found (look for "Metadata button found:" and "Audience button found:" in console)
4. Verify CSRF token is available (look for "CSRF token found: Yes" in console)
5. Check network tab for API requests and responses

## Recent Fixes
- Fixed JavaScript event handling to prevent form submission
- Added proper button element passing to fetch functions
- Enhanced CSRF token detection from multiple sources
- Added comprehensive console logging for debugging
- Fixed bulk metadata API to handle track IDs instead of UUIDs

## Files Modified
- `static/assets/track-admin-alerts.js` (new)
- `apps/soundcharts/templates/admin/soundcharts/track/change_form.html`
- `apps/soundcharts/templates/admin/soundcharts/track/change_list.html`
- `apps/soundcharts/admin_views/track_admin.py`
- `docs/track_admin_alerts_implementation.md` (this file)
