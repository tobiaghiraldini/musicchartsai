from django.contrib import admin
from ..models import ChartRanking


class ChartRankingInline(admin.TabularInline):
    """Inline admin for ChartRankings within Chart admin"""

    model = ChartRanking
    extra = 0
    readonly_fields = ("fetched_at", "get_entries_count", "get_top_tracks")
    fields = (
        "ranking_date",
        "total_entries",
        "get_entries_count",
        "get_top_tracks",
        "fetched_at",
    )
    ordering = ("-ranking_date",)

    def get_entries_count(self, obj):
        """Display the actual count of entries"""
        count = obj.entries.count()
        if count == 0:
            return "0 entries"
        elif count == 1:
            return "1 entry"
        else:
            return f"{count} entries"

    get_entries_count.short_description = "Entries Count"

    def get_top_tracks(self, obj):
        """Display top 3 tracks for quick reference"""
        top_entries = obj.entries.select_related("track").order_by("position")[:3]
        if not top_entries:
            return "No entries"

        tracks = []
        for entry in top_entries:
            track_name = entry.track.name if entry.track else "Unknown"
            tracks.append(f"#{entry.position} {track_name}")

        return " | ".join(tracks)

    get_top_tracks.short_description = "Top Tracks"

    def has_add_permission(self, request, obj=None):
        """ChartRankings should be created through the import process, not manually"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion of individual rankings"""
        return True
