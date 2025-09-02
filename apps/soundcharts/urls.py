from django.urls import path
from .views import (
    AudienceChartView, 
    AudienceDataRefreshView, 
    audience_chart_data,
    AudienceDashboardView,
    TracksWithAudienceView
)

app_name = 'soundcharts'

urlpatterns = [
    # Dashboard views
    path('audience/dashboard/', AudienceDashboardView.as_view(), name='audience_dashboard'),
    
    # API endpoints
    path('api/tracks-with-audience/', TracksWithAudienceView.as_view(), name='tracks_with_audience'),
    
    # Audience chart data endpoints
    path('audience/chart/<str:track_uuid>/', AudienceChartView.as_view(), name='audience_chart_all_platforms'),
    path('audience/chart/<str:track_uuid>/<str:platform_slug>/', AudienceChartView.as_view(), name='audience_chart_single_platform'),
    
    # Audience data refresh endpoint
    path('audience/refresh/<str:track_uuid>/<str:platform_slug>/', AudienceDataRefreshView.as_view(), name='audience_refresh'),
    
    # Legacy endpoint for backward compatibility
    path('audience/chart-data/<str:track_uuid>/', audience_chart_data, name='audience_chart_data_legacy'),
    path('audience/chart-data/<str:track_uuid>/<str:platform_slug>/', audience_chart_data, name='audience_chart_data_platform_legacy'),
]
