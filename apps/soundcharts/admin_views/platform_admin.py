from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Count, Q
from .soundcharts_admin_mixin import SoundchartsAdminMixin
from ..models import Chart, ChartRanking


class PlatformChartsInline(admin.TabularInline):
    """
    Custom inline view for displaying related charts in a nice table format
    """
    model = Chart
    extra = 0
    readonly_fields = ('get_chart_info', 'get_chart_stats', 'get_chart_actions')
    fields = ('get_chart_info', 'get_chart_stats', 'get_chart_actions')
    can_delete = False
    max_num = 0
    template = 'admin/soundcharts/platform/charts_inline.html'
    
    def get_chart_info(self, obj):
        """Display chart name and basic info"""
        if not obj:
            return "No chart data"
        
        chart_url = reverse('admin:soundcharts_chart_change', args=[obj.id])
        chart_name = obj.name or "Unnamed Chart"
        chart_type = obj.type or "Unknown"
        frequency = obj.frequency or "Unknown"
        country = obj.country_code or "Unknown"
        
        return format_html(
            '<div class="chart-info">'
            '<div class="chart-name"><a href="{}">{}</a></div>'
            '<div class="chart-meta">Type: {} | Frequency: {} | Country: {}</div>'
            '</div>',
            chart_url, chart_name, chart_type, frequency, country
        )
    
    get_chart_info.short_description = "Chart Information"
    get_chart_info.allow_tags = True
    
    def get_chart_stats(self, obj):
        """Display chart statistics"""
        if not obj:
            return "No data"
        
        # Get ranking statistics
        rankings = obj.rankings.all()
        total_rankings = rankings.count()
        
        # Get latest ranking date
        latest_ranking = rankings.order_by('-ranking_date').first()
        latest_date = latest_ranking.ranking_date.strftime('%Y-%m-%d') if latest_ranking else "Never"
        
        # Get total entries across all rankings
        total_entries = sum(ranking.total_entries for ranking in rankings)
        
        return format_html(
            '<div class="chart-stats">'
            '<div class="stat-item"><strong>Rankings:</strong> {}</div>'
            '<div class="stat-item"><strong>Latest:</strong> {}</div>'
            '<div class="stat-item"><strong>Total Entries:</strong> {:,}</div>'
            '</div>',
            total_rankings, latest_date, total_entries
        )
    
    get_chart_stats.short_description = "Statistics"
    get_chart_stats.allow_tags = True
    
    def get_chart_actions(self, obj):
        """Display action buttons for the chart"""
        if not obj:
            return "No actions"
        
        chart_url = reverse('admin:soundcharts_chart_change', args=[obj.id])
        rankings_url = reverse('admin:soundcharts_chartranking_changelist') + f'?chart__id__exact={obj.id}'
        
        return format_html(
            '<div class="chart-actions">'
            '<a href="{}" class="button">View Chart</a> '
            '<a href="{}" class="button secondary">View Rankings</a>'
            '</div>',
            chart_url, rankings_url
        )
    
    get_chart_actions.short_description = "Actions"
    get_chart_actions.allow_tags = True
    
    def has_add_permission(self, request, obj=None):
        """Charts are managed through the import process"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Charts are read-only in this view"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Charts are managed through the import process"""
        return False


class PlatformAdmin(SoundchartsAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "slug")
    ordering = ("name",)
    
    # Add the custom inline for charts
    inlines = [PlatformChartsInline]
    
    fieldsets = (
        (
            "Platform Information",
            {"fields": ("name", "slug")},
        ),
        (
            "Related Charts",
            {
                "description": "Charts associated with this platform",
                "fields": (),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    
    readonly_fields = ("created_at", "updated_at")
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Override change view to add import charts button"""
        extra_context = extra_context or {}
        
        # Get the platform object
        platform = self.get_object(request, object_id)
        if platform:
            # Add context for the import charts button
            extra_context.update({
                'show_import_charts_button': True,
                'platform_slug': platform.slug,
                'import_charts_url': reverse('admin:soundcharts_chart_import'),
            })
        
        return super().change_view(request, object_id, form_url, extra_context)
