# API and Frontend Integration

## Overview

This document provides a comprehensive guide to the API and frontend integration features implemented in MusicChartsAI, including chart visualization, data management, and user interface enhancements.

## Chart Visualization System

### ApexCharts Integration

MusicChartsAI leverages ApexCharts for interactive data visualization, providing both static and dynamic chart capabilities.

#### Benefits of ApexCharts Integration

- **Dynamic Data Visualization**: Leverage models from other applications to create charts that dynamically adapt to your data
- **Customized Chart Appearance**: Customize appearance and behavior using templates and configuration
- **API Data Integration**: Create charts using API data in specific pages or sections
- **Modular Design**: Charts are organized into a dedicated Django application for code organization

#### Implementation Architecture

**File Structure**:
```
static/assets/
├── charts.js              # Chart configuration and rendering
├── admin-import.js        # Admin interface functionality
└── track-admin-alerts.js  # Track admin alerts system

templates/
├── apps/charts.html       # Chart visualization templates
├── soundcharts/
│   ├── dashboard.html     # Soundcharts dashboard
│   └── song_audience_detail.html  # Song detail page
└── admin/
    └── soundcharts/       # Admin interface templates
```

### Chart Types and Implementation

#### 1. Dashboard Charts (Static Data)

**Main Chart Options**:
```javascript
// static/assets/charts.js
const getMainChartOptions = () => {
    return {
        chart: {
            type: 'area',
            height: '420px',
            fontFamily: 'Inter, sans-serif',
            foreColor: '#4B5563',
            toolbar: {
                show: false
            }
        },
        series: [
            {
                name: 'Revenue',
                data: [6356, 6218, 6156, 6526, 6356, 6256, 6056],
                color: '#1A56DB'
            },
            {
                name: 'Revenue (previous period)',
                data: [6556, 6725, 6424, 6356, 6586, 6756, 6616],
                color: '#FDBA8C'
            }
        ],
        xaxis: {
            categories: ['01 Feb', '02 Feb', '03 Feb', '04 Feb', '05 Feb', '06 Feb', '07 Feb'],
        },
    };
}
```

**Signups Chart**:
```javascript
const getSignupsChartOptions = () => {
    return {
        series: [{
            name: 'Users',
            data: [1334, 2435, 1753, 1328, 1155, 1632, 1336]
        }],
        labels: ['01 Feb', '02 Feb', '03 Feb', '04 Feb', '05 Feb', '06 Feb', '07 Feb'],
        chart: {
            type: 'bar',
            height: '140px',
            foreColor: '#4B5563',
            fontFamily: 'Inter, sans-serif',
            toolbar: {
                show: false
            }
        },
    };
}
```

#### 2. API-Based Charts (Dynamic Data)

**Bar Chart with API Data**:
```javascript
// static/assets/charts.js
if (document.getElementById('products-bar-chart-api')) {
    const apiUrl = '/api/product/';
    let dt = []

    const fetchData = async () => {
        try {
            const response = await fetch(apiUrl);
            const data = await response.json();
            dt = data
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    };
    await fetchData();
    
    const options = {
        colors: ['#1A56DB', '#FDBA8C'],
        series: [
            {
                name: 'Product',
                color: '#1A56DB',
                data: dt.map(product => ({ x: product.name, y: product.price }))
            },
        ],
        chart: {
            type: 'bar',
            height: '420px',
            fontFamily: 'Inter, sans-serif',
            foreColor: '#4B5563',
            toolbar: {
                show: false
            }
        },
    };

    const chart = new ApexCharts(document.getElementById('products-bar-chart-api'), options); 
    chart.render();
}
```

**Pie Chart with API Data**:
```javascript
if (document.getElementById('products-pie-chart-api')) {
    const apiUrl = '/api/product/';
    let dt = []

    const fetchData = async () => {
        try {
            const response = await fetch(apiUrl);
            const data = await response.json();
            dt = data
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    };
    await fetchData();

    const chart = new ApexCharts(document.getElementById('products-pie-chart-api'), pieChartOptions(dt));
    chart.render();

    // Dark mode support
    document.addEventListener('dark-mode', function () {
        chart.updateOptions(pieChartOptions(dt));
    });
}
```

#### 3. Template View Charts (Database Data)

**View Implementation**:
```python
# apps/charts/views.py
from django.shortcuts import render
from apps.pages.models import Product
from django.core import serializers

def index(request):
    products = serializers.serialize('json', Product.objects.all())
    context = {
        'segment': 'charts',
        'parent': 'apps',
        'products': products
    }
    return render(request, 'apps/charts.html', context)
```

**Template Integration**:
```html
<!-- templates/apps/charts.html -->
<div class="flex gap-5 items-center justify-between">
    <div class="w-full" id="products-bar-chart"></div>
    <div class="w-full" id="products-pie-chart"></div>
</div>

<script>
    // Pull data from the backend
    const products = JSON.parse('{{ products | safe }}');

    function getProductsBarChart(data) {
        return {
            series: [{
                name: 'Products',
                data: data.map(item => item.fields.price)
            }],
            chart: {
                type: 'bar',
                height: '420px'
            }
        };
    }

    const getProductsPieChart = (data) => {
        return {
            series: data.map(item => item.fields.price),
            labels: data.map(item => item.fields.name),
            chart: {
                type: 'pie',
                height: '420px'
            }
        };
    }

    (async () => {
        const productsBarChart = new ApexCharts(document.getElementById('products-bar-chart'), getProductsBarChart(products));
        productsBarChart.render();

        const productsPieChart = new ApexCharts(document.getElementById('products-pie-chart'), getProductsPieChart(products));
        productsPieChart.render();

        // Dark mode support
        document.addEventListener('dark-mode', function () {
            productsPieChart.updateOptions(getProductsPieChart(products));
        });
    })();
</script>
```

### Soundcharts Dashboard Integration

#### Real-time Analytics Dashboard

**Data Aggregation**:
```python
# apps/pages/views.py
def dashboard(request):
    # Weekly rankings aggregation
    week_start = timezone.now() - timedelta(days=7)
    weekly_rankings = ChartRanking.objects.filter(fetched_at__gte=week_start).count()
    
    # Top platforms
    top_platforms = Chart.objects.values('platform__name').annotate(
        total_rankings=Count('chartranking')
    ).order_by('-total_rankings')[:5]
    
    # Top performing tracks
    top_tracks = Track.objects.annotate(
        ranking_count=Count('chartrankingentry')
    ).order_by('-ranking_count')[:10]
    
    # Chart health metrics
    chart_health = Chart.objects.annotate(
        last_sync=Max('chartranking__fetched_at')
    ).filter(last_sync__isnull=False)
    
    context = {
        'weekly_rankings': weekly_rankings,
        'top_platforms': list(top_platforms),
        'top_tracks': top_tracks,
        'chart_health': chart_health,
    }
    return render(request, 'soundcharts/dashboard.html', context)
```

**Dashboard Chart Configuration**:
```javascript
// ApexCharts Configuration for Soundcharts Dashboard
const weeklyRankingsChart = {
    chart: {
        type: 'area',
        height: '350px',
        fontFamily: 'Inter, sans-serif',
        foreColor: '#4B5563',
        toolbar: {
            show: false
        }
    },
    series: [{
        name: 'Daily Rankings',
        data: weeklyRankingsData, // From backend
        color: '#1C64F2'
    }],
    xaxis: {
        categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    },
    fill: {
        type: 'gradient',
        gradient: {
            shade: 'light',
            type: 'vertical',
            shadeIntensity: 0.5,
            gradientToColors: ['#3B82F6'],
            inverseColors: false,
            opacityFrom: 0.8,
            opacityTo: 0.1,
            stops: [0, 100]
        }
    }
};
```

## API Endpoints and Data Integration

### REST API Structure

#### Product API Endpoint

**URL**: `/api/product/`

**Response Format**:
```json
[
    {
        "id": 3,
        "name": "Adidas",
        "info": "Just another cool product",
        "price": 201
    },
    {
        "id": 4,
        "name": "Nike",
        "info": "This is a shoe shop",
        "price": 66
    },
    {
        "id": 5,
        "name": "Puma",
        "info": "Over priced Puma",
        "price": 666
    }
]
```

#### Soundcharts API Endpoints

**Track Audience Data**:
```python
# URL: /soundcharts/audience/chart/<track_uuid>/<platform_slug>/?limit=30
class AudienceChartView(View):
    def get(self, request, track_uuid, platform_slug):
        # Get track and platform data
        track = get_object_or_404(Track, uuid=track_uuid)
        platform = get_object_or_404(Platform, slug=platform_slug)
        
        # Get chart data with limit
        limit = request.GET.get('limit', 30)
        chart_data = TrackAudienceTimeSeries.get_chart_data(track, platform, limit)
        
        return JsonResponse({
            'success': True,
            'track': {
                'name': track.name,
                'uuid': track.uuid,
                'credit_name': track.credit_name
            },
            'platform': {
                'name': platform.name,
                'slug': platform.slug
            },
            'chart_data': {
                'labels': [item['date'] for item in chart_data],
                'datasets': [{
                    'label': f'{track.name} on {platform.name}',
                    'data': [item['audience_value'] for item in chart_data],
                    'borderColor': '#3b82f6',
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                    'tension': 0.1
                }]
            }
        })
```

**Multi-Platform Audience Data**:
```python
# URL: /soundcharts/audience/chart/<track_uuid>/?limit=30
class MultiPlatformAudienceChartView(View):
    def get(self, request, track_uuid):
        track = get_object_or_404(Track, uuid=track_uuid)
        platforms = Platform.objects.filter(
            trackaudiencetimeseries__track=track
        ).distinct()
        
        limit = request.GET.get('limit', 30)
        chart_data = {}
        
        for platform in platforms:
            platform_data = TrackAudienceTimeSeries.get_chart_data(track, platform, limit)
            chart_data[platform.slug] = {
                'labels': [item['date'] for item in platform_data],
                'data': [item['audience_value'] for item in platform_data]
            }
        
        return JsonResponse({
            'success': True,
            'track': {
                'name': track.name,
                'uuid': track.uuid,
                'credit_name': track.credit_name
            },
            'platforms': list(platforms.values('name', 'slug')),
            'chart_data': chart_data
        })
```

### Data Processing and Optimization

#### Audience Data Processing

**Model Implementation**:
```python
# apps/soundcharts/models.py
class TrackAudienceTimeSeries(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    date = models.DateField()
    audience_value = models.BigIntegerField()
    
    @classmethod
    def get_chart_data(cls, track, platform, limit=None):
        queryset = cls.objects.filter(track=track, platform=platform)
        
        if limit:
            # Get the most recent N records, then sort for display
            recent_records = queryset.order_by('-date')[:limit]
            recent_records = list(recent_records)
            recent_records.sort(key=lambda x: x.date)
            return [{'date': record.date, 'audience_value': record.audience_value} for record in recent_records]
        else:
            # No limit, just order by date ascending
            return queryset.order_by('date').values('date', 'audience_value')
```

**Data Verification and Fix**:
```python
# debug_audience_charts.py
def verify_chart_data(track_uuid=None):
    if track_uuid:
        tracks = Track.objects.filter(uuid=track_uuid)
    else:
        tracks = Track.objects.filter(trackaudiencetimeseries__isnull=False).distinct()
    
    for track in tracks:
        print(f"\n=== Track: {track.name} ({track.uuid}) ===")
        
        # Get all audience data for this track
        all_data = TrackAudienceTimeSeries.objects.filter(track=track).order_by('-date')
        
        if not all_data.exists():
            print("No audience data found")
            continue
            
        print(f"Total data points: {all_data.count()}")
        print(f"Latest date: {all_data.first().date}")
        print(f"Oldest date: {all_data.last().date}")
        
        # Test chart data method
        for platform in Platform.objects.filter(trackaudiencetimeseries__track=track).distinct():
            chart_data = TrackAudienceTimeSeries.get_chart_data(track, platform, limit=30)
            print(f"Platform {platform.name}: {len(chart_data)} data points")
            if chart_data:
                print(f"  Chart data range: {chart_data[0]['date']} to {chart_data[-1]['date']}")
```

## Frontend Integration Features

### Admin Interface Enhancements

#### Track Admin Alerts System

**JavaScript Implementation**:
```javascript
// static/assets/track-admin-alerts.js
function showTrackAlert(message, type) {
    // Remove existing alerts
    hideTrackAlert();
    
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = `
        <div class="alert-content">
            <span class="alert-message">${message}</span>
            <button type="button" class="alert-close" onclick="hideTrackAlert()">×</button>
        </div>
    `;
    
    // Insert at top of content area
    const contentArea = document.querySelector('.content-main');
    if (contentArea) {
        contentArea.insertBefore(alertDiv, contentArea.firstChild);
        
        // Auto-hide success alerts after 5 seconds
        if (type === 'success') {
            setTimeout(hideTrackAlert, 5000);
        }
    }
}

function fetchTrackMetadata(trackId) {
    const button = event.target;
    const originalText = button.textContent;
    
    button.disabled = true;
    button.textContent = 'Fetching...';
    
    fetch(`/admin/soundcharts/track/${trackId}/fetch-metadata/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showTrackAlert('Metadata fetched successfully!', 'success');
            // Reload page to show updated data
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showTrackAlert(data.error || 'Failed to fetch metadata', 'error');
        }
    })
    .catch(error => {
        showTrackAlert('Network error occurred', 'error');
    })
    .finally(() => {
        button.disabled = false;
        button.textContent = originalText;
    });
}
```

#### Admin Import Templates Consistency

**Unified CSS Framework**:
```css
/* static/assets/admin-import.css */
.module {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    padding: 1.5rem;
}

.form-row {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 1rem;
}

.field-box {
    flex: 1;
    min-width: 200px;
}

.vTextField, .vSelectField, .vIntegerField {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    font-size: 0.875rem;
}

.alert-success, .alert-error, .alert-warning, .alert-info {
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 0.375rem;
    border-left: 4px solid;
}

.alert-success {
    background-color: #d1fae5;
    border-left-color: #10b981;
    color: #065f46;
}

.alert-error {
    background-color: #fee2e2;
    border-left-color: #ef4444;
    color: #991b1b;
}
```

**Unified JavaScript Framework**:
```javascript
// static/assets/admin-import.js
function showAlert(message, type) {
    // Unified alert system for all admin import templates
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = `
        <div class="alert-content">
            <span class="alert-message">${message}</span>
            <button type="button" class="alert-close" onclick="hideAlert()">×</button>
        </div>
    `;
    
    const contentArea = document.querySelector('.content-main');
    if (contentArea) {
        contentArea.insertBefore(alertDiv, contentArea.firstChild);
    }
}

function fetchCharts() {
    showLoading(true);
    
    const limit = document.getElementById('limit').value;
    const offset = document.getElementById('offset').value;
    
    fetch(`/admin/soundcharts/chart/fetch-charts/?limit=${limit}&offset=${offset}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayCharts(data.charts);
            } else {
                showAlert(data.error || 'Failed to fetch charts', 'error');
            }
        })
        .catch(error => {
            showAlert('Network error occurred', 'error');
        })
        .finally(() => {
            showLoading(false);
        });
}

function addChart(slug, button) {
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Adding...';
    
    fetch(`/admin/soundcharts/chart/add-chart/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ slug: slug })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(`Chart ${slug} added successfully!`, 'success');
            button.textContent = 'Added';
            button.disabled = true;
        } else {
            showAlert(data.error || 'Failed to add chart', 'error');
            button.disabled = false;
            button.textContent = originalText;
        }
    })
    .catch(error => {
        showAlert('Network error occurred', 'error');
        button.disabled = false;
        button.textContent = originalText;
    });
}
```

### Extended User Model Integration

#### Profile Management System

**Model Implementation**:
```python
# apps/users/models.py
ROLE_CHOICES = (
    ('admin', 'Admin'),
    ('user', 'User'),
)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    full_name = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    zip_code = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    avatar = models.ImageField(upload_to='avatar', null=True, blank=True)

    def __str__(self):
        return self.user.username
```

**Form Implementation**:
```python
# apps/users/forms.py
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ('user', 'role', 'avatar',)

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            self.fields[field_name].widget.attrs['placeholder'] = field.label
            self.fields[field_name].widget.attrs['class'] = 'shadow-sm bg-gray-50 border border-gray-300 text-gray-900 sm:text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500'
            self.fields[field_name].widget.attrs['required'] = False
```

**View Implementation**:
```python
# apps/users/views.py
def profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully')
    else:
        form = ProfileForm(instance=profile)
    
    context = {
        'form': form,
        'segment': 'profile',
    }
    return render(request, 'dashboard/profile.html', context)
```

**Template Integration**:
```html
<!-- templates/dashboard/profile.html -->
{% for field in form %}
    <div class="col-span-6 sm:col-span-3">
        <label for="{{ field.id_for_label }}" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">{{ field.label }}</label>
        {{ field }}
    </div>
{% endfor %}
```

## DataTables Integration

### Dynamic Table Management

**Form Implementation**:
```python
# apps/tables/forms.py
from django import forms
from apps.pages.models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'shadow-sm bg-gray-50 border border-gray-300 text-gray-900 sm:text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500'
```

**View Implementation**:
```python
# apps/tables/views.py
def datatables(request):
    filters = product_filter(request)
    product_list = Product.objects.filter(**filters)
    form = ProductForm()
    
    # Pagination
    paginator = Paginator(product_list, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product created successfully')
            return redirect('apps:datatables')
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'segment': 'datatables',
        'parent': 'apps',
    }
    return render(request, 'apps/datatables.html', context)
```

**Frontend Integration**:
```javascript
// templates/apps/datatables.html
fetch('/api/product/')
    .then(response => response.json())
    .then(data => {
        $('#products-body').DataTable({
            data: data,
            columns: [
                { title: 'ID', data: 'id' },
                { title: 'Name', data: 'name' },
                { title: 'Info', data: 'info' },
                { title: 'Price', data: 'price' },
                { 
                    title: 'Actions', 
                    data: null,
                    render: function(data, type, row) {
                        return `
                            <button onclick="editProduct(${row.id})" class="btn btn-sm btn-primary">Edit</button>
                            <button onclick="deleteProduct(${row.id})" class="btn btn-sm btn-danger">Delete</button>
                        `;
                    }
                }
            ],
            responsive: true,
            pageLength: 25,
            order: [[0, 'desc']]
        });
    })
    .catch(error => {
        console.error('Error loading data:', error);
    });
```

## Performance Optimization

### Frontend Performance

#### Chart Rendering Optimization

**Lazy Loading**:
```javascript
// Load charts only when visible
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const chartId = entry.target.id;
            loadChart(chartId);
            observer.unobserve(entry.target);
        }
    });
});

document.querySelectorAll('.chart-container').forEach(container => {
    observer.observe(container);
});
```

**Memory Management**:
```javascript
// Clean up charts when not needed
function destroyChart(chartId) {
    const chart = ApexCharts.getChartByID(chartId);
    if (chart) {
        chart.destroy();
    }
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    document.querySelectorAll('.apexcharts-canvas').forEach(canvas => {
        const chartId = canvas.id;
        destroyChart(chartId);
    });
});
```

#### API Optimization

**Caching Strategy**:
```python
# views.py
from django.core.cache import cache

def get_chart_data(request, track_uuid, platform_slug):
    cache_key = f"chart_data_{track_uuid}_{platform_slug}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return JsonResponse(cached_data)
    
    # Generate data
    data = generate_chart_data(track_uuid, platform_slug)
    
    # Cache for 1 hour
    cache.set(cache_key, data, 3600)
    
    return JsonResponse(data)
```

**Database Optimization**:
```python
# Efficient queries with select_related and prefetch_related
def get_track_data(track_uuid):
    return Track.objects.select_related(
        'primary_artist', 'primary_genre'
    ).prefetch_related(
        'artists', 'genres', 'trackaudiencetimeseries__platform'
    ).get(uuid=track_uuid)
```

## Error Handling and User Experience

### Comprehensive Error Handling

#### Frontend Error Handling

**API Error Handling**:
```javascript
async function fetchData(url) {
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Unknown error occurred');
        }
        
        return data;
    } catch (error) {
        console.error('Error fetching data:', error);
        showAlert(`Error: ${error.message}`, 'error');
        throw error;
    }
}
```

**Chart Error Handling**:
```javascript
function renderChart(chartId, options) {
    try {
        const chart = new ApexCharts(document.getElementById(chartId), options);
        chart.render();
        return chart;
    } catch (error) {
        console.error('Error rendering chart:', error);
        showAlert('Failed to render chart. Please refresh the page.', 'error');
        return null;
    }
}
```

#### Backend Error Handling

**API Error Responses**:
```python
# views.py
def handle_api_error(error, context=""):
    logger.error(f"API Error {context}: {str(error)}")
    
    if isinstance(error, Track.DoesNotExist):
        return JsonResponse({
            'success': False,
            'error': 'Track not found',
            'code': 'TRACK_NOT_FOUND'
        }, status=404)
    
    if isinstance(error, Platform.DoesNotExist):
        return JsonResponse({
            'success': False,
            'error': 'Platform not found',
            'code': 'PLATFORM_NOT_FOUND'
        }, status=404)
    
    return JsonResponse({
        'success': False,
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR'
    }, status=500)
```

## Testing and Quality Assurance

### Frontend Testing

**Chart Rendering Tests**:
```javascript
// Test chart configuration
function testChartConfiguration() {
    const options = getMainChartOptions();
    
    // Verify required properties
    assert(options.chart !== undefined, 'Chart configuration missing');
    assert(options.series !== undefined, 'Series data missing');
    assert(options.xaxis !== undefined, 'X-axis configuration missing');
    
    // Verify data format
    assert(Array.isArray(options.series), 'Series should be an array');
    assert(options.series.length > 0, 'Series should contain data');
}

// Test API integration
async function testAPIIntegration() {
    try {
        const data = await fetchData('/api/product/');
        assert(data.length > 0, 'API should return data');
        assert(data[0].hasOwnProperty('id'), 'Data should have id property');
        assert(data[0].hasOwnProperty('name'), 'Data should have name property');
    } catch (error) {
        console.error('API test failed:', error);
    }
}
```

### Backend Testing

**API Endpoint Tests**:
```python
# tests.py
from django.test import TestCase, Client
from django.urls import reverse
import json

class ChartAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.track = Track.objects.create(
            name="Test Track",
            uuid="test-uuid-123"
        )
        self.platform = Platform.objects.create(
            name="Test Platform",
            slug="test-platform"
        )
    
    def test_chart_data_api(self):
        url = reverse('soundcharts:audience_chart', args=[
            self.track.uuid, self.platform.slug
        ])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('chart_data', data)
        self.assertIn('track', data)
        self.assertIn('platform', data)
```

## Future Enhancements

### Planned Features

1. **Real-time Updates**: WebSocket integration for live chart updates
2. **Advanced Visualizations**: 3D charts, heatmaps, and advanced chart types
3. **Interactive Features**: Chart zooming, filtering, and drill-down capabilities
4. **Export Functionality**: PDF and image export for charts
5. **Mobile Optimization**: Touch-friendly chart interactions
6. **Performance Monitoring**: Chart rendering performance metrics
7. **Accessibility**: Screen reader support and keyboard navigation
8. **Internationalization**: Multi-language support for chart labels

### Technical Improvements

1. **Virtual Scrolling**: For large datasets
2. **Progressive Loading**: Load chart data in chunks
3. **Service Workers**: Offline chart functionality
4. **WebAssembly**: High-performance data processing
5. **GraphQL**: More efficient data fetching
6. **Micro-frontends**: Modular chart components

## Conclusion

The API and frontend integration in MusicChartsAI provides a comprehensive, scalable, and user-friendly platform for music data visualization and management. The system combines advanced charting capabilities, robust API endpoints, efficient data processing, and excellent user experience to deliver a professional-grade music analytics platform.

Key strengths include:
- **Advanced Charting**: ApexCharts integration with dynamic data visualization
- **Robust API Design**: RESTful endpoints with comprehensive error handling
- **User Experience**: Consistent admin interface with real-time feedback
- **Performance**: Optimized data processing and caching strategies
- **Extensibility**: Modular architecture supporting future enhancements
- **Quality Assurance**: Comprehensive testing and error handling
