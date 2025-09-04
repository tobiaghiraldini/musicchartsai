from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import Track, Platform, TrackAudienceTimeSeries
from .audience_processor import AudienceDataProcessor
import json
import logging

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class TopArtistsView(View):

    def get(self, request):
        """
        Get top artists
        """
        return JsonResponse({
            'success': True,
            'artists': [
                {
                    'name': 'Artist 1',
                    'slug': 'artist-1',
                    'metric_name': 'Listeners'
                }
            ]
        })

@method_decorator(login_required, name='dispatch')
class TopSongsView(View):
    """
    View for getting top songs
    """
    
    def get(self, request):
        """
        Get top songs
        """
        return JsonResponse({
            'success': True,
            'songs': [
                {
                    'name': 'Song 1',
                    'slug': 'song-1',
                    'metric_name': 'Listeners'
                }
            ]
        })

@method_decorator(login_required, name="dispatch")
class PlatformListView(View):
    """
    View for listing platforms
    """
    
    def get(self, request):
        """
        Get all platforms
        """
        platforms = Platform.objects.all().values('name', 'slug', 'audience_metric_name')
        return JsonResponse({
            'success': True,
            'platforms': {platforms}
        })

@method_decorator(login_required, name='dispatch')
class AudienceChartView(View):
    """
    View for providing audience chart data
    """
    
    def get(self, request, track_uuid, platform_slug=None):
        """
        Get audience chart data for a track
        
        Args:
            track_uuid: SoundCharts track UUID
            platform_slug: Platform slug (optional, if not provided returns all platforms)
        """
        try:
            track = get_object_or_404(Track, uuid=track_uuid)
            
            if platform_slug:
                # Single platform chart data
                try:
                    platform = Platform.objects.get(slug=platform_slug)
                    chart_data = self._get_single_platform_data(track, platform, request)
                    return JsonResponse({
                        'success': True,
                        'track': {
                            'name': track.name,
                            'credit_name': track.credit_name,
                            'uuid': track.uuid
                        },
                        'platform': {
                            'name': platform.name,
                            'slug': platform.slug,
                            'metric_name': platform.audience_metric_name
                        },
                        'chart_data': chart_data
                    })
                except Platform.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': f'Platform {platform_slug} not found'
                    }, status=404)
            else:
                # Multi-platform comparison data
                platforms = Platform.objects.filter(
                    audience_timeseries__track=track
                ).distinct()
                
                if not platforms.exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'No audience data found for this track'
                    }, status=404)
                
                chart_data = self._get_multi_platform_data(track, platforms, request)
                return JsonResponse({
                    'success': True,
                    'track': {
                        'name': track.name,
                        'credit_name': track.credit_name,
                        'uuid': track.uuid
                    },
                    'platforms': [{
                        'name': p.name,
                        'slug': p.slug,
                        'metric_name': p.audience_metric_name
                    } for p in platforms],
                    'chart_data': chart_data
                })
                
        except Exception as e:
            logger.error(f"Error in AudienceChartView: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    def _get_single_platform_data(self, track, platform, request):
        """Get chart data for a single platform"""
        # Get query parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        limit = request.GET.get('limit')
        
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                limit = None
        
        # Get the data using the model method
        try:
            data = track.get_audience_chart_data(
                platform, 
                start_date=start_date, 
                end_date=end_date, 
                limit=limit
            )
            # Convert to list to avoid queryset issues
            data = list(data)
            logger.info(f"Retrieved {len(data)} data points for {track.name} on {platform.name}")
        except Exception as e:
            logger.error(f"Error getting chart data for {track.name} on {platform.name}: {e}")
            data = []
        
        # Format for charting libraries
        chart_data = {
            'labels': [item['date'].strftime('%Y-%m-%d') for item in data],
            'datasets': [{
                'label': f'{track.name} on {platform.name}',
                'data': [item['audience_value'] for item in data],
                'borderColor': '#3b82f6',
                'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                'tension': 0.1
            }]
        }
        
        return chart_data
    
    def _get_multi_platform_data(self, track, platforms, request):
        """Get chart data for multiple platforms comparison"""
        # Get query parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        limit = request.GET.get('limit')
        
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                limit = None
        
        # Get the data using the model method
        try:
            data = track.get_platform_audience_comparison(
                platforms, 
                start_date=start_date, 
                end_date=end_date, 
                limit=limit
            )
            # Convert to list to avoid queryset issues
            data = list(data)
            logger.info(f"Retrieved {len(data)} data points for {track.name} across {len(platforms)} platforms")
        except Exception as e:
            logger.error(f"Error getting platform comparison data for {track.name}: {e}")
            data = []
        
        # Group data by platform
        platform_data = {}
        dates = set()
        
        for item in data:
            platform_name = item['platform__name']
            date = item['date'].strftime('%Y-%m-%d')
            value = item['audience_value']
            
            if platform_name not in platform_data:
                platform_data[platform_name] = {}
            
            platform_data[platform_name][date] = value
            dates.add(date)
        
        # Sort dates
        sorted_dates = sorted(list(dates))
        
        # Create chart datasets
        datasets = []
        colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899']
        
        for i, (platform_name, date_values) in enumerate(platform_data.items()):
            color = colors[i % len(colors)]
            data_values = [date_values.get(date, None) for date in sorted_dates]
            
            datasets.append({
                'label': f'{track.name} on {platform_name}',
                'data': data_values,
                'borderColor': color,
                'backgroundColor': f'{color}20',
                'tension': 0.1
            })
        
        chart_data = {
            'labels': sorted_dates,
            'datasets': datasets
        }
        
        return chart_data


@method_decorator(login_required, name='dispatch')
class AudienceDataRefreshView(View):
    """
    View for manually refreshing audience data
    """
    
    def post(self, request, track_uuid, platform_slug):
        """
        Manually refresh audience data for a track on a specific platform
        """
        try:
            track = get_object_or_404(Track, uuid=track_uuid)
            platform = get_object_or_404(Platform, slug=platform_slug)
            
            # Process the data
            processor = AudienceDataProcessor()
            result = processor.process_and_store_audience_data(
                track_uuid, 
                platform_slug, 
                force_refresh=True
            )
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': f'Successfully refreshed audience data for {track.name} on {platform.name}',
                    'records_created': result['records_created'],
                    'records_updated': result['records_updated']
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                }, status=400)
                
        except Exception as e:
            logger.error(f"Error in AudienceDataRefreshView: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)


# Legacy view for backward compatibility
@login_required
def audience_chart_data(request, track_uuid, platform_slug=None):
    """Legacy function-based view for audience chart data"""
    view = AudienceChartView()
    return view.get(request, track_uuid, platform_slug)


@method_decorator(login_required, name='dispatch')
class AudienceDashboardView(View):
    """
    View for the audience dashboard page
    """
    
    def get(self, request):
        """Render the audience dashboard page"""
        return render(request, 'dashboard/audience_charts.html')


@method_decorator(login_required, name='dispatch')
class TracksWithAudienceView(View):
    """
    API view to get tracks with audience data for the dashboard
    """
    
    def get(self, request):
        """
        Get all tracks that have audience data
        """
        try:
            # Get tracks that have audience time-series data
            tracks_with_audience = Track.objects.filter(
                audience_timeseries__isnull=False
            ).distinct().select_related().prefetch_related('audience_timeseries__platform')
            
            tracks_data = []
            
            for track in tracks_with_audience:
                # Get platforms for this track
                platforms = Platform.objects.filter(
                    audience_timeseries__track=track
                ).distinct()
                
                # Get latest audience data for each platform
                platforms_data = []
                for platform in platforms:
                    latest_audience = TrackAudienceTimeSeries.objects.filter(
                        track=track,
                        platform=platform
                    ).order_by('-date').first()
                    
                    platforms_data.append({
                        'name': platform.name,
                        'slug': platform.slug,
                        'metric_name': platform.audience_metric_name,
                        'latest_value': latest_audience.audience_value if latest_audience else 0,
                        'latest_date': latest_audience.date.isoformat() if latest_audience else None,
                        'data_points': TrackAudienceTimeSeries.objects.filter(
                            track=track,
                            platform=platform
                        ).count()
                    })
                
                tracks_data.append({
                    'uuid': track.uuid,
                    'name': track.name,
                    'credit_name': track.credit_name,
                    'image_url': track.image_url,
                    'audience_fetched_at': track.audience_fetched_at.isoformat() if track.audience_fetched_at else None,
                    'platforms': platforms_data
                })
            
            return JsonResponse({
                'success': True,
                'tracks': tracks_data,
                'total_tracks': len(tracks_data)
            })
            
        except Exception as e:
            logger.error(f"Error in TracksWithAudienceView: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)