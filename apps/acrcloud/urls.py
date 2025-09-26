from django.urls import path
from .views import (
    UploadAudioView,
    ViewAudiosView,
    SongDetailView,
    AnalysisReportView,
    PatternMatchingReportView,
    FilePondUploadView,
    RetryAnalysisView,
    DeleteSongView,
    AnalysisStatusView,
    ACRCloudWebhookView,
    TestUploadView,
)

app_name = "acrcloud"

urlpatterns = [
    # Main views
    path("upload/", UploadAudioView.as_view(), name="upload_audio"),
    path("songs/", ViewAudiosView.as_view(), name="view_audios"),
    path("song/<uuid:song_id>/", SongDetailView.as_view(), name="song_detail"),
    path("analysis/<uuid:analysis_id>/", AnalysisReportView.as_view(), name="analysis_report"),
    path("analysis/<uuid:analysis_id>/pattern-matching/", PatternMatchingReportView.as_view(), name="pattern_matching_report"),
    
    # API endpoints
    path("api/upload/", FilePondUploadView.as_view(), name="filepond_upload"),
    path("api/test-upload/", TestUploadView.as_view(), name="test_upload"),
    path("api/song/<uuid:song_id>/status/", AnalysisStatusView.as_view(), name="analysis_status"),
    
    # Webhook endpoints
    path("webhook/file-scanning/", ACRCloudWebhookView.as_view(), name="acrcloud_webhook"),
    
    # Actions
    path("song/<uuid:song_id>/retry/", RetryAnalysisView.as_view(), name="retry_analysis"),
    path("song/<uuid:song_id>/delete/", DeleteSongView.as_view(), name="delete_song"),
]