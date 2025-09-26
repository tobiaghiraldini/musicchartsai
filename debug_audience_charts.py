#!/usr/bin/env python3
"""
Debug script to verify audience chart data correctness
Run this script to check data consistency between admin view and chart data
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.soundcharts.models import Track, TrackAudienceTimeSeries, Platform


def debug_audience_data():
    """Debug audience data for tracks with time series data"""
    
    print("🔍 Debugging Audience Chart Data")
    print("=" * 50)
    
    # Get tracks with audience time series data
    tracks_with_data = Track.objects.filter(
        audience_timeseries__isnull=False
    ).distinct()[:5]  # Limit to first 5 for testing
    
    if not tracks_with_data.exists():
        print("❌ No tracks with audience time series data found")
        return
    
    for track in tracks_with_data:
        print(f"\n📊 Track: {track.name} ({track.uuid})")
        print("-" * 40)
        
        # Get platforms for this track
        platforms = Platform.objects.filter(
            audience_timeseries__track=track
        ).distinct()
        
        for platform in platforms:
            print(f"\n🎵 Platform: {platform.name}")
            
            # Get all data points (admin view equivalent)
            all_data = TrackAudienceTimeSeries.objects.filter(
                track=track, 
                platform=platform
            ).order_by('-date')
            
            print(f"   Total data points: {all_data.count()}")
            
            if all_data.exists():
                latest = all_data.first()
                oldest = all_data.last()
                print(f"   Latest date: {latest.date} (value: {latest.audience_value:,})")
                print(f"   Oldest date: {oldest.date} (value: {oldest.audience_value:,})")
                
                # Test the chart data method with limit=30
                chart_data = list(track.get_audience_chart_data(platform, limit=30))
                print(f"   Chart data points (limit=30): {len(chart_data)}")
                
                if chart_data:
                    chart_latest = chart_data[-1]  # Last item (most recent)
                    chart_oldest = chart_data[0]   # First item (oldest in chart)
                    print(f"   Chart latest date: {chart_latest['date']} (value: {chart_latest['audience_value']:,})")
                    print(f"   Chart oldest date: {chart_oldest['date']} (value: {chart_oldest['audience_value']:,})")
                    
                    # Verify consistency
                    if chart_latest['date'] == latest.date:
                        print("   ✅ Chart shows correct latest date")
                    else:
                        print(f"   ❌ Chart latest date mismatch! Expected: {latest.date}, Got: {chart_latest['date']}")
                    
                    if len(chart_data) <= 30:
                        print("   ✅ Chart data limit working correctly")
                    else:
                        print(f"   ❌ Chart data limit exceeded! Expected: ≤30, Got: {len(chart_data)}")
                else:
                    print("   ⚠️  No chart data returned")
            else:
                print("   ⚠️  No data points found")


def test_specific_track(track_uuid):
    """Test a specific track's data"""
    
    print(f"\n🎯 Testing specific track: {track_uuid}")
    print("=" * 50)
    
    try:
        track = Track.objects.get(uuid=track_uuid)
        print(f"Track: {track.name}")
        
        platforms = Platform.objects.filter(
            audience_timeseries__track=track
        ).distinct()
        
        for platform in platforms:
            print(f"\nPlatform: {platform.name}")
            
            # Raw database query
            raw_data = list(TrackAudienceTimeSeries.objects.filter(
                track=track, 
                platform=platform
            ).order_by('-date').values('date', 'audience_value')[:30])
            
            # Chart data method
            chart_data = list(track.get_audience_chart_data(platform, limit=30))
            
            print(f"Raw data count: {len(raw_data)}")
            print(f"Chart data count: {len(chart_data)}")
            
            if raw_data and chart_data:
                print(f"Raw latest: {raw_data[0]['date']}")
                print(f"Chart latest: {chart_data[-1]['date']}")
                print(f"Raw oldest: {raw_data[-1]['date']}")
                print(f"Chart oldest: {chart_data[0]['date']}")
                
                # Check if they match
                raw_dates = [item['date'] for item in raw_data]
                chart_dates = [item['date'] for item in chart_data]
                
                if raw_dates == chart_dates:
                    print("✅ Data matches perfectly!")
                else:
                    print("❌ Data mismatch detected!")
                    print(f"Raw dates: {raw_dates[:5]}...")
                    print(f"Chart dates: {chart_dates[:5]}...")
            
    except Track.DoesNotExist:
        print(f"❌ Track with UUID {track_uuid} not found")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific track
        track_uuid = sys.argv[1]
        test_specific_track(track_uuid)
    else:
        # General debug
        debug_audience_data()
    
    print("\n" + "=" * 50)
    print("Debug complete! 🎉")
