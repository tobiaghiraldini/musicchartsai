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
    readonly_fields = ('name', 'slug', 'type', 'frequency', 'country_code', 'get_chart_link')
    fields = ('name', 'slug', 'type', 'frequency', 'country_code', 'get_chart_link')
    can_delete = False
    max_num = 0
    
    def get_chart_link(self, obj):
        """Display a link to view the chart details"""
        if not obj:
            return "No chart data"
        
        chart_url = reverse('admin:soundcharts_chart_change', args=[obj.id])
        return format_html(
            '<a href="{}" class="button">View Chart</a>',
            chart_url
        )
    
    get_chart_link.short_description = "Actions"
    get_chart_link.allow_tags = True
    
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
