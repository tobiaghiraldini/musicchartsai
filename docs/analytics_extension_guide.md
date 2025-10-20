# Analytics Extension Guide

**Quick guide for adding new metrics to the Music Analytics feature**

---

## 🎯 **Goal**

This guide helps you extend the analytics with new data sources like:
- Radio airplay
- Playlist metrics
- Shazam tags
- TikTok video usage
- Custom metrics

---

## 📊 **Current Data Flow**

```
User Search → Backend API Call → SoundCharts API → Aggregate → Display
                                     ↓
                                Database (for tracks)
```

---

## 🔧 **Step-by-Step: Adding a New Metric**

### **Example: Adding Radio Airplay**

---

### **1. Define the Data Source**

**Identify**:
- SoundCharts endpoint: `/api/v2/artist/{uuid}/radio/{country}`
- What data it returns: `{ date, spins, reach, stations }`
- Metric type: Count-based (similar to streaming)

---

### **2. Add Backend Fetch Method**

**File**: `apps/soundcharts/analytics_service.py`

```python
def _fetch_radio_data(self, artist_uuid, country, start_date, end_date):
    """
    Fetch radio airplay data from SoundCharts.
    
    Similar to _fetch_streaming_data but for radio.
    """
    all_data_points = []
    current_start = start_date
    
    while current_start < end_date:
        batch_end = min(current_start + timedelta(days=90), end_date)
        
        # API call
        response = self.soundcharts_service.get_radio_airplay(
            artist_uuid, country, 
            start_date=current_start, 
            end_date=batch_end
        )
        
        # Parse response
        items = response.get('items', [])
        for item in items:
            plot_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
            spins = item.get('spins', 0)
            
            all_data_points.append({
                'date': plot_date,
                'value': spins,
                'artist__uuid': artist_uuid,
                'country': country
            })
        
        current_start = batch_end + timedelta(days=1)
    
    return all_data_points
```

---

### **3. Add API Client Method**

**File**: `apps/soundcharts/service.py`

```python
class SoundchartsService:
    def get_radio_airplay(self, artist_uuid, country, start_date, end_date):
        """
        Get radio airplay spins for an artist in a country.
        """
        url = f'{self.base_url}/api/v2/artist/{artist_uuid}/radio/{country}'
        
        params = {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d'),
            'offset': 0,
            'limit': 100
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        return response.json()
```

---

### **4. Integrate into Main Fetch Method**

**File**: `apps/soundcharts/analytics_service.py`

```python
def fetch_and_aggregate_artist_metrics(self, artist_ids, platform_ids, start_date, end_date, country=None):
    """
    Main aggregation method.
    """
    # Existing code for streaming/social...
    
    # NEW: Add radio data
    radio_data = []
    if country:  # Radio is country-specific
        for artist in artists:
            if not artist.uuid:
                continue
            
            try:
                artist_radio = self._fetch_radio_data(
                    artist.uuid, country, start_date, end_date
                )
                
                # Add metadata
                for point in artist_radio:
                    point['artist__name'] = artist.name
                    point['metric_type'] = 'Radio Spins'
                
                radio_data.extend(artist_radio)
            except Exception as e:
                logger.error(f"Error fetching radio for {artist.name}: {e}")
    
    # Aggregate radio data
    radio_summary = self._aggregate_radio_data(radio_data)
    
    # Add to results
    results['radio_metrics'] = radio_summary
    
    return results
```

---

### **5. Add Aggregation Method**

```python
def _aggregate_radio_data(self, radio_data):
    """
    Aggregate radio airplay data.
    """
    if not radio_data:
        return None
    
    # Group by artist
    by_artist = {}
    for point in radio_data:
        artist_name = point['artist__name']
        if artist_name not in by_artist:
            by_artist[artist_name] = {
                'dates': [],
                'values': []
            }
        
        by_artist[artist_name]['dates'].append(point['date'])
        by_artist[artist_name]['values'].append(point['value'])
    
    # Calculate metrics
    artist_summaries = []
    for artist_name, data in by_artist.items():
        sorted_data = sorted(zip(data['dates'], data['values']), key=lambda x: x[0])
        values = [v for d, v in sorted_data]
        
        artist_summaries.append({
            'artist_name': artist_name,
            'total_spins': sum(values),
            'avg_daily_spins': sum(values) / len(values),
            'peak_spins': max(values),
            'data_points': len(values)
        })
    
    return {
        'total_spins_all_artists': sum(s['total_spins'] for s in artist_summaries),
        'artists': artist_summaries
    }
```

---

### **6. Update View Response**

**File**: `apps/soundcharts/views.py`

```python
@login_required
def analytics_search_results(request):
    # ... existing code ...
    
    # Call service
    results = analytics_service.fetch_and_aggregate_artist_metrics(
        artist_ids, platform_ids, start_date, end_date, country
    )
    
    # Existing response data
    response_data = {
        'success': results.get('success', True),
        'summary': results.get('summary', {}),
        'platform_summaries': results.get('platform_summaries', []),
        'detailed_breakdown': results.get('detailed_breakdown', []),
        'metadata': results.get('metadata', {}),
        
        # NEW: Add radio metrics
        'radio_metrics': results.get('radio_metrics'),
    }
    
    return JsonResponse(response_data)
```

---

### **7. Add Frontend Display**

**File**: `templates/soundcharts/analytics_search.html`

```javascript
function renderResults(data) {
    // Clear previous results
    resultsContainer.innerHTML = '';
    
    // Existing: Platform summaries, table, etc.
    // ...
    
    // NEW: Radio metrics section
    if (data.radio_metrics) {
        resultsContainer.innerHTML += renderRadioMetrics(data.radio_metrics);
    }
    
    // Show container
    resultsContainer.classList.remove('hidden');
}

function renderRadioMetrics(radioData) {
    if (!radioData || !radioData.artists || radioData.artists.length === 0) {
        return '';
    }
    
    let html = '<div class="mt-8">';
    html += '<h3 class="text-xl font-bold text-gray-900 dark:text-white mb-4">📻 Radio Airplay</h3>';
    
    // Summary card
    html += '<div class="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-6 mb-6">';
    html += '<div class="text-center">';
    html += '<p class="text-sm text-purple-600 dark:text-purple-400 mb-2">Total Radio Spins</p>';
    html += '<p class="text-4xl font-bold text-purple-700 dark:text-purple-300">';
    html += formatNumber(radioData.total_spins_all_artists);
    html += '</p></div></div>';
    
    // Per-artist breakdown
    html += '<div class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">';
    html += '<table class="min-w-full divide-y divide-gray-200 dark:divide-gray-600">';
    html += '<thead class="bg-gray-50 dark:bg-gray-700"><tr>';
    html += '<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300">Artist</th>';
    html += '<th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300">Total Spins</th>';
    html += '<th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300">Avg Daily</th>';
    html += '<th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300">Peak</th>';
    html += '</tr></thead><tbody class="divide-y divide-gray-200 dark:divide-gray-600">';
    
    radioData.artists.forEach(artist => {
        html += '<tr class="hover:bg-gray-50 dark:hover:bg-gray-700">';
        html += '<td class="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">' + artist.artist_name + '</td>';
        html += '<td class="px-6 py-4 text-sm text-right text-gray-900 dark:text-white">' + formatNumber(artist.total_spins) + '</td>';
        html += '<td class="px-6 py-4 text-sm text-right text-gray-600 dark:text-gray-400">' + formatNumber(artist.avg_daily_spins) + '</td>';
        html += '<td class="px-6 py-4 text-sm text-right text-gray-600 dark:text-gray-400">' + formatNumber(artist.peak_spins) + '</td>';
        html += '</tr>';
    });
    
    html += '</tbody></table></div></div>';
    
    return html;
}
```

---

### **8. Update Excel Export**

**File**: `apps/soundcharts/views.py`

```python
@login_required
def analytics_export_excel(request):
    # ... existing code ...
    
    # Fetch results
    results = analytics_service.fetch_and_aggregate_artist_metrics(...)
    
    # Existing: Create sheets for platform summaries, detailed breakdown
    # ...
    
    # NEW: Add radio sheet
    if results.get('radio_metrics'):
        radio_sheet = workbook.create_sheet(title='Radio Airplay')
        
        # Headers
        radio_sheet.append(['Artist', 'Total Spins', 'Avg Daily', 'Peak', 'Data Points'])
        
        # Data
        for artist in results['radio_metrics']['artists']:
            radio_sheet.append([
                artist['artist_name'],
                artist['total_spins'],
                round(artist['avg_daily_spins'], 2),
                artist['peak_spins'],
                artist['data_points']
            ])
        
        # Styling
        for cell in radio_sheet[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='D8BFD8', end_color='D8BFD8', fill_type='solid')
    
    # Save and return
    # ...
```

---

## 📋 **Checklist for New Metrics**

When adding a new metric type, ensure:

- [ ] **Backend**:
  - [ ] API client method in `service.py`
  - [ ] Fetch method in `analytics_service.py`
  - [ ] Aggregation method
  - [ ] Integration into main fetch method
  - [ ] Updated response in view

- [ ] **Frontend**:
  - [ ] Render function for new metric
  - [ ] Call render function in `renderResults()`
  - [ ] Proper styling (use color scheme)
  - [ ] Responsive design

- [ ] **Export**:
  - [ ] New sheet in Excel export
  - [ ] Proper headers and data

- [ ] **Documentation**:
  - [ ] Update `analytics_technical_architecture.md`
  - [ ] Add examples
  - [ ] Update this extension guide

- [ ] **Testing**:
  - [ ] Test with real data
  - [ ] Test error handling (no data, API errors)
  - [ ] Test Excel export

---

## 🎨 **UI Guidelines**

### **Color Scheme for New Metric Types**

Use distinct colors to differentiate metric types:

| Metric Type | Primary Color | Tailwind Classes |
|-------------|---------------|------------------|
| Streaming | Green | `bg-green-50`, `text-green-600` |
| Social | Blue | `bg-blue-50`, `text-blue-600` |
| Radio | Purple | `bg-purple-50`, `text-purple-600` |
| Playlists | Pink | `bg-pink-50`, `text-pink-600` |
| Shazam | Orange | `bg-orange-50`, `text-orange-600` |
| TikTok | Teal | `bg-teal-50`, `text-teal-600` |

### **Card Layout**

Follow existing pattern:
```html
<div class="bg-{color}-50 dark:bg-{color}-900/20 rounded-lg p-6">
    <div class="text-center">
        <p class="text-sm text-{color}-600 dark:text-{color}-400 mb-2">
            {Metric Label}
        </p>
        <p class="text-4xl font-bold text-{color}-700 dark:text-{color}-300">
            {Value}
        </p>
    </div>
</div>
```

### **Table Style**

Match existing tables:
- Gray header background
- Hover effect on rows
- Right-align numbers
- Left-align text

---

## 🔌 **API Response Format**

### **Standard Structure**

All metric additions should follow this pattern:

```json
{
  "success": true,
  "summary": { ... },
  "platform_summaries": [ ... ],
  "detailed_breakdown": [ ... ],
  "metadata": { ... },
  
  // NEW METRIC:
  "{metric_name}_metrics": {
    "total_{metric}": 123456,
    "artists": [
      {
        "artist_name": "Artist Name",
        "total_{metric}": 12345,
        "avg_daily_{metric}": 411,
        "peak_{metric}": 567,
        "data_points": 30
      }
    ]
  }
}
```

### **Error Handling**

If metric not available:
```json
{
  "radio_metrics": null  // or omit entirely
}
```

Frontend should check:
```javascript
if (data.radio_metrics && data.radio_metrics.artists) {
    renderRadioMetrics(data.radio_metrics);
}
```

---

## 🧪 **Testing New Metrics**

### **1. Backend Test**

```python
# Test in Django shell
from apps.soundcharts.analytics_service import AnalyticsService
from datetime import date

service = AnalyticsService()

results = service.fetch_and_aggregate_artist_metrics(
    artist_ids=[123],
    platform_ids=[1],
    start_date=date(2024, 9, 1),
    end_date=date(2024, 9, 30),
    country='IT'
)

# Check radio metrics
print(results.get('radio_metrics'))
```

### **2. API Test**

```bash
# Test the view endpoint
curl -X POST http://localhost:8000/soundcharts/analytics/results/ \
  -H "Content-Type: application/json" \
  -d '{
    "artist_ids": ["123"],
    "platform_ids": ["1"],
    "start_date": "2024-09-01",
    "end_date": "2024-09-30",
    "country": "IT"
  }'
```

### **3. Frontend Test**

1. Open browser console
2. Run search
3. Check response: `console.log(data.radio_metrics)`
4. Verify rendering: Check DOM for new elements

---

## 🚀 **Performance Tips**

### **Caching**

Cache expensive API calls:
```python
from django.core.cache import cache

def _fetch_radio_data(self, artist_uuid, country, start_date, end_date):
    cache_key = f'radio:{artist_uuid}:{country}:{start_date}:{end_date}'
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    # Fetch from API
    data = self._fetch_radio_data_from_api(...)
    
    # Cache for 1 hour
    cache.set(cache_key, data, timeout=3600)
    
    return data
```

### **Parallel Fetching**

For multiple artists:
```python
from concurrent.futures import ThreadPoolExecutor

def _fetch_all_artists_radio(self, artist_uuids, country, start_date, end_date):
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(self._fetch_radio_data, uuid, country, start_date, end_date)
            for uuid in artist_uuids
        ]
        
        results = [f.result() for f in futures]
    
    return results
```

---

## 📚 **Examples**

### **Example 1: Simple Count Metric (Shazam Tags)**

```python
# 1. Fetch
def _fetch_shazam_data(self, artist_uuid, start_date, end_date):
    response = self.soundcharts_service.get_shazam_tags(artist_uuid, start_date, end_date)
    return [{'date': item['date'], 'value': item['tags']} for item in response['items']]

# 2. Aggregate
def _aggregate_shazam_data(self, data):
    total = sum(point['value'] for point in data)
    return {'total_tags': total, 'avg_daily': total / len(data)}

# 3. Render
function renderShazamMetrics(data) {
    return `<div class="text-orange-600">🔍 ${formatNumber(data.total_tags)} Shazam Tags</div>`;
}
```

### **Example 2: Complex Metric (Playlist Reach)**

```python
# 1. Fetch with multiple data points
def _fetch_playlist_data(self, artist_uuid, platform, start_date, end_date):
    response = self.soundcharts_service.get_playlists(artist_uuid, platform)
    
    return [{
        'playlist_name': p['name'],
        'followers': p['followers'],
        'track_count': p['tracks_count'],
        'added_at': p['added_at']
    } for p in response['playlists']]

# 2. Aggregate with grouping
def _aggregate_playlist_data(self, data):
    return {
        'total_playlists': len(data),
        'total_followers': sum(p['followers'] for p in data),
        'playlists': sorted(data, key=lambda x: x['followers'], reverse=True)[:10]  # Top 10
    }

# 3. Render as table
function renderPlaylistMetrics(data) {
    let html = '<table>';
    data.playlists.forEach(p => {
        html += `<tr><td>${p.playlist_name}</td><td>${formatNumber(p.followers)}</td></tr>`;
    });
    html += '</table>';
    return html;
}
```

---

## 🎓 **Common Patterns**

### **Pattern 1: Date-Series Metric**
Use for: Streaming, followers, spins, views
```python
data = [{'date': '2024-09-01', 'value': 1000}, ...]
first = data[0]['value']
last = data[-1]['value']
growth = last - first
```

### **Pattern 2: Aggregated Count**
Use for: Total streams, total spins
```python
total = sum(point['value'] for point in data)
```

### **Pattern 3: Peak Detection**
Use for: Most popular day, highest position
```python
peak = max(data, key=lambda x: x['value'])
```

### **Pattern 4: Top-N List**
Use for: Top tracks, top playlists
```python
sorted_items = sorted(data, key=lambda x: x['metric'], reverse=True)
top_10 = sorted_items[:10]
```

---

## ✅ **Final Checklist**

Before deploying a new metric:

- [ ] Code follows existing patterns
- [ ] Error handling implemented
- [ ] Caching considered
- [ ] Frontend matches design system
- [ ] Excel export includes new metric
- [ ] Documentation updated
- [ ] Tested with real data
- [ ] Tested with missing data
- [ ] Tested with errors (API down)
- [ ] Performance is acceptable
- [ ] Code reviewed

---

## 🆘 **Need Help?**

**Common Issues**:

1. **API returns 404**: Check artist UUID exists in SoundCharts
2. **No data in response**: Check date range, platform availability
3. **Frontend not rendering**: Check console for JS errors, verify JSON structure
4. **Excel export fails**: Check all data is serializable (no datetime objects)

**Reference Files**:
- `analytics_technical_architecture.md` - Full technical details
- `analytics_phase1_complete_enhanced.md` - Phase 1 implementation
- `analytics_phase2_complete.md` - Phase 2 implementation

---

**Quick Start**: Copy the radio airplay example above and adapt for your metric!

