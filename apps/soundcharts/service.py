from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)


class SoundchartsService:
    def __init__(self):
        self.app_id = settings.SOUNDCHARTS_APP_ID  # This should be the app ID
        self.api_key = settings.SOUNDCHARTS_API_KEY  # This should be the API key
        self.api_url = settings.SOUNDCHARTS_API_URL
        self.headers = {"x-app-id": self.app_id, "x-api-key": self.api_key}

    def get_platforms(self, limit=100, offset=0):
        url = f"{self.api_url}/api/v2/chart/song/platforms"
        try:
            headers = {"x-app-id": self.app_id, "x-api-key": self.api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            logger.debug(f"Platforms API response: {data}")

            # Handle different possible response structures
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Check if data is nested in a 'data' field
                if "data" in data:
                    return data["data"]
                # Check if data is nested in a 'results' field
                elif "results" in data:
                    return data["results"]
                # Check if data is nested in a 'platforms' field
                elif "platforms" in data:
                    return data["platforms"]
                # Check if data is nested in an 'items' field (common in paginated responses)
                elif "items" in data:
                    return data["items"]
                # If it's a dict but not nested, return as is
                else:
                    return data
            else:
                logger.error(f"Unexpected response type: {type(data)}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting platforms: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting platforms: {e}")
            return None

    def get_song_metadata(self, uuid):
        url = f"{self.api_url}/api/v2.25/song/{uuid}"
        try:
            headers = {"x-app-id": self.app_id, "x-api-key": self.api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Song metadata API response: {data}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting song metadata: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting song metadata: {e}")
            return None

    def get_song_audience(self, uuid, platform="spotify"):
        """
        Fetch audience and demographic data for a song from Soundcharts API
        Endpoint: /api/v2/song/{uuid}/audience/{platform}
        """
        url = f"{self.api_url}/api/v2/song/{uuid}/audience/{platform}"
        try:
            headers = {"x-app-id": self.app_id, "x-api-key": self.api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Song audience API response for {uuid} on {platform}: {data}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting song audience for {uuid} on {platform}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting song audience for {uuid} on {platform}: {e}")
            return None

    def get_song_audience_for_platform(self, uuid, platform="spotify"):
        """
        Fetch time-series audience data for a song from Soundcharts API
        Endpoint: /api/v2/song/{uuid}/audience/{platform}/plots
        This returns historical audience data over time for charting purposes
        """
        url = f"{self.api_url}/api/v2/song/{uuid}/audience/{platform}"
        try:
            headers = {"x-app-id": self.app_id, "x-api-key": self.api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Song audience for platform API response for {uuid} on {platform}: {data}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting song audience for platform {uuid} on {platform}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting song audience for platform {uuid} on {platform}: {e}")
            return None

    def get_song_metadata_enhanced(self, uuid):
        """
        Enhanced metadata fetching with additional fields
        """
        url = f"{self.api_url}/api/v2.25/song/{uuid}"
        try:
            headers = {"x-app-id": self.app_id, "x-api-key": self.api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Enhanced song metadata API response: {data}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting enhanced song metadata: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting enhanced song metadata: {e}")
            return None

    def get_artist_metadata(self, uuid):
        url = f"{self.api_url}/api/v2.9/artist/{uuid}"
        try:
            headers = {"x-app-id": self.app_id, "x-api-key": self.api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Artist metadata API response: {data}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting artist metadata: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting artist metadata: {e}")
            return None

    def get_artist_audience_for_platform(self, uuid, platform="spotify", date='latest'):
        url = f"{self.api_url}/api/v2/artist/{uuid}/audience/{platform}/report/{date}"
        try:
            headers = {"x-app-id": self.app_id, "x-api-key": self.api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Artist audience for platform API response: {data}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting artist audience for platform: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting artist audience for platform: {e}")
            return None


    def search_artists(self, q, limit=100, offset=0):
        # Try the search endpoint first as it's more reliable
        url = f"{self.api_url}/api/v2/artist/search/{q}"
        try:
            headers = {"x-app-id": self.app_id, "x-api-key": self.api_key}
            params = {"limit": limit, "offset": offset}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Artists API response: {data}")

            # Handle different possible response structures
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                if "items" in data:
                    return data["items"]
                elif "data" in data:
                    return data["data"]
                elif "results" in data:
                    return data["results"]
                elif "artists" in data:
                    return data["artists"]
                else:
                    return data
            else:
                logger.error(f"Unexpected response type: {type(data)}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting artists: {e}")
            # If search fails, try to get specific artists from the sandbox data
            return self._get_sandbox_artists()
        except Exception as e:
            logger.error(f"Unexpected error getting artists: {e}")
            return self._get_sandbox_artists()

    def get_charts(self, platform_code="spotify", country_code="IT", offset=0, limit=100):
        """
        Docs:
        """
        # /api/v2/chart/song/by-platform/spotify?countryCode=IT&offset=0&limit=100
        url = f"{self.api_url}/api/v2/chart/song/by-platform/{platform_code}?countryCode={country_code}&offset={offset}&limit={limit}"
        try:
            headers = {"x-app-id": self.app_id, "x-api-key": self.api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Charts API response: {data}")
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Check if data is nested in a 'data' field
                if "data" in data:
                    return data["data"]
                # Check if data is nested in a 'results' field
                elif "results" in data:
                    return data["results"]
                # Check if data is nested in a 'platforms' field
                elif "platforms" in data:
                    return data["platforms"]
                # Check if data is nested in an 'items' field (common in paginated responses)
                elif "items" in data:
                    return data["items"]
                # If it's a dict but not nested, return as is
                else:
                    return data
            else:
                logger.error(f"Unexpected response type: {type(data)}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting song rankings: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting song rankings: {e}")
            return None

    def get_song_ranking_for_date(self, platform_slug, datetime=None):
        """
        Docs:
        https://doc.api.soundcharts.com/documentation/reference/charts/get-song-ranking-for-a-date
        Params:
        platform_slug global-28
        datetime 2020-10-06T18:00:01+00:00
        """
        # /api/v2.14/chart/song/{slug}/ranking/{datetime}
        if datetime:
            # Handle datetime objects properly
            if hasattr(datetime, 'strftime'):
                # It's a datetime object, format it properly for Soundcharts API
                # The API expects ISO format with timezone: 2020-10-06T18:00:01+00:00
                if datetime.tzinfo is not None:
                    # Timezone-aware datetime
                    atom_datetime = datetime.strftime('%Y-%m-%dT%H:%M:%S%z')
                    # Ensure timezone format is correct (replace +0000 with +00:00)
                    if atom_datetime.endswith('+0000'):
                        atom_datetime = atom_datetime[:-5] + '+00:00'
                    elif atom_datetime.endswith('-0000'):
                        atom_datetime = atom_datetime[:-5] + '+00:00'
                else:
                    # Naive datetime - assume UTC
                    atom_datetime = datetime.strftime('%Y-%m-%dT%H:%M:%S+00:00')
            else:
                # It's a string - need to ensure it's properly formatted
                datetime_str = str(datetime)
                
                # If it's already properly formatted (has seconds and timezone), use it
                if '+' in datetime_str or datetime_str.count(':') >= 2:
                    atom_datetime = datetime_str
                else:
                    # Incomplete format from datetime-local input (e.g., "2025-10-14T16:16")
                    # Add seconds and UTC timezone
                    if 'T' in datetime_str and datetime_str.count(':') == 1:
                        # Format: YYYY-MM-DDTHH:MM - add seconds and timezone
                        atom_datetime = f"{datetime_str}:00+00:00"
                    else:
                        # Unexpected format, use as is and let the API reject it
                        atom_datetime = datetime_str
        else:
            atom_datetime = "latest"
            
        url = f"{self.api_url}/api/v2.14/chart/song/{platform_slug}/ranking/{atom_datetime}"

        try:
            headers = {"x-app-id": self.app_id, "x-api-key": self.api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Rankings API response: {data}")

            # Return the raw response for the admin views to parse
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting song rankings: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting song rankings: {e}")
            return None

    def get_tracks(self, limit=100, offset=0, artist_uuid=None):
        """
        Get tracks from Soundcharts API
        """
        if artist_uuid:
            url = f"{self.api_url}/api/v2.34/artist/{artist_uuid}/tracks"
        else:
            url = f"{self.api_url}/api/v2/referential/tracks"

        try:
            headers = {"x-app-id": self.app_id, "x-api-key": self.api_key}
            params = {"limit": limit, "offset": offset}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Tracks API response: {data}")

            # Handle different possible response structures
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                if "items" in data:
                    return data["items"]
                elif "data" in data:
                    return data["data"]
                elif "results" in data:
                    return data["results"]
                elif "tracks" in data:
                    return data["tracks"]
                else:
                    return data
            else:
                logger.error(f"Unexpected response type: {type(data)}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting tracks: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting tracks: {e}")
            return None

    def get_venues(self, limit=100, offset=0, country_code=None):
        """
        Get venues from Soundcharts API
        """
        if country_code:
            url = f"{self.api_url}/api/v2/referential/venues?countryCode={country_code}"
        else:
            url = f"{self.api_url}/api/v2/referential/venues"

        try:
            headers = {"x-app-id": self.app_id, "x-api-key": self.api_key}
            params = {"limit": limit, "offset": offset}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Venues API response: {data}")

            # Handle different possible response structures
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                if "items" in data:
                    return data["items"]
                elif "data" in data:
                    return data["data"]
                elif "results" in data:
                    return data["results"]
                elif "venues" in data:
                    return data["venues"]
                else:
                    return data
            else:
                logger.error(f"Unexpected response type: {type(data)}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting venues: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting venues: {e}")
            return None

    def get_genres(self, limit=100, offset=0):
        """
        Get genres from Soundcharts API
        """
        url = f"{self.api_url}/api/v2/referential/genres"
        try:
            headers = {"x-app-id": self.app_id, "x-api-key": self.api_key}
            params = {"limit": limit, "offset": offset}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Genres API response: {data}")

            # Handle different possible response structures
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                if "items" in data:
                    return data["items"]
                elif "data" in data:
                    return data["data"]
                elif "results" in data:
                    return data["results"]
                elif "genres" in data:
                    return data["genres"]
                else:
                    return data
            else:
                logger.error(f"Unexpected response type: {type(data)}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting genres: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting genres: {e}")
            return None

    def _get_sandbox_artists(self):
        """Fallback method to get sandbox artists data"""
        logger.info("Using sandbox artists data as fallback")
        return [
            {
                "uuid": "11e81bcc-9c1c-ce38-b96b-a0369fe50396",
                "name": "Billie Eilish",
                "slug": "billie-eilish",
                "appUrl": "https://soundcharts.com/artist/billie-eilish",
                "imageUrl": "https://soundcharts.com/artist/billie-eilish/image",
            },
            {
                "uuid": "ca22091a-3c00-11e9-974f-549f35141000",
                "name": "Tones & I",
                "slug": "tones-i",
                "appUrl": "https://soundcharts.com/artist/tones-i",
                "imageUrl": "https://soundcharts.com/artist/tones-i/image",
            },
        ]

    def get_albums_by_artist(self, uuid, limit=100, offset=0):
        url = f"{self.api_url}/api/v2.34/artist/{uuid}/albums"
        try:
            headers = {"x-app-id": self.app_id, "x-api-key": self.api_key}
            params = {"limit": limit, "offset": offset}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Albums API response: {data}")

            # Handle different possible response structures
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                if "items" in data:
                    return data["items"]
                elif "data" in data:
                    return data["data"]
                elif "results" in data:
                    return data["results"]
                elif "albums" in data:
                    return data["albums"]
                else:
                    return data
            else:
                logger.error(f"Unexpected response type: {type(data)}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting albums: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting albums: {e}")
            return None
