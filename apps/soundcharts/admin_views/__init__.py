# Import all admin classes to maintain backward compatibility
from .soundcharts_admin_mixin import SoundchartsAdminMixin
from .platform_admin import PlatformAdmin
from .artist_admin import ArtistAdmin
from .album_admin import AlbumAdmin
from .track_admin import TrackAdmin
from .venue_admin import VenueAdmin
from .chart_admin import ChartAdmin
from .genre_admin import GenreAdmin
from .chart_ranking_admin import ChartRankingAdmin, ChartRankingEntrySummaryAdmin
from .chart_ranking_entry_admin import ChartRankingEntryAdmin
from .metadata_fetch_task_admin import MetadataFetchTaskAdmin
from .chart_sync_admin import ChartSyncScheduleAdmin, ChartSyncExecutionAdmin

__all__ = [
    "SoundchartsAdminMixin",
    "PlatformAdmin",
    "ArtistAdmin",
    "AlbumAdmin",
    "TrackAdmin",
    "VenueAdmin",
    "ChartAdmin",
    "GenreAdmin",
    "ChartRankingAdmin",
    "ChartRankingEntrySummaryAdmin",
    "ChartRankingEntryAdmin",
    "MetadataFetchTaskAdmin",
    "ChartSyncScheduleAdmin",
    "ChartSyncExecutionAdmin",
]
