from django.contrib import admin

from apps.soundcharts.admin_views.track_audience_admin import TrackAudienceAdmin
from .models import (
    Platform,
    Artist,
    Album,
    Track,
    Venue,
    Chart,
    Genre,
    ChartRanking,
    ChartRankingEntry,
    ChartRankingEntrySummary,
    MetadataFetchTask,
    TrackAudienceTimeSeries,
    ChartSyncSchedule,
    ChartSyncExecution,
)
from .admin_views import (
    PlatformAdmin,
    ArtistAdmin,
    AlbumAdmin,
    TrackAdmin,
    VenueAdmin,
    ChartAdmin,
    GenreAdmin,
    ChartRankingAdmin,
    ChartRankingEntryAdmin,
    ChartRankingEntrySummaryAdmin,
    MetadataFetchTaskAdmin,
    ChartSyncScheduleAdmin,
    ChartSyncExecutionAdmin,
)

# Register your models here.
admin.site.register(Platform, PlatformAdmin)
admin.site.register(Artist, ArtistAdmin)
admin.site.register(Album, AlbumAdmin)
admin.site.register(Track, TrackAdmin)
admin.site.register(Venue, VenueAdmin)
admin.site.register(Chart, ChartAdmin)
admin.site.register(Genre, GenreAdmin)
admin.site.register(ChartRanking, ChartRankingAdmin)
admin.site.register(ChartRankingEntry, ChartRankingEntryAdmin)
admin.site.register(ChartRankingEntrySummary, ChartRankingEntrySummaryAdmin)
admin.site.register(MetadataFetchTask, MetadataFetchTaskAdmin)
admin.site.register(ChartSyncSchedule, ChartSyncScheduleAdmin)
admin.site.register(ChartSyncExecution, ChartSyncExecutionAdmin)

# Register TrackAudienceTimeSeries with inline admin
admin.site.register(TrackAudienceTimeSeries, TrackAudienceAdmin)
