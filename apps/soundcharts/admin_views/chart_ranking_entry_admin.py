from django.contrib import admin
from django.utils.html import format_html
from ..models import ChartRankingEntry


class ChartRankingEntryAdmin(admin.ModelAdmin):
    list_display = (
        "position",
        "get_track_info",
        "ranking",
        "get_position_trend",
        "weeks_on_chart",
        "get_streams",
    )
    list_filter = (
        "ranking__chart",
        "ranking__ranking_date",
        "position",
        "weeks_on_chart",
        "track",
    )
    search_fields = ("track__name", "track__uuid", "track__credit_name")
    ordering = ("ranking__ranking_date", "position")
    readonly_fields = ("api_data",)
    list_per_page = 100
    date_hierarchy = "ranking__ranking_date"

    fieldsets = (
        (
            "Position Information",
            {
                "fields": (
                    "position",
                    "previous_position",
                    "position_change",
                    "weeks_on_chart",
                )
            },
        ),
        ("Track Information", {"fields": ("track",)}),
        ("Raw API Data", {"fields": ("api_data",), "classes": ("collapse",)}),
    )

    def get_track_info(self, obj):
        """Display track name and artist in a readable format"""
        if not obj.track:
            return "Unknown Track"

        track_name = obj.track.name
        artist_name = (
            obj.track.credit_name if obj.track.credit_name else "Unknown Artist"
        )

        return format_html(
            "<strong>{}</strong><br><small>{}</small>", track_name, artist_name
        )

    get_track_info.short_description = "Track & Artist"
    get_track_info.allow_tags = True

    def get_position_trend(self, obj):
        """Display position trend with visual indicators"""
        if obj.position_change is None:
            return "New"
        elif obj.position_change == 0:
            return "→ No change"
        elif obj.position_change > 0:
            return f"↑ +{obj.position_change}"
        else:
            return f"↓ {obj.position_change}"

    get_position_trend.short_description = "Position Trend"

    def get_streams(self, obj):
        """Display stream count from API data"""
        if obj.api_data and "metric" in obj.api_data:
            metric = obj.api_data["metric"]
            if metric:
                return f"{metric:,}"
        return "N/A"

    get_streams.short_description = "Streams"

    def get_queryset(self, request):
        """Optimize queryset for better performance"""
        return super().get_queryset(request).select_related("track", "ranking__chart")

    def has_add_permission(self, request):
        """Entries should only be created through the ranking import process"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Entries should only be deleted when the entire ranking is deleted"""
        return False
