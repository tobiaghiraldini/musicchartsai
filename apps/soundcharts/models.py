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
