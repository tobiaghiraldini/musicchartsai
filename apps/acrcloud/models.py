from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
import uuid
import json

User = get_user_model()


class Song(models.Model):
    """Model to store uploaded songs for analysis"""
    
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('analyzed', 'Analyzed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_songs')
    title = models.CharField(max_length=255, blank=True)
    artist = models.CharField(max_length=255, blank=True)
    audio_file = models.FileField(
        upload_to='acrcloud/songs/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['mp3', 'wav', 'm4a', 'flac', 'aac'])]
    )
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text="File size in bytes")
    duration = models.FloatField(null=True, blank=True, help_text="Duration in seconds")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Song"
        verbose_name_plural = "Songs"
    
    def __str__(self):
        return f"{self.title or self.original_filename} - {self.artist or 'Unknown Artist'}"


class Analysis(models.Model):
    """Model to store ACRCloud analysis results"""
    
    ANALYSIS_TYPE_CHOICES = [
        ('fingerprint', 'Fingerprint Analysis'),
        ('cover', 'Cover Detection'),
        ('lyrics', 'Lyrics Analysis'),
        ('full', 'Full Analysis'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='analyses')
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=Song.STATUS_CHOICES, default='processing')
    acrcloud_file_id = models.CharField(max_length=255, null=True, blank=True)
    raw_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Analysis"
        verbose_name_plural = "Analyses"
    
    def __str__(self):
        return f"{self.song.title} - {self.get_analysis_type_display()}"


class AnalysisReport(models.Model):
    """Model to store detailed analysis reports and findings"""
    
    RISK_LEVEL_CHOICES = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    MATCH_TYPE_CHOICES = [
        ('exact', 'Exact Match'),
        ('cover', 'Cover Song'),
        ('similar', 'Similar Song'),
        ('no_match', 'No Match'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.OneToOneField(Analysis, on_delete=models.CASCADE, related_name='report')
    
    # Overall assessment
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='low')
    match_type = models.CharField(max_length=20, choices=MATCH_TYPE_CHOICES, default='no_match')
    confidence_score = models.FloatField(null=True, blank=True, help_text="Overall confidence score (0-100)")
    
    # Fingerprint analysis results
    fingerprint_matches = models.JSONField(default=list, blank=True)
    fingerprint_score = models.FloatField(null=True, blank=True)
    fingerprint_similarity = models.FloatField(null=True, blank=True)
    
    # Cover detection results
    cover_matches = models.JSONField(default=list, blank=True)
    cover_score = models.FloatField(null=True, blank=True)
    cover_similarity = models.FloatField(null=True, blank=True)
    
    # Lyrics analysis results
    lyrics_matches = models.JSONField(default=list, blank=True)
    lyrics_similarity = models.FloatField(null=True, blank=True)
    
    # Additional metadata
    detected_genre = models.CharField(max_length=100, blank=True, null=True)
    detected_language = models.CharField(max_length=10, blank=True, null=True)
    isrc_code = models.CharField(max_length=12, blank=True, null=True)
    
    # Summary and recommendations
    summary = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Analysis Report"
        verbose_name_plural = "Analysis Reports"
    
    def __str__(self):
        return f"Report for {self.analysis.song.title} - {self.get_risk_level_display()}"
    
    def get_primary_match(self):
        """Get the primary match from fingerprint or cover analysis"""
        if self.fingerprint_matches:
            return self.fingerprint_matches[0]
        elif self.cover_matches:
            return self.cover_matches[0]
        return None
    
    def is_fraud_detected(self):
        """Determine if fraud is detected based on analysis results"""
        return (
            self.risk_level in ['high', 'critical'] or
            (self.match_type == 'exact' and self.confidence_score and self.confidence_score > 80) or
            (self.match_type == 'cover' and self.confidence_score and self.confidence_score > 70)
        )


class ACRCloudConfig(models.Model):
    """Model to store ACRCloud API configuration"""
    
    name = models.CharField(max_length=100, unique=True)
    base_url = models.URLField()
    bearer_token = models.CharField(max_length=500)
    container_id = models.CharField(max_length=100)
    identify_host = models.CharField(max_length=100)
    identify_access_key = models.CharField(max_length=100)
    identify_access_secret = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "ACRCloud Configuration"
        verbose_name_plural = "ACRCloud Configurations"
    
    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
