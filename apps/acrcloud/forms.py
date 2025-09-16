"""
Forms for ACRCloud app
"""
from django import forms
from .models import Song, ACRCloudConfig


class SongUploadForm(forms.ModelForm):
    """Form for uploading songs"""
    
    class Meta:
        model = Song
        fields = ['title', 'artist', 'audio_file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter song title (optional)'
            }),
            'artist': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter artist name (optional)'
            }),
            'audio_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'audio/*'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['audio_file'].required = True
        self.fields['title'].required = False
        self.fields['artist'].required = False
    
    def clean_audio_file(self):
        audio_file = self.cleaned_data.get('audio_file')
        
        if audio_file:
            # Check file size (max 50MB)
            max_size = 50 * 1024 * 1024  # 50MB
            if audio_file.size > max_size:
                raise forms.ValidationError(f'File size must be less than {max_size // (1024 * 1024)}MB')
            
            # Check file extension
            allowed_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.aac']
            file_extension = audio_file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError(f'File type not supported. Allowed types: {", ".join(allowed_extensions)}')
        
        return audio_file


class ACRCloudConfigForm(forms.ModelForm):
    """Form for ACRCloud configuration"""
    
    class Meta:
        model = ACRCloudConfig
        fields = ['name', 'base_url', 'bearer_token', 'container_id', 
                 'identify_host', 'identify_access_key', 'identify_access_secret', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'base_url': forms.URLInput(attrs={'class': 'form-control'}),
            'bearer_token': forms.TextInput(attrs={'class': 'form-control', 'type': 'password'}),
            'container_id': forms.TextInput(attrs={'class': 'form-control'}),
            'identify_host': forms.TextInput(attrs={'class': 'form-control'}),
            'identify_access_key': forms.TextInput(attrs={'class': 'form-control'}),
            'identify_access_secret': forms.TextInput(attrs={'class': 'form-control', 'type': 'password'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def clean_base_url(self):
        base_url = self.cleaned_data.get('base_url')
        if base_url and not base_url.startswith(('http://', 'https://')):
            raise forms.ValidationError('Base URL must start with http:// or https://')
        return base_url
    
    def clean_identify_host(self):
        identify_host = self.cleaned_data.get('identify_host')
        if identify_host and not identify_host.startswith('identify-'):
            raise forms.ValidationError('Identify host must start with "identify-"')
        return identify_host


class SongSearchForm(forms.Form):
    """Form for searching songs"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title, artist, or filename...'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + Song.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values from GET parameters
        if 'search' in self.data:
            self.fields['search'].initial = self.data['search']
        if 'status' in self.data:
            self.fields['status'].initial = self.data['status']
