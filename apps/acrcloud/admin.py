from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Song, Analysis, AnalysisReport, ACRCloudConfig


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ['title', 'artist', 'user', 'status', 'file_size_mb', 'duration', 'created_at']
    list_filter = ['status', 'created_at', 'user']
    search_fields = ['title', 'artist', 'original_filename', 'user__username']
    readonly_fields = ['id', 'file_size', 'created_at', 'updated_at']
    raw_id_fields = ['user']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'title', 'artist', 'original_filename')
        }),
        ('File Information', {
            'fields': ('audio_file', 'file_size', 'duration', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_mb(self, obj):
        return f"{obj.file_size / (1024 * 1024):.2f} MB"
    file_size_mb.short_description = 'File Size (MB)'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ['song_title', 'analysis_type', 'status', 'acrcloud_file_id', 'created_at']
    list_filter = ['analysis_type', 'status', 'created_at']
    search_fields = ['song__title', 'song__artist', 'acrcloud_file_id']
    readonly_fields = ['id', 'created_at', 'completed_at', 'raw_response_preview']
    raw_id_fields = ['song']
    
    fieldsets = (
        ('Analysis Information', {
            'fields': ('id', 'song', 'analysis_type', 'status', 'acrcloud_file_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at')
        }),
        ('Raw Response', {
            'fields': ('raw_response_preview',),
            'classes': ('collapse',)
        }),
    )
    
    def song_title(self, obj):
        return obj.song.title or obj.song.original_filename
    song_title.short_description = 'Song Title'
    
    def raw_response_preview(self, obj):
        if obj.raw_response:
            return format_html(
                '<pre style="max-height: 200px; overflow-y: auto;">{}</pre>',
                str(obj.raw_response)[:1000] + ('...' if len(str(obj.raw_response)) > 1000 else '')
            )
        return '-'
    raw_response_preview.short_description = 'Raw Response Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('song', 'song__user')


@admin.register(AnalysisReport)
class AnalysisReportAdmin(admin.ModelAdmin):
    list_display = ['song_title', 'risk_level', 'match_type', 'confidence_score', 'fraud_detected', 'created_at']
    list_filter = ['risk_level', 'match_type', 'created_at']
    search_fields = ['analysis__song__title', 'analysis__song__artist']
    readonly_fields = ['id', 'created_at', 'updated_at', 'fraud_detected']
    raw_id_fields = ['analysis']
    
    fieldsets = (
        ('Report Overview', {
            'fields': ('id', 'analysis', 'risk_level', 'match_type', 'confidence_score', 'fraud_detected')
        }),
        ('Fingerprint Analysis', {
            'fields': ('fingerprint_score', 'fingerprint_similarity', 'fingerprint_matches'),
            'classes': ('collapse',)
        }),
        ('Cover Detection', {
            'fields': ('cover_score', 'cover_similarity', 'cover_matches'),
            'classes': ('collapse',)
        }),
        ('Lyrics Analysis', {
            'fields': ('lyrics_similarity', 'lyrics_matches'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('detected_genre', 'detected_language', 'isrc_code'),
            'classes': ('collapse',)
        }),
        ('Summary', {
            'fields': ('summary', 'recommendations')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def song_title(self, obj):
        return obj.analysis.song.title or obj.analysis.song.original_filename
    song_title.short_description = 'Song Title'
    
    def fraud_detected(self, obj):
        return obj.is_fraud_detected()
    fraud_detected.boolean = True
    fraud_detected.short_description = 'Fraud Detected'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('analysis', 'analysis__song', 'analysis__song__user')


@admin.register(ACRCloudConfig)
class ACRCloudConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'base_url', 'container_id', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'base_url', 'container_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Configuration', {
            'fields': ('name', 'is_active')
        }),
        ('API Endpoints', {
            'fields': ('base_url', 'container_id', 'identify_host')
        }),
        ('Authentication', {
            'fields': ('bearer_token', 'identify_access_key', 'identify_access_secret'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request)


# Customize admin site headers
admin.site.site_header = "ACRCloud Music Analysis Admin"
admin.site.site_title = "ACRCloud Admin"
admin.site.index_title = "Music Analysis Management"
