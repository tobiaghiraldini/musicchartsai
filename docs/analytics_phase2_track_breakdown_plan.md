# Music Analytics Phase 2 - Track Breakdown Plan

**Date**: October 17, 2025  
**Status**: 🚧 Planning & Implementation

---

## 🎯 **Goal**

Add track-level streaming counts to the analytics dashboard to answer:
> "Which songs contributed to Achille Lauro's 8.5M monthly listeners in Italy in September?"

---

## 📊 **What Phase 2 Will Add**

### **Track Breakdown Section**

**Expandable section under each Artist × Platform row** showing:

```
▼ Achille Lauro - Spotify (8.5M monthly listeners)
  
  Track Streaming Breakdown:
  ┌─────────────────┬───────────────┬──────────────┬─────────┐
  │ Track           │ Total Streams │ Avg Daily    │ Peak    │
  ├─────────────────┼───────────────┼──────────────┼─────────┤
  │ AMOR            │ 12.5M         │ 416K         │ 520K    │
  │ Rolls Royce     │ 8.3M          │ 276K         │ 350K    │
  │ Marilù          │ 3.2M          │ 106K         │ 150K    │
  │ (10 more...)    │               │              │         │
  └─────────────────┴───────────────┴──────────────┴─────────┘
  
  Total Streams Across All Tracks: 45.2M
```

---

## 🔍 **Data Sources**

### **Option 1: Chart Data** (Already Available)

**What we have**:
- `ChartRankingEntry` - tracks that appeared in charts
- Includes position, metric data from API
- Limited to tracks that charted

**Pros**:
- ✅ Already in database
- ✅ No additional API calls
- ✅ Has stream counts in `api_data`

**Cons**:
- ❌ Only tracks that made charts
- ❌ May not include all artist's tracks
- ❌ Metric data might be incomplete

---

### **Option 2: Track Audience API** (Existing Endpoint)

**Endpoint**: `/api/v2/song/{uuid}/audience/{platform}`

**What it provides**:
- Track audience data per platform
- Time-series data similar to artist endpoint
- Already used in `TrackAudienceTimeSeries`

**Pros**:
- ✅ Direct track data
- ✅ Already implemented in service
- ✅ Per-platform breakdown

**Cons**:
- ⚠️ May not provide stream counts (need to verify)
- ⚠️ Requires track UUID for each track
- ⚠️ Many API calls (1 per track per platform)

---

### **Option 3: Artist's Tracks from Charts** (Hybrid)

**Process**:
1. Get all artist's tracks: `Track.objects.filter(artists=artist)`
2. Find which tracks appeared in charts during the period
3. Extract stream counts from chart ranking data
4. Aggregate by track

**Pros**:
- ✅ Uses existing data
- ✅ Leverages chart sync system
- ✅ Has stream counts in chart metrics

**Cons**:
- ⚠️ Limited to charted tracks
- ⚠️ May miss non-charting songs

---

## 💡 **Recommended Approach**

**Use existing chart data + track audience data (hybrid)**:

1. **Primary Source**: `ChartRankingEntry` for tracks in selected period
   - Filter by artist
   - Filter by date range
   - Extract stream counts from `api_data`

2. **Fallback**: `TrackAudienceTimeSeries` for additional metrics
   - Supplement with audience time-series data
   - Fill gaps if available

3. **Aggregation**: Sum across all tracks per artist per platform

---

## 🏗️ **Implementation Plan**

### **Step 1: Backend Service** (Day 1)

**File**: `apps/soundcharts/analytics_service.py`

**New method**:
```python
def get_track_breakdown_for_artist(self, artist_id, platform_id, start_date, end_date, country=None):
    """
    Get track-level streaming breakdown for an artist on a platform.
    
    Returns:
        - tracks: List of tracks with streaming counts
        - total_streams: Sum of all track streams
        - top_track: Track with most streams
    """
```

**Data aggregation**:
```python
# Get all tracks for artist
tracks = Track.objects.filter(artists=artist)

# Get chart entries for these tracks in date range
chart_entries = ChartRankingEntry.objects.filter(
    track__in=tracks,
    ranking__ranking_date__range=(start_date, end_date),
    ranking__chart__platform=platform
)

# Extract metrics from api_data
# Aggregate by track
```

---

### **Step 2: API Endpoint** (Day 1)

**Add to `views.py`**:
```python
@login_required
def analytics_track_breakdown(request):
    """
    Get track breakdown for specific artist × platform combination
    Returns JSON with track-level data
    """
```

**URL**: `/soundcharts/analytics/tracks/<artist_id>/<platform_id>/`

---

### **Step 3: Frontend - Expandable Rows** (Day 2)

**Update `analytics_search.html`** table rows:

**Add expand button** to each Artist × Platform row:
```html
<tr>
    <td>
        <button onclick="toggleTrackBreakdown(artistId, platformId)">
            ▶ Achille Lauro
        </button>
    </td>
    ...
</tr>
<tr id="tracks-{artistId}-{platformId}" class="hidden">
    <td colspan="7">
        <!-- Track breakdown table loads here via AJAX -->
    </td>
</tr>
```

**AJAX loading**:
- Click expand → fetch track data
- Show loading spinner
- Render track table
- Click collapse → hide

---

### **Step 4: Track Table Design** (Day 2)

**Nested table** inside expanded row:

```html
<div class="p-4 bg-gray-50 dark:bg-gray-800">
    <h4>🎵 Tracks for Achille Lauro on Spotify</h4>
    
    <table>
        <thead>
            <tr>
                <th>Track Name</th>
                <th>Total Streams</th>
                <th>Avg Daily</th>
                <th>Peak Position</th>
                <th>Days on Chart</th>
            </tr>
        </thead>
        <tbody>
            <!-- Track rows -->
        </tbody>
    </table>
    
    <div class="summary">
        Total Streams Across All Tracks: 45.2M
    </div>
</div>
```

---

### **Step 5: Excel Export Enhancement** (Day 3)

**Add new sheet** to Excel workbook:
- Sheet 1: Artist Summary (existing)
- **Sheet 2: Track Breakdown** (new)

**Structure**:
```
Artist          Platform    Track Name      Total Streams   Avg Daily   Peak
Achille Lauro   Spotify     AMOR            12.5M           416K        520K
Achille Lauro   Spotify     Rolls Royce     8.3M            276K        350K
```

---

## 🔧 **Technical Considerations**

### **1. Data Availability**

**Challenge**: Not all tracks may have chart data or audience data

**Solution**: 
- Show message if no track data available
- Display what we have, note incomplete data
- Provide "Fetch Track Data" button for missing tracks

---

### **2. Performance**

**Challenge**: Many tracks × many platforms = many queries

**Solution**:
- Lazy loading (only fetch when expanded)
- Cache results in frontend
- Limit to top 20 tracks initially
- "Load More" button if >20 tracks

---

### **3. Metric Clarification**

**Different metrics per source**:
- **Chart data**: Stream counts (if available in `api_data`)
- **Audience data**: Monthly listeners (cumulative)
- **Need to clarify**: Which is which in the UI

---

## 📋 **Phase 2 Deliverables**

**Must Have**:
- ✅ Expandable track breakdown per Artist × Platform row
- ✅ Track name, total streams, average daily
- ✅ Sum of all track streams
- ✅ Loading state while fetching

**Nice to Have**:
- Chart position history
- Track growth over period
- Top tracks highlighted
- Track comparison charts

**Future Enhancements**:
- Track filtering (top N, search)
- Sort by different columns
- Track detail page link
- Export track data separately

---

## 🎯 **Success Criteria**

User can:
1. See artist-level monthly listeners (Phase 1) ✅
2. Click to expand and see track breakdown (Phase 2)
3. View total streams per track
4. See which tracks are top performers
5. Understand the difference between:
   - Monthly listeners (unique people)
   - Total streams (play counts)

---

## ⏱️ **Estimated Timeline**

- **Day 1**: Backend service + API endpoint (4-6 hours)
- **Day 2**: Frontend expandable rows + AJAX (4-6 hours)
- **Day 3**: Excel export + refinements (3-4 hours)
- **Total**: 2-3 working days

---

## 🚀 **Implementation Sequence**

1. Create track breakdown service method
2. Add API endpoint for track data
3. Update analytics table with expand buttons
4. Implement AJAX loading
5. Render track breakdown table
6. Add to Excel export
7. Test and refine

**Ready to start implementation!**

