from django.contrib import admin
from ..models import Venue
from .soundcharts_admin_mixin import SoundchartsAdminMixin


class VenueAdmin(SoundchartsAdminMixin, admin.ModelAdmin):
    list_display = ("name", "uuid", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "uuid")
    ordering = ("name",)
    readonly_fields = ("uuid",)
