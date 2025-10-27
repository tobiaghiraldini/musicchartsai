from django.db import models


import logging

logger = logging.getLogger(__name__)


class Platform(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=True)
    
    # Enhanced platform metadata
    platform_type = models.CharField(max_length=50, choices=[
        ('audience', 'Audience'),
        ('streaming', 'Streaming'),
        ('song_chart', 'Song Chart'),
        ('artist_chart', 'Artist Chart'),
        ('album_chart', 'Album Chart'),
        ('playlist', 'Playlist'),
        ('radio', 'Radio'),
        ('other', 'Other'),
    ], default='streaming', help_text="Type of platform")
    
    audience_metric_name = models.CharField(max_length=100, default="Listeners", 
                                         help_text="Name of the audience metric (e.g., 'Listeners', 'Followers')")
    
    # Platform identification
    platform_identifier = models.CharField(max_length=255, blank=True, 
                                        help_text="Platform-specific identifier (e.g., 'spotify', 'apple_music')")
    
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
    
    # Metadata fetch tracking
    metadata_fetched_at = models.DateTimeField(null=True, blank=True, help_text="When metadata was last fetched")
    audience_fetched_at = models.DateTimeField(null=True, blank=True, help_text="When audience data was last fetched")
    
    # ACRCloud specific fields
    acrcloud_id = models.CharField(max_length=255, blank=True, help_text="ACRCloud artist identifier")
    musicbrainz_id = models.CharField(max_length=255, blank=True, help_text="MusicBrainz artist ID")
    
    # Platform-specific IDs
    platform_ids = models.JSONField(default=dict, blank=True, help_text="Platform-specific artist IDs")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    @classmethod
    def create_from_soundcharts(cls, artist_data):
        """
        Creates or updates artist from SoundCharts API data
        artist_data format: {
            "uuid": "11e81bcc-9c1c-ce38-b96b-a0369fe50396",
            "slug": "billie-eilish",
            "name": "Billie Eilish",
            "appUrl": "https://app.soundcharts.com/app/artist/billie-eilish/overview",
            "imageUrl": "https://assets.soundcharts.com/artist/c/1/c/11e81bcc-9c1c-ce38-b96b-a0369fe50396.jpg"
        }
        """
        uuid = artist_data.get('uuid', '').strip()
        name = artist_data.get('name', '').strip()
        slug = artist_data.get('slug', '').strip()
        app_url = artist_data.get('appUrl', '').strip()
        image_url = artist_data.get('imageUrl', '').strip()
        
        if not uuid or not name:
            return None
        
        # Create or get artist by UUID (most reliable identifier)
        artist, created = cls.objects.get_or_create(
            uuid=uuid,
            defaults={
                'name': name,
                'slug': slug,
                'appUrl': app_url,
                'imageUrl': image_url,
                'countryCode': '',  # Will be updated if available
                'cityName': '',
                'gender': '',
                'type': '',
                'biography': '',
                'isni': '',
                'ipi': '',
            }
        )
        
        # Update fields if artist already exists
        if not created:
            artist.name = name
            artist.slug = slug
            artist.appUrl = app_url
            artist.imageUrl = image_url
            artist.save()
        
        return artist


class Album(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.CharField(max_length=255)
    
    # ACRCloud specific fields
    acrcloud_id = models.CharField(max_length=255, blank=True, help_text="ACRCloud album identifier")
    musicbrainz_id = models.CharField(max_length=255, blank=True, help_text="MusicBrainz album ID")
    
    # Platform-specific IDs
    platform_ids = models.JSONField(default=dict, blank=True, help_text="Platform-specific album IDs")
    
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
    
    # Genre relationships
    genres = models.ManyToManyField("Genre", related_name="tracks", blank=True, help_text="Track genres")
    primary_genre = models.ForeignKey(
        "Genre", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="primary_tracks",
        help_text="Primary genre for this track"
    )
    
    # Artist relationships
    artists = models.ManyToManyField("Artist", related_name="tracks", blank=True, help_text="Track artists")
    primary_artist = models.ForeignKey(
        "Artist", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="primary_tracks",
        help_text="Primary artist for this track"
    )
    
    # Metadata fetch tracking
    metadata_fetched_at = models.DateTimeField(null=True, blank=True, help_text="When metadata was last fetched")
    audience_fetched_at = models.DateTimeField(null=True, blank=True, help_text="When audience data was last fetched")
    
    # ACRCloud specific fields
    acrcloud_id = models.CharField(max_length=255, blank=True, help_text="ACRCloud track identifier")
    acrcloud_score = models.IntegerField(null=True, blank=True, help_text="ACRCloud confidence score")
    acrcloud_analyzed_at = models.DateTimeField(null=True, blank=True, help_text="When ACRCloud analysis was performed")
    
    # Enhanced external IDs
    upc = models.CharField(max_length=255, blank=True, help_text="Universal Product Code")
    musicbrainz_id = models.CharField(max_length=255, blank=True, help_text="MusicBrainz track ID")
    
    # Platform-specific IDs (stored as JSON for flexibility)
    platform_ids = models.JSONField(default=dict, blank=True, help_text="Platform-specific track IDs")
    
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
    
    def get_audience_chart_data(self, platform, start_date=None, end_date=None, limit=None):
        """Get audience chart data for this track on a specific platform"""
        from .models import TrackAudienceTimeSeries
        return TrackAudienceTimeSeries.get_chart_data(self, platform, start_date, end_date, limit)
    
    def get_platform_audience_comparison(self, platforms, start_date=None, end_date=None, limit=None):
        """Get audience comparison data across multiple platforms"""
        from .models import TrackAudienceTimeSeries
        return TrackAudienceTimeSeries.get_platform_comparison(self, platforms, start_date, end_date, limit)


class Genre(models.Model):
    """
    Hierarchical genre model that supports root/sub relationships from SoundCharts API
    """
    name = models.CharField(max_length=255, help_text="Genre name (e.g., 'alternative', 'electronic')")
    slug = models.SlugField(max_length=255, unique=True, help_text="URL-friendly genre identifier")
    uuid = models.CharField(max_length=255, blank=True, help_text="SoundCharts genre UUID if available")
    
    # Hierarchical relationships
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subgenres',
        help_text="Parent genre (root genre). Null for root genres."
    )
    
    # Genre metadata
    level = models.IntegerField(default=0, help_text="Hierarchy level (0=root, 1=sub)")
    description = models.TextField(blank=True, help_text="Optional genre description")
    
    # SoundCharts specific data
    soundcharts_root = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Original root genre name from SoundCharts API"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level', 'name']
        verbose_name = "Genre"
        verbose_name_plural = "Genres"
        indexes = [
            models.Index(fields=['parent', 'level']),
            models.Index(fields=['slug']),
            models.Index(fields=['soundcharts_root']),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    @property
    def full_path(self):
        """Returns the full genre path (e.g., 'Electronic > House')"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name
    
    @property
    def is_root(self):
        """Returns True if this is a root genre"""
        return self.parent is None
    
    @property
    def is_subgenre(self):
        """Returns True if this is a subgenre"""
        return self.parent is not None
    
    def get_all_subgenres(self):
        """Returns all subgenres recursively"""
        subgenres = list(self.subgenres.all())
        for subgenre in self.subgenres.all():
            subgenres.extend(subgenre.get_all_subgenres())
        return subgenres
    
    @classmethod
    def get_root_genres(cls):
        """Returns all root genres"""
        return cls.objects.filter(parent__isnull=True)
    
    @classmethod
    def create_from_soundcharts(cls, genre_data):
        """
        Creates or updates genre structure from SoundCharts API data
        genre_data format: {"root": "electronic", "sub": ["house", "techno"]}
        """
        root_name = genre_data.get('root', '').strip()
        sub_names = genre_data.get('sub', [])
        
        if not root_name:
            return None
        
        # Create or get root genre
        root_genre, created = cls.objects.get_or_create(
            name=root_name,
            parent__isnull=True,  # Ensure it's a root genre
            defaults={
                'slug': cls._generate_unique_slug(root_name),
                'level': 0,
                'soundcharts_root': root_name,
            }
        )
        
        # Create subgenres (filter out duplicates with root name)
        subgenres = []
        for sub_name in sub_names:
            sub_name = sub_name.strip()
            if sub_name and sub_name != root_name:  # Skip if same as root
                sub_genre, created = cls.objects.get_or_create(
                    name=sub_name,
                    parent=root_genre,
                    defaults={
                        'slug': cls._generate_unique_slug(sub_name, parent=root_genre),
                        'level': 1,
                        'soundcharts_root': root_name,
                    }
                )
                subgenres.append(sub_genre)
        
        return root_genre, subgenres
    
    @staticmethod
    def _generate_slug(name):
        """Generate a URL-friendly slug from genre name"""
        import re
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    @classmethod
    def _generate_unique_slug(cls, name, parent=None):
        """Generate a unique slug for a genre, handling duplicates"""
        base_slug = cls._generate_slug(name)
        slug = base_slug
        counter = 1
        
        # Check for existing slugs
        while cls.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug


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

    # Entry/Exit tracking
    entry_date = models.DateTimeField(
        null=True, blank=True,
        help_text="Date when the track first entered this chart (from SoundCharts API)"
    )
    exit_date = models.DateTimeField(
        null=True, blank=True,
        help_text="Date when the track left this chart (calculated from last appearance)"
    )

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


class TrackAudienceTimeSeries(models.Model):
    """
    Stores time-series audience data for tracks from Soundcharts API
    Designed for charting and trend analysis per platform
    """
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name="audience_timeseries")
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name="audience_timeseries")
    
    # Time-series data
    date = models.DateField(help_text="Date of the audience measurement")
    audience_value = models.BigIntegerField(help_text="Audience value for this date/platform")
    
    # Platform-specific identifier (e.g., Spotify track ID)
    platform_identifier = models.CharField(max_length=255, blank=True, 
                                        help_text="Platform-specific identifier (e.g., '2Fxmhks0bxGSBdJ92vM42m')")
    
    # Metadata
    fetched_at = models.DateTimeField(auto_now_add=True)
    api_data = models.JSONField(default=dict, help_text="Raw API response data for this entry")
    
    class Meta:
        unique_together = ['track', 'platform', 'date']
        ordering = ['-date']
        verbose_name = "Track Audience Time Series"
        verbose_name_plural = "Track Audience Time Series"
        indexes = [
            models.Index(fields=['track', 'platform', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['platform', 'date']),
        ]
    
    def __str__(self):
        return f"{self.track.name} - {self.platform.name} - {self.date} ({self.audience_value:,})"
    
    @classmethod
    def get_chart_data(cls, track, platform, start_date=None, end_date=None, limit=None):
        """
        Get formatted data ready for charting
        Returns data ordered by date for line charts (most recent records, ordered oldest to newest)
        """
        queryset = cls.objects.filter(track=track, platform=platform)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        if limit:
            # Get the most recent dates first, then order for display
            # First, get the most recent N records
            recent_records = queryset.order_by('-date')[:limit]
            # Convert to list to avoid queryset issues
            recent_records = list(recent_records)
            # Sort by date ascending for chart display
            recent_records.sort(key=lambda x: x.date)
            return [{'date': record.date, 'audience_value': record.audience_value} for record in recent_records]
        else:
            # No limit, just order by date ascending
            return queryset.order_by('date').values('date', 'audience_value')
    
    @classmethod
    def get_platform_comparison(cls, track, platforms, start_date=None, end_date=None, limit=None):
        """
        Get data for multiple platforms for comparison charts
        Returns data grouped by platform for multi-line charts
        """
        queryset = cls.objects.filter(track=track, platform__in=platforms)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        if limit:
            # Get the most recent dates within limit
            recent_dates = queryset.values('date').distinct().order_by('-date')[:limit]
            queryset = queryset.filter(date__in=recent_dates.values_list('date', flat=True))
        
        return queryset.values('platform__name', 'date', 'audience_value').order_by('platform__name', 'date')
    
    @classmethod
    def get_latest_audience(cls, track, platform):
        """Get the most recent audience value for a track on a specific platform"""
        try:
            return cls.objects.filter(track=track, platform=platform).latest('date')
        except cls.DoesNotExist:
            return None
    
    @property
    def formatted_audience_value(self):
        """Returns formatted audience value for display"""
        if self.audience_value >= 1_000_000_000:
            return f"{self.audience_value / 1_000_000_000:.1f}B"
        elif self.audience_value >= 1_000_000:
            return f"{self.audience_value / 1_000_000:.1f}M"
        elif self.audience_value >= 1_000:
            return f"{self.audience_value / 1_000:.1f}K"
        else:
            return f"{self.audience_value:,}"


class ArtistAudience(models.Model):
    """
    Stores audience and demographic data for artists from Soundcharts API
    """
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="audience_data")
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, help_text="Platform for this audience data")
    
    # Audience metrics
    total_listeners = models.BigIntegerField(null=True, blank=True, help_text="Total number of listeners")
    unique_listeners = models.BigIntegerField(null=True, blank=True, help_text="Unique listeners")
    repeat_listeners = models.BigIntegerField(null=True, blank=True, help_text="Repeat listeners")
    
    # Demographic data (age groups)
    age_13_17 = models.IntegerField(null=True, blank=True, help_text="Listeners aged 13-17")
    age_18_24 = models.IntegerField(null=True, blank=True, help_text="Listeners aged 18-24")
    age_25_34 = models.IntegerField(null=True, blank=True, help_text="Listeners aged 25-34")
    age_35_44 = models.IntegerField(null=True, blank=True, help_text="Listeners aged 35-44")
    age_45_54 = models.IntegerField(null=True, blank=True, help_text="Listeners aged 45-54")
    age_45_59 = models.IntegerField(null=True, blank=True, help_text="Listeners aged 45-59")
    age_55_64 = models.IntegerField(null=True, blank=True, help_text="Listeners aged 55-64")
    age_60_150 = models.IntegerField(null=True, blank=True, help_text="Listeners aged 60+")
    age_65_plus = models.IntegerField(null=True, blank=True, help_text="Listeners aged 65+")
    
    # Gender demographics
    gender_male = models.IntegerField(null=True, blank=True, help_text="Male listeners percentage")
    gender_female = models.IntegerField(null=True, blank=True, help_text="Female listeners percentage")
    
    # Geographic data
    top_countries = models.JSONField(default=list, help_text="Top countries by listeners")
    top_cities = models.JSONField(default=list, help_text="Top cities by listeners")
    
    # Raw API data
    api_data = models.JSONField(default=dict, help_text="Raw API response data")
    report_date = models.DateField(null=True, blank=True, help_text="Date of the audience report")
    
    # Metadata
    fetched_at = models.DateTimeField(auto_now_add=True, help_text="When this data was fetched")
    
    class Meta:
        unique_together = ['artist', 'platform', 'report_date']
        ordering = ['-fetched_at']
        verbose_name = "Artist Audience"
        verbose_name_plural = "Artist Audiences"
    
    def __str__(self):
        return f"{self.artist.name} - {self.platform.name} - {self.fetched_at.strftime('%Y-%m-%d')}"


class ArtistAudienceTimeSeries(models.Model):
    """
    Stores time-series audience data for artists from Soundcharts API
    Designed for charting and trend analysis per platform
    """
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="audience_timeseries")
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name="artist_audience_timeseries")
    
    # Time-series data
    date = models.DateField(help_text="Date of the audience measurement")
    audience_value = models.BigIntegerField(help_text="Audience value for this date/platform")
    
    # Platform-specific identifier (e.g., Spotify artist ID)
    platform_identifier = models.CharField(max_length=255, blank=True, 
                                        help_text="Platform-specific identifier (e.g., '06HL4z0CvFAxyc27GXpf02' for Taylor Swift)")
    
    # Metadata
    fetched_at = models.DateTimeField(auto_now_add=True)
    api_data = models.JSONField(default=dict, help_text="Raw API response data for this entry")
    
    class Meta:
        unique_together = ['artist', 'platform', 'date']
        ordering = ['-date']
        verbose_name = "Artist Audience Time Series"
        verbose_name_plural = "Artist Audience Time Series"
        indexes = [
            models.Index(fields=['artist', 'platform', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['platform', 'date']),
        ]
    
    def __str__(self):
        return f"{self.artist.name} - {self.platform.name} - {self.date} ({self.audience_value:,})"
    
    @classmethod
    def get_chart_data(cls, artist, platform, start_date=None, end_date=None, limit=None):
        """
        Get formatted data ready for charting
        Returns data ordered by date for line charts (most recent records, ordered oldest to newest)
        """
        queryset = cls.objects.filter(artist=artist, platform=platform)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        if limit:
            # Get the most recent dates first, then order for display
            recent_records = queryset.order_by('-date')[:limit]
            recent_records = list(recent_records)
            recent_records.sort(key=lambda x: x.date)
            return [{'date': record.date, 'audience_value': record.audience_value} for record in recent_records]
        else:
            return queryset.order_by('date').values('date', 'audience_value')
    
    @classmethod
    def get_platform_comparison(cls, artist, platforms, start_date=None, end_date=None, limit=None):
        """
        Get data for multiple platforms for comparison charts
        Returns data grouped by platform for multi-line charts
        """
        queryset = cls.objects.filter(artist=artist, platform__in=platforms)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        if limit:
            # Get the most recent dates within limit
            recent_dates = queryset.values('date').distinct().order_by('-date')[:limit]
            queryset = queryset.filter(date__in=recent_dates.values_list('date', flat=True))
        
        return queryset.values('platform__name', 'date', 'audience_value').order_by('platform__name', 'date')
    
    @classmethod
    def get_latest_audience(cls, artist, platform):
        """Get the most recent audience value for an artist on a specific platform"""
        try:
            return cls.objects.filter(artist=artist, platform=platform).latest('date')
        except cls.DoesNotExist:
            return None
    
    @property
    def formatted_audience_value(self):
        """Returns formatted audience value for display"""
        if self.audience_value >= 1_000_000_000:
            return f"{self.audience_value / 1_000_000_000:.1f}B"
        elif self.audience_value >= 1_000_000:
            return f"{self.audience_value / 1_000_000:.1f}M"
        elif self.audience_value >= 1_000:
            return f"{self.audience_value / 1_000:.1f}K"
        else:
            return f"{self.audience_value:,}"


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


class ChartSyncSchedule(models.Model):
    """
    Manages scheduled chart synchronization tasks with Soundcharts API
    """
    SYNC_FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom Interval'),
    ]
    
    chart = models.ForeignKey(
        Chart, 
        on_delete=models.CASCADE, 
        related_name="sync_schedules",
        help_text="Chart to sync"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this sync schedule is active"
    )
    sync_frequency = models.CharField(
        max_length=50, 
        choices=SYNC_FREQUENCY_CHOICES,
        help_text="How often to sync this chart"
    )
    custom_interval_hours = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Custom interval in hours (only used if sync_frequency is 'custom')"
    )
    last_sync_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When this chart was last synced"
    )
    next_sync_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When this chart should be synced next"
    )
    
    # Sync statistics
    total_executions = models.IntegerField(
        default=0,
        help_text="Total number of sync executions"
    )
    successful_executions = models.IntegerField(
        default=0,
        help_text="Number of successful sync executions"
    )
    failed_executions = models.IntegerField(
        default=0,
        help_text="Number of failed sync executions"
    )
    
    # Sync options
    sync_immediately = models.BooleanField(
        default=False,
        help_text="Whether to start sync immediately when schedule is created"
    )
    sync_historical_data = models.BooleanField(
        default=True,
        help_text="Whether to sync all historical data based on chart frequency"
    )
    fetch_track_metadata = models.BooleanField(
        default=True,
        help_text="Whether to fetch track metadata during chart sync"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True,
        help_text="User who created this sync schedule"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Chart Sync Schedule"
        verbose_name_plural = "Chart Sync Schedules"
        constraints = [
            models.UniqueConstraint(
                fields=['chart'],
                name='unique_chart_sync_schedule'
            )
        ]
    
    def __str__(self):
        return f"{self.chart.name} - {self.get_sync_frequency_display()}"
    
    def save(self, *args, **kwargs):
        # Set sync_frequency from chart frequency if not already set
        if not self.sync_frequency and self.chart:
            chart_freq = self.chart.frequency.lower()
            if chart_freq in ['daily', 'weekly', 'monthly']:
                self.sync_frequency = chart_freq
            else:
                self.sync_frequency = 'weekly'  # default fallback
        
        # Calculate next_sync_at if not set
        if self.is_active and not self.next_sync_at:
            self.calculate_next_sync()
        
        super().save(*args, **kwargs)
        
        # Trigger immediate sync if requested
        if self.sync_immediately and self.is_active:
            self._trigger_immediate_sync()
        
        # Ensure the periodic task is scheduled (only on creation)
        if not self.pk:  # New instance
            self._ensure_periodic_task_scheduled()
    
    def _trigger_immediate_sync(self):
        """Trigger immediate sync for this schedule"""
        # Import here to avoid circular imports
        from .tasks import sync_chart_rankings_task
        
        # Create execution record
        execution = ChartSyncExecution.objects.create(
            schedule=self,
            status='pending'
        )
        
        # Queue the sync task
        task = sync_chart_rankings_task.delay(self.id, execution.id)
        execution.celery_task_id = task.id
        execution.status = 'running'
        execution.save()
        
        # Reset the immediate sync flag
        self.sync_immediately = False
        self.save(update_fields=['sync_immediately'])
    
    def _ensure_periodic_task_scheduled(self):
        """Ensure the periodic task is scheduled in Celery Beat"""
        try:
            from celery import current_app
            from celery.schedules import crontab
            
            # Check if the periodic task is already scheduled
            beat_schedule = current_app.conf.beat_schedule or {}
            if 'process-chart-sync-schedules' not in beat_schedule:
                # Schedule the periodic task
                current_app.conf.beat_schedule.update({
                    'process-chart-sync-schedules': {
                        'task': 'apps.soundcharts.tasks.process_scheduled_chart_syncs',
                        'schedule': 300.0,  # Every 5 minutes
                    },
                })
                logger.info("Scheduled periodic chart sync task")
        except Exception as e:
            logger.warning(f"Could not schedule periodic task: {e}")
    
    def calculate_next_sync(self):
        """Calculate when the next sync should occur"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        
        if self.sync_frequency == 'daily':
            self.next_sync_at = now + timedelta(days=1)
        elif self.sync_frequency == 'weekly':
            self.next_sync_at = now + timedelta(weeks=1)
        elif self.sync_frequency == 'monthly':
            self.next_sync_at = now + timedelta(days=30)
        elif self.sync_frequency == 'custom' and self.custom_interval_hours:
            self.next_sync_at = now + timedelta(hours=self.custom_interval_hours)
        else:
            self.next_sync_at = now + timedelta(weeks=1)  # fallback
    
    @property
    def success_rate(self):
        """Returns success rate as percentage"""
        if self.total_executions == 0:
            return 0
        return int((self.successful_executions / self.total_executions) * 100)
    
    @property
    def is_overdue(self):
        """Returns True if sync is overdue"""
        from django.utils import timezone
        return self.next_sync_at and self.next_sync_at < timezone.now()


class ChartSyncExecution(models.Model):
    """
    Tracks individual chart sync executions
    """
    EXECUTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    schedule = models.ForeignKey(
        ChartSyncSchedule, 
        on_delete=models.CASCADE, 
        related_name="executions",
        help_text="The sync schedule this execution belongs to"
    )
    status = models.CharField(
        max_length=20, 
        choices=EXECUTION_STATUS_CHOICES, 
        default='pending',
        help_text="Current status of this execution"
    )
    
    # Execution details
    started_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this execution started"
    )
    completed_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When this execution completed"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if execution failed"
    )
    
    # Results
    rankings_created = models.IntegerField(
        default=0,
        help_text="Number of chart rankings created in this execution"
    )
    rankings_updated = models.IntegerField(
        default=0,
        help_text="Number of chart rankings updated in this execution"
    )
    tracks_created = models.IntegerField(
        default=0,
        help_text="Number of tracks created in this execution"
    )
    tracks_updated = models.IntegerField(
        default=0,
        help_text="Number of tracks updated in this execution"
    )
    
    # Celery task tracking
    celery_task_id = models.CharField(
        max_length=255, 
        null=True,
        blank=True,
        help_text="Celery task ID for this execution"
    )
    
    # Retry information
    retry_count = models.IntegerField(
        default=0,
        help_text="Number of retry attempts"
    )
    max_retries = models.IntegerField(
        default=3,
        help_text="Maximum number of retries allowed"
    )
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = "Chart Sync Execution"
        verbose_name_plural = "Chart Sync Executions"
    
    def __str__(self):
        return f"{self.schedule.chart.name} - {self.status} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration(self):
        """Returns execution duration in seconds"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_successful(self):
        """Returns True if execution was successful"""
        return self.status == 'completed'
    
    def mark_completed(self, rankings_created=0, rankings_updated=0, tracks_created=0, tracks_updated=0):
        """Mark execution as completed with results"""
        from django.utils import timezone
        
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.rankings_created = rankings_created
        self.rankings_updated = rankings_updated
        self.tracks_created = tracks_created
        self.tracks_updated = tracks_updated
        self.save()
        
        # Update schedule statistics
        self.schedule.total_executions += 1
        self.schedule.successful_executions += 1
        self.schedule.last_sync_at = self.completed_at
        self.schedule.calculate_next_sync()
        self.schedule.save()
    
    def mark_failed(self, error_message=""):
        """Mark execution as failed with error message"""
        from django.utils import timezone
        
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save()
        
        # Update schedule statistics
        self.schedule.total_executions += 1
        self.schedule.failed_executions += 1
        self.schedule.save()
