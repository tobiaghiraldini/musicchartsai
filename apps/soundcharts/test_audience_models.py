"""
Test file for the new audience time-series models and functionality
"""
from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from .models import Track, Platform, TrackAudienceTimeSeries


class TrackAudienceTimeSeriesTestCase(TestCase):
    """Test cases for TrackAudienceTimeSeries model"""
    
    def setUp(self):
        """Set up test data"""
        # Create test platform
        self.platform = Platform.objects.create(
            name="Spotify",
            slug="spotify",
            platform_type="streaming",
            audience_metric_name="Listeners",
            platform_identifier="spotify"
        )
        
        # Create test track
        self.track = Track.objects.create(
            name="Test Song",
            uuid="test-uuid-123",
            credit_name="Test Artist"
        )
        
        # Create some test audience data
        base_date = date.today()
        for i in range(7):  # Last 7 days
            test_date = base_date - timedelta(days=i)
            TrackAudienceTimeSeries.objects.create(
                track=self.track,
                platform=self.platform,
                date=test_date,
                audience_value=1000000 + (i * 50000),  # Increasing trend
                platform_identifier="test_spotify_id"
            )
    
    def test_model_creation(self):
        """Test that TrackAudienceTimeSeries records are created correctly"""
        self.assertEqual(TrackAudienceTimeSeries.objects.count(), 7)
        
        latest_record = TrackAudienceTimeSeries.objects.latest('date')
        self.assertEqual(latest_record.track, self.track)
        self.assertEqual(latest_record.platform, self.platform)
        self.assertEqual(latest_record.audience_value, 1000000)
    
    def test_get_chart_data(self):
        """Test the get_chart_data class method"""
        chart_data = TrackAudienceTimeSeries.get_chart_data(
            self.track, 
            self.platform, 
            limit=5
        )
        
        self.assertEqual(len(chart_data), 5)
        
        # Check data is ordered by date
        dates = [item['date'] for item in chart_data]
        self.assertEqual(dates, sorted(dates))
    
    def test_get_platform_comparison(self):
        """Test the get_platform_comparison class method"""
        # Create another platform for comparison
        platform2 = Platform.objects.create(
            name="Apple Music",
            slug="apple_music",
            platform_type="streaming",
            audience_metric_name="Listeners"
        )
        
        # Add some data for the second platform
        base_date = date.today()
        for i in range(5):
            test_date = base_date - timedelta(days=i)
            TrackAudienceTimeSeries.objects.create(
                track=self.track,
                platform=platform2,
                date=test_date,
                audience_value=800000 + (i * 40000),
                platform_identifier="test_apple_id"
            )
        
        comparison_data = TrackAudienceTimeSeries.get_platform_comparison(
            self.track, 
            [self.platform, platform2], 
            limit=5
        )
        
        # Should have data from both platforms
        platform_names = set(item['platform__name'] for item in comparison_data)
        self.assertEqual(platform_names, {"Spotify", "Apple Music"})
    
    def test_track_methods(self):
        """Test the convenience methods added to Track model"""
        # Test single platform chart data
        chart_data = self.track.get_audience_chart_data(self.platform, limit=3)
        self.assertEqual(len(chart_data), 3)
        
        # Test platform comparison
        comparison_data = self.track.get_platform_audience_comparison([self.platform], limit=3)
        self.assertEqual(len(comparison_data), 3)
    
    def test_formatted_audience_value(self):
        """Test the formatted_audience_value property"""
        record = TrackAudienceTimeSeries.objects.first()
        
        # Test different value ranges
        record.audience_value = 1500
        self.assertEqual(record.formatted_audience_value, "1.5K")
        
        record.audience_value = 1500000
        self.assertEqual(record.formatted_audience_value, "1.5M")
        
        record.audience_value = 1500000000
        self.assertEqual(record.formatted_audience_value, "1.5B")
    
    def test_unique_constraint(self):
        """Test that unique constraint works correctly"""
        # Try to create duplicate record
        with self.assertRaises(Exception):
            TrackAudienceTimeSeries.objects.create(
                track=self.track,
                platform=self.platform,
                date=date.today(),
                audience_value=999999,
                platform_identifier="duplicate"
            )


class PlatformModelTestCase(TestCase):
    """Test cases for enhanced Platform model"""
    
    def test_platform_creation(self):
        """Test that Platform model works with new fields"""
        platform = Platform.objects.create(
            name="Test Platform",
            slug="test_platform",
            platform_type="social",
            audience_metric_name="Followers",
            platform_identifier="test_social"
        )
        
        self.assertEqual(platform.platform_type, "social")
        self.assertEqual(platform.audience_metric_name, "Followers")
        self.assertEqual(platform.platform_identifier, "test_social")
    
    def test_platform_defaults(self):
        """Test that Platform model has correct defaults"""
        platform = Platform.objects.create(
            name="Default Platform",
            slug="default_platform"
        )
        
        self.assertEqual(platform.platform_type, "streaming")
        self.assertEqual(platform.audience_metric_name, "Listeners")
        self.assertEqual(platform.platform_identifier, "")
