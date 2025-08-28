from django.db import models


# Create your models here.
class Platform(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Artist(models.Model):
    uuid = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    appUrl = models.CharField(max_length=255)
    imageUrl = models.CharField(max_length=255)
    countryCode = models.CharField(max_length=2)
    cityName = models.CharField(max_length=255, blank=True)
    gender = models.CharField(max_length=255, blank=True)
    type = models.CharField(max_length=255, blank=True)
    birthDate = models.DateField(blank=True, null=True)
    careerStage = models.CharField(max_length=255, blank=True)
    genres = models.ManyToManyField("Genre", related_name="artists")
    biography = models.TextField(blank=True)
    isni = models.CharField(max_length=255, blank=True)
    ipi = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Album(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Track(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.CharField(max_length=255)
    credit_name = models.CharField(max_length=255, blank=True)
    image_url = models.CharField(max_length=255, blank=True)
    
    # Enhanced metadata fields
    slug = models.CharField(max_length=255, blank=True, help_text="Soundcharts track slug")
    release_date = models.DateField(null=True, blank=True, help_text="Track release date")
    duration = models.IntegerField(null=True, blank=True, help_text="Track duration in seconds")
    isrc = models.CharField(max_length=255, null=True, blank=True, help_text="International Standard Recording Code")
    label = models.CharField(max_length=255, null=True, blank=True, help_text="Record label")
    genre = models.CharField(max_length=255, null=True, blank=True, help_text="Primary genre")
    
    # Metadata fetch tracking
    metadata_fetched_at = models.DateTimeField(null=True, blank=True, help_text="When metadata was last fetched")
    audience_fetched_at = models.DateTimeField(null=True, blank=True, help_text="When audience data was last fetched")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.credit_name:
            return f"{self.name} - {self.credit_name}"
        return self.name

    @property
    def display_name(self):
        """Returns a display name with artist for inline views"""
        if self.credit_name:
            return f"{self.name} - {self.credit_name}"
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Venue(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Chart(models.Model):
    name = models.CharField(max_length=255)
    # uuid = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, default="")
    type = models.CharField(max_length=100, default="song")
    frequency = models.CharField(max_length=100, default="weekly")
    country_code = models.CharField(max_length=2, default="IT")
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, null=True)
    web_url = models.CharField(max_length=255, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.platform.name} - {self.frequency} - ({self.country_code})"


class Radio(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    city_name = models.CharField(max_length=255)
    country_code = models.CharField(max_length=255)
    country_name = models.CharField(max_length=255)
    time_zone = models.CharField(max_length=255)
    reach = models.IntegerField()
    first_aired_at = models.DateTimeField()
    image_url = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ChartRanking(models.Model):
    """
    Stores a complete ranking snapshot for a specific chart and date
    """

    chart = models.ForeignKey(Chart, on_delete=models.SET_NULL, related_name="rankings", null=True)
    ranking_date = models.DateTimeField(
        help_text="Date when this ranking was published"
    )
    fetched_at = models.DateTimeField(
        auto_now_add=True, help_text="When this ranking was fetched from API"
    )

    # Metadata from API
    total_entries = models.IntegerField(
        default=0, help_text="Total number of entries in this ranking"
    )

    # API response metadata
    api_version = models.CharField(
        max_length=50, blank=True, help_text="API version used"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["chart", "ranking_date"], name="unique_chart_ranking_date"
            )
        ]
        ordering = ["-ranking_date"]
        verbose_name = "Chart Ranking"
        verbose_name_plural = "Chart Rankings"

    def __str__(self):
        return f"{self.chart.name} - {self.ranking_date.strftime('%Y-%m-%d %H:%M')}"

    @property
    def entries_count(self):
        return self.entries.count()


class ChartRankingEntry(models.Model):
    """
    Stores individual song entries within a chart ranking
    """

    ranking = models.ForeignKey(
        ChartRanking, on_delete=models.SET_NULL, related_name="entries", null=True
    )
    track = models.ForeignKey(
        Track, on_delete=models.CASCADE, related_name="song_rankings"
    )

    # Position information
    position = models.IntegerField(help_text="Current position in the chart")
    previous_position = models.IntegerField(
        null=True, blank=True, help_text="Previous position (if available)"
    )
    position_change = models.IntegerField(
        null=True, blank=True, help_text="Position change from previous ranking"
    )
    weeks_on_chart = models.IntegerField(
        null=True, blank=True, help_text="Number of weeks on chart"
    )

    # # Track information
    # track_name = models.CharField(max_length=500, help_text="Name of the track")
    # track_uuid = models.CharField(
    #     max_length=255, blank=True, help_text="Soundcharts track UUID"
    # )
    # track_slug = models.CharField(
    #     max_length=255, blank=True, help_text="Soundcharts track slug"
    # )

    # # Artist information
    # artist_name = models.CharField(max_length=500, help_text="Name of the artist")
    # artist_uuid = models.CharField(
    #     max_length=255, blank=True, help_text="Soundcharts artist UUID"
    # )
    # artist_slug = models.CharField(
    #     max_length=255, blank=True, help_text="Soundcharts artist slug"
    # )

    # # Album information (if available)
    # album_name = models.CharField(
    #     max_length=500, blank=True, help_text="Name of the album"
    # )
    # album_uuid = models.CharField(
    #     max_length=255, blank=True, help_text="Soundcharts album UUID"
    # )
    # album_slug = models.CharField(
    #     max_length=255, blank=True, help_text="Soundcharts album slug"
    # )

    # # Metrics and performance data
    # streams = models.BigIntegerField(null=True, blank=True, help_text="Stream count")
    # views = models.BigIntegerField(null=True, blank=True, help_text="View count")
    # sales = models.BigIntegerField(null=True, blank=True, help_text="Sales count")
    # airplay = models.IntegerField(null=True, blank=True, help_text="Airplay count")

    # # Additional metadata
    # label = models.CharField(max_length=255, blank=True, help_text="Record label")
    # genre = models.CharField(max_length=255, blank=True, help_text="Genre")
    # country_code = models.CharField(max_length=2, blank=True, help_text="Country code")

    # API metadata
    api_data = models.JSONField(
        default=dict, help_text="Raw API response data for this entry"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ranking", "position"], name="unique_ranking_position"
            )
        ]
        ordering = ["position"]
        verbose_name = "Chart Ranking Entry"
        verbose_name_plural = "Chart Ranking Entries"

    def __str__(self):
        track_info = f"#{self.position} - {self.track.name}"
        if self.track.credit_name:
            track_info += f" ({self.track.credit_name})"

        # Add position trend info
        if self.position_change is not None:
            if self.position_change > 0:
                track_info += f" ↑+{self.position_change}"
            elif self.position_change < 0:
                track_info += f" ↓{self.position_change}"
            else:
                track_info += " →"

        # Add weeks on chart info
        if self.weeks_on_chart:
            track_info += f" ({self.weeks_on_chart}w)"

        return track_info

    @property
    def position_trend(self):
        """Returns a string representation of position trend"""
        if self.position_change is None:
            return "New"
        elif self.position_change == 0:
            return "No change"
        elif self.position_change > 0:
            return f"↑ +{self.position_change}"
        else:
            return f"↓ {self.position_change}"

    @property
    def metric_display(self):
        """Returns formatted metric (stream count) from API data"""
        if self.api_data and "metric" in self.api_data:
            metric = self.api_data["metric"]
            if metric:
                return f"{metric:,}"
        return "N/A"

    @property
    def short_trend(self):
        """Returns a short position trend for inline display"""
        if self.position_change is None:
            return "New"
        elif self.position_change == 0:
            return "→"
        elif self.position_change > 0:
            return f"↑+{self.position_change}"
        else:
            return f"↓{abs(self.position_change)}"


class TrackAudience(models.Model):
    """
    Stores audience and demographic data for tracks from Soundcharts API
    """
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name="audience_data")
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, help_text="Platform for this audience data")
    
    # Audience metrics
    total_listeners = models.BigIntegerField(null=True, blank=True, help_text="Total number of listeners")
    unique_listeners = models.BigIntegerField(null=True, blank=True, help_text="Unique listeners")
    repeat_listeners = models.BigIntegerField(null=True, blank=True, help_text="Repeat listeners")
    
    # Demographic data
    age_13_17 = models.IntegerField(null=True, blank=True, help_text="Listeners aged 13-17")
    age_18_24 = models.IntegerField(null=True, blank=True, help_text="Listeners aged 18-24")
    age_25_34 = models.IntegerField(null=True, blank=True, help_text="Listeners aged 25-34")
    age_35_44 = models.IntegerField(null=True, blank=True, help_text="Listeners aged 35-44")
    age_45_54 = models.IntegerField(null=True, blank=True, help_text="Listeners aged 45-54")
    age_55_64 = models.IntegerField(null=True, blank=True, help_text="Listeners aged 55-64")
    age_65_plus = models.IntegerField(null=True, blank=True, help_text="Listeners aged 65+")
    
    # Geographic data
    top_countries = models.JSONField(default=list, help_text="Top countries by listeners")
    top_cities = models.JSONField(default=list, help_text="Top cities by listeners")
    
    # Raw API data
    api_data = models.JSONField(default=dict, help_text="Raw API response data")
    
    # Metadata
    fetched_at = models.DateTimeField(auto_now_add=True, help_text="When this data was fetched")
    
    class Meta:
        unique_together = ['track', 'platform']
        ordering = ['-fetched_at']
        verbose_name = "Track Audience"
        verbose_name_plural = "Track Audiences"
    
    def __str__(self):
        return f"{self.track.name} - {self.platform.name} - {self.fetched_at.strftime('%Y-%m-%d')}"


class MetadataFetchTask(models.Model):
    """
    Tracks the status of metadata fetching tasks
    """
    TASK_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    TASK_TYPE_CHOICES = [
        ('metadata', 'Track Metadata'),
        ('audience', 'Track Audience'),
        ('bulk_metadata', 'Bulk Metadata'),
        ('bulk_audience', 'Bulk Audience'),
    ]
    
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='pending')
    
    # Task details
    track_uuids = models.JSONField(default=list, help_text="List of track UUIDs to process")
    total_tracks = models.IntegerField(default=0, help_text="Total number of tracks to process")
    processed_tracks = models.IntegerField(default=0, help_text="Number of tracks processed")
    successful_tracks = models.IntegerField(default=0, help_text="Number of tracks successfully processed")
    failed_tracks = models.IntegerField(default=0, help_text="Number of tracks that failed")
    
    # Celery task info
    celery_task_id = models.CharField(max_length=255, blank=True, help_text="Celery task ID")
    
    # Error handling
    error_message = models.TextField(blank=True, help_text="Error message if task failed")
    retry_count = models.IntegerField(default=0, help_text="Number of retry attempts")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Metadata Fetch Task"
        verbose_name_plural = "Metadata Fetch Tasks"
    
    def __str__(self):
        return f"{self.get_task_type_display()} - {self.status} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def progress_percentage(self):
        """Returns progress as a percentage"""
        if self.total_tracks == 0:
            return 0
        return int((self.processed_tracks / self.total_tracks) * 100)


class ChartRankingEntrySummary(ChartRankingEntry):
    """
    Proxy model for displaying chart ranking entries in a native admin table format
    """
    class Meta:
        proxy = True
        verbose_name = 'Chart Entry Summary'
        verbose_name_plural = 'Chart Entries Summary'
