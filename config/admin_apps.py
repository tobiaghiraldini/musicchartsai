"""
Custom AdminConfig implementation.

This module provides a custom AdminConfig class that applies custom ordering
to the default Django AdminSite by overriding the get_app_list method.
"""


from django.contrib.admin.apps import AdminConfig as DjangoAdminConfig
from django.contrib.admin.sites import site as default_admin_site


class AdminConfig(DjangoAdminConfig):
    """
    Custom AdminConfig that applies custom ordering to the default admin site.
    
    This class extends Django's AdminConfig and overrides the get_app_list
    method to provide custom ordering for apps and models.
    """
    
    def ready(self):
        """
        Apply custom ordering to the admin site when the app is ready.
        """
        super().ready()
        
        # Store the original get_app_list method
        original_get_app_list = default_admin_site.get_app_list
        
        def custom_get_app_list(request):
            """
            Return a sorted list of all the installed apps that have been
            registered in this site with custom ordering.
            
            Args:
                request: The HTTP request object
                
            Returns:
                list: Sorted list of apps with custom ordering
            """
            # Define custom ordering for apps
            app_ordering = {
                "Pages": 1,
                "Users": 2,
                "Tasks": 3,
                "Soundcharts": 5,
                "ACR Cloud": 5,
                "Charts": 6,
                "Dynamic DataTables": 7,
                "Dynamic API": 8,
                "Authentication and Authorization": 1,
                "Celery Results": 3,
                "Auth Token": 4,
            }
            
            # Define custom ordering for models within each app
            model_ordering = {
                # Pages app models
                "Pages": 2,
                # Users app models
                "Groups": 1,
                "Users": 1,
                "User profiles": 2,
                # Tasks app models
                "Tasks": 3,
                # # Charts app models
                # "Charts": 1,
                # "Chart entries": 2,
                # Soundcharts app models
                "Artists": 5,
                "Tracks": 6,
                "Albums": 7,
                "Genres": 8,
                "Platforms": 1,
                "Charts": 2,
                "Chart rankings": 3,
                "Chart ranking entries": 4,
                "Venues": 9,
                "Metadata fetch tasks": 10,
                "Task results": 2,
                # ACR Cloud app models
                "ACR Cloud": 1,
                "ACR Cloud results": 2,
                # Dynamic DataTables app models
                "Dynamic DataTables": 1,
                "Dynamic DataTable entries": 2,
                # Dynamic API app models
                "Dynamic API": 1,
                "Dynamic API endpoints": 2,
                # Django built-in models
                # "Groups": 1,
                # "Users": 2,
                "Content types": 3,
                "Sessions": 4,
                "Sites": 5,
                "Log entries": 6,
            }
            
            app_dict = default_admin_site._build_app_dict(request)
            
            # Sort the apps by custom ordering
            app_list = sorted(
                app_dict.values(), 
                key=lambda x: app_ordering.get(x['name'], 999)
            )
            
            # Sort the models within each app by custom ordering
            for app in app_list:
                app['models'].sort(
                    key=lambda x: model_ordering.get(x['name'], 999)
                )
            
            return app_list
        
        # Apply the custom get_app_list method
        default_admin_site.get_app_list = custom_get_app_list
