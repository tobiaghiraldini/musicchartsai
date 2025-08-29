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
        
        # Override the default admin site's get_app_list method to customize app ordering
        original_get_app_list = admin.site.get_app_list
        
        def custom_get_app_list(request):
            app_list = original_get_app_list(request)
            
            # Define the desired app order
            app_order = [
                'authentication and authorization',
                'users',
                'soundcharts',
                'acr',
            ]
            
            # Create a mapping of app names to their desired order
            order_mapping = {app_name: index for index, app_name in enumerate(app_order)}
            
            # Sort the app list based on the defined order
            # Apps not in the order list will appear at the end
            app_list.sort(key=lambda x: order_mapping.get(x['name'].lower(), len(app_order)))
            
            return app_list
        
        # Replace the default admin site's get_app_list method
        admin.site.get_app_list = custom_get_app_list
