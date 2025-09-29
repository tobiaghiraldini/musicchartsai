from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect
import logging

from ..models import ChartSyncSchedule, ChartSyncExecution, Chart
from ..tasks import sync_chart_rankings_task

logger = logging.getLogger(__name__)


class ChartSyncExecutionInline(admin.TabularInline):
    """Inline admin for chart sync executions"""
    model = ChartSyncExecution
    extra = 0
    readonly_fields = (
        'started_at', 'completed_at', 'duration', 'rankings_created', 
        'rankings_updated', 'tracks_created', 'tracks_updated'
    )
    fields = (
        'status', 'started_at', 'completed_at', 'duration', 
        'rankings_created', 'rankings_updated', 'tracks_created', 
        'tracks_updated', 'error_message'
    )
    
    def duration(self, obj):
        """Display execution duration"""
        if obj.duration:
            return f"{obj.duration:.1f}s"
        return "-"
    duration.short_description = "Duration"
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


class ChartSyncScheduleAdmin(admin.ModelAdmin):
    """Admin interface for chart sync schedules"""
    
    list_display = (
        'chart_name',
        'chart_platform',
        'sync_frequency',
        'is_active',
        'last_sync_at',
        'next_sync_at',
        'success_rate_display',
        'total_executions',
        'is_overdue_display',
        'created_at',
    )
    
    list_filter = (
        'is_active',
        'sync_frequency',
        'chart__platform',
        'created_at',
    )
    
    search_fields = (
        'chart__name',
        'chart__slug',
    )
    
    readonly_fields = (
        'total_executions',
        'successful_executions', 
        'failed_executions',
        'success_rate',
        'is_overdue',
        'created_at',
        'updated_at',
    )
    
    fieldsets = (
        ('Chart Information', {
            'fields': ('chart', 'is_active')
        }),
        ('Sync Configuration', {
            'fields': ('sync_frequency', 'custom_interval_hours')
        }),
        ('Sync Options', {
            'fields': ('sync_immediately', 'sync_historical_data', 'fetch_track_metadata'),
            'description': 'Configure sync behavior and data fetching options'
        }),
        ('Schedule Information', {
            'fields': ('last_sync_at', 'next_sync_at', 'is_overdue')
        }),
        ('Statistics', {
            'fields': (
                'total_executions', 
                'successful_executions', 
                'failed_executions', 
                'success_rate'
            )
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ChartSyncExecutionInline]
    
    actions = ['activate_schedules', 'deactivate_schedules', 'trigger_manual_sync']
    
    def chart_name(self, obj):
        """Display chart name with link"""
        url = reverse('admin:soundcharts_chart_change', args=[obj.chart.id])
        return format_html('<a href="{}">{}</a>', url, obj.chart.name)
    chart_name.short_description = 'Chart'
    chart_name.admin_order_field = 'chart__name'
    
    def chart_platform(self, obj):
        """Display chart platform"""
        return obj.chart.platform.name if obj.chart.platform else '-'
    chart_platform.short_description = 'Platform'
    chart_platform.admin_order_field = 'chart__platform__name'
    
    def success_rate_display(self, obj):
        """Display success rate with color coding"""
        rate = obj.success_rate
        if rate >= 90:
            color = 'green'
        elif rate >= 70:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{}%</span>', 
            color, 
            rate
        )
    success_rate_display.short_description = 'Success Rate'
    success_rate_display.admin_order_field = 'successful_executions'
    
    def is_overdue_display(self, obj):
        """Display overdue status with color coding"""
        if obj.is_overdue:
            return format_html('<span style="color: red;">⚠ Overdue</span>')
        return format_html('<span style="color: green;">✓ On Time</span>')
    is_overdue_display.short_description = 'Status'
    is_overdue_display.admin_order_field = 'next_sync_at'
    
    def success_rate(self, obj):
        """Display success rate as percentage"""
        return f"{obj.success_rate}%"
    
    def is_overdue(self, obj):
        """Display overdue status"""
        return "Yes" if obj.is_overdue else "No"
    
    def activate_schedules(self, request, queryset):
        """Activate selected schedules"""
        count = queryset.update(is_active=True)
        self.message_user(
            request, 
            f"Successfully activated {count} sync schedule(s).",
            messages.SUCCESS
        )
    activate_schedules.short_description = "Activate selected schedules"
    
    def deactivate_schedules(self, request, queryset):
        """Deactivate selected schedules"""
        count = queryset.update(is_active=False)
        self.message_user(
            request, 
            f"Successfully deactivated {count} sync schedule(s).",
            messages.SUCCESS
        )
    deactivate_schedules.short_description = "Deactivate selected schedules"
    
    def trigger_manual_sync(self, request, queryset):
        """Trigger manual sync for selected schedules"""
        count = 0
        for schedule in queryset:
            if schedule.is_active:
                # Create execution record
                execution = ChartSyncExecution.objects.create(
                    schedule=schedule,
                    status='pending'
                )
                
                # Queue the sync task
                task = sync_chart_rankings_task.delay(schedule.id, execution.id)
                execution.celery_task_id = task.id
                execution.status = 'running'
                execution.save()
                
                count += 1
        
        self.message_user(
            request, 
            f"Successfully triggered sync for {count} schedule(s).",
            messages.SUCCESS
        )
    trigger_manual_sync.short_description = "Trigger manual sync"
    
    def get_urls(self):
        """Add custom URLs for sync management"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                'add-chart-to-sync/<int:chart_id>/',
                self.admin_site.admin_view(self.add_chart_to_sync),
                name='soundcharts_chartsyncschedule_add_chart'
            ),
            path(
                'remove-chart-from-sync/<int:chart_id>/',
                self.admin_site.admin_view(self.remove_chart_from_sync),
                name='soundcharts_chartsyncschedule_remove_chart'
            ),
        ]
        return custom_urls + urls
    
    def add_chart_to_sync(self, request, chart_id):
        """Add a chart to sync schedule"""
        try:
            chart = get_object_or_404(Chart, id=chart_id)
            
            # Check if schedule already exists
            schedule, created = ChartSyncSchedule.objects.get_or_create(
                chart=chart,
                defaults={
                    'created_by': request.user,
                    'is_active': True,
                }
            )
            
            if created:
                message = f"Chart '{chart.name}' added to sync schedule."
                messages.success(request, message)
            else:
                message = f"Chart '{chart.name}' is already in sync schedule."
                messages.info(request, message)
                
        except Exception as e:
            logger.error(f"Error adding chart to sync: {e}")
            messages.error(request, f"Error adding chart to sync: {str(e)}")
        
        return redirect('admin:soundcharts_chart_changelist')
    
    def remove_chart_from_sync(self, request, chart_id):
        """Remove a chart from sync schedule"""
        try:
            chart = get_object_or_404(Chart, id=chart_id)
            schedule = ChartSyncSchedule.objects.filter(chart=chart).first()
            
            if schedule:
                schedule.delete()
                message = f"Chart '{chart.name}' removed from sync schedule."
                messages.success(request, message)
            else:
                message = f"Chart '{chart.name}' is not in sync schedule."
                messages.info(request, message)
                
        except Exception as e:
            logger.error(f"Error removing chart from sync: {e}")
            messages.error(request, f"Error removing chart from sync: {str(e)}")
        
        return redirect('admin:soundcharts_chart_changelist')


class ChartSyncExecutionAdmin(admin.ModelAdmin):
    """Admin interface for chart sync executions"""
    
    list_display = (
        'schedule_chart',
        'status',
        'started_at',
        'completed_at',
        'duration_display',
        'rankings_created',
        'rankings_updated',
        'tracks_created',
        'tracks_updated',
    )
    
    list_filter = (
        'status',
        'schedule__chart__platform',
        'started_at',
    )
    
    search_fields = (
        'schedule__chart__name',
        'schedule__chart__slug',
    )
    
    readonly_fields = (
        'schedule',
        'started_at',
        'completed_at',
        'duration',
        'celery_task_id',
        'retry_count',
    )
    
    fieldsets = (
        ('Execution Information', {
            'fields': ('schedule', 'status', 'celery_task_id')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration')
        }),
        ('Results', {
            'fields': (
                'rankings_created', 
                'rankings_updated', 
                'tracks_created', 
                'tracks_updated'
            )
        }),
        ('Error Information', {
            'fields': ('error_message', 'retry_count', 'max_retries'),
            'classes': ('collapse',)
        }),
    )
    
    def schedule_chart(self, obj):
        """Display chart name"""
        return obj.schedule.chart.name
    schedule_chart.short_description = 'Chart'
    schedule_chart.admin_order_field = 'schedule__chart__name'
    
    def duration_display(self, obj):
        """Display execution duration"""
        if obj.duration:
            return f"{obj.duration:.1f}s"
        return "-"
    duration_display.short_description = 'Duration'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
