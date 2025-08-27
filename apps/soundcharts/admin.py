from django.contrib import admin
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
