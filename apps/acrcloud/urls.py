from django.urls import path
from .views import (
    UploadAudioView,
    ViewAudiosView,
)

app_name = "acrcloud"

urlpatterns = [
    path("upload_audio/", UploadAudioView.as_view(), name="upload_audio"),
    path("view_audios/", ViewAudiosView.as_view(), name="view_audios"),
]