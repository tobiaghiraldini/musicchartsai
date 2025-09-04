from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import json


from apps.soundcharts.models import ChartRanking, Chart, Track, Platform, TrackAudienceTimeSeries

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
