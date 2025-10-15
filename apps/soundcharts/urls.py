from django.urls import path
from .views import (
    AudienceChartView, 
    AudienceDataRefreshView, 
    audience_chart_data,
    AudienceDashboardView,
    TracksWithAudienceView,
    PlatformListView,
    TopArtistsView,
    TopSongsView,
    SongAudienceDetailView,
    ChartSyncScheduleAPIView,
    ChartSyncScheduleDetailAPIView,
    ChartSyncTriggerAPIView,
    ChartSyncStatusAPIView,
    # Artist views
    ArtistSearchView,
    ArtistListView,
    ArtistDetailView,
    ArtistAudienceChartView,
    ArtistSaveView,
    ArtistMetadataFetchView,
    ArtistAudienceFetchView,
)

app_name = 'soundcharts'

urlpatterns = [
    # Dashboard views
    path('audience/dashboard/', AudienceDashboardView.as_view(), name='audience_dashboard'),
    path('top_artists/', TopArtistsView.as_view(), name='top_artists'),
    path('top_songs/', TopSongsView.as_view(), name='top_songs'),
    path('platforms/', PlatformListView.as_view(), name='platform_list'),
    # API endpoints
    path('api/tracks-with-audience/', TracksWithAudienceView.as_view(), name='tracks_with_audience'),
    
    # Chart Sync API endpoints
    path('api/sync/schedules/', ChartSyncScheduleAPIView.as_view(), name='chart_sync_schedules'),
    path('api/sync/schedules/<int:schedule_id>/', ChartSyncScheduleDetailAPIView.as_view(), name='chart_sync_schedule_detail'),
    path('api/sync/trigger/', ChartSyncTriggerAPIView.as_view(), name='chart_sync_trigger'),
    path('api/sync/status/<int:chart_id>/', ChartSyncStatusAPIView.as_view(), name='chart_sync_status'),
    
    # Audience chart data endpoints
    path('audience/chart/<str:track_uuid>/', AudienceChartView.as_view(), name='audience_chart_all_platforms'),
    path('audience/chart/<str:track_uuid>/<str:platform_slug>/', AudienceChartView.as_view(), name='audience_chart_single_platform'),
    
    # Audience data refresh endpoint
    path('audience/refresh/<str:track_uuid>/<str:platform_slug>/', AudienceDataRefreshView.as_view(), name='audience_refresh'),
    
    # Legacy endpoint for backward compatibility
    path('audience/chart-data/<str:track_uuid>/', audience_chart_data, name='audience_chart_data_legacy'),
    path('audience/chart-data/<str:track_uuid>/<str:platform_slug>/', audience_chart_data, name='audience_chart_data_platform_legacy'),
    
    # Song detail page
    path('songs/<str:track_uuid>/audience/', SongAudienceDetailView.as_view(), name='song_audience_detail'),
    
    # Artist pages
    path('artists/search/', ArtistSearchView.as_view(), name='artist_search'),
    path('artists/', ArtistListView.as_view(), name='artist_list'),
    path('artists/<str:artist_uuid>/', ArtistDetailView.as_view(), name='artist_detail'),
    
    # Artist API endpoints
    path('api/artists/save/', ArtistSaveView.as_view(), name='artist_save'),
    path('api/artists/fetch-metadata/', ArtistMetadataFetchView.as_view(), name='artist_fetch_metadata'),
    path('api/artists/fetch-audience/', ArtistAudienceFetchView.as_view(), name='artist_fetch_audience'),
    
    # Artist audience chart data endpoints
    path('artists/<str:artist_uuid>/audience/chart/', ArtistAudienceChartView.as_view(), name='artist_audience_chart_all'),
    path('artists/<str:artist_uuid>/audience/chart/<str:platform_slug>/', ArtistAudienceChartView.as_view(), name='artist_audience_chart_single'),
]
