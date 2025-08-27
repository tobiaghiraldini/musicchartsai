from django.contrib import admin
from ..models import Track
from .soundcharts_admin_mixin import SoundchartsAdminMixin


class TrackAdmin(SoundchartsAdminMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "uuid",
        "credit_name",
        "image_url",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "uuid", "credit_name")
    ordering = ("name",)
    readonly_fields = ("uuid",)
