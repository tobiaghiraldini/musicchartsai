from django.apps import AppConfig
from django.contrib import admin


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"

    def ready(self):
        # Customize admin site appearance
        admin.site.site_header = "Music Charts AI Admin"
        admin.site.site_title = "Music Charts AI Admin"
        admin.site.index_title = "Music Charts AI Admin"
