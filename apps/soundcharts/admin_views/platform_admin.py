from django.contrib import admin
from .soundcharts_admin_mixin import SoundchartsAdminMixin


class PlatformAdmin(SoundchartsAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "slug")
    ordering = ("name",)
