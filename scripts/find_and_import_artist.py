#!/usr/bin/env python
"""
Script to search for an artist in Soundcharts and import them into the database.

Usage:
    python scripts/find_and_import_artist.py "Artist Name"

Example:
    python scripts/find_and_import_artist.py "Taylor Swift"
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.soundcharts.service import SoundchartsService
from apps.soundcharts.models import Artist

def find_and_import_artist(search_query):
    """Search for an artist and import the first match"""
    service = SoundchartsService()
    
    print(f"🔍 Searching for: '{search_query}'...")
    results = service.search_artists(search_query, limit=10)
    
    if not results:
        print("❌ No artists found")
        return
    
    print(f"\n✅ Found {len(results)} artist(s):\n")
    
    for i, artist_data in enumerate(results, 1):
        name = artist_data.get('name', 'Unknown')
        uuid = artist_data.get('uuid', 'N/A')
        country = artist_data.get('countryCode', 'N/A')
        career = artist_data.get('careerStage', 'N/A')
        
        print(f"{i}. {name}")
        print(f"   UUID: {uuid}")
        print(f"   Country: {country}")
        print(f"   Career Stage: {career}")
        print()
    
    # Ask user to select
    try:
        choice = input("Enter the number of the artist to import (or 'q' to quit): ").strip()
        if choice.lower() == 'q':
            print("Cancelled.")
            return
        
        idx = int(choice) - 1
        if idx < 0 or idx >= len(results):
            print("❌ Invalid selection")
            return
        
        selected = results[idx]
        
        # Create or update artist
        artist = Artist.create_from_soundcharts(selected)
        
        if artist:
            print(f"\n✅ Artist imported successfully!")
            print(f"   Name: {artist.name}")
            print(f"   UUID: {artist.uuid}")
            print(f"   ID: {artist.id}")
            print(f"\nNow you can:")
            print(f"1. View in admin: http://localhost:8000/admin/soundcharts/artist/{artist.id}/change/")
            print(f"2. Use 'Fetch Metadata from API' button to get full details")
            print(f"3. Use 'Fetch Audience Data from API' button to get audience info")
        else:
            print("❌ Failed to import artist")
            
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
    except KeyboardInterrupt:
        print("\nCancelled.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/find_and_import_artist.py \"Artist Name\"")
        print("Example: python scripts/find_and_import_artist.py \"Taylor Swift\"")
        sys.exit(1)
    
    search_query = " ".join(sys.argv[1:])
    find_and_import_artist(search_query)

