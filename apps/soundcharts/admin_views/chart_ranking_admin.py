from django.contrib import admin
from django.urls import path
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import redirect
from django.template.loader import render_to_string

from ..models import ChartRanking


class ChartRankingAdmin(admin.ModelAdmin):
    list_display = (
        "chart",
        "ranking_date",
        "total_entries",
        "get_entries_count",
        "get_top_tracks",
        "get_view_entries_link",
        "fetched_at",
    )
    list_filter = ("chart", "ranking_date", "fetched_at")
    search_fields = ("chart__name", "chart__slug")
    ordering = ("-ranking_date", "-fetched_at")
    readonly_fields = ("fetched_at", "get_entries_summary", "get_entries_table")
    date_hierarchy = "ranking_date"
    actions = ["view_entries_in_table"]

    fieldsets = (
        (
            "Chart Information",
            {"fields": ("chart", "ranking_date")},
        ),
        (
            "API Data",
            {
                "fields": (
                    "total_entries",
                    "api_version",
                    "fetched_at",
                )
            },
        ),
        (
            "Entries Summary",
            {
                "description": "Quick overview of the chart entries",
                "fields": ("get_entries_summary",),
                "classes": ("collapse",),
            },
        ),
        (
            "Chart Entries",
            {
                "description": "Individual song rankings for this chart. Entries are automatically managed through the ranking import process.",
                "fields": ("get_entries_table",),
                "classes": ("collapse",),
            },
        ),
    )

    def get_urls(self):
        """Add custom URLs for better entry viewing"""
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:ranking_id>/entries/",
                self.admin_site.admin_view(self.view_entries),
                name="chart_ranking_entries",
            ),
        ]
        return custom_urls + urls

    def view_entries(self, request, ranking_id):
        """Custom view to show entries in a proper interactive data table format"""
        ranking = get_object_or_404(ChartRanking, id=ranking_id)
        entries = ranking.entries.select_related("track").order_by("position")

        # Prepare data for the data table
        table_data = []
        for entry in entries:
            track = entry.track
            if track:
                track_url = reverse("admin:soundcharts_track_change", args=[track.id])
            else:
                track_url = "#"

            # Format trend data
            if entry.position_change is None:
                trend_text = "New"
                trend_class = "new"
                trend_icon = "🆕"
            elif entry.position_change == 0:
                trend_text = "No change"
                trend_class = "no-change"
                trend_icon = "→"
            elif entry.position_change > 0:
                trend_text = f"+{entry.position_change}"
                trend_class = "up"
                trend_icon = "↑"
            else:
                trend_text = f"{entry.position_change}"
                trend_class = "down"
                trend_icon = "↓"

            # Format streams
            streams = "N/A"
            if entry.api_data and "metric" in entry.api_data:
                metric = entry.api_data["metric"]
                if metric:
                    streams = f"{metric:,}"

            # Format weeks
            weeks = str(entry.weeks_on_chart) if entry.weeks_on_chart else "N/A"

            table_data.append(
                {
                    "id": entry.id,
                    "position": entry.position,
                    "track_name": track.name if track else "Unknown",
                    "track_url": track_url,
                    "artist_name": track.credit_name
                    if track and track.credit_name
                    else "Unknown Artist",
                    "trend_text": trend_text,
                    "trend_class": trend_class,
                    "trend_icon": trend_icon,
                    "weeks": weeks,
                    "streams": streams,
                    "previous_position": entry.previous_position or "N/A",
                    "position_change": entry.position_change or 0,
                    "api_data": entry.api_data,
                }
            )

        context = {
            "ranking": ranking,
            "entries": entries,
            "table_data": table_data,
            "title": f"Chart Entries - {ranking.chart.name} ({ranking.ranking_date.strftime('%Y-%m-%d')})",
            "opts": self.model._meta,
        }

        return TemplateResponse(
            request, "admin/soundcharts/ranking_entries.html", context
        )

    def get_entries_count(self, obj):
        """Display the actual count of entries with better formatting"""
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

    def get_view_entries_link(self, obj):
        """Display a link to view entries in a data table"""
        if obj.entries.count() == 0:
            return "No entries"

        # Use the custom view instead of the admin changelist
        url = reverse("admin:chart_ranking_entries", args=[obj.id])
        return format_html(
            '<a href="{}" target="_blank">View Entries ({})</a>',
            url,
            obj.entries.count(),
        )

    get_view_entries_link.short_description = "View Entries"
    get_view_entries_link.allow_tags = True

    def get_entries_summary(self, obj):
        """Display summary statistics about the entries"""
        entries = obj.entries.all()
        if not entries:
            return "No entries available"

        # Get some basic stats
        total_entries = entries.count()
        new_entries = entries.filter(position_change__isnull=True).count()
        moving_up = entries.filter(position_change__gt=0).count()
        moving_down = entries.filter(position_change__lt=0).count()
        no_change = entries.filter(position_change=0).count()

        # Return formatted text instead of HTML
        summary = f"""
Chart Summary:
• Total Entries: {total_entries}
• New Entries: {new_entries}
• Moving Up: {moving_up}
• Moving Down: {moving_down}
• No Change: {no_change}
        """.strip()

        return summary

    get_entries_summary.short_description = "Entries Summary"

    def get_entries_table(self, obj):
        """Display entries as an interactive data table using external template"""
        entries = obj.entries.select_related("track").order_by("position")
        if not entries:
            return "No entries available"

        # Render the mini table template
        context = {
            "entries": entries,
            "ranking_id": obj.id,
        }

        return render_to_string("admin/soundcharts/mini_entries_table.html", context)

    get_entries_table.short_description = "Chart Entries"
    get_entries_table.allow_tags = True

    def view_entries_in_table(self, request, queryset):
        """Admin action to view entries in a data table"""
        if queryset.count() != 1:
            self.message_user(
                request, "Please select exactly one chart ranking to view entries."
            )
            return

        ranking = queryset.first()
        url = reverse("admin:chart_ranking_entries", args=[ranking.id])
        return redirect(url)

    view_entries_in_table.short_description = "View entries in data table"

    def get_queryset(self, request):
        """Optimize queryset to include related data"""
        return (
            super()
            .get_queryset(request)
            .select_related("chart")
            .prefetch_related("entries__track")
        )
