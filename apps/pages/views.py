from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Max
from django.utils import timezone
from datetime import timedelta
import json
from apps.soundcharts.models import ChartRanking, Chart, Track, Platform, ChartRankingEntry

@login_required(login_url='/users/signin/')
def index(request):
    # Get current date and week ranges
    now = timezone.now()
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    
    # Weekly Rankings Data for Main Chart
    weekly_rankings = []
    weekly_total = 0
    weekly_by_platform = {}
    
    # Get daily counts for the last 7 days, aggregated by platform
    for i in range(7):
        day = week_start + timedelta(days=i)
        
        # Total count for this day
        day_count = ChartRanking.objects.filter(
            fetched_at__date=day.date()
        ).count()
        
        # Count by platform for this day
        platform_counts = ChartRanking.objects.filter(
            fetched_at__date=day.date()
        ).values(
            'chart__platform__name'
        ).annotate(
            count=Count('id')
        ).order_by('chart__platform__name')
        
        daily_platforms = {}
        for platform_data in platform_counts:
            platform_name = platform_data['chart__platform__name'] or 'Unknown'
            daily_platforms[platform_name] = platform_data['count']
            
            # Add to weekly platform totals
            if platform_name not in weekly_by_platform:
                weekly_by_platform[platform_name] = 0
            weekly_by_platform[platform_name] += platform_data['count']
        
        weekly_rankings.append({
            'date': day.strftime('%Y-%m-%d'),
            'day_name': day.strftime('%A'),
            'count': day_count,
            'platforms': daily_platforms,
            'platforms_json': json.dumps(daily_platforms)
        })
        weekly_total += day_count
    
    # Calculate percentage change from previous week
    prev_week_start = week_start - timedelta(days=7)
    prev_week_total = ChartRanking.objects.filter(
        fetched_at__gte=prev_week_start,
        fetched_at__lt=week_start
    ).count()
    
    if prev_week_total > 0:
        percentage_change = ((weekly_total - prev_week_total) / prev_week_total) * 100
    else:
        percentage_change = 100 if weekly_total > 0 else 0
    
    # Top Platforms This Month
    top_platforms = Chart.objects.filter(
        rankings__fetched_at__gte=month_start
    ).values(
        'platform__name'
    ).annotate(
        rankings_count=Count('rankings')
    ).order_by('-rankings_count')[:5]
    
    # Top Performing Tracks This Week  
    top_tracks = Track.objects.filter(
        song_rankings__ranking__fetched_at__gte=week_start
    ).annotate(
        chart_appearances=Count('song_rankings')
    ).order_by('-chart_appearances')[:5]
    
    # Platform Performance Stats
    platform_stats = []
    for platform in Platform.objects.all():
        week_rankings = ChartRanking.objects.filter(
            chart__platform=platform,
            fetched_at__gte=week_start
        ).count()
        
        prev_week_rankings = ChartRanking.objects.filter(
            chart__platform=platform,
            fetched_at__gte=prev_week_start,
            fetched_at__lt=week_start
        ).count()
        
        if prev_week_rankings > 0:
            change = ((week_rankings - prev_week_rankings) / prev_week_rankings) * 100
        else:
            change = 100 if week_rankings > 0 else 0
            
        platform_stats.append({
            'name': platform.name,
            'current': week_rankings,
            'change': change
        })
    
    # Chart Health Metrics
    total_charts = Chart.objects.count()
    active_charts = Chart.objects.filter(
        rankings__fetched_at__gte=week_start
    ).distinct().count()
    
    chart_health = (active_charts / total_charts * 100) if total_charts > 0 else 0
    
    # Recent Activity Stats
    total_tracks = Track.objects.count()
    total_rankings_ever = ChartRanking.objects.count()
    avg_entries_per_ranking = ChartRanking.objects.aggregate(
        avg_entries=Avg('total_entries')
    )['avg_entries'] or 0

    context = {
        'segment': 'dashboard',
        # Main chart data
        'weekly_rankings_data': weekly_rankings,
        'weekly_total': weekly_total,
        'weekly_by_platform': weekly_by_platform,
        'percentage_change': round(percentage_change, 1),
        'is_positive_change': percentage_change >= 0,
        
        # Statistics
        'top_platforms': top_platforms,
        'top_tracks': top_tracks,
        'platform_stats': platform_stats,
        
        # Health metrics
        'total_charts': total_charts,
        'active_charts': active_charts,
        'chart_health': round(chart_health, 1),
        'chart_health_percentage': round(chart_health, 1),
        
        # Overall stats
        'total_tracks': total_tracks,
        'total_rankings_ever': total_rankings_ever,
        'avg_entries_per_ranking': round(avg_entries_per_ranking, 1),
    }
    return render(request, "dashboard/index.html", context)

@login_required(login_url='/users/signin/')
def starter(request):

  context = {}
  return render(request, "pages/starter.html", context)

@login_required(login_url='/users/signin/')
def docs(request):
    context = {}
    return render(request, "pages/docs.html", context)

@login_required(login_url='/users/signin/')
def charts_list(request):
    """
    View for displaying the main charts table
    Shows chart name, platform, frequency, rankings count, last chart date
    """
    # Get filter parameters
    platform_filter = request.GET.get('platform', '')
    frequency_filter = request.GET.get('frequency', '')
    country_filter = request.GET.get('country', '')
    
    # Base queryset
    charts = Chart.objects.select_related('platform').annotate(
        rankings_count=Count('rankings'),
        last_ranking_date=Max('rankings__ranking_date')
    ).order_by('-last_ranking_date')
    
    # Apply filters
    if platform_filter:
        charts = charts.filter(platform__slug=platform_filter)
    if frequency_filter:
        charts = charts.filter(frequency=frequency_filter)
    if country_filter:
        charts = charts.filter(country_code=country_filter)
    
    # Get filter options
    platforms = Platform.objects.all().order_by('name')
    frequencies = Chart.objects.values_list('frequency', flat=True).distinct().order_by('frequency')
    countries = Chart.objects.values_list('country_code', flat=True).distinct().order_by('country_code')
    
    context = {
        'segment': 'charts',
        'charts': charts,
        'platforms': platforms,
        'frequencies': frequencies,
        'countries': countries,
        'current_filters': {
            'platform': platform_filter,
            'frequency': frequency_filter,
            'country': country_filter,
        }
    }
    return render(request, "dashboard/charts_table.html", context)

@login_required(login_url='/users/signin/')
def chart_rankings(request, chart_id):
    """
    View for displaying chart rankings for a specific chart
    Shows all rankings downloaded for that chart, ordered by date
    """
    chart = get_object_or_404(Chart, id=chart_id)
    
    # Get filter parameters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset - don't annotate entries_count since it's a property
    rankings = ChartRanking.objects.filter(chart=chart).order_by('-ranking_date')
    
    # Apply date filters
    if date_from:
        rankings = rankings.filter(ranking_date__date__gte=date_from)
    if date_to:
        rankings = rankings.filter(ranking_date__date__lte=date_to)
    
    context = {
        'segment': 'charts',
        'chart': chart,
        'rankings': rankings,
        'current_filters': {
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, "dashboard/chart_rankings_table.html", context)

@login_required(login_url='/users/signin/')
def ranking_songs(request, ranking_id):
    """
    View for displaying songs in a specific chart ranking
    Shows individual songs with positions, metadata, and other data
    """
    ranking = get_object_or_404(ChartRanking, id=ranking_id)
    
    # Get filter parameters
    position_from = request.GET.get('position_from', '')
    position_to = request.GET.get('position_to', '')
    track_name = request.GET.get('track_name', '')
    
    # Base queryset
    entries = ChartRankingEntry.objects.filter(ranking=ranking).select_related('track').order_by('position')
    
    # Apply filters
    if position_from:
        entries = entries.filter(position__gte=position_from)
    if position_to:
        entries = entries.filter(position__lte=position_to)
    if track_name:
        entries = entries.filter(track__name__icontains=track_name)
    
    context = {
        'segment': 'charts',
        'ranking': ranking,
        'entries': entries,
        'current_filters': {
            'position_from': position_from,
            'position_to': position_to,
            'track_name': track_name,
        }
    }
    return render(request, "dashboard/ranking_songs_table.html", context)
