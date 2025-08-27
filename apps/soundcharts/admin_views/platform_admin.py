from django.contrib import admin
from django.urls import reverse
from .soundcharts_admin_mixin import SoundchartsAdminMixin


class PlatformAdmin(SoundchartsAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "slug")
    ordering = ("name",)
    
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
