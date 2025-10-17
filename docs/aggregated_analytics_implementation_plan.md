# Music Analytics Aggregation System - Implementation Plan

## 📋 Overview

Build an aggregation system to answer questions like: **"What were the total metrics for artist X across all platforms in month Y?"**

### Core Requirements
- **Primary Use Case**: Aggregate all tracks for selected artist(s) over a time period
- **Typical Timeframe**: Monthly aggregations
- **Metric**: Audience data (views/listens/plays) already collected per platform
- **Geographic Filter**: Derived from country-specific charts we sync
- **Historical Data**: Trigger sync tasks if requested data doesn't exist yet

---

## 🎯 Success Criteria

User can:
1. Open "Music Analytics" page from sidebar
2. Select artist(s), date range (month), platforms, country
3. Click "Search" and see:
   - If data exists: immediate results with aggregated metrics
   - If data missing: "Syncing data..." message, then results when ready
4. View results in table format with totals per platform
5. See breakdown by track within the artist
6. Export results to Excel

---

## 🏗️ Architecture Overview

### Data Flow

```
User Form → Aggregation Service → Check Data Availability
                                           ↓
                    ┌──────────────────────┴────────────────────┐
                    ↓                                            ↓
              Data Exists                                  Data Missing
                    ↓                                            ↓
          Calculate Aggregations                      Trigger Sync Tasks
                    ↓                                            ↓
          Display Results                            Show "Syncing" Page
                                                                 ↓
                                                          Poll for Completion
                                                                 ↓
                                                          Display Results
```

### Technology Stack
- **Backend**: Django ORM aggregations (no new models needed)
- **Frontend**: Django templates + HTMX for dynamic updates
- **Async Tasks**: Celery for background data syncing
- **Export**: openpyxl for Excel generation

---

## 📊 Data Model Analysis

### Existing Models We'll Use

**1. TrackAudienceTimeSeries**
```python
# Stores: track, platform, date, audience_value
# This is our PRIMARY data source
```

**2. ArtistAudienceTimeSeries**
```python
# Stores: artist, platform, date, audience_value
# Secondary source for artist-level metrics
```

**3. Track (with M2M to Artist)**
```python
# To get all tracks for an artist
Track.objects.filter(artists=artist)
```

**4. Chart (with country_code)**
```python
# To determine which countries we have data for
Chart.objects.values('country_code').distinct()
```

**5. Platform**
```python
# Platform selection and metric names
```

### Aggregation Strategy

**Query Pattern:**
```python
# Get all tracks for artist
tracks = Track.objects.filter(artists__in=selected_artists)

# Aggregate audience data across date range
TrackAudienceTimeSeries.objects.filter(
    track__in=tracks,
    platform__in=selected_platforms,
    date__range=(start_date, end_date)
).values('platform__name', 'track__name').annotate(
    total_audience=Sum('audience_value'),
    avg_daily=Avg('audience_value'),
    peak_value=Max('audience_value'),
    days_tracked=Count('date')
)
```

**Country Filtering:**
```python
# Infer country from charts that include these tracks
# OR: Filter by platforms active in specific country charts
relevant_charts = Chart.objects.filter(country_code=selected_country)
# Then check which tracks appear in those charts' rankings
```

---

## 🛠️ Implementation Breakdown

### Phase 1: Aggregation Service Layer

**File**: `apps/soundcharts/aggregation_service.py`

```python
class MusicAnalyticsAggregationService:
    """
    Service for aggregating music metrics across artists, tracks, platforms, and time periods
    """
    
    def check_data_availability(self, artist_ids, platform_ids, start_date, end_date, country=None):
        """
        Check if we have complete data for the requested parameters
        Returns: {
            'has_data': bool,
            'missing_dates': list,
            'missing_platforms': list,
            'coverage_percentage': float
        }
        """
        
    def aggregate_artist_metrics(self, artist_ids, platform_ids, start_date, end_date, country=None):
        """
        Aggregate all tracks for given artists
        Returns: {
            'summary': {platform: total_value},
            'by_track': [{track, platform, metrics}],
            'date_range': {start, end},
            'artists': [{name, id}]
        }
        """
        
    def trigger_missing_data_sync(self, artist_ids, platform_ids, start_date, end_date, country=None):
        """
        Trigger Celery tasks to fetch missing data
        Returns: {
            'sync_task_id': str,
            'estimated_time': int,
            'charts_to_sync': list
        }
        """
```

---

### Phase 2: Backend Views & API

**File**: `apps/soundcharts/views.py`

Add views:
1. `analytics_search_form` - Display search form
2. `analytics_search_results` - Process form, show results or trigger sync
3. `analytics_check_sync_status` - AJAX endpoint to poll sync progress
4. `analytics_export_excel` - Export results to Excel

**File**: `apps/soundcharts/urls.py`

```python
urlpatterns = [
    # ... existing patterns ...
    path('analytics/', views.analytics_search_form, name='analytics_search'),
    path('analytics/results/', views.analytics_search_results, name='analytics_results'),
    path('analytics/sync-status/<task_id>/', views.analytics_check_sync_status, name='analytics_sync_status'),
    path('analytics/export/<result_id>/', views.analytics_export_excel, name='analytics_export'),
]
```

---

### Phase 3: Celery Tasks for Data Syncing

**File**: `apps/soundcharts/tasks.py`

```python
@shared_task
def sync_missing_analytics_data(artist_ids, platform_ids, start_date, end_date, country=None):
    """
    Background task to sync missing audience data
    1. Identify relevant charts
    2. For each date in range, fetch chart rankings
    3. Extract track audience data
    4. Store in TrackAudienceTimeSeries
    5. Update progress for polling
    """
```

---

### Phase 4: Frontend - Search Form

**File**: `templates/soundcharts/analytics_search.html`

**Form Fields:**
1. **Artist Selection** (Required)
   - Autocomplete multi-select
   - Search existing artists in DB
   - Display: name, image thumbnail

2. **Date Range** (Required)
   - Month/Year picker (default to last month)
   - OR: Start date + End date pickers
   - Validation: max 12 months range

3. **Platforms** (Optional, default: ALL)
   - Multi-select checkboxes
   - Show platform logos
   - Options from `Platform.objects.all()`

4. **Country** (Optional, default: ALL)
   - Dropdown select
   - Options from `Chart.objects.values('country_code').distinct()`
   - Show only countries with active chart syncs

5. **Aggregation Options**
   - Group by: Track | Platform | Date
   - Show daily breakdown: Yes/No

**Submit Button**: "Analyze Metrics"

---

### Phase 5: Frontend - Results Page

**File**: `templates/soundcharts/analytics_results.html`

**Layout:**

**A. Summary Cards (Top)**
```
┌─────────────────┬─────────────────┬─────────────────┐
│  Total Plays    │  Total Tracks   │  Avg Daily      │
│  15.8M          │  12 tracks      │  526K           │
└─────────────────┴─────────────────┴─────────────────┘
```

**B. Platform Breakdown**
```
Platform        Total Audience    % of Total    Peak Value
Spotify         12.5M             79%           450K
YouTube         3.2M              20%           120K
Shazam          89K               1%            5K
─────────────────────────────────────────────────────────
TOTAL           15.8M             100%          -
```

**C. Track Breakdown (Expandable)**
```
▼ Track: "AMOR" - Achille Lauro
  Platform    Total      Avg Daily   Peak    Days Tracked
  Spotify     8.5M       283K        320K    30
  YouTube     2.1M       70K         85K     30
  
▼ Track: "Rolls Royce" - Achille Lauro
  Platform    Total      Avg Daily   Peak    Days Tracked
  Spotify     4.0M       133K        150K    30
  YouTube     1.1M       37K         42K     30
```

**D. Export Button**
- "Download Excel Report" button
- Includes all data + metadata (filters used, date generated)

---

### Phase 6: Frontend - Syncing Status Page

**File**: `templates/soundcharts/analytics_syncing.html`

**Display:**
- Progress bar with % completion
- "Fetching data for September 2024..."
- Estimated time remaining
- **Auto-refresh** every 5 seconds using HTMX polling
- Once complete, redirect to results page

---

### Phase 7: Sidebar Menu Integration

**File**: `templates/includes/sidebar.html`

Add new menu item:
```html
<li class="nav-item">
    <a href="{% url 'analytics_search' %}" class="nav-link">
        <i class="fas fa-chart-line"></i>
        <span>Music Analytics</span>
    </a>
</li>
```

Under the "SoundCharts" section or create new "Analytics" section.

---

## 🔄 Implementation Sequence

### Step 1: Backend Foundation (Day 1-2)
- [ ] Create `aggregation_service.py`
- [ ] Implement `check_data_availability()`
- [ ] Implement `aggregate_artist_metrics()` with test data
- [ ] Write unit tests for aggregation logic

### Step 2: Basic Views (Day 2-3)
- [ ] Create `analytics_search_form` view
- [ ] Create basic form template (no styling yet)
- [ ] Create `analytics_search_results` view
- [ ] Test with existing data (no sync logic yet)

### Step 3: Results Display (Day 3-4)
- [ ] Create results template with summary cards
- [ ] Add platform breakdown table
- [ ] Add track breakdown (expandable/collapsible)
- [ ] Style with Tailwind CSS to match existing dashboard

### Step 4: Sidebar Integration (Day 4)
- [ ] Add "Music Analytics" menu item
- [ ] Test navigation flow

### Step 5: Data Sync Logic (Day 5-6)
- [ ] Implement `trigger_missing_data_sync()`
- [ ] Create Celery task for background syncing
- [ ] Create syncing status page
- [ ] Add HTMX polling for progress updates

### Step 6: Excel Export (Day 6-7)
- [ ] Implement Excel export functionality
- [ ] Format workbook with multiple sheets (summary, details)
- [ ] Add download button to results page

### Step 7: Refinements (Day 7-8)
- [ ] Add form validation
- [ ] Add loading states
- [ ] Add error handling (no data, sync failed, etc.)
- [ ] Add tooltips and help text
- [ ] Performance optimization (caching, pagination)

### Step 8: Testing & Documentation (Day 8-9)
- [ ] End-to-end testing with real data
- [ ] Write user documentation
- [ ] Update `docs/aggregated_analytics_implementation.md`
- [ ] Create demo video/screenshots

---

## 🔧 Pre-Implementation Refinements (Updated)

### 1. Platform Model Enhancement

**Issue**: SoundCharts has different endpoints for different platform types:
- Audience platforms (e.g., `/api/v2/artist/{uuid}/audience/{platform}`)
- Chart platforms (e.g., `/api/v2/chart/song/by-platform/{platform}`)
- Streaming platforms (different metrics)

**Solution**: Add `platform_source` or enhance existing `platform_type` field:

```python
class Platform(models.Model):
    # ... existing fields ...
    
    platform_type = models.CharField(max_length=50, choices=[
        ('audience', 'Audience'),          # For audience endpoints
        ('streaming', 'Streaming'),        # For streaming data
        ('song_chart', 'Song Chart'),      # For chart rankings
        ('artist_chart', 'Artist Chart'),
        ('album_chart', 'Album Chart'),
        ('playlist', 'Playlist'),
        ('radio', 'Radio'),
        ('other', 'Other'),
    ], default='streaming')
    
    # This already exists and helps identify the platform
    platform_identifier = models.CharField(max_length=255, blank=True)
```

**Note**: The existing `platform_type` field should work. We'll ensure it's populated correctly when fetching platforms from different endpoints.

---

### 2. Artist Data Quality & SoundCharts UUID

**Issue**: Artists come from two sources:
- **ACR Analysis**: Created during track analysis, may lack SoundCharts UUID
- **SoundCharts API**: Have complete UUID and metadata

**Problem**: Aggregation requires SoundCharts UUID to fetch artist audience data.

**Solution**: 
1. Add validation in aggregation search form - only show artists with `uuid` populated
2. In aggregation service, filter artists:
   ```python
   valid_artists = Artist.objects.filter(
       id__in=artist_ids,
       uuid__isnull=False  # Ensure SoundCharts UUID exists
   ).exclude(uuid='')
   ```
3. Add a field to distinguish source:
   ```python
   # Optional enhancement to Artist model
   source = models.CharField(max_length=20, choices=[
       ('soundcharts', 'SoundCharts API'),
       ('acrcloud', 'ACRCloud Analysis'),
       ('manual', 'Manual Entry'),
   ], default='soundcharts')
   ```
4. Display warning in UI if selected artist lacks UUID

**Comment in Code**:
```python
# NOTE: Artists from ACRCloud analysis may not have SoundCharts UUIDs
# These artists cannot be used for audience aggregation until their
# SoundCharts UUID is populated via manual search or API matching
```

---

### 3. Country Filter Limitation

**Critical Constraint**: 
- `TrackAudienceTimeSeries` does NOT have a `country` field
- SoundCharts audience endpoints are generally global/platform-wide, not country-specific
- Chart data has country associations, but audience data does not

**Updated Approach**:
- **Country filter in form**: Informational/contextual only
- **Actual filtering**: Filter by charts from that country (indirect)
- **Display**: Show note that results are global audience metrics, filtered by tracks appearing in country-specific charts

**UI Note**:
```html
<div class="text-sm text-gray-600 dark:text-gray-400 mt-2">
  ℹ️ Country filter shows tracks that appeared in [Country] charts. 
  Audience metrics are platform-wide, not country-specific.
</div>
```

**Code Comment**:
```python
# TODO: Country filtering limitation
# Currently, audience data (TrackAudienceTimeSeries) does not have country-level granularity.
# We filter by tracks that appeared in country-specific charts, but the audience metrics
# themselves are global per platform. SoundCharts API may provide country-specific audience
# data in the future, which would require:
# 1. Adding 'country' field to TrackAudienceTimeSeries model
# 2. Fetching country-specific audience data from different endpoints
# 3. Updating aggregation queries to filter by country directly
```

---

### 4. UI Pattern Reuse (Mandatory)

**Must reuse existing patterns from**:
- `artist_list.html`: Table structure, action buttons, status badges
- `artist_search.html`: Search form, autocomplete, AJAX patterns
- `artist_detail.html`: Card layouts, platform breakdown
- `song_audience_detail.html`: Chart display, metrics formatting

**Specific components to reuse**:
1. **Autocomplete**: Existing artist search AJAX endpoint
2. **Date pickers**: HTML5 date inputs with Tailwind styling
3. **Multi-select**: Checkbox groups with "Select All" toggle
4. **Loading states**: Spinner SVG with pulse animation
5. **Notification toasts**: `showNotification()` function pattern
6. **Table styling**: Same classes, hover states, dark mode support

**Form Controls to Use**:
- **Artist selection**: Autocomplete multi-select (reuse search endpoint)
- **Platform selection**: Checkbox group with platform logos
- **Date range**: Month picker (HTML5 `<input type="month">`) or date range
- **Country selection**: Dropdown `<select>` (informational)

---

### 5. Permissions & Access Control

**MVP**: All authenticated users can access analytics

**Code Comment**:
```python
@login_required  # MVP: Basic authentication only
def analytics_search_form(request):
    """
    Music Analytics search form view.
    
    TODO: Add role-based permissions in the future:
    - @permission_required('soundcharts.view_analytics')
    - Different user roles: admin, analyst, viewer
    - Limit date range access based on subscription tier
    - Rate limiting for expensive aggregation queries
    """
    pass
```

---

## 🚨 Technical Considerations

### 1. Performance Optimization

**Challenge**: Aggregating millions of records could be slow

**Solutions**:
- Use Django ORM `.aggregate()` (runs in DB, not Python)
- Add database indexes on:
  - `TrackAudienceTimeSeries.date`
  - `TrackAudienceTimeSeries.platform_id`
  - `Track.artists` (M2M through table)
- Implement Redis caching for repeated queries
- Paginate results if >1000 records

### 2. Data Availability Detection

**Challenge**: Efficiently checking if data exists for date range

**Solution**:
```python
# Instead of checking every single date:
existing_dates = TrackAudienceTimeSeries.objects.filter(
    track__in=tracks,
    date__range=(start, end)
).values('date').distinct().values_list('date', flat=True)

expected_dates = [start + timedelta(days=x) for x in range((end-start).days + 1)]
missing_dates = set(expected_dates) - set(existing_dates)
```

### 3. Country Filtering

**Challenge**: `TrackAudienceTimeSeries` doesn't have a `country` field

**Approaches**:
- **Option A**: Add `country` field to model (requires migration + backfill)
- **Option B**: Infer country from chart relationships (complex queries)
- **Option C**: Make country filter optional/informational only

**Recommendation**: Start with Option C for MVP, add Option A if needed.

### 4. Sync Task Management

**Challenge**: Multiple users might trigger overlapping syncs

**Solution**:
- Check for existing sync tasks before creating new ones
- Use task deduplication with Celery task IDs
- Store sync status in cache or dedicated model

---

## 📝 Database Changes

### NO NEW MODELS REQUIRED ✅

We can build this entirely on existing models!

### Optional Enhancement (Future):

```python
class AnalyticsQuery(models.Model):
    """Store user queries for caching and history"""
    user = models.ForeignKey(User)
    query_params = models.JSONField()  # Filters used
    created_at = models.DateTimeField(auto_now_add=True)
    result_cache = models.JSONField(null=True)  # Cached results
    
class SyncTask(models.Model):
    """Track sync tasks to avoid duplicates"""
    task_id = models.CharField(unique=True)
    query_params = models.JSONField()
    status = models.CharField(choices=[...])
    progress = models.IntegerField(default=0)
    completed_at = models.DateTimeField(null=True)
```

But these are **NOT required for MVP**.

---

## 🧪 Testing Strategy

### Unit Tests
- Aggregation service methods
- Date range validation
- Data availability checks

### Integration Tests
- Full query flow with sample data
- Sync task triggering
- Excel export generation

### Manual Testing Checklist
- [ ] Search with existing data → immediate results
- [ ] Search with missing data → triggers sync
- [ ] Sync completion → shows results
- [ ] Export Excel → downloads correctly
- [ ] Multiple artists selected
- [ ] All platforms vs. specific platforms
- [ ] Date range validation (max 12 months)
- [ ] Empty results handling

---

## 📚 Documentation Updates

Update these files:
1. `docs/aggregated_analytics_implementation.md` (this file)
2. `docs/soundcharts_dashboard.md` (add analytics section)
3. `docs/audience_data_system.md` (reference analytics)
4. User guide with screenshots

---

## 🎯 MVP vs. Future Enhancements

### MVP (Required for Launch)
- ✅ Search form with artist, date, platform, country filters
- ✅ Results page with aggregated data
- ✅ Summary statistics (total, by platform)
- ✅ Track-level breakdown
- ✅ Basic Excel export
- ✅ Sync trigger for missing data
- ✅ Syncing status page

### Future Enhancements
- 📊 Interactive charts (line graphs, bar charts)
- 📈 Trend analysis (growth %, comparisons)
- 💾 Saved queries (bookmarks)
- 🔔 Scheduled reports (email digest)
- 🌍 Advanced geo filtering (city-level)
- 📱 Mobile-optimized view
- 🤖 AI insights (anomaly detection, predictions)

---

## ⏱️ Estimated Timeline

**Total: 8-9 working days** (assuming ~6 hours focused work per day)

- **Days 1-2**: Backend aggregation service
- **Days 2-4**: Basic views and results display
- **Days 4-5**: UI integration (sidebar, styling)
- **Days 5-6**: Sync logic and status polling
- **Days 6-7**: Excel export
- **Days 7-8**: Refinements and error handling
- **Days 8-9**: Testing and documentation

**Can be compressed** if working full-time or parallelizing tasks.

---

## 🚀 Ready to Implement?

This plan provides:
- ✅ Clear architecture using existing models
- ✅ Step-by-step implementation sequence
- ✅ Technical solutions for challenges
- ✅ MVP scope definition

**Next Step**: Get your approval on this plan, then I'll start implementing as the Executor.

