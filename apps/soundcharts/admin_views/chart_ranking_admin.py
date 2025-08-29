from django.contrib import admin
from django.urls import path
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.db.models import Count, Sum, Min, Max, Q
from django.db.models.functions import Trunc
from django.db.models import DateTimeField

from ..models import ChartRanking, ChartRankingEntrySummary


class ChartRankingEntrySummaryAdmin(admin.ModelAdmin):
    """
    Admin for displaying chart ranking entries in a native admin table format
    """
    change_list_template = 'admin/soundcharts/chart_ranking_entries_summary.html'
    
    list_display = (
        'position',
        'get_track_info',
        'get_position_trend',
        'weeks_on_chart',
        'get_streams',
        'previous_position',
    )
    
    list_filter = ('weeks_on_chart',)
    search_fields = ('track__name', 'track__credit_name')
    ordering = ('position',)
    list_per_page = 100
    
    def get_queryset(self, request):
        """Filter entries for a specific ranking"""
        qs = super().get_queryset(request)
        # Get ranking_id from the URL or context
        ranking_id = request.GET.get('ranking_id')
        if ranking_id:
            qs = qs.filter(ranking_id=ranking_id)
        return qs.select_related('track')
    
    def changelist_view(self, request, extra_context=None):
        """Override changelist view to provide custom context"""
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
        
        # Get ranking_id from request
        ranking_id = request.GET.get('ranking_id')
        if ranking_id:
            ranking = ChartRanking.objects.select_related('chart__platform').get(id=ranking_id)
            response.context_data['ranking'] = ranking
            
            # Add summary statistics
            metrics = {
                'total_entries': Count('id'),
                'new_entries': Count('id', filter=Q(position_change__isnull=True)),
                'moving_up': Count('id', filter=Q(position_change__gt=0)),
                'moving_down': Count('id', filter=Q(position_change__lt=0)),
                'no_change': Count('id', filter=Q(position_change=0)),
            }
            
            response.context_data['summary'] = dict(qs.aggregate(**metrics))
            
            # Add chart metadata for better context
            response.context_data['chart_metadata'] = {
                'chart_name': ranking.chart.name,
                'platform_name': ranking.chart.platform.name if ranking.chart.platform else 'Unknown',
                'frequency': ranking.chart.frequency,
                'ranking_date': ranking.ranking_date,
                'total_api_entries': ranking.total_entries,
                'actual_entries': qs.count(),
            }
        
        return response
    
    def get_track_info(self, obj):
        """Display track name and artist in a readable format"""
        if not obj.track:
            return "Unknown Track"
        
        track_name = obj.track.name
        artist_name = obj.track.credit_name if obj.track.credit_name else "Unknown Artist"
        
        return format_html(
            "<strong>{}</strong><br><small>{}</small>", 
            track_name, 
            artist_name
        )
    
    get_track_info.short_description = "Track & Artist"
    get_track_info.allow_tags = True
    
    def get_position_trend(self, obj):
        """Display position trend with appropriate styling"""
        if obj.position_change is None:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">🆕 New</span>'
            )
        elif obj.position_change == 0:
            return format_html(
                '<span style="color: #6c757d;">→ No change</span>'
            )
        elif obj.position_change > 0:
            return format_html(
                '<span style="color: #dc3545;">↑ +{}</span>', 
                obj.position_change
            )
        else:
            return format_html(
                '<span style="color: #007bff;">↓ {}</span>', 
                abs(obj.position_change)
            )
    
    get_position_trend.short_description = "Trend"
    get_position_trend.allow_tags = True
    
    def get_streams(self, obj):
        """Display streams from API data"""
        if obj.api_data and 'metric' in obj.api_data:
            metric = obj.api_data['metric']
            if metric:
                return f"{metric:,}"
        return "N/A"
    
    get_streams.short_description = "Streams"
    
    def has_add_permission(self, request):
        """Entries are managed through the import process"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Entries are read-only"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Entries are managed through the import process"""
        return False


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
            '<a href="{}">View Entries ({})</a>',
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
        """Display entries as a native Django admin table"""
        entries = obj.entries.select_related("track").order_by("position")
        if not entries:
            return "No entries available"

        # Create a link to view entries in the native admin format
        url = reverse("admin:soundcharts_chartrankingentrysummary_changelist") + f"?ranking_id={obj.id}"
        
        return format_html(
            '<div style="margin: 10px 0;">'
            '<a href="{}" class="button">'
            'View Entries in Admin Table ({})</a>'
            '</div>',
            url,
            entries.count()
        )

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
