from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from ..models import MetadataFetchTask


class MetadataFetchTaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'task_type',
        'status',
        'total_tracks',
        'processed_tracks',
        'successful_tracks',
        'failed_tracks',
        'progress_bar',
        'created_at',
        'started_at',
        'completed_at',
    )
    list_filter = ('task_type', 'status', 'created_at')
    readonly_fields = (
        'id',
        'created_at',
        'started_at',
        'completed_at',
        'progress_percentage',
        'celery_task_id',
    )
    search_fields = ('celery_task_id',)
    ordering = ('-created_at',)
    
    fieldsets = (
        (
            'Task Information',
            {
                'fields': (
                    'id',
                    'task_type',
                    'status',
                    'celery_task_id',
                )
            },
        ),
        (
            'Progress',
            {
                'fields': (
                    'total_tracks',
                    'processed_tracks',
                    'successful_tracks',
                    'failed_tracks',
                    'progress_percentage',
                )
            },
        ),
        (
            'Timestamps',
            {
                'fields': (
                    'created_at',
                    'started_at',
                    'completed_at',
                )
            },
        ),
        (
            'Error Handling',
            {
                'fields': (
                    'error_message',
                    'retry_count',
                ),
                'classes': ('collapse',),
            },
        ),
        (
            'Track UUIDs',
            {
                'fields': ('track_uuids',),
                'classes': ('collapse',),
            },
        ),
    )
    
    def progress_bar(self, obj):
        """Display a visual progress bar"""
        if obj.total_tracks == 0:
            return "0%"
        
        percentage = obj.progress_percentage
        color = "green" if percentage == 100 else "orange" if percentage > 50 else "red"
        
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; height: 20px; background-color: {}; border-radius: 3px; '
            'display: flex; align-items: center; justify-content: center; color: white; '
            'font-size: 12px; font-weight: bold;">{}%</div></div>',
            percentage, color, percentage
        )
    
    progress_bar.short_description = "Progress"
    progress_bar.allow_tags = True
    
    def has_add_permission(self, request):
        """Tasks are created programmatically"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Tasks are read-only"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup"""
        return True
