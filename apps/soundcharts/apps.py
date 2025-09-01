from django.apps import AppConfig
from django.contrib import admin


class SoundchartsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.soundcharts'
    verbose_name = 'Soundcharts'

    def ready(self):
        # Customize admin site appearance
        admin.site.site_header = "Soundcharts Admin"
        admin.site.site_title = "Soundcharts Admin"
        admin.site.index_title = "Soundcharts Admin"
        
        # Note: Removed the problematic get_app_list override
        # The admin site will use its default app ordering
