from django.contrib import admin
from apps.soundcharts.admin_views.soundcharts_admin_mixin import SoundchartsAdminMixin


class TrackAudienceAdmin(SoundchartsAdminMixin, admin.ModelAdmin):
    list_display = ("track", "platform", "date", "audience_value")
    list_filter = ("platform", "date")
    search_fields = ("track__name", "platform__name")
    ordering = ("-date",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("track", "platform")

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return super().change_view(request, object_id, form_url, extra_context)