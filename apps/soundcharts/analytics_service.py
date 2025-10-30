"""
Music Analytics Aggregation Service

This service fetches and aggregates artist-level audience data using SoundCharts API endpoints:
- /api/v2/artist/{uuid}/streaming/{platform} - Streaming data (Spotify monthly listeners, YouTube views)
- /api/v2.37/artist/{uuid}/social/{platform}/followers/ - Social media followers

Phase 1: Fetch fresh data from API and display (current implementation)
Phase 2: Add track-level breakdown
"""

from django.db.models import Sum, Avg, Max, Min, Count, Q
from django.utils import timezone

from datetime import datetime, timedelta
from apps.soundcharts.models import (
    Artist, 
    ArtistAudienceTimeSeries, 
    Platform,
    Chart
)
from apps.soundcharts.service import SoundchartsService
import logging
import requests

logger = logging.getLogger(__name__)


class MusicAnalyticsService:
    """
    Service for aggregating artist-level music analytics data.
    
    Uses SoundCharts API to fetch artist streaming and social media metrics,
    then aggregates them for reporting purposes.
    """
    
    def __init__(self):
        """Initialize the analytics service and SoundCharts API client."""
        self.soundcharts = SoundchartsService()
    
    def fetch_and_aggregate_artist_metrics(self, artist_ids, platform_ids, start_date, end_date, country=None):
        """
        Fetch fresh data from SoundCharts API and aggregate metrics.
        
        This is the main method for Phase 1 - it calls SoundCharts API endpoints
        to get streaming and social audience data, then aggregates and returns results.
        
        Args:
            artist_ids: List of artist IDs
            platform_ids: List of platform IDs
            start_date: Start date for data range
            end_date: End date for data range
            country: Optional country code to filter by (uses countryPlots data)
            
        Returns:
            dict with aggregated metrics or error
        """
        # Validate artists
        validation = self.validate_artists(artist_ids)
        if not validation['valid_artists'].exists():
            return {
                'success': False,
                'error': validation['error'],
                'data': None
            }
        
        valid_artists = validation['valid_artists']
        platforms = Platform.objects.filter(id__in=platform_ids)
        
        # Fetch data from SoundCharts API
        all_data = []
        errors = []
        successes = []
        
        for artist in valid_artists:
            for platform in platforms:
                try:
                    # Determine which API endpoint to use based on platform type
                    data = self._fetch_platform_data(artist, platform, start_date, end_date, country)
                    if data:
                        all_data.extend(data)
                        successes.append(f"{artist.name} on {platform.name}: {len(data)} data points")
                    else:
                        errors.append(f"{artist.name} on {platform.name}: No data available")
                except Exception as e:
                    error_msg = f"{artist.name} on {platform.name}: {str(e)}"
                    logger.error(f"Error fetching data: {error_msg}")
                    errors.append(error_msg)
        
        # Log summary
        logger.info(f"Data fetch complete: {len(successes)} successful, {len(errors)} failed/empty")
        
        if not all_data:
            # Build helpful error message
            error_details = {
                'message': 'No data available from SoundCharts API for the selected criteria.',
                'total_attempts': len(valid_artists) * len(platforms),
                'successful': len(successes),
                'failed': len(errors),
                'failures': errors[:5],  # First 5 failures
                'suggestions': []
            }
            
            # Add helpful suggestions
            error_details['suggestions'].append('Try a different date range (e.g., last month or September 2024)')
            error_details['suggestions'].append('Verify the artist has data on SoundCharts.com')
            error_details['suggestions'].append('Try different platforms (Spotify and YouTube are most common)')
            
            return {
                'success': False,
                'error': error_details['message'],
                'error_details': error_details,
                'data': None
            }
        
        # Aggregate the fetched data
        result = self._aggregate_fetched_data(all_data, valid_artists, platforms, start_date, end_date, country)
        
        if validation.get('error'):
            result['warning'] = validation['error']
        
        return result
    
    def _fetch_platform_data(self, artist, platform, start_date, end_date, country=None):
        """
        Fetch data for a specific artist-platform combination from SoundCharts API.
        
        Args:
            artist: Artist model instance
            platform: Platform model instance
            start_date: Start date
            end_date: End date
            country: Optional country code to filter by (uses countryPlots data)
            
        Returns:
            List of data points with {artist, platform, date, value, country}
        """
        data_points = []
        
        # Determine platform type and call appropriate endpoint
        # Based on SoundCharts API documentation
        platform_slug = platform.slug.lower()
        
        # STREAMING endpoint platforms (confirmed from SoundCharts docs)
        # GET /api/v2/artist/{uuid}/streaming/{platform}
        # Only works for: Spotify, YouTube
        # These endpoints return countryPlots with geographic breakdown
        streaming_platforms = ['spotify', 'youtube']
        
        # SOCIAL endpoint platforms (confirmed from SoundCharts docs)
        # GET /api/v2.37/artist/{uuid}/social/{platform}/followers/
        # Works for: Instagram, TikTok, Facebook, Twitter, YouTube (subscribers)
        social_platforms = ['instagram', 'tiktok', 'facebook', 'twitter']
        
        # RADIO/AIRPLAY endpoint (confirmed from SoundCharts docs)
        # GET /api/v2/artist/{uuid}/broadcast-groups
        # Returns aggregated daily radio spin counts
        radio_platforms = ['airplay', 'radio']
        
        if platform_slug in streaming_platforms:
            logger.info(f"Using STREAMING endpoint for {platform.name}")
            data_points = self._fetch_streaming_data(artist, platform, start_date, end_date, country)
        elif platform_slug in social_platforms:
            logger.info(f"Using SOCIAL endpoint for {platform.name}")
            data_points = self._fetch_social_data(artist, platform, start_date, end_date, country)
        elif platform_slug in radio_platforms:
            logger.info(f"Using RADIO endpoint for {platform.name}")
            data_points = self._fetch_radio_data(artist, platform, start_date, end_date, country)
        else:
            # For other platforms, log and skip
            logger.warning(f"Platform {platform.name} ({platform_slug}) not supported for streaming, social, or radio endpoints. Skipping.")
            logger.info(f"Supported streaming platforms: {streaming_platforms}")
            logger.info(f"Supported social platforms: {social_platforms}")
            logger.info(f"Supported radio platforms: {radio_platforms}")
        
        return data_points
    
    def _fetch_streaming_data(self, artist, platform, start_date, end_date, country=None):
        """
        Fetch streaming data from /api/v2/artist/{uuid}/streaming/{platform}
        
        Returns daily Spotify monthly listeners, YouTube views, etc.
        If country is specified, extracts country-specific values from countryPlots.
        
        Args:
            artist: Artist model instance
            platform: Platform model instance
            start_date: Start date
            end_date: End date
            country: Optional country code (e.g., 'IT', 'US')
        """
        try:
            # SoundCharts API allows max 90 days per request
            # Split into batches if needed
            data_points = []
            current_start = start_date
            
            while current_start <= end_date:
                current_end = min(current_start + timedelta(days=89), end_date)
                
                # Call SoundCharts API
                url = f"{self.soundcharts.api_url}/api/v2/artist/{artist.uuid}/streaming/{platform.slug}"
                params = {
                    'startDate': current_start.strftime('%Y-%m-%d'),
                    'endDate': current_end.strftime('%Y-%m-%d')
                }
                
                logger.info(f"Fetching streaming data: {url} with params {params}")
                
                response = requests.get(url, headers=self.soundcharts.headers, params=params)
                response.raise_for_status()
                api_data = response.json()
                
                # DEBUG: Log full API response to understand structure
                logger.info(f"API Response for {artist.name} on {platform.name}: {api_data}")
                
                # Parse the response
                # Actual format from API: {"items": [{"date": "2024-09-01", "value": 12500000, "cityPlots": [...], "countryPlots": [...]}, ...]}
                plots = api_data.get('items', [])  # Use 'items' not 'plots'
                
                if not plots:
                    # Fallback to other possible keys
                    logger.warning(f"No 'items' in API response. Full response keys: {list(api_data.keys())}")
                    plots = api_data.get('plots', []) or api_data.get('data', []) or api_data.get('values', [])
                
                for plot in plots:
                    plot_date_str = plot.get('date')
                    value = plot.get('value')
                    
                    # If country filter is specified, use countryPlots instead of global value
                    if country and 'countryPlots' in plot:
                        country_plots = plot.get('countryPlots', [])
                        country_data = next((cp for cp in country_plots if cp.get('countryCode') == country), None)
                        if country_data:
                            value = country_data.get('value')
                            logger.info(f"Using country-specific value for {country}: {value}")
                        else:
                            # Country not in data for this date, skip this date
                            logger.debug(f"No data for country {country} on {plot_date_str}")
                            continue
                    
                    if plot_date_str and value is not None:
                        # Parse date (could be various formats)
                        try:
                            plot_date = datetime.strptime(plot_date_str, '%Y-%m-%d').date()
                        except:
                            try:
                                plot_date = datetime.fromisoformat(plot_date_str.split('T')[0]).date()
                            except:
                                logger.warning(f"Could not parse date: {plot_date_str}")
                                continue
                        
                        data_points.append({
                            'artist': artist,
                            'artist_name': artist.name,
                            'artist_uuid': artist.uuid,
                            'platform': platform,
                            'platform_name': platform.name,
                            'platform_slug': platform.slug,
                            'date': plot_date,
                            'value': int(value),
                            'metric_name': platform.audience_metric_name or 'Listeners',
                            'country': country  # Store country if filtered
                        })
                
                current_start = current_end + timedelta(days=1)
            
            logger.info(f"Fetched {len(data_points)} streaming data points for {artist.name} on {platform.name}")
            return data_points
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"No streaming data available for {artist.name} on {platform.name}")
            else:
                logger.error(f"HTTP error fetching streaming data: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching streaming data for {artist.name} on {platform.name}: {e}")
            return []
    
    def _fetch_social_data(self, artist, platform, start_date, end_date, country=None):
        """
        Fetch social data from /api/v2.37/artist/{uuid}/social/{platform}/followers/
        
        Returns Instagram, TikTok, YouTube follower counts over time.
        
        Note: Social platforms typically don't provide country-level breakdown,
        so the country parameter may not filter data for social endpoints.
        """
        try:
            data_points = []
            current_start = start_date
            
            while current_start <= end_date:
                current_end = min(current_start + timedelta(days=89), end_date)
                
                # Call SoundCharts API
                url = f"{self.soundcharts.api_url}/api/v2.37/artist/{artist.uuid}/social/{platform.slug}/followers/"
                params = {
                    'startDate': current_start.strftime('%Y-%m-%d'),
                    'endDate': current_end.strftime('%Y-%m-%d')
                }
                
                logger.info(f"Fetching social data: {url} with params {params}")
                
                response = requests.get(url, headers=self.soundcharts.headers, params=params)
                response.raise_for_status()
                api_data = response.json()
                
                # DEBUG: Log full API response
                logger.info(f"API Response for {artist.name} on {platform.name}: {api_data}")
                
                # Parse response  
                # Actual format: {"items": [{"date": "...", "value": ...}, ...]}
                plots = api_data.get('items', [])  # Use 'items' not 'plots'
                
                if not plots:
                    # Fallback to other possible keys
                    logger.warning(f"No 'items' in API response. Full response keys: {list(api_data.keys())}")
                    plots = api_data.get('plots', []) or api_data.get('data', []) or api_data.get('values', [])
                
                for plot in plots:
                    plot_date_str = plot.get('date')
                    value = plot.get('value')
                    
                    if plot_date_str and value is not None:
                        try:
                            plot_date = datetime.strptime(plot_date_str, '%Y-%m-%d').date()
                        except:
                            try:
                                plot_date = datetime.fromisoformat(plot_date_str.split('T')[0]).date()
                            except:
                                logger.warning(f"Could not parse date: {plot_date_str}")
                                continue
                        
                        data_points.append({
                            'artist': artist,
                            'artist_name': artist.name,
                            'artist_uuid': artist.uuid,
                            'platform': platform,
                            'platform_name': platform.name,
                            'platform_slug': platform.slug,
                            'date': plot_date,
                            'value': int(value),
                            'metric_name': platform.audience_metric_name or 'Followers'
                        })
                
                current_start = current_end + timedelta(days=1)
            
            logger.info(f"Fetched {len(data_points)} social data points for {artist.name} on {platform.name}")
            return data_points
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"No social data available for {artist.name} on {platform.name}")
            else:
                logger.error(f"HTTP error fetching social data: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching social data for {artist.name} on {platform.name}: {e}")
            return []
    
    def _fetch_radio_data(self, artist, platform, start_date, end_date, country=None):
        """
        Fetch radio airplay data from /api/v2/artist/{uuid}/broadcast-groups
        
        Returns aggregated daily radio spin counts.
        Country filter is applied if provided.
        
        Args:
            artist: Artist model instance
            platform: Platform model instance (should be 'airplay')
            start_date: Start date
            end_date: End date
            country: Optional country code to filter by
            
        Returns:
            List of data points with daily spin counts
        """
        try:
            data_points = []
            
            # Call SoundCharts radio spin count API
            # Note: API has 90-day limit, so we need to batch if period is longer
            current_start = start_date
            
            while current_start <= end_date:
                current_end = min(current_start + timedelta(days=89), end_date)
                
                # Use the service method we just created
                api_data = self.soundcharts.get_artist_radio_spin_count(
                    artist_uuid=artist.uuid,
                    start_date=current_start.strftime('%Y-%m-%d'),
                    end_date=current_end.strftime('%Y-%m-%d'),
                    country_code=country
                )
                
                if not api_data:
                    logger.warning(f"No radio data returned for {artist.name}")
                    current_start = current_end + timedelta(days=1)
                    continue
                
                # DEBUG: Log API response structure
                logger.info(f"Radio API Response for {artist.name}: {len(api_data.get('items', []))} records")
                
                # Parse response
                # Actual format from /broadcast-groups (REAL format, not docs):
                # {"items": [{"playCount": 10, "radio": {...}}, ...]}
                # Each item = total plays on ONE radio station for the entire period
                items = api_data.get('items', [])
                
                # Calculate total spins across all stations
                period_total_spins = 0
                radio_stations = set()
                
                for item in items:
                    # Extract play count (total for this station during period)
                    play_count = item.get('playCount', 0)
                    period_total_spins += play_count
                    
                    # Track unique radio stations
                    radio_info = item.get('radio', {})
                    radio_name = radio_info.get('name')
                    if radio_name:
                        radio_stations.add(radio_name)
                
                # Since we don't have daily breakdown, create a single data point for the period
                # We'll distribute the total evenly across the period for averaging purposes
                if period_total_spins > 0:
                    # Calculate average daily spins
                    period_days = (current_end - current_start).days + 1
                    avg_daily_spins = period_total_spins / period_days if period_days > 0 else period_total_spins
                    
                    # Create one data point representing the period average
                    # (This will be used for aggregation with start/end values)
                    mid_date = current_start + timedelta(days=period_days // 2)
                    
                    data_points.append({
                        'artist': artist,
                        'artist_name': artist.name,
                        'artist_uuid': artist.uuid,
                        'platform': platform,
                        'platform_name': platform.name,
                        'platform_slug': platform.slug,
                        'date': mid_date,
                        'value': avg_daily_spins,  # Average daily spins
                        'metric_name': 'Radio Spins',
                        'stations_count': len(radio_stations),
                        'total_spins': period_total_spins,  # Total for the period
                        'period_days': period_days
                    })
                    
                    logger.info(f"Processed {period_total_spins} total spins across {len(radio_stations)} stations for {artist.name}")
                
                current_start = current_end + timedelta(days=1)
            
            logger.info(f"Fetched {len(data_points)} radio data points for {artist.name}")
            return data_points
            
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 404:
                logger.warning(f"No radio data available for {artist.name}")
            else:
                logger.error(f"HTTP error fetching radio data: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching radio data for {artist.name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _aggregate_fetched_data(self, data_points, artists, platforms, start_date, end_date, country=None):
        """
        Aggregate the fetched data points into summary metrics.
        
        Args:
            data_points: List of {artist, platform, date, value} dicts
            artists: QuerySet of artists
            platforms: QuerySet of platforms
            start_date: Start date
            end_date: End date
            
        Returns:
            dict with aggregated metrics
        """
        if not data_points:
            return {
                'success': False,
                'error': 'No data points to aggregate',
                'data': None
            }
        
        # Group by platform
        platform_totals = {}
        for point in data_points:
            platform_name = point['platform_name']
            if platform_name not in platform_totals:
                platform_totals[platform_name] = {
                    'platform__name': platform_name,
                    'platform__slug': point['platform_slug'],
                    'platform__audience_metric_name': point['metric_name'],
                    'values': [],
                    'data_points': 0
                }
            platform_totals[platform_name]['values'].append(point['value'])
            platform_totals[platform_name]['data_points'] += 1
        
        # Calculate aggregates for each platform
        by_platform = []
        for platform_name, data in platform_totals.items():
            values = data['values']
            by_platform.append({
                'platform__name': platform_name,
                'platform__slug': data['platform__slug'],
                'platform__audience_metric_name': data['platform__audience_metric_name'],
                'total_audience': sum(values),
                'avg_daily': sum(values) / len(values) if values else 0,
                'peak_value': max(values) if values else 0,
                'min_value': min(values) if values else 0,
                'data_points': len(values)
            })
        
        # Sort by total audience descending
        by_platform.sort(key=lambda x: x['total_audience'], reverse=True)
        
        # Group by artist
        artist_totals = {}
        for point in data_points:
            artist_name = point['artist_name']
            if artist_name not in artist_totals:
                artist_totals[artist_name] = {
                    'artist__name': artist_name,
                    'artist__uuid': point['artist_uuid'],
                    'values': [],
                    'platforms': set()
                }
            artist_totals[artist_name]['values'].append(point['value'])
            artist_totals[artist_name]['platforms'].add(point['platform_name'])
        
        # Calculate aggregates for each artist
        by_artist = []
        for artist_name, data in artist_totals.items():
            values = data['values']
            by_artist.append({
                'artist__name': artist_name,
                'artist__uuid': data['artist__uuid'],
                'total_audience': sum(values),
                'avg_daily': sum(values) / len(values) if values else 0,
                'peak_value': max(values) if values else 0,
                'platforms_count': len(data['platforms']),
                'data_points': len(values)
            })
        
        # Sort by total audience descending
        by_artist.sort(key=lambda x: x['total_audience'], reverse=True)
        
        # Detailed breakdown (artist × platform)
        detailed = {}
        for point in data_points:
            key = (point['artist_name'], point['platform_name'])
            if key not in detailed:
                detailed[key] = {
                    'artist__name': point['artist_name'],
                    'artist__uuid': point['artist_uuid'],
                    'platform__name': point['platform_name'],
                    'platform__slug': point['platform_slug'],
                    'platform__audience_metric_name': point['metric_name'],
                    'values': [],
                    'dates': []
                }
            detailed[key]['values'].append(point['value'])
            detailed[key]['dates'].append(point['date'])
        
        # Calculate aggregates for detailed breakdown
        detailed_breakdown = []
        for key, data in detailed.items():
            values = data['values']
            dates = data['dates']
            
            # Sort by date to get first and last values
            sorted_data = sorted(zip(dates, values), key=lambda x: x[0])
            first_value = sorted_data[0][1] if sorted_data else 0
            latest_value = sorted_data[-1][1] if sorted_data else 0
            
            # Get track stream totals for this artist-platform combination
            track_streams_total = self.get_track_stream_total_for_artist_platform(
                data['artist__uuid'],
                data['platform__slug'],
                start_date,
                end_date,
                country
            )
            
            detailed_breakdown.append({
                'artist__name': data['artist__name'],
                'artist__uuid': data['artist__uuid'],
                'platform__name': data['platform__name'],
                'platform__slug': data['platform__slug'],
                'platform__audience_metric_name': data['platform__audience_metric_name'],
                'current_audience': latest_value,  # Latest value (most recent)
                'month_average': sum(values) / len(values) if values else 0,  # Average over period
                'difference': latest_value - first_value,  # Growth (latest - first)
                'peak_value': max(values) if values else 0,
                'first_value': first_value,  # Start of period
                'latest_value': latest_value,  # End of period
                'data_points': len(values),
                'total_track_streams': track_streams_total  # Sum of all track streams from charts
            })
        
        # Sort by artist name, then current audience descending
        detailed_breakdown.sort(key=lambda x: (x['artist__name'], -x['current_audience']))
        
        # Calculate overall summary with start/end values
        all_values = [p['value'] for p in data_points]
        
        # Sort all data points by date to get first and last values
        sorted_points = sorted(data_points, key=lambda x: x['date'])
        first_period_value = sorted_points[0]['value'] if sorted_points else 0
        last_period_value = sorted_points[-1]['value'] if sorted_points else 0
        
        return {
            'success': True,
            'error': None,
            'data': {
                'summary': {
                    'period_average': sum(all_values) / len(all_values) if all_values else 0,  # Average across period
                    'start_value': first_period_value,  # Value at start of period
                    'end_value': last_period_value,  # Value at end of period
                    'difference': last_period_value - first_period_value,  # Growth/decline
                    'peak_value': max(all_values) if all_values else 0,
                    'total_artists': len(artist_totals),
                    'total_platforms': len(platform_totals),
                    'date_range_days': (end_date - start_date).days + 1,
                    # Keep legacy fields for backward compatibility
                    'average_daily': sum(all_values) / len(all_values) if all_values else 0,
                    'total_audience': last_period_value,  # Same as end_value
                },
                'by_platform': by_platform,
                'by_artist': by_artist,
                'detailed_breakdown': detailed_breakdown,
                'date_range': {
                    'start': start_date,
                    'end': end_date,
                    'days': (end_date - start_date).days + 1
                },
                'metadata': {
                    'artists': [{'id': a.id, 'name': a.name, 'uuid': a.uuid} for a in artists],
                    'platforms': [{'id': p.id, 'name': p.name, 'slug': p.slug} for p in platforms],
                    'generated_at': timezone.now().isoformat(),
                    'data_source': 'soundcharts_api',
                    'total_data_points': len(data_points)
                }
            }
        }
    
    def validate_artists(self, artist_ids):
        """
        Validate that artists have SoundCharts UUIDs.
        
        NOTE: Artists from ACRCloud analysis may not have SoundCharts UUIDs.
        These artists cannot be used for audience aggregation until their
        SoundCharts UUID is populated via manual search or API matching.
        
        Args:
            artist_ids: List of artist IDs to validate
            
        Returns:
            dict with:
                - valid_artists: QuerySet of valid artists
                - invalid_artists: List of artist names without UUIDs
                - error: Error message if any
        """
        artists = Artist.objects.filter(id__in=artist_ids)
        
        # Filter artists with valid UUIDs
        valid_artists = artists.filter(
            uuid__isnull=False
        ).exclude(uuid='')
        
        # Find artists without UUIDs
        invalid_artists = artists.filter(
            Q(uuid__isnull=True) | Q(uuid='')
        )
        
        result = {
            'valid_artists': valid_artists,
            'invalid_artists': [artist.name for artist in invalid_artists],
            'error': None
        }
        
        if not valid_artists.exists():
            result['error'] = 'No valid artists selected. All artists must have SoundCharts UUIDs.'
        elif invalid_artists.exists():
            result['error'] = f"Warning: {len(invalid_artists)} artist(s) skipped (missing UUID): {', '.join(result['invalid_artists'])}"
        
        return result
    
    def check_data_availability(self, artist_ids, platform_ids, start_date, end_date):
        """
        Check if we have data for the requested parameters.
        
        Args:
            artist_ids: List of artist IDs
            platform_ids: List of platform IDs
            start_date: Start date for data range
            end_date: End date for data range
            
        Returns:
            dict with:
                - has_complete_data: bool
                - coverage_percentage: float (0-100)
                - missing_dates: list of dates with no data
                - artists_with_data: QuerySet of artists with data
                - platforms_with_data: QuerySet of platforms with data
        """
        # Validate artists first
        validation = self.validate_artists(artist_ids)
        if not validation['valid_artists'].exists():
            return {
                'has_complete_data': False,
                'coverage_percentage': 0,
                'missing_dates': [],
                'artists_with_data': Artist.objects.none(),
                'platforms_with_data': Platform.objects.none(),
                'error': validation['error']
            }
        
        valid_artists = validation['valid_artists']
        platforms = Platform.objects.filter(id__in=platform_ids)
        
        # Check what data exists
        existing_data = ArtistAudienceTimeSeries.objects.filter(
            artist__in=valid_artists,
            platform__in=platforms,
            date__range=(start_date, end_date)
        )
        
        # Calculate expected vs actual data points
        date_range = (end_date - start_date).days + 1
        expected_count = len(valid_artists) * len(platforms) * date_range
        actual_count = existing_data.count()
        
        coverage = (actual_count / expected_count * 100) if expected_count > 0 else 0
        
        # Find missing dates
        existing_dates = set(existing_data.values_list('date', flat=True).distinct())
        expected_dates = {start_date + timedelta(days=x) for x in range(date_range)}
        missing_dates = sorted(expected_dates - existing_dates)
        
        return {
            'has_complete_data': coverage >= 90,  # Consider 90%+ as complete
            'coverage_percentage': round(coverage, 1),
            'missing_dates': missing_dates,
            'artists_with_data': Artist.objects.filter(
                id__in=existing_data.values_list('artist_id', flat=True).distinct()
            ),
            'platforms_with_data': Platform.objects.filter(
                id__in=existing_data.values_list('platform_id', flat=True).distinct()
            ),
            'error': None
        }
    
    def aggregate_artist_metrics(self, artist_ids, platform_ids, start_date, end_date):
        """
        Aggregate artist-level metrics for the specified parameters.
        
        This aggregates data from ArtistAudienceTimeSeries which should be populated
        from SoundCharts streaming and social endpoints.
        
        Args:
            artist_ids: List of artist IDs to aggregate
            platform_ids: List of platform IDs to include
            start_date: Start date for aggregation
            end_date: End date for aggregation
            
        Returns:
            dict with:
                - summary: Overall metrics by platform
                - by_artist: Breakdown by artist
                - by_platform: Breakdown by platform
                - date_range: Date range info
                - metadata: Additional info (filters, timestamp, etc.)
        """
        # Validate artists
        validation = self.validate_artists(artist_ids)
        if not validation['valid_artists'].exists():
            return {
                'success': False,
                'error': validation['error'],
                'data': None
            }
        
        valid_artists = validation['valid_artists']
        platforms = Platform.objects.filter(id__in=platform_ids)
        
        # Get audience data
        queryset = ArtistAudienceTimeSeries.objects.filter(
            artist__in=valid_artists,
            platform__in=platforms,
            date__range=(start_date, end_date)
        )
        
        if not queryset.exists():
            return {
                'success': False,
                'error': 'No data available for the selected criteria. Please ensure audience data has been synced for these artists.',
                'data': None
            }
        
        # Aggregate by platform
        platform_aggregates = queryset.values(
            'platform__id',
            'platform__name',
            'platform__slug',
            'platform__audience_metric_name'
        ).annotate(
            total_audience=Sum('audience_value'),
            avg_daily=Avg('audience_value'),
            peak_value=Max('audience_value'),
            min_value=Min('audience_value'),
            data_points=Count('id')
        ).order_by('-total_audience')
        
        # Aggregate by artist
        artist_aggregates = queryset.values(
            'artist__id',
            'artist__name',
            'artist__uuid',
            'artist__imageUrl'
        ).annotate(
            total_audience=Sum('audience_value'),
            avg_daily=Avg('audience_value'),
            peak_value=Max('audience_value'),
            platforms_count=Count('platform', distinct=True),
            data_points=Count('id')
        ).order_by('-total_audience')
        
        # Aggregate by artist AND platform for detailed breakdown
        detailed_breakdown = queryset.values(
            'artist__id',
            'artist__name',
            'artist__uuid',
            'platform__id',
            'platform__name',
            'platform__slug',
            'platform__audience_metric_name'
        ).annotate(
            total_audience=Sum('audience_value'),
            avg_daily=Avg('audience_value'),
            peak_value=Max('audience_value'),
            min_value=Min('audience_value'),
            data_points=Count('id')
        ).order_by('artist__name', '-total_audience')
        
        # Calculate overall summary
        overall_total = queryset.aggregate(
            grand_total=Sum('audience_value'),
            overall_avg=Avg('audience_value'),
            overall_peak=Max('audience_value')
        )
        
        return {
            'success': True,
            'error': validation.get('error'),  # May have warnings about invalid artists
            'data': {
                'summary': {
                    'total_audience': overall_total['grand_total'] or 0,
                    'average_daily': overall_total['overall_avg'] or 0,
                    'peak_value': overall_total['overall_peak'] or 0,
                    'total_artists': valid_artists.count(),
                    'total_platforms': platforms.count(),
                    'date_range_days': (end_date - start_date).days + 1,
                },
                'by_platform': list(platform_aggregates),
                'by_artist': list(artist_aggregates),
                'detailed_breakdown': list(detailed_breakdown),
                'date_range': {
                    'start': start_date,
                    'end': end_date,
                    'days': (end_date - start_date).days + 1
                },
                'metadata': {
                    'artists': [{'id': a.id, 'name': a.name, 'uuid': a.uuid} for a in valid_artists],
                    'platforms': [{'id': p.id, 'name': p.name, 'slug': p.slug} for p in platforms],
                    'generated_at': timezone.now().isoformat(),
                    'invalid_artists': validation['invalid_artists']
                }
            }
        }
    
    def get_available_countries(self):
        """
        Get list of countries that have charts in the system.
        
        This is used to populate the country filter dropdown.
        The country filter is informational - it helps users understand
        which geographic markets we're tracking, but doesn't directly
        filter audience data (which is global per platform).
        
        TODO: Country filtering limitation
        Currently, audience data (ArtistAudienceTimeSeries) does not have country-level granularity.
        The country filter shows which countries have active charts, but audience metrics
        are global per platform. SoundCharts provides city-level data for Spotify
        (top 50 cities) which is stored in api_data JSON field.
        
        Future enhancement would require:
        1. Adding 'country' field to ArtistAudienceTimeSeries model
        2. Fetching country-specific audience data from SoundCharts
        3. Updating aggregation queries to filter by country directly
        """
        countries = Chart.objects.values(
            'country_code'
        ).distinct().order_by('country_code')
        
        return [c['country_code'] for c in countries if c['country_code']]
    
    def format_number(self, value):
        """
        Format large numbers for display (1.5M, 12.3K, etc.)
        
        Args:
            value: Numeric value to format
            
        Returns:
            Formatted string
        """
        if value is None:
            return 'N/A'
        
        if value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.1f}B"
        elif value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{value / 1_000:.1f}K"
        else:
            return f"{int(value):,}"
    
    def get_track_stream_total_for_artist_platform(self, artist_uuid, platform_slug, start_date, end_date, country=None):
        """
        Get total track streams for an artist on a specific platform.
        
        This aggregates all track streams from chart ranking data for a given artist-platform
        combination during the specified date range.
        
        Args:
            artist_uuid: Artist UUID
            platform_slug: Platform slug
            start_date: Start date
            end_date: End date
            country: Optional country filter
            
        Returns:
            int: Total streams across all tracks
        """
        from apps.soundcharts.models import Track, ChartRankingEntry
        
        try:
            # Get artist by UUID
            artist = Artist.objects.get(uuid=artist_uuid)
            platform = Platform.objects.get(slug=platform_slug)
            
            # Special handling for radio/airplay: sum radio spins across all tracks via SoundCharts API
            if platform.slug.lower() in ['airplay', 'radio']:
                try:
                    # Reuse the radio breakdown to obtain a correct total
                    radio_result = self._get_track_radio_breakdown(artist, platform, start_date, end_date, country)
                    if radio_result.get('success') and radio_result.get('summary'):
                        return radio_result['summary'].get('total_spins', 0) or 0
                    return 0
                except Exception as e:
                    logger.error(f"Error aggregating radio spins total: {e}")
                    return 0

            # For non-radio platforms, sum chart metrics across all tracks
            tracks = Track.objects.filter(artists=artist)
            if not tracks.exists():
                return 0
            chart_entries = ChartRankingEntry.objects.filter(
                track__in=tracks,
                ranking__ranking_date__range=(start_date, end_date),
                ranking__chart__platform=platform
            )
            total_streams = 0
            for entry in chart_entries:
                metric = entry.api_data.get('metric', 0) if entry.api_data else 0
                total_streams += metric
            return total_streams
            
        except (Artist.DoesNotExist, Platform.DoesNotExist):
            logger.warning(f"Artist {artist_uuid} or platform {platform_slug} not found for track aggregation")
            return 0
        except Exception as e:
            logger.error(f"Error calculating track stream totals: {e}")
            return 0
    
    def get_track_breakdown_for_artist(self, artist_id, platform_id, start_date, end_date, country=None):
        """
        Get track-level breakdown for an artist on a specific platform.
        
        Phase 2: Shows which tracks contributed to the artist's audience metrics.
        Uses chart ranking data to get stream counts per track.
        
        Args:
            artist_id: Artist ID
            platform_id: Platform ID
            start_date: Start date for period
            end_date: End date for period
            country: Optional country filter
            
        Returns:
            dict with:
                - tracks: List of tracks with streaming metrics
                - total_streams: Sum of all track streams
                - top_track: Track with most streams
                - summary: Aggregated metrics
        """
        from apps.soundcharts.models import Track, ChartRankingEntry
        
        try:
            artist = Artist.objects.get(id=artist_id)
            platform = Platform.objects.get(id=platform_id)
        except (Artist.DoesNotExist, Platform.DoesNotExist):
            return {
                'success': False,
                'error': 'Artist or platform not found'
            }
        
        # Check if this is a radio platform - handle differently
        if platform.slug.lower() in ['airplay', 'radio']:
            return self._get_track_radio_breakdown(artist, platform, start_date, end_date, country)
        
        # Get all tracks for this artist
        tracks = Track.objects.filter(artists=artist)
        
        if not tracks.exists():
            return {
                'success': False,
                'error': f'No tracks found for {artist.name}'
            }
        
        # Get chart entries for these tracks in the date range
        chart_entries = ChartRankingEntry.objects.filter(
            track__in=tracks,
            ranking__ranking_date__range=(start_date, end_date),
            ranking__chart__platform=platform
        ).select_related('track', 'ranking', 'ranking__chart')
        
        if not chart_entries.exists():
            return {
                'success': False,
                'error': f'No chart data found for {artist.name} on {platform.name} in the selected period. Tracks may not have charted during this time.',
                'tracks': []
            }
        
        # Aggregate by track
        track_data = {}
        for entry in chart_entries:
            track_id = entry.track.id
            
            if track_id not in track_data:
                track_data[track_id] = {
                    'track_name': entry.track.name,
                    'track_uuid': entry.track.uuid,
                    'track_credit': entry.track.credit_name or '',
                    'stream_counts': [],
                    'positions': [],
                    'dates': [],
                    'weeks_on_chart': entry.weeks_on_chart or 0,
                    'entry_date': entry.entry_date,  # From API
                    'first_appearance': entry.ranking.ranking_date,  # Track first appearance in our data
                    'last_appearance': entry.ranking.ranking_date   # Track last appearance in our data
                }
            
            # Extract metric (stream count) from api_data
            metric = entry.api_data.get('metric', 0) if entry.api_data else 0
            track_data[track_id]['stream_counts'].append(metric)
            track_data[track_id]['positions'].append(entry.position)
            track_data[track_id]['dates'].append(entry.ranking.ranking_date.date())
            
            # Update first and last appearance dates
            if entry.ranking.ranking_date < track_data[track_id]['first_appearance']:
                track_data[track_id]['first_appearance'] = entry.ranking.ranking_date
            if entry.ranking.ranking_date > track_data[track_id]['last_appearance']:
                track_data[track_id]['last_appearance'] = entry.ranking.ranking_date
            
            # Update entry_date if this entry has one and we don't have it yet
            if entry.entry_date and not track_data[track_id]['entry_date']:
                track_data[track_id]['entry_date'] = entry.entry_date
        
        # Calculate aggregates for each track
        track_list = []
        total_streams = 0
        
        for track_id, data in track_data.items():
            streams = data['stream_counts']
            positions = data['positions']
            
            track_total = sum(streams)
            track_avg = sum(streams) / len(streams) if streams else 0
            track_peak = max(streams) if streams else 0
            best_position = min(positions) if positions else 999
            
            total_streams += track_total
            
            track_list.append({
                'track_name': data['track_name'],
                'track_uuid': data['track_uuid'],
                'track_credit': data['track_credit'],
                'total_streams': track_total,
                'avg_daily_streams': track_avg,
                'peak_streams': track_peak,
                'best_position': best_position,
                'weeks_on_chart': data['weeks_on_chart'],
                'data_points': len(streams),
                'entry_date': data['entry_date'].isoformat() if data['entry_date'] else None,
                'first_appearance': data['first_appearance'].date().isoformat() if data['first_appearance'] else None,
                'last_appearance': data['last_appearance'].date().isoformat() if data['last_appearance'] else None,
            })
        
        # Sort by total streams descending
        track_list.sort(key=lambda x: x['total_streams'], reverse=True)
        
        top_track = track_list[0] if track_list else None
        
        return {
            'success': True,
            'artist': {
                'id': artist.id,
                'name': artist.name,
                'uuid': artist.uuid
            },
            'platform': {
                'id': platform.id,
                'name': platform.name,
                'slug': platform.slug
            },
            'period': {
                'start': start_date,
                'end': end_date,
                'days': (end_date - start_date).days + 1
            },
            'tracks': track_list,
            'summary': {
                'total_tracks': len(track_list),
                'total_streams': total_streams,
                'avg_streams_per_track': total_streams / len(track_list) if track_list else 0,
            },
            'top_track': top_track,
            'data_source': 'chart_rankings',
            'note': 'Stream counts from chart ranking data. Only includes tracks that appeared in charts during the period.'
        }
    
    def _get_track_radio_breakdown(self, artist, platform, start_date, end_date, country=None):
        """
        Get track-level radio spin breakdown for an artist.
        
        Calls SoundCharts API to get track-by-track radio spins.
        
        Args:
            artist: Artist model instance
            platform: Platform model instance (airplay)
            start_date: Start date
            end_date: End date
            country: Optional country filter
            
        Returns:
            dict with track breakdown data
        """
        from apps.soundcharts.models import Track
        
        # Get all tracks for this artist
        tracks = Track.objects.filter(artists=artist)
        
        if not tracks.exists():
            return {
                'success': False,
                'error': f'No tracks found for {artist.name}'
            }
        
        # Fetch radio spin data for each track
        track_list = []
        total_spins = 0
        
        for track in tracks:
            try:
                # Call track radio spin count API
                api_data = self.soundcharts.get_track_radio_spin_count(
                    track_uuid=track.uuid,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    country_code=country
                )
                
                if not api_data or not api_data.get('items'):
                    continue
                
                # Aggregate spins for this track
                # Actual format from /broadcast-groups (REAL format, not docs):
                # {"items": [{"playCount": 10, "radio": {...}}, ...]}
                # Each item = total plays on ONE radio station for the entire period
                items = api_data.get('items', [])
                
                track_total_spins = 0
                radio_stations = set()
                
                for item in items:
                    # Extract play count (total for this station during period)
                    play_count = item.get('playCount', 0)
                    track_total_spins += play_count
                    
                    # Track unique stations
                    radio_info = item.get('radio', {})
                    if radio_info.get('name'):
                        radio_stations.add(radio_info['name'])
                
                if track_total_spins > 0:
                    # Calculate metrics
                    period_days = (end_date - start_date).days + 1
                    avg_daily = track_total_spins / period_days if period_days > 0 else 0
                    
                    # Note: We don't have daily breakdown, so we can't calculate true peak
                    # Use total as a proxy for impact
                    peak_spins = track_total_spins
                    
                    track_list.append({
                        'track_name': track.name,
                        'track_uuid': track.uuid,
                        'track_credit': track.credit_name or '',
                        'total_streams': track_total_spins,  # For consistency with chart-based data
                        'total_spins': track_total_spins,
                        'avg_daily_streams': avg_daily,
                        'peak_streams': peak_spins,
                        'stations_count': len(radio_stations),
                        'data_points': period_days,  # Period duration in days
                        'best_position': None,  # N/A for radio
                        'weeks_on_chart': None,  # N/A for radio
                        'entry_date': None,
                        'first_appearance': None,
                        'last_appearance': None,
                    })
                    
                    total_spins += track_total_spins
                    
            except Exception as e:
                logger.error(f"Error fetching radio spins for track {track.uuid}: {e}")
                continue
        
        if not track_list:
            return {
                'success': False,
                'error': f'No radio airplay data found for {artist.name} in the selected period.',
                'tracks': []
            }
        
        # Sort by total spins descending
        track_list.sort(key=lambda x: x['total_spins'], reverse=True)
        
        top_track = track_list[0] if track_list else None
        
        return {
            'success': True,
            'artist': {
                'id': artist.id,
                'name': artist.name,
                'uuid': artist.uuid
            },
            'platform': {
                'id': platform.id,
                'name': platform.name,
                'slug': platform.slug
            },
            'period': {
                'start': start_date,
                'end': end_date,
                'days': (end_date - start_date).days + 1
            },
            'tracks': track_list,
            'summary': {
                'total_tracks': len(track_list),
                'total_streams': total_spins,  # For consistency
                'total_spins': total_spins,
                'avg_streams_per_track': total_spins / len(track_list) if track_list else 0,
            },
            'top_track': top_track,
            'data_source': 'radio_api',
            'note': 'Radio airplay counts from SoundCharts API. Shows tracks that received radio spins during the period.'
        }

