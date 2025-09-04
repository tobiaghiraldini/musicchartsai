from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

# Create your views here.
@method_decorator(login_required, name='dispatch')
class UploadAudioView(View):
    """
    View for uploading audio files
    """
    def get(self, request):
        return render(request, 'acrcloud/upload_audio.html')

@method_decorator(login_required, name='dispatch')
class ViewAudiosView(View):
    """
    View for viewing audio files
    """
    def get(self, request):
        return render(request, 'acrcloud/view_audios.html')