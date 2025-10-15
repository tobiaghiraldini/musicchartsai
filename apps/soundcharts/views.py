from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Track, Platform, Artist, TrackAudienceTimeSeries, ArtistAudienceTimeSeries, ChartRankingEntry, ChartSyncSchedule, ChartSyncExecution, Chart
from .audience_processor import AudienceDataProcessor
from .tasks import sync_chart_rankings_task
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
            ).distinct().select_related('primary_artist').prefetch_related('audience_timeseries__platform')
            
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
                
                # Include artist information
                artist_data = None
                if track.primary_artist:
                    artist_data = {
                        'uuid': track.primary_artist.uuid,
                        'name': track.primary_artist.name,
                        'slug': track.primary_artist.slug,
                    }
                
                tracks_data.append({
                    'uuid': track.uuid,
                    'name': track.name,
                    'credit_name': track.credit_name,
                    'image_url': track.image_url,
                    'artist': artist_data,
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


@method_decorator(login_required, name='dispatch')
class SongAudienceDetailView(View):
    """
    View for displaying detailed audience analytics for a specific song
    """
    
    def get(self, request, track_uuid):
        """
        Display detailed audience analytics for a specific track
        """
        try:
            # Get the track
            track = get_object_or_404(Track, uuid=track_uuid)
            
            # Check if audience data needs to be fetched
            _check_and_fetch_audience_data(track)
            
            # Get platforms that have audience data for this track
            platforms = Platform.objects.filter(
                audience_timeseries__track=track
            ).distinct().order_by('name')
            
            # Get latest audience data for each platform
            platforms_data = []
            for platform in platforms:
                latest_audience = TrackAudienceTimeSeries.objects.filter(
                    track=track,
                    platform=platform
                ).order_by('-date').first()
                
                platforms_data.append({
                    'platform': platform,
                    'latest_audience': latest_audience,
                    'data_points': TrackAudienceTimeSeries.objects.filter(
                        track=track,
                        platform=platform
                    ).count()
                })
            
            # Get recent chart rankings for this track
            recent_rankings = ChartRankingEntry.objects.filter(
                track=track
            ).select_related('ranking__chart').order_by('-ranking__ranking_date')[:10]
            
            # Get related tracks (same artist or similar genres)
            related_tracks = []
            if track.primary_artist:
                related_tracks = Track.objects.filter(
                    primary_artist=track.primary_artist
                ).exclude(uuid=track.uuid)[:5]
            elif track.artists.exists():
                related_tracks = Track.objects.filter(
                    artists__in=track.artists.all()
                ).exclude(uuid=track.uuid).distinct()[:5]
            
            context = {
                'track': track,
                'platforms_data': platforms_data,
                'recent_rankings': recent_rankings,
                'related_tracks': related_tracks,
                'segment': 'charts',
            }
            
            return render(request, 'soundcharts/song_audience_detail.html', context)
            
        except Exception as e:
            logger.error(f"Error in SongAudienceDetailView: {e}")
            return render(request, 'soundcharts/song_audience_detail.html', {
                'error': 'Failed to load song details',
                'segment': 'charts',
            })


# Chart Sync API Views
@method_decorator(staff_member_required, name='dispatch')
class ChartSyncScheduleAPIView(View):
    """
    API view for managing chart sync schedules
    """
    
    def get(self, request):
        """Get all chart sync schedules"""
        try:
            schedules = ChartSyncSchedule.objects.select_related('chart', 'chart__platform').all()
            
            schedules_data = []
            for schedule in schedules:
                schedules_data.append({
                    'id': schedule.id,
                    'chart': {
                        'id': schedule.chart.id,
                        'name': schedule.chart.name,
                        'platform': schedule.chart.platform.name if schedule.chart.platform else None,
                        'frequency': schedule.chart.frequency,
                    },
                    'is_active': schedule.is_active,
                    'sync_frequency': schedule.sync_frequency,
                    'custom_interval_hours': schedule.custom_interval_hours,
                    'last_sync_at': schedule.last_sync_at.isoformat() if schedule.last_sync_at else None,
                    'next_sync_at': schedule.next_sync_at.isoformat() if schedule.next_sync_at else None,
                    'total_executions': schedule.total_executions,
                    'successful_executions': schedule.successful_executions,
                    'failed_executions': schedule.failed_executions,
                    'success_rate': schedule.success_rate,
                    'is_overdue': schedule.is_overdue,
                    'created_at': schedule.created_at.isoformat(),
                })
            
            return JsonResponse({
                'success': True,
                'schedules': schedules_data
            })
            
        except Exception as e:
            logger.error(f"Error getting chart sync schedules: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def post(self, request):
        """Create a new chart sync schedule"""
        try:
            data = json.loads(request.body)
            chart_id = data.get('chart_id')
            
            if not chart_id:
                return JsonResponse({
                    'success': False,
                    'error': 'chart_id is required'
                }, status=400)
            
            chart = get_object_or_404(Chart, id=chart_id)
            
            # Check if schedule already exists
            if ChartSyncSchedule.objects.filter(chart=chart).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Chart sync schedule already exists for this chart'
                }, status=400)
            
            # Create new schedule
            schedule = ChartSyncSchedule.objects.create(
                chart=chart,
                created_by=request.user,
                is_active=data.get('is_active', True),
                sync_frequency=data.get('sync_frequency'),
                custom_interval_hours=data.get('custom_interval_hours'),
                sync_immediately=data.get('sync_immediately', False),
                sync_historical_data=data.get('sync_historical_data', True),
                fetch_track_metadata=data.get('fetch_track_metadata', True),
            )
            
            return JsonResponse({
                'success': True,
                'schedule': {
                    'id': schedule.id,
                    'chart': {
                        'id': schedule.chart.id,
                        'name': schedule.chart.name,
                    },
                    'is_active': schedule.is_active,
                    'sync_frequency': schedule.sync_frequency,
                    'custom_interval_hours': schedule.custom_interval_hours,
                    'sync_immediately': schedule.sync_immediately,
                    'sync_historical_data': schedule.sync_historical_data,
                    'fetch_track_metadata': schedule.fetch_track_metadata,
                    'next_sync_at': schedule.next_sync_at.isoformat() if schedule.next_sync_at else None,
                }
            })
            
        except Exception as e:
            logger.error(f"Error creating chart sync schedule: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(staff_member_required, name='dispatch')
class ChartSyncScheduleDetailAPIView(View):
    """
    API view for managing individual chart sync schedules
    """
    
    def get(self, request, schedule_id):
        """Get a specific chart sync schedule"""
        try:
            schedule = get_object_or_404(ChartSyncSchedule, id=schedule_id)
            
            # Get recent executions
            executions = ChartSyncExecution.objects.filter(
                schedule=schedule
            ).order_by('-started_at')[:10]
            
            executions_data = []
            for execution in executions:
                executions_data.append({
                    'id': execution.id,
                    'status': execution.status,
                    'started_at': execution.started_at.isoformat(),
                    'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                    'duration': execution.duration,
                    'rankings_created': execution.rankings_created,
                    'rankings_updated': execution.rankings_updated,
                    'tracks_created': execution.tracks_created,
                    'tracks_updated': execution.tracks_updated,
                    'error_message': execution.error_message,
                })
            
            return JsonResponse({
                'success': True,
                'schedule': {
                    'id': schedule.id,
                    'chart': {
                        'id': schedule.chart.id,
                        'name': schedule.chart.name,
                        'platform': schedule.chart.platform.name if schedule.chart.platform else None,
                        'frequency': schedule.chart.frequency,
                    },
                    'is_active': schedule.is_active,
                    'sync_frequency': schedule.sync_frequency,
                    'custom_interval_hours': schedule.custom_interval_hours,
                    'last_sync_at': schedule.last_sync_at.isoformat() if schedule.last_sync_at else None,
                    'next_sync_at': schedule.next_sync_at.isoformat() if schedule.next_sync_at else None,
                    'total_executions': schedule.total_executions,
                    'successful_executions': schedule.successful_executions,
                    'failed_executions': schedule.failed_executions,
                    'success_rate': schedule.success_rate,
                    'is_overdue': schedule.is_overdue,
                    'created_at': schedule.created_at.isoformat(),
                    'executions': executions_data,
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting chart sync schedule {schedule_id}: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def put(self, request, schedule_id):
        """Update a chart sync schedule"""
        try:
            schedule = get_object_or_404(ChartSyncSchedule, id=schedule_id)
            data = json.loads(request.body)
            
            # Update fields
            if 'is_active' in data:
                schedule.is_active = data['is_active']
            if 'sync_frequency' in data:
                schedule.sync_frequency = data['sync_frequency']
            if 'custom_interval_hours' in data:
                schedule.custom_interval_hours = data['custom_interval_hours']
            
            schedule.save()
            
            return JsonResponse({
                'success': True,
                'schedule': {
                    'id': schedule.id,
                    'is_active': schedule.is_active,
                    'sync_frequency': schedule.sync_frequency,
                    'custom_interval_hours': schedule.custom_interval_hours,
                    'next_sync_at': schedule.next_sync_at.isoformat() if schedule.next_sync_at else None,
                }
            })
            
        except Exception as e:
            logger.error(f"Error updating chart sync schedule {schedule_id}: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def delete(self, request, schedule_id):
        """Delete a chart sync schedule"""
        try:
            schedule = get_object_or_404(ChartSyncSchedule, id=schedule_id)
            chart_name = schedule.chart.name
            schedule.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Chart sync schedule for "{chart_name}" deleted successfully'
            })
            
        except Exception as e:
            logger.error(f"Error deleting chart sync schedule {schedule_id}: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(staff_member_required, name='dispatch')
class ChartSyncTriggerAPIView(View):
    """
    API view for triggering manual chart syncs
    """
    
    def post(self, request):
        """Trigger manual sync for a chart"""
        try:
            data = json.loads(request.body)
            chart_id = data.get('chart_id')
            
            if not chart_id:
                return JsonResponse({
                    'success': False,
                    'error': 'chart_id is required'
                }, status=400)
            
            chart = get_object_or_404(Chart, id=chart_id)
            
            try:
                schedule = ChartSyncSchedule.objects.get(chart=chart)
            except ChartSyncSchedule.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Chart sync schedule not found for this chart'
                }, status=404)
            
            if not schedule.is_active:
                return JsonResponse({
                    'success': False,
                    'error': 'Chart sync schedule is not active'
                }, status=400)
            
            # Create execution record
            execution = ChartSyncExecution.objects.create(
                schedule=schedule,
                status='pending'
            )
            
            # Queue the sync task
            task = sync_chart_rankings_task.delay(schedule.id, execution.id)
            execution.celery_task_id = task.id
            execution.status = 'running'
            execution.save()
            
            return JsonResponse({
                'success': True,
                'execution': {
                    'id': execution.id,
                    'status': execution.status,
                    'celery_task_id': execution.celery_task_id,
                    'started_at': execution.started_at.isoformat(),
                },
                'message': f'Manual sync triggered for chart "{chart.name}"'
            })
            
        except Exception as e:
            logger.error(f"Error triggering manual sync: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(staff_member_required, name='dispatch')
class ChartSyncStatusAPIView(View):
    """
    API view for getting chart sync status
    """
    
    def get(self, request, chart_id):
        """Get sync status for a specific chart"""
        try:
            chart = get_object_or_404(Chart, id=chart_id)
            
            try:
                schedule = ChartSyncSchedule.objects.get(chart=chart)
                
                # Get latest execution
                latest_execution = ChartSyncExecution.objects.filter(
                    schedule=schedule
                ).order_by('-started_at').first()
                
                return JsonResponse({
                    'success': True,
                    'status': {
                        'has_schedule': True,
                        'is_active': schedule.is_active,
                        'sync_frequency': schedule.sync_frequency,
                        'last_sync_at': schedule.last_sync_at.isoformat() if schedule.last_sync_at else None,
                        'next_sync_at': schedule.next_sync_at.isoformat() if schedule.next_sync_at else None,
                        'total_executions': schedule.total_executions,
                        'success_rate': schedule.success_rate,
                        'is_overdue': schedule.is_overdue,
                        'latest_execution': {
                            'id': latest_execution.id,
                            'status': latest_execution.status,
                            'started_at': latest_execution.started_at.isoformat(),
                            'completed_at': latest_execution.completed_at.isoformat() if latest_execution.completed_at else None,
                            'error_message': latest_execution.error_message,
                        } if latest_execution else None,
                    }
                })
                
            except ChartSyncSchedule.DoesNotExist:
                return JsonResponse({
                    'success': True,
                    'status': {
                        'has_schedule': False,
                        'is_active': False,
                    }
                })
            
        except Exception as e:
            logger.error(f"Error getting chart sync status for chart {chart_id}: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


def _check_and_fetch_audience_data(track):
    """
    Check if audience data needs to be fetched and trigger fetch if needed
    """
    from datetime import timedelta
    from django.utils import timezone
    from .tasks import fetch_track_audience_data
    
    # Check if audience data is stale or missing
    should_fetch = False
    
    if not track.audience_fetched_at:
        # Never fetched audience data
        should_fetch = True
    else:
        # Check if audience data is older than 7 days
        cutoff_date = timezone.now() - timedelta(days=7)
        if track.audience_fetched_at < cutoff_date:
            should_fetch = True
    
    # Check if track has any audience data at all
    if not TrackAudienceTimeSeries.objects.filter(track=track).exists():
        should_fetch = True
    
    if should_fetch:
        # Queue audience data fetch task
        fetch_track_audience_data.delay(track.uuid)
        logger.info(f"Queued audience data fetch for track {track.uuid}")


# ============================================================================
# ARTIST VIEWS
# ============================================================================

@method_decorator(login_required, name='dispatch')
class ArtistSearchView(View):
    """View for searching artists via Soundcharts API"""
    
    def get(self, request):
        """Render the artist search page"""
        return render(request, 'soundcharts/artist_search.html', {
            'segment': 'artists',
        })
    
    def post(self, request):
        """Search for artists via API"""
        try:
            data = json.loads(request.body)
            query = data.get('query', '').strip()
            
            if not query:
                return JsonResponse({
                    'success': False,
                    'error': 'Search query is required'
                }, status=400)
            
            from .service import SoundchartsService
            service = SoundchartsService()
            
            # Search for artists
            results = service.search_artists(query, limit=20)
            
            if results:
                return JsonResponse({
                    'success': True,
                    'artists': results
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No artists found or API error occurred'
                })
                
        except Exception as e:
            logger.error(f"Error searching artists: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(login_required, name='dispatch')
class ArtistListView(View):
    """View for listing stored artists"""
    
    def get(self, request):
        """Get all stored artists with their audience data"""
        try:
            artists = Artist.objects.all().prefetch_related(
                'genres', 
                'audience_timeseries__platform'
            ).order_by('name')
            
            artists_data = []
            for artist in artists:
                # Get platforms that have audience data
                platforms_with_data = Platform.objects.filter(
                    artist_audience_timeseries__artist=artist
                ).distinct()
                
                artists_data.append({
                    'id': artist.id,
                    'uuid': artist.uuid,
                    'name': artist.name,
                    'slug': artist.slug,
                    'image_url': artist.imageUrl,
                    'country_code': artist.countryCode,
                    'career_stage': artist.careerStage,
                    'has_audience_data': platforms_with_data.exists(),
                    'platforms_count': platforms_with_data.count(),
                    'metadata_fetched': artist.metadata_fetched_at is not None,
                    'audience_fetched': artist.audience_fetched_at is not None,
                })
            
            return render(request, 'soundcharts/artist_list.html', {
                'artists': artists_data,
                'segment': 'artists',
            })
            
        except Exception as e:
            logger.error(f"Error in ArtistListView: {e}")
            return render(request, 'soundcharts/artist_list.html', {
                'error': 'Failed to load artists',
                'segment': 'artists',
            })


@method_decorator(login_required, name='dispatch')
class ArtistDetailView(View):
    """View for displaying detailed analytics for a specific artist"""
    
    def get(self, request, artist_uuid):
        """Display detailed audience analytics for a specific artist"""
        try:
            # Get the artist
            artist = get_object_or_404(Artist, uuid=artist_uuid)
            
            # Get platforms that have audience data for this artist
            platforms = Platform.objects.filter(
                artist_audience_timeseries__artist=artist
            ).distinct().order_by('name')
            
            # Get latest audience data for each platform
            platforms_data = []
            for platform in platforms:
                latest_audience = ArtistAudienceTimeSeries.objects.filter(
                    artist=artist,
                    platform=platform
                ).order_by('-date').first()
                
                platforms_data.append({
                    'platform': platform,
                    'latest_audience': latest_audience,
                    'data_points': ArtistAudienceTimeSeries.objects.filter(
                        artist=artist,
                        platform=platform
                    ).count()
                })
            
            # Get tracks by this artist
            related_tracks = Track.objects.filter(
                Q(primary_artist=artist) | Q(artists=artist)
            ).distinct()[:10]
            
            context = {
                'artist': artist,
                'platforms_data': platforms_data,
                'related_tracks': related_tracks,
                'segment': 'artists',
            }
            
            return render(request, 'soundcharts/artist_detail.html', context)
            
        except Exception as e:
            logger.error(f"Error in ArtistDetailView: {e}")
            return render(request, 'soundcharts/artist_detail.html', {
                'error': 'Failed to load artist details',
                'segment': 'artists',
            })


@method_decorator(login_required, name='dispatch')
class ArtistAudienceChartView(View):
    """View for providing artist audience chart data"""
    
    def get(self, request, artist_uuid, platform_slug=None):
        """Get audience chart data for an artist"""
        try:
            artist = get_object_or_404(Artist, uuid=artist_uuid)
            
            if platform_slug:
                # Single platform chart data
                try:
                    platform = Platform.objects.get(slug=platform_slug)
                    chart_data = self._get_single_platform_data(artist, platform, request)
                    return JsonResponse({
                        'success': True,
                        'artist': {
                            'name': artist.name,
                            'uuid': artist.uuid
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
                # All platforms chart data
                platforms = Platform.objects.filter(
                    artist_audience_timeseries__artist=artist
                ).distinct()
                
                platforms_data = []
                for platform in platforms:
                    chart_data = self._get_single_platform_data(artist, platform, request)
                    platforms_data.append({
                        'platform': {
                            'name': platform.name,
                            'slug': platform.slug,
                            'metric_name': platform.audience_metric_name
                        },
                        'chart_data': chart_data
                    })
                
                return JsonResponse({
                    'success': True,
                    'artist': {
                        'name': artist.name,
                        'uuid': artist.uuid
                    },
                    'platforms': platforms_data
                })
                
        except Exception as e:
            logger.error(f"Error in ArtistAudienceChartView: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _get_single_platform_data(self, artist, platform, request):
        """Get chart data for a single platform"""
        try:
            limit = int(request.GET.get('limit', 30))
            
            # Get time-series data
            chart_data = ArtistAudienceTimeSeries.get_chart_data(
                artist=artist,
                platform=platform,
                limit=limit
            )
            
            if not chart_data:
                return {
                    'labels': [],
                    'datasets': [{
                        'label': platform.audience_metric_name,
                        'data': []
                    }]
                }
            
            # Convert to chart.js format
            labels = [str(item['date']) for item in chart_data]
            values = [item['audience_value'] for item in chart_data]
            
            return {
                'labels': labels,
                'datasets': [{
                    'label': platform.audience_metric_name,
                    'data': values,
                    'fill': True,
                    'tension': 0.4
                }]
            }
            
        except Exception as e:
            logger.error(f"Error getting chart data for {artist.name} on {platform.slug}: {e}")
            return {
                'labels': [],
                'datasets': [{
                    'label': platform.audience_metric_name,
                    'data': []
                }]
            }


@method_decorator(login_required, name='dispatch')
class ArtistSaveView(View):
    """API view to save an artist from search results to database"""
    
    def post(self, request):
        """Save an artist from Soundcharts to database"""
        try:
            data = json.loads(request.body)
            artist_data = data.get('artist')
            
            if not artist_data:
                return JsonResponse({
                    'success': False,
                    'error': 'No artist data provided'
                }, status=400)
            
            # Create or update artist
            artist = Artist.create_from_soundcharts(artist_data)
            
            if artist:
                return JsonResponse({
                    'success': True,
                    'message': f'Artist "{artist.name}" saved successfully',
                    'artist': {
                        'id': artist.id,
                        'uuid': artist.uuid,
                        'name': artist.name,
                        'slug': artist.slug
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to save artist'
                }, status=500)
                
        except Exception as e:
            logger.error(f"Error saving artist: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(login_required, name='dispatch')
class ArtistMetadataFetchView(View):
    """API view to fetch and update artist metadata"""
    
    def post(self, request):
        """Fetch metadata for an artist"""
        try:
            data = json.loads(request.body)
            artist_uuid = data.get('uuid')
            
            if not artist_uuid:
                return JsonResponse({
                    'success': False,
                    'error': 'Artist UUID is required'
                }, status=400)
            
            # Get or create artist
            artist = Artist.objects.filter(uuid=artist_uuid).first()
            if not artist:
                return JsonResponse({
                    'success': False,
                    'error': 'Artist not found in database'
                }, status=404)
            
            # Fetch metadata from API
            from .service import SoundchartsService
            service = SoundchartsService()
            metadata = service.get_artist_metadata(artist_uuid)
            
            if metadata and 'object' in metadata:
                artist_data = metadata['object']
                
                # Update artist fields
                if 'name' in artist_data:
                    artist.name = artist_data['name']
                if 'biography' in artist_data:
                    artist.biography = artist_data['biography']
                if 'countryCode' in artist_data:
                    artist.countryCode = artist_data['countryCode']
                if 'careerStage' in artist_data:
                    artist.careerStage = artist_data['careerStage']
                # Add more fields as needed
                
                artist.metadata_fetched_at = timezone.now()
                artist.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Metadata fetched for "{artist.name}"'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to fetch metadata from API'
                }, status=500)
                
        except Exception as e:
            logger.error(f"Error fetching artist metadata: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(login_required, name='dispatch')
class ArtistAudienceFetchView(View):
    """API view to fetch and store artist audience data"""
    
    def post(self, request):
        """Fetch audience data for an artist"""
        try:
            data = json.loads(request.body)
            artist_uuid = data.get('uuid')
            platform_slug = data.get('platform', 'spotify')
            
            if not artist_uuid:
                return JsonResponse({
                    'success': False,
                    'error': 'Artist UUID is required'
                }, status=400)
            
            # Get artist
            artist = Artist.objects.filter(uuid=artist_uuid).first()
            if not artist:
                return JsonResponse({
                    'success': False,
                    'error': 'Artist not found in database'
                }, status=404)
            
            # Get platform
            platform = Platform.objects.filter(slug=platform_slug).first()
            if not platform:
                return JsonResponse({
                    'success': False,
                    'error': f'Platform {platform_slug} not found'
                }, status=404)
            
            # Fetch audience data from API
            from .service import SoundchartsService
            service = SoundchartsService()
            audience_data = service.get_artist_audience_for_platform(artist_uuid, platform=platform_slug)
            
            if audience_data and 'items' in audience_data:
                # Process and store time-series data
                items = audience_data.get('items', [])
                records_created = 0
                records_updated = 0
                
                for item in items:
                    item_date_str = item.get('date')
                    if not item_date_str:
                        continue
                    
                    try:
                        # Parse date
                        if 'T' in item_date_str:
                            item_date = datetime.fromisoformat(item_date_str.replace('Z', '+00:00')).date()
                        else:
                            item_date = datetime.strptime(item_date_str, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        continue
                    
                    # Get audience value
                    audience_value = (item.get('followerCount') or 
                                    item.get('likeCount') or 
                                    item.get('viewCount'))
                    if audience_value is None:
                        continue
                    
                    # Store time-series record
                    ts_record, created = ArtistAudienceTimeSeries.objects.update_or_create(
                        artist=artist,
                        platform=platform,
                        date=item_date,
                        defaults={
                            'audience_value': audience_value,
                            'api_data': item,
                            'fetched_at': timezone.now()
                        }
                    )
                    
                    if created:
                        records_created += 1
                    else:
                        records_updated += 1
                
                # Update fetch timestamp
                artist.audience_fetched_at = timezone.now()
                artist.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Fetched audience data for "{artist.name}" on {platform.name}: {records_created} created, {records_updated} updated',
                    'data': {
                        'records_created': records_created,
                        'records_updated': records_updated
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to fetch audience data from API'
                }, status=500)
                
        except Exception as e:
            logger.error(f"Error fetching artist audience: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)