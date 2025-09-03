from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import redirect
import json
import logging
from datetime import datetime, timedelta

from ..models import Chart, ChartRanking, ChartRankingEntry, Track, Platform
from ..service import SoundchartsService
from .soundcharts_admin_mixin import SoundchartsAdminMixin


class ChartRankingsInline(admin.TabularInline):
    """Inline for displaying chart rankings in the chart change view"""
    model = ChartRanking
    extra = 0
    readonly_fields = ('ranking_date', 'total_entries', 'get_entries_count', 'get_ranking_link', 'fetched_at')
    fields = ('ranking_date', 'total_entries', 'get_entries_count', 'get_ranking_link', 'fetched_at')
    can_delete = False
    ordering = ('-ranking_date',)
    
    def get_entries_count(self, obj):
        """Display the actual count of entries"""
        if not obj:
            return "0 entries"
        count = obj.entries.count()
        if count == 0:
            return "0 entries"
        elif count == 1:
            return "1 entry"
        else:
            return f"{count} entries"
    
    get_entries_count.short_description = "Entries Count"
    
    def get_ranking_link(self, obj):
        """Display a link to view the ranking details"""
        if not obj or not obj.pk:
            return "-"
        
        url = reverse("admin:soundcharts_chartranking_change", args=[obj.pk])
        return format_html(
            '<a href="{}" class="button" target="_blank">View Details</a>',
            url
        )
    
    get_ranking_link.short_description = "View Ranking"
    get_ranking_link.allow_tags = True
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

logger = logging.getLogger(__name__)





class ChartAdmin(SoundchartsAdminMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "platform",
        "slug",
        "frequency",
        "get_rankings_count",
        "get_total_entries",
        "get_avg_entries",
        "get_ranking_date_range",
        "get_latest_ranking_link",
        "get_top_tracks",
        "get_performance_trend",
        "get_activity_status",
        "get_frequency_compliance",
        "get_data_quality",
        "get_last_import",
        "get_ranking_consistency",
        "get_ranking_completeness",
        "get_ranking_health",
        "get_import_efficiency",
        "get_data_freshness",
        "get_data_reliability",
        "get_data_coverage",
        "get_data_accuracy",
        "get_data_timeliness",
        "get_data_completeness",
        "get_data_validity",
        "get_data_integrity",
        "get_data_performance",
        "get_data_reliability_score",
        "get_data_quality_score",
        "get_overall_score",
        "get_data_status",
        "get_data_summary",
        "get_data_insights",
        "get_data_recommendations",
        "get_data_alerts",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at", "platform", "rankings__ranking_date")
    search_fields = ("name", "slug")
    ordering = ("name",)
    readonly_fields = ("slug", "get_rankings_summary")
    inlines = [ChartRankingsInline]
    actions = ["view_chart_rankings"]
    fieldsets = (
        (
            "Chart Information",
            {
                "fields": (
                    "name",
                    "platform",
                    "slug",
                    "type",
                    "frequency",
                    "country_code",
                    "web_url",
                )
            },
        ),

        (
            "Rankings Summary",
            {"fields": ("get_rankings_summary",), "classes": ("collapse",)},
        ),
    )

    def get_rankings_count(self, obj):
        """Display the count of rankings for this chart"""
        count = obj.rankings.count()
        if count == 0:
            return "0 rankings"
        elif count == 1:
            return "1 ranking"
        else:
            return f"{count} rankings"

    get_rankings_count.short_description = "Rankings"

    def get_total_entries(self, obj):
        """Display the total number of entries across all rankings for this chart"""
        total = sum(ranking.total_entries for ranking in obj.rankings.all())
        if total == 0:
            return "0 entries"
        else:
            return f"{total:,} entries"

    get_total_entries.short_description = "Total Entries"

    def get_avg_entries(self, obj):
        """Display the average number of entries per ranking for this chart"""
        rankings = obj.rankings.all()
        if not rankings:
            return "N/A"

        total_entries = sum(ranking.total_entries for ranking in rankings)
        avg = total_entries / rankings.count()
        return f"{avg:.1f} avg"

    get_avg_entries.short_description = "Avg Entries"

    def get_ranking_date_range(self, obj):
        """Display the date range of rankings for this chart"""
        rankings = obj.rankings.all()
        if not rankings:
            return "No rankings"

        latest = rankings.order_by("-ranking_date").first()
        earliest = rankings.order_by("ranking_date").first()

        if latest == earliest:
            return latest.ranking_date.strftime("%Y-%m-%d")
        else:
            return f"{earliest.ranking_date.strftime('%Y-%m-%d')} to {latest.ranking_date.strftime('%Y-%m-%d')}"

    get_ranking_date_range.short_description = "Ranking Date Range"

    def get_latest_ranking_link(self, obj):
        """Display a link to the most recent ranking for this chart"""
        latest_ranking = obj.rankings.order_by("-ranking_date").first()
        if not latest_ranking:
            return "No rankings"

        url = reverse("admin:soundcharts_chartranking_change", args=[latest_ranking.id])
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            url,
            latest_ranking.ranking_date.strftime("%Y-%m-%d"),
        )

    get_latest_ranking_link.short_description = "Latest Ranking"
    get_latest_ranking_link.allow_tags = True

    def get_top_tracks(self, obj):
        """Display the top performing tracks across all rankings for this chart"""
        latest_ranking = obj.rankings.order_by("-ranking_date").first()
        if not latest_ranking:
            return "No rankings"

        top_entries = latest_ranking.entries.select_related("track").order_by(
            "position"
        )[:3]
        if not top_entries:
            return "No entries"

        tracks = []
        for entry in top_entries:
            track_name = entry.track.name if entry.track else "Unknown"
            tracks.append(f"#{entry.position} {track_name}")

        return " | ".join(tracks)

    get_top_tracks.short_description = "Top Tracks"

    def get_performance_trend(self, obj):
        """Display the performance trend of this chart based on recent rankings"""
        rankings = obj.rankings.order_by("-ranking_date")[:2]
        if len(rankings) < 2:
            return "Insufficient data"

        current = rankings[0]
        previous = rankings[1]

        if current.total_entries > previous.total_entries:
            return "↗ Growing"
        elif current.total_entries < previous.total_entries:
            return "↘ Declining"
        else:
            return "→ Stable"

    get_performance_trend.short_description = "Trend"

    def get_activity_status(self, obj):
        """Display the activity status of this chart based on recent ranking updates"""
        latest_ranking = obj.rankings.order_by("-ranking_date").first()
        if not latest_ranking:
            return "Inactive"

        now = datetime.now()
        days_since_update = (now.date() - latest_ranking.ranking_date.date()).days

        if days_since_update <= 1:
            return "🟢 Active"
        elif days_since_update <= 7:
            return "🟡 Recent"
        elif days_since_update <= 30:
            return "🟠 Stale"
        else:
            return "🔴 Inactive"

    get_activity_status.short_description = "Status"

    def get_frequency_compliance(self, obj):
        """Display how well this chart follows its declared frequency"""
        rankings = obj.rankings.order_by("-ranking_date")[:2]
        if len(rankings) < 2:
            return "N/A"

        current = rankings[0].ranking_date
        previous = rankings[1].ranking_date
        days_between = (current - previous).days

        if obj.frequency == "daily" and days_between <= 2:
            return "✅ Compliant"
        elif obj.frequency == "weekly" and 5 <= days_between <= 9:
            return "✅ Compliant"
        elif obj.frequency == "monthly" and 25 <= days_between <= 35:
            return "✅ Compliant"
        else:
            return f"⚠️ {days_between}d gap"

    get_frequency_compliance.short_description = "Frequency"

    def get_data_quality(self, obj):
        """Display the data quality score for this chart based on ranking completeness"""
        latest_ranking = obj.rankings.order_by("-ranking_date").first()
        if not latest_ranking:
            return "N/A"

        entries_count = latest_ranking.entries.count()
        total_entries = latest_ranking.total_entries

        if total_entries == 0:
            return "N/A"

        completeness = entries_count / total_entries

        if completeness >= 0.95:
            return "🟢 Excellent"
        elif completeness >= 0.8:
            return "🟡 Good"
        elif completeness >= 0.6:
            return "🟠 Fair"
        else:
            return "🔴 Poor"

    get_data_quality.short_description = "Quality"

    def get_last_import(self, obj):
        """Display when this chart was last imported from the API"""
        latest_ranking = obj.rankings.order_by("-fetched_at").first()
        if not latest_ranking:
            return "Never"

        now = datetime.now()
        days_since_import = (now.date() - latest_ranking.fetched_at.date()).days

        if days_since_import == 0:
            return "Today"
        elif days_since_import == 1:
            return "Yesterday"
        elif days_since_import <= 7:
            return f"{days_since_import} days ago"
        else:
            return latest_ranking.fetched_at.strftime("%Y-%m-%d")

    get_last_import.short_description = "Last Import"

    def get_rankings_summary(self, obj):
        """Display summary statistics about the chart's ranking history"""
        rankings = obj.rankings.all()
        if not rankings:
            return "No rankings available for this chart"

        total_rankings = rankings.count()
        latest_ranking = rankings.order_by("-ranking_date").first()
        earliest_ranking = rankings.order_by("ranking_date").first()
        total_entries = sum(ranking.total_entries for ranking in rankings)

        summary = f"""
Ranking History Summary:
• Total Rankings: {total_rankings}
• Date Range: {earliest_ranking.ranking_date.strftime("%Y-%m-%d")} to {latest_ranking.ranking_date.strftime("%Y-%m-%d")}
• Total Entries Processed: {total_entries:,}
        """.strip()

        return summary

    get_rankings_summary.short_description = "Rankings Summary"

    def get_ranking_consistency(self, obj):
        """Display the consistency of rankings for this chart over time"""
        rankings = obj.rankings.order_by("-ranking_date")[:3]
        if len(rankings) < 2:
            return "N/A"

        # Calculate the average change in total entries
        changes = []
        for i in range(len(rankings) - 1):
            current = rankings[i].total_entries
            previous = rankings[i + 1].total_entries
            if previous > 0:
                change = abs(current - previous) / previous
                changes.append(change)

        if not changes:
            return "N/A"

        avg_change = sum(changes) / len(changes)

        if avg_change <= 0.05:
            return "🟢 Very Stable"
        elif avg_change <= 0.1:
            return "🟡 Stable"
        elif avg_change <= 0.2:
            return "🟠 Moderate"
        else:
            return "🔴 Volatile"

    get_ranking_consistency.short_description = "Consistency"

    def get_ranking_completeness(self, obj):
        """Display the completeness of rankings for this chart based on expected frequency"""
        rankings = obj.rankings.order_by("ranking_date")
        if not rankings:
            return "0%"

        now = datetime.now()

        # Calculate expected number of rankings based on frequency
        if obj.frequency == "daily":
            expected_days = 30  # Last 30 days
            expected_rankings = 30
        elif obj.frequency == "weekly":
            expected_weeks = 12  # Last 12 weeks
            expected_rankings = 12
        elif obj.frequency == "monthly":
            expected_months = 6  # Last 6 months
            expected_rankings = 6
        else:
            return "N/A"

        # Count actual rankings in the expected period
        if obj.frequency == "daily":
            start_date = now - timedelta(days=expected_days)
        elif obj.frequency == "weekly":
            start_date = now - timedelta(weeks=expected_weeks)
        elif obj.frequency == "monthly":
            start_date = now - timedelta(days=expected_months * 30)

        actual_rankings = rankings.filter(ranking_date__gte=start_date).count()
        completeness = (actual_rankings / expected_rankings) * 100

        if completeness >= 90:
            return f"🟢 {completeness:.0f}%"
        elif completeness >= 75:
            return f"🟡 {completeness:.0f}%"
        elif completeness >= 50:
            return f"🟠 {completeness:.0f}%"
        else:
            return f"🔴 {completeness:.0f}%"

    get_ranking_completeness.short_description = "Completeness"

    def get_ranking_health(self, obj):
        """Display the overall health score for this chart's rankings"""
        rankings = obj.rankings.all()
        if not rankings:
            return "🔴 No Data"

        # Calculate health score based on multiple factors
        score = 0
        max_score = 100

        # Activity score (25 points)
        latest_ranking = rankings.order_by("-ranking_date").first()
        if latest_ranking:
            now = datetime.now()
            days_since_update = (now.date() - latest_ranking.ranking_date.date()).days

            if days_since_update <= 1:
                score += 25
            elif days_since_update <= 7:
                score += 20
            elif days_since_update <= 30:
                score += 15
            elif days_since_update <= 90:
                score += 10
            else:
                score += 5

        # Frequency compliance score (25 points)
        if len(rankings) >= 2:
            current = rankings.order_by("-ranking_date")[0].ranking_date
            previous = rankings.order_by("-ranking_date")[1].ranking_date
            days_between = (current - previous).days

            if obj.frequency == "daily" and days_between <= 2:
                score += 25
            elif obj.frequency == "weekly" and 5 <= days_between <= 9:
                score += 25
            elif obj.frequency == "monthly" and 25 <= days_between <= 35:
                score += 25
            elif obj.frequency == "daily" and days_between <= 7:
                score += 20
            elif obj.frequency == "weekly" and days_between <= 14:
                score += 20
            elif obj.frequency == "monthly" and days_between <= 60:
                score += 20
            else:
                score += 10

        # Data quality score (25 points)
        if latest_ranking and latest_ranking.total_entries > 0:
            entries_count = latest_ranking.entries.count()
            completeness = entries_count / latest_ranking.total_entries
            score += int(completeness * 25)

        # Consistency score (25 points)
        if len(rankings) >= 3:
            changes = []
            for i in range(len(rankings) - 1):
                current = rankings.order_by("-ranking_date")[i].total_entries
                previous = rankings.order_by("-ranking_date")[i + 1].total_entries
                if previous > 0:
                    change = abs(current - previous) / previous
                    changes.append(change)

            if changes:
                avg_change = sum(changes) / len(changes)
                if avg_change <= 0.05:
                    score += 25
                elif avg_change <= 0.1:
                    score += 20
                elif avg_change <= 0.2:
                    score += 15
                else:
                    score += 10

        # Determine health level
        if score >= 90:
            return f"🟢 {score}/100"
        elif score >= 75:
            return f"🟡 {score}/100"
        elif score >= 50:
            return f"🟠 {score}/100"
        else:
            return f"🔴 {score}/100"

    get_ranking_health.short_description = "Health"

    def get_import_efficiency(self, obj):
        """Display the import efficiency for this chart's rankings"""
        latest_ranking = obj.rankings.order_by("-ranking_date").first()
        if not latest_ranking:
            return "N/A"

        # Calculate time difference between ranking date and when it was fetched
        time_diff = latest_ranking.fetched_at - latest_ranking.ranking_date

        if time_diff.days > 0:
            return f"⚠️ {time_diff.days}d delay"
        elif time_diff.seconds > 3600:  # More than 1 hour
            return f"🟡 {time_diff.seconds // 3600}h delay"
        elif time_diff.seconds > 300:  # More than 5 minutes
            return f"🟠 {time_diff.seconds // 60}m delay"
        else:
            return "🟢 Real-time"

    get_import_efficiency.short_description = "Import Speed"

    def get_data_freshness(self, obj):
        """Display the freshness of ranking data for this chart"""
        latest_ranking = obj.rankings.order_by("-ranking_date").first()
        if not latest_ranking:
            return "N/A"

        now = datetime.now()
        days_since_ranking = (now.date() - latest_ranking.ranking_date.date()).days

        if days_since_ranking == 0:
            return "🟢 Today"
        elif days_since_ranking == 1:
            return "🟢 Yesterday"
        elif days_since_ranking <= 3:
            return f"🟡 {days_since_ranking} days ago"
        elif days_since_ranking <= 7:
            return f"🟠 {days_since_ranking} days ago"
        elif days_since_ranking <= 30:
            return f"🔴 {days_since_ranking} days ago"
        else:
            return f"🔴 {days_since_ranking} days ago"

    get_data_freshness.short_description = "Data Age"

    def get_data_reliability(self, obj):
        """Display the reliability of ranking data for this chart"""
        latest_ranking = obj.rankings.order_by("-ranking_date").first()
        if not latest_ranking:
            return "N/A"

        # Check API version
        api_version = latest_ranking.api_version
        if not api_version:
            return "⚠️ Unknown API"

        # Check if API version is recent
        if api_version.startswith("v2."):
            version_num = float(api_version[1:])
            if version_num >= 2.14:
                return "🟢 Latest API"
            elif version_num >= 2.0:
                return "🟡 Stable API"
            else:
                return "🟠 Legacy API"
        else:
            return "🔴 Unknown API"

    get_data_reliability.short_description = "API Version"

    def get_data_coverage(self, obj):
        """Display the typical coverage of ranking data for this chart"""
        rankings = obj.rankings.all()
        if not rankings:
            return "N/A"

        # Calculate average entries per ranking
        total_entries = sum(ranking.total_entries for ranking in rankings)
        avg_entries = total_entries / rankings.count()

        if avg_entries >= 100:
            return f"🟢 {avg_entries:.0f} avg"
        elif avg_entries >= 50:
            return f"🟡 {avg_entries:.0f} avg"
        elif avg_entries >= 20:
            return f"🟠 {avg_entries:.0f} avg"
        else:
            return f"🔴 {avg_entries:.0f} avg"

    get_data_coverage.short_description = "Coverage"

    def get_data_accuracy(self, obj):
        """Display the accuracy of ranking data for this chart"""
        latest_ranking = obj.rankings.order_by("-ranking_date").first()
        if not latest_ranking:
            return "N/A"

        # Check if entries have position change data
        entries_with_changes = latest_ranking.entries.filter(
            position_change__isnull=False
        ).count()
        total_entries = latest_ranking.entries.count()

        if total_entries == 0:
            return "N/A"

        accuracy_percentage = (entries_with_changes / total_entries) * 100

        if accuracy_percentage >= 90:
            return f"🟢 {accuracy_percentage:.0f}%"
        elif accuracy_percentage >= 75:
            return f"🟡 {accuracy_percentage:.0f}%"
        elif accuracy_percentage >= 50:
            return f"🟠 {accuracy_percentage:.0f}%"
        else:
            return f"🔴 {accuracy_percentage:.0f}%"

    get_data_accuracy.short_description = "Accuracy"

    def get_data_timeliness(self, obj):
        """Display the timeliness of ranking data for this chart"""
        latest_ranking = obj.rankings.order_by("-ranking_date").first()
        if not latest_ranking:
            return "N/A"

        # Calculate time difference between ranking date and when it was fetched
        time_diff = latest_ranking.fetched_at - latest_ranking.ranking_date

        if time_diff.days > 7:
            return "🔴 Very Late"
        elif time_diff.days > 3:
            return "🟠 Late"
        elif time_diff.days > 1:
            return "🟡 Delayed"
        elif time_diff.seconds > 3600:  # More than 1 hour
            return "🟡 Hours"
        elif time_diff.seconds > 300:  # More than 5 minutes
            return "🟠 Minutes"
        else:
            return "🟢 Real-time"

    get_data_timeliness.short_description = "Timeliness"

    def get_data_completeness(self, obj):
        """Display the completeness of ranking data for this chart"""
        latest_ranking = obj.rankings.order_by("-ranking_date").first()
        if not latest_ranking:
            return "N/A"

        # Check if entries have all required fields
        entries_with_all_data = latest_ranking.entries.filter(
            position__isnull=False, track__isnull=False
        ).count()
        total_entries = latest_ranking.entries.count()

        if total_entries == 0:
            return "N/A"

        completeness_percentage = (entries_with_all_data / total_entries) * 100

        if completeness_percentage >= 95:
            return f"🟢 {completeness_percentage:.0f}%"
        elif completeness_percentage >= 85:
            return f"🟡 {completeness_percentage:.0f}%"
        elif completeness_percentage >= 70:
            return f"🟠 {completeness_percentage:.0f}%"
        else:
            return f"🔴 {completeness_percentage:.0f}%"

    get_data_completeness.short_description = "Completeness"

    def get_data_validity(self, obj):
        """Display the validity of ranking data for this chart"""
        latest_ranking = obj.rankings.order_by("-ranking_date").first()
        if not latest_ranking:
            return "N/A"

        # Check for data validation issues
        invalid_entries = 0
        total_entries = latest_ranking.entries.count()

        if total_entries == 0:
            return "N/A"

        # Check for entries with invalid positions
        invalid_positions = latest_ranking.entries.filter(position__lt=1).count()

        # Check for entries with duplicate positions
        positions = list(latest_ranking.entries.values_list("position", flat=True))
        duplicate_positions = len(positions) - len(set(positions))

        # Check for entries without tracks
        entries_without_tracks = latest_ranking.entries.filter(
            track__isnull=True
        ).count()

        total_invalid = invalid_positions + duplicate_positions + entries_without_tracks
        validity_percentage = ((total_entries - total_invalid) / total_entries) * 100

        if validity_percentage >= 95:
            return f"🟢 {validity_percentage:.0f}%"
        elif validity_percentage >= 85:
            return f"🟡 {validity_percentage:.0f}%"
        elif validity_percentage >= 70:
            return f"🟠 {validity_percentage:.0f}%"
        else:
            return f"🔴 {validity_percentage:.0f}%"

    get_data_validity.short_description = "Validity"

    def get_data_integrity(self, obj):
        """Display the overall data integrity score for this chart"""
        latest_ranking = obj.rankings.order_by("-ranking_date").first()
        if not latest_ranking:
            return "🔴 No Data"

        # Calculate integrity score based on multiple factors
        score = 0
        max_score = 100

        # Data quality score (25 points)
        if latest_ranking.total_entries > 0:
            entries_count = latest_ranking.entries.count()
            completeness = entries_count / latest_ranking.total_entries
            score += int(completeness * 25)

        # Data accuracy score (25 points)
        entries_with_changes = latest_ranking.entries.filter(
            position_change__isnull=False
        ).count()
        total_entries = latest_ranking.entries.count()
        if total_entries > 0:
            accuracy = entries_with_changes / total_entries
            score += int(accuracy * 25)

        # Data validity score (25 points)
        invalid_entries = 0
        if total_entries > 0:
            # Check for entries with invalid positions
            invalid_positions = latest_ranking.entries.filter(position__lt=1).count()
            # Check for entries without tracks
            entries_without_tracks = latest_ranking.entries.filter(
                track__isnull=True
            ).count()
            # Check for duplicate positions
            positions = list(latest_ranking.entries.values_list("position", flat=True))
            duplicate_positions = len(positions) - len(set(positions))

            total_invalid = (
                invalid_positions + duplicate_positions + entries_without_tracks
            )
            validity = (total_entries - total_invalid) / total_entries
            score += int(validity * 25)

        # Data freshness score (25 points)
        now = datetime.now()
        days_since_ranking = (now.date() - latest_ranking.ranking_date.date()).days

        if days_since_ranking <= 1:
            score += 25
        elif days_since_ranking <= 3:
            score += 20
        elif days_since_ranking <= 7:
            score += 15
        elif days_since_ranking <= 30:
            score += 10
        else:
            score += 5

        # Determine integrity level
        if score >= 90:
            return f"🟢 {score}/100"
        elif score >= 75:
            return f"🟡 {score}/100"
        elif score >= 50:
            return f"🟠 {score}/100"
        else:
            return f"🔴 {score}/100"

    get_data_integrity.short_description = "Integrity"

    def get_data_performance(self, obj):
        """Display the overall performance metrics for this chart"""
        rankings = obj.rankings.all()
        if not rankings:
            return "🔴 No Data"

        # Calculate performance score based on multiple factors
        score = 0
        max_score = 100

        # Frequency compliance score (25 points)
        if len(rankings) >= 2:
            current = rankings.order_by("-ranking_date")[0].ranking_date
            previous = rankings.order_by("-ranking_date")[1].ranking_date
            days_between = (current - previous).days

            if obj.frequency == "daily" and days_between <= 2:
                score += 25
            elif obj.frequency == "weekly" and 5 <= days_between <= 9:
                score += 25
            elif obj.frequency == "monthly" and 25 <= days_between <= 35:
                score += 25
            elif obj.frequency == "daily" and days_between <= 7:
                score += 20
            elif obj.frequency == "weekly" and days_between <= 14:
                score += 20
            elif obj.frequency == "monthly" and days_between <= 60:
                score += 20
            else:
                score += 10

        # Data coverage score (25 points)
        total_entries = sum(ranking.total_entries for ranking in rankings)
        avg_entries = total_entries / rankings.count() if rankings.count() > 0 else 0

        if avg_entries >= 100:
            score += 25
        elif avg_entries >= 50:
            score += 20
        elif avg_entries >= 20:
            score += 15
        else:
            score += 10

        # Data freshness score (25 points)
        latest_ranking = rankings.order_by("-ranking_date").first()
        if latest_ranking:
            now = datetime.now()
            days_since_ranking = (now.date() - latest_ranking.ranking_date.date()).days

            if days_since_ranking <= 1:
                score += 25
            elif days_since_ranking <= 3:
                score += 20
            elif days_since_ranking <= 7:
                score += 15
            elif days_since_ranking <= 30:
                score += 10
            else:
                score += 5

        # Data consistency score (25 points)
        if len(rankings) >= 3:
            changes = []
            for i in range(len(rankings) - 1):
                current = rankings.order_by("-ranking_date")[i].total_entries
                previous = rankings.order_by("-ranking_date")[i + 1].total_entries
                if previous > 0:
                    change = abs(current - previous) / previous
                    changes.append(change)

            if changes:
                avg_change = sum(changes) / len(changes)
                if avg_change <= 0.05:
                    score += 25
                elif avg_change <= 0.1:
                    score += 20
                elif avg_change <= 0.2:
                    score += 15
                else:
                    score += 10

        # Determine performance level
        if score >= 90:
            return f"🟢 {score}/100"
        elif score >= 75:
            return f"🟡 {score}/100"
        elif score >= 50:
            return f"🟠 {score}/100"
        else:
            return f"🔴 {score}/100"

    get_data_performance.short_description = "Performance"

    def get_data_reliability_score(self, obj):
        """Display the overall reliability score for this chart's data"""
        rankings = obj.rankings.all()
        if not rankings:
            return "🔴 No Data"

        # Calculate reliability score based on multiple factors
        score = 0
        max_score = 100

        # API version reliability (25 points)
        latest_ranking = rankings.order_by("-ranking_date").first()
        if latest_ranking and latest_ranking.api_version:
            api_version = latest_ranking.api_version
            if api_version.startswith("v2."):
                version_num = float(api_version[1:])
                if version_num >= 2.14:
                    score += 25
                elif version_num >= 2.0:
                    score += 20
                else:
                    score += 15
            else:
                score += 10
        else:
            score += 5

        # Data consistency reliability (25 points)
        if len(rankings) >= 3:
            changes = []
            for i in range(len(rankings) - 1):
                current = rankings.order_by("-ranking_date")[i].total_entries
                previous = rankings.order_by("-ranking_date")[i + 1].total_entries
                if previous > 0:
                    change = abs(current - previous) / previous
                    changes.append(change)

            if changes:
                avg_change = sum(changes) / len(changes)
                if avg_change <= 0.05:
                    score += 25
                elif avg_change <= 0.1:
                    score += 20
                elif avg_change <= 0.2:
                    score += 15
                else:
                    score += 10

        # Data completeness reliability (25 points)
        if latest_ranking and latest_ranking.total_entries > 0:
            entries_count = latest_ranking.entries.count()
            completeness = entries_count / latest_ranking.total_entries
            score += int(completeness * 25)

        # Data accuracy reliability (25 points)
        if latest_ranking:
            entries_with_changes = latest_ranking.entries.filter(
                position_change__isnull=False
            ).count()
            total_entries = latest_ranking.entries.count()
            if total_entries > 0:
                accuracy = entries_with_changes / total_entries
                score += int(accuracy * 25)

        # Determine reliability level
        if score >= 90:
            return f"🟢 {score}/100"
        elif score >= 75:
            return f"🟡 {score}/100"
        elif score >= 50:
            return f"🟠 {score}/100"
        else:
            return f"🔴 {score}/100"

    get_data_reliability_score.short_description = "Reliability"

    def get_data_quality_score(self, obj):
        """Display the overall data quality score for this chart"""
        latest_ranking = obj.rankings.order_by("-ranking_date").first()
        if not latest_ranking:
            return "🔴 No Data"

        # Calculate quality score based on multiple factors
        score = 0
        max_score = 100

        # Data completeness quality (25 points)
        if latest_ranking.total_entries > 0:
            entries_count = latest_ranking.entries.count()
            completeness = entries_count / latest_ranking.total_entries
            score += int(completeness * 25)

        # Data accuracy quality (25 points)
        entries_with_changes = latest_ranking.entries.filter(
            position_change__isnull=False
        ).count()
        total_entries = latest_ranking.entries.count()
        if total_entries > 0:
            accuracy = entries_with_changes / total_entries
            score += int(accuracy * 25)

        # Data validity quality (25 points)
        if total_entries > 0:
            # Check for entries with invalid positions
            invalid_positions = latest_ranking.entries.filter(position__lt=1).count()
            # Check for entries without tracks
            entries_without_tracks = latest_ranking.entries.filter(
                track__isnull=True
            ).count()
            # Check for duplicate positions
            positions = list(latest_ranking.entries.values_list("position", flat=True))
            duplicate_positions = len(positions) - len(set(positions))

            total_invalid = (
                invalid_positions + duplicate_positions + entries_without_tracks
            )
            validity = (total_entries - total_invalid) / total_entries
            score += int(validity * 25)

        # Data freshness quality (25 points)
        now = datetime.now()
        days_since_ranking = (now.date() - latest_ranking.ranking_date.date()).days

        if days_since_ranking <= 1:
            score += 25
        elif days_since_ranking <= 3:
            score += 20
        elif days_since_ranking <= 7:
            score += 15
        elif days_since_ranking <= 30:
            score += 10
        else:
            score += 5

        # Determine quality level
        if score >= 90:
            return f"🟢 {score}/100"
        elif score >= 75:
            return f"🟡 {score}/100"
        elif score >= 50:
            return f"🟠 {score}/100"
        else:
            return f"🔴 {score}/100"

    get_data_quality_score.short_description = "Quality Score"

    def get_overall_score(self, obj):
        """Display the overall comprehensive score for this chart"""
        rankings = obj.rankings.all()
        if not rankings:
            return "🔴 No Data"

        # Calculate overall score based on multiple factors
        score = 0
        max_score = 100

        # Health score (25 points)
        health_score = 0
        latest_ranking = rankings.order_by("-ranking_date").first()
        if latest_ranking:
            now = datetime.now()
            days_since_update = (now.date() - latest_ranking.ranking_date.date()).days

            if days_since_update <= 1:
                health_score += 25
            elif days_since_update <= 7:
                health_score += 20
            elif days_since_update <= 30:
                health_score += 15
            elif days_since_update <= 90:
                health_score += 10
            else:
                health_score += 5

        # Performance score (25 points)
        performance_score = 0
        if len(rankings) >= 2:
            current = rankings.order_by("-ranking_date")[0].ranking_date
            previous = rankings.order_by("-ranking_date")[1].ranking_date
            days_between = (current - previous).days

            if obj.frequency == "daily" and days_between <= 2:
                performance_score += 25
            elif obj.frequency == "weekly" and 5 <= days_between <= 9:
                performance_score += 25
            elif obj.frequency == "monthly" and 25 <= days_between <= 35:
                performance_score += 25
            elif obj.frequency == "daily" and days_between <= 7:
                performance_score += 20
            elif obj.frequency == "weekly" and days_between <= 14:
                performance_score += 20
            elif obj.frequency == "monthly" and days_between <= 60:
                performance_score += 20
            else:
                performance_score += 10

        # Quality score (25 points)
        quality_score = 0
        if latest_ranking and latest_ranking.total_entries > 0:
            entries_count = latest_ranking.entries.count()
            completeness = entries_count / latest_ranking.total_entries
            score += int(completeness * 25)

        # Reliability score (25 points)
        reliability_score = 0
        if latest_ranking and latest_ranking.api_version:
            api_version = latest_ranking.api_version
            if api_version.startswith("v2."):
                version_num = float(api_version[1:])
                if version_num >= 2.14:
                    reliability_score += 25
                elif version_num >= 2.0:
                    reliability_score += 20
                else:
                    reliability_score += 15
            else:
                reliability_score += 10
        else:
            reliability_score += 5

        # Calculate overall score
        overall_score = (
            health_score + performance_score + quality_score + reliability_score
        ) / 4

        # Determine overall level
        if overall_score >= 90:
            return f"🟢 {overall_score:.0f}/100"
        elif overall_score >= 75:
            return f"🟡 {overall_score:.0f}/100"
        elif overall_score >= 50:
            return f"🟠 {overall_score:.0f}/100"
        else:
            return f"🔴 {overall_score:.0f}/100"

    get_overall_score.short_description = "Overall Score"

    def get_data_status(self, obj):
        """Display the overall data status for this chart"""
        rankings = obj.rankings.all()
        if not rankings:
            return "🔴 No Data"

        latest_ranking = rankings.order_by("-ranking_date").first()
        if not latest_ranking:
            return "🔴 No Rankings"

        # Check multiple status factors
        now = datetime.now()
        days_since_ranking = (now.date() - latest_ranking.ranking_date.date()).days

        # Determine primary status
        if days_since_ranking <= 1:
            primary_status = "🟢 Active"
        elif days_since_ranking <= 7:
            primary_status = "🟡 Recent"
        elif days_since_ranking <= 30:
            primary_status = "🟠 Stale"
        else:
            primary_status = "🔴 Inactive"

        # Check for data quality issues
        quality_issues = []
        if latest_ranking.total_entries > 0:
            entries_count = latest_ranking.entries.count()
            completeness = entries_count / latest_ranking.total_entries
            if completeness < 0.8:
                quality_issues.append("Low completeness")

        # Check for frequency compliance issues
        frequency_issues = []
        if len(rankings) >= 2:
            current = rankings.order_by("-ranking_date")[0].ranking_date
            previous = rankings.order_by("-ranking_date")[1].ranking_date
            days_between = (current - previous).days

            if obj.frequency == "daily" and days_between > 7:
                frequency_issues.append("Missing daily updates")
            elif obj.frequency == "weekly" and days_between > 14:
                frequency_issues.append("Missing weekly updates")
            elif obj.frequency == "monthly" and days_between > 60:
                frequency_issues.append("Missing monthly updates")

        # Combine status with issues
        if quality_issues or frequency_issues:
            issues = ", ".join(quality_issues + frequency_issues)
            return f"{primary_status} ⚠️ {issues}"
        else:
            return primary_status

    get_data_status.short_description = "Status"

    def get_data_summary(self, obj):
        """Display a comprehensive summary of this chart's data"""
        rankings = obj.rankings.all()
        if not rankings:
            return "🔴 No Data Available"

        latest_ranking = rankings.order_by("-ranking_date").first()
        total_rankings = rankings.count()
        total_entries = sum(ranking.total_entries for ranking in rankings)

        # Calculate key metrics
        avg_entries = total_entries / total_rankings if total_rankings > 0 else 0

        # Determine data age
        now = datetime.now()
        days_since_ranking = (now.date() - latest_ranking.ranking_date.date()).days

        if days_since_ranking <= 1:
            age_status = "🟢 Fresh"
        elif days_since_ranking <= 7:
            age_status = "🟡 Recent"
        elif days_since_ranking <= 30:
            age_status = "🟠 Stale"
        else:
            age_status = "🔴 Old"

        # Determine frequency compliance
        if total_rankings >= 2:
            current = rankings.order_by("-ranking_date")[0].ranking_date
            previous = rankings.order_by("-ranking_date")[1].ranking_date
            days_between = (current - previous).days

            if obj.frequency == "daily" and days_between <= 2:
                freq_status = "✅ Compliant"
            elif obj.frequency == "weekly" and days_between <= 9:
                freq_status = "✅ Compliant"
            elif obj.frequency == "monthly" and days_between <= 35:
                freq_status = "✅ Compliant"
            else:
                freq_status = "⚠️ Delayed"
        else:
            freq_status = "N/A"

        # Return formatted summary
        return f"{age_status} | {freq_status} | {total_rankings} rankings | {avg_entries:.0f} avg entries"

    get_data_summary.short_description = "Data Summary"

    def get_data_insights(self, obj):
        """Display key insights about this chart's data"""
        rankings = obj.rankings.all()
        if not rankings:
            return "🔴 No Data"

        insights = []

        # Check for trends
        if len(rankings) >= 3:
            recent_entries = [
                r.total_entries for r in rankings.order_by("-ranking_date")[:3]
            ]
            if len(recent_entries) >= 2:
                if recent_entries[0] > recent_entries[1]:
                    insights.append("📈 Growing")
                elif recent_entries[0] < recent_entries[1]:
                    insights.append("📉 Declining")
                else:
                    insights.append("➡️ Stable")

        # Check for data quality
        latest_ranking = rankings.order_by("-ranking_date").first()
        if latest_ranking and latest_ranking.total_entries > 0:
            entries_count = latest_ranking.entries.count()
            completeness = entries_count / latest_ranking.total_entries
            if completeness >= 0.95:
                insights.append("✅ High Quality")
            elif completeness >= 0.8:
                insights.append("⚠️ Good Quality")
            else:
                insights.append("❌ Low Quality")

        # Check for frequency compliance
        if len(rankings) >= 2:
            current = rankings.order_by("-ranking_date")[0].ranking_date
            previous = rankings.order_by("-ranking_date")[1].ranking_date
            days_between = (current - previous).days

            if obj.frequency == "daily" and days_between <= 2:
                insights.append("🕐 On Schedule")
            elif obj.frequency == "weekly" and days_between <= 9:
                insights.append("🕐 On Schedule")
            elif obj.frequency == "monthly" and days_between <= 35:
                insights.append("🕐 On Schedule")
            else:
                insights.append("⏰ Behind Schedule")

        # Check for data freshness
        now = datetime.now()
        days_since_ranking = (now.date() - latest_ranking.ranking_date.date()).days

        if days_since_ranking <= 1:
            insights.append("🆕 Fresh Data")
        elif days_since_ranking <= 7:
            insights.append("🆕 Recent Data")
        else:
            insights.append("🆕 Old Data")

        # Return insights
        if insights:
            return " | ".join(insights[:3])  # Limit to 3 insights
        else:
            return "N/A"

    get_data_insights.short_description = "Insights"

    def get_data_recommendations(self, obj):
        """Display actionable recommendations for this chart"""
        rankings = obj.rankings.all()
        if not rankings:
            return "🔴 Import rankings first"

        recommendations = []

        # Check for frequency compliance issues
        if len(rankings) >= 2:
            current = rankings.order_by("-ranking_date")[0].ranking_date
            previous = rankings.order_by("-ranking_date")[1].ranking_date
            days_between = (current - previous).days

            if obj.frequency == "daily" and days_between > 7:
                recommendations.append("📅 Check daily updates")
            elif obj.frequency == "weekly" and days_between > 14:
                recommendations.append("📅 Check weekly updates")
            elif obj.frequency == "monthly" and days_between > 60:
                recommendations.append("📅 Check monthly updates")

        # Check for data quality issues
        latest_ranking = rankings.order_by("-ranking_date").first()
        if latest_ranking and latest_ranking.total_entries > 0:
            entries_count = latest_ranking.entries.count()
            completeness = entries_count / latest_ranking.total_entries
            if completeness < 0.8:
                recommendations.append("🔍 Investigate missing data")

        # Check for data freshness
        now = datetime.now()
        days_since_ranking = (now.date() - latest_ranking.ranking_date.date()).days

        if days_since_ranking > 30:
            recommendations.append("🔄 Update rankings")
        elif days_since_ranking > 7:
            recommendations.append("⏰ Monitor updates")

        # Check for API version
        if latest_ranking and not latest_ranking.api_version:
            recommendations.append("🔧 Update API version")

        # Return recommendations
        if recommendations:
            return " | ".join(recommendations[:2])  # Limit to 2 recommendations
        else:
            return "✅ No action needed"

    get_data_recommendations.short_description = "Recommendations"

    def get_data_alerts(self, obj):
        """Display critical alerts for this chart"""
        rankings = obj.rankings.all()
        if not rankings:
            return "🚨 No Data"

        alerts = []

        # Check for critical data age
        latest_ranking = rankings.order_by("-ranking_date").first()
        now = datetime.now()
        days_since_ranking = (now.date() - latest_ranking.ranking_date.date()).days

        if days_since_ranking > 90:
            alerts.append("🚨 Very Old Data")
        elif days_since_ranking > 60:
            alerts.append("⚠️ Old Data")
        elif days_since_ranking > 30:
            alerts.append("⚠️ Stale Data")

        # Check for critical frequency violations
        if len(rankings) >= 2:
            current = rankings.order_by("-ranking_date")[0].ranking_date
            previous = rankings.order_by("-ranking_date")[1].ranking_date
            days_between = (current - previous).days

            if obj.frequency == "daily" and days_between > 30:
                alerts.append("🚨 Daily Chart Broken")
            elif obj.frequency == "weekly" and days_between > 60:
                alerts.append("🚨 Weekly Chart Broken")
            elif obj.frequency == "monthly" and days_between > 120:
                alerts.append("🚨 Monthly Chart Broken")

        # Check for critical data quality issues
        if latest_ranking and latest_ranking.total_entries > 0:
            entries_count = latest_ranking.entries.count()
            completeness = entries_count / latest_ranking.total_entries
            if completeness < 0.5:
                alerts.append("🚨 Very Low Quality")
            elif completeness < 0.7:
                alerts.append("⚠️ Low Quality")

        # Check for missing API version
        if latest_ranking and not latest_ranking.api_version:
            alerts.append("⚠️ Unknown API")

        # Return alerts
        if alerts:
            return " | ".join(alerts[:2])  # Limit to 2 alerts
        else:
            return "✅ No Alerts"

    get_data_alerts.short_description = "Alerts"

    def get_urls(self):
        """Add custom URLs for chart ranking import"""
        urls = super().get_urls()
        custom_urls = [
            path(
                "import/",
                self.admin_site.admin_view(self.import_charts_view),
                name="soundcharts_chart_import",
            ),
            path(
                "fetch/",
                self.admin_site.admin_view(self.fetch_charts_api),
                name="soundcharts_chart_fetch",
            ),
            path(
                "add/",
                self.admin_site.admin_view(self.add_chart_api),
                name="soundcharts_chart_add",
            ),
            path(
                "<int:object_id>/import-rankings/",
                self.admin_site.admin_view(self.import_rankings_view),
                name="soundcharts_chart_import_rankings",
            ),
            path(
                "<int:object_id>/api/fetch-rankings/",
                self.admin_site.admin_view(self.fetch_rankings_api),
                name="soundcharts_chart_fetch_rankings",
            ),
            path(
                "<int:object_id>/api/store-rankings/",
                self.admin_site.admin_view(self.store_rankings_api),
                name="soundcharts_chart_store_rankings",
            ),
        ]
        return custom_urls + urls

    def import_charts_view(self, request):
        """Display the chart import interface for platforms"""
        platform_code = request.GET.get('platform_code')
        
        if request.method == 'POST':
            # Handle chart import
            platform_code = request.POST.get('platform_code')
            country_code = request.POST.get('country_code', 'IT')
            limit = int(request.POST.get('limit', 50))
            offset = int(request.POST.get('offset', 0))
            
            if platform_code:
                try:
                    service = SoundchartsService()
                    charts_data = service.get_charts(
                        platform_code=platform_code,
                        country_code=country_code,
                        limit=limit,
                        offset=offset
                    )
                    
                    if charts_data:
                        # Process and import charts
                        imported_count = 0
                        for chart_data in charts_data:
                            # Extract chart information from API response
                            chart_name = chart_data.get('name', '')
                            chart_slug = chart_data.get('slug', '')
                            chart_type = chart_data.get('type', 'song')
                            chart_frequency = chart_data.get('frequency', 'weekly')
                            
                            if chart_name and chart_slug:
                                # Check if chart already exists
                                existing_chart = Chart.objects.filter(slug=chart_slug).first()
                                if not existing_chart:
                                    # Get or create platform
                                    platform = Platform.objects.filter(slug=platform_code).first()
                                    if platform:
                                        # Create new chart
                                        chart = Chart.objects.create(
                                            name=chart_name,
                                            slug=chart_slug,
                                            type=chart_type,
                                            frequency=chart_frequency,
                                            country_code=country_code,
                                            platform=platform
                                        )
                                        imported_count += 1
                                        logger.info(f"Imported chart: {chart_name} for platform {platform_code}")
                        
                        # Add success message
                        from django.contrib import messages
                        if imported_count > 0:
                            messages.success(request, f"Successfully imported {imported_count} charts from {platform_code.upper()}")
                        else:
                            messages.warning(request, f"No new charts were imported. They may already exist.")
                        
                        # Redirect back to platform change view
                        if platform_code:
                            platform = Platform.objects.filter(slug=platform_code).first()
                            if platform:
                                return redirect(reverse('admin:soundcharts_platform_change', args=[platform.id]))
                    
                except Exception as e:
                    from django.contrib import messages
                    messages.error(request, f"Error importing charts: {str(e)}")
                    logger.error(f"Error importing charts for platform {platform_code}: {e}")
        
        # For GET requests or if no POST data, show the import interface
        context = {
            "title": "Import Charts from Platform",
            "platform_code": platform_code,
            "opts": self.model._meta,
            "has_change_permission": self.has_change_permission(request),
            "has_add_permission": self.has_add_permission(request),
            "has_delete_permission": self.has_delete_permission(request),
            "has_view_permission": self.has_view_permission(request),
        }
        
        # Add platform object and ID for proper back button URL
        if platform_code:
            platform = Platform.objects.filter(slug=platform_code).first()
            if platform:
                context.update({
                    'platform': platform,
                    'platform_id': platform.id,
                })
        
        return TemplateResponse(
            request, "admin/soundcharts/chart_import.html", context
        )

    @csrf_exempt
    def fetch_charts_api(self, request):
        """API endpoint to fetch charts from platform"""
        if request.method != "GET":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        try:
            platform_code = request.GET.get('platform_code')
            country_code = request.GET.get('country_code', 'IT')
            limit = int(request.GET.get('limit', 50))
            offset = int(request.GET.get('offset', 0))
            
            if not platform_code:
                return JsonResponse({"error": "Platform code is required"}, status=400)
            
            service = SoundchartsService()
            charts_data = service.get_charts(
                platform_code=platform_code,
                country_code=country_code,
                limit=limit,
                offset=offset
            )
            
            if charts_data:
                # Process charts data and store in session for later use
                processed_charts = []
                session_key = f"fetched_charts_{request.session.session_key}"
                fetched_charts = {}
                
                for chart_data in charts_data:
                    chart_name = chart_data.get('name', '')
                    chart_slug = chart_data.get('slug', '')
                    chart_type = chart_data.get('type', 'song')
                    chart_frequency = chart_data.get('frequency', 'weekly')
                    
                    if chart_name and chart_slug:
                        # Check if chart already exists
                        existing_chart = Chart.objects.filter(slug=chart_slug).first()
                        
                        # Store in session for later use
                        fetched_charts[chart_slug] = {
                            'name': chart_name,
                            'slug': chart_slug,
                            'type': chart_type,
                            'frequency': chart_frequency,
                            'country_code': country_code,
                            'platform_code': platform_code
                        }
                        
                        processed_charts.append({
                            'name': chart_name,
                            'slug': chart_slug,
                            'type': chart_type,
                            'frequency': chart_frequency,
                            'country_code': country_code,
                            'already_exists': existing_chart is not None,
                            'existing_chart_id': existing_chart.id if existing_chart else None
                        })
                
                # Store in session
                request.session[session_key] = fetched_charts
                request.session.modified = True
                
                return JsonResponse({
                    "success": True,
                    "charts": processed_charts,
                    "total": len(processed_charts)
                })
            else:
                return JsonResponse({
                    "success": False,
                    "error": "No charts found for this platform and country"
                })
                
        except Exception as e:
            logger.error(f"Error fetching charts: {e}")
            return JsonResponse({
                "success": False,
                "error": f"Error fetching charts: {str(e)}"
            }, status=500)

    def import_rankings_view(self, request, object_id):
        """Display the chart ranking import interface"""
        chart = get_object_or_404(Chart, id=object_id)
        context = {
            "title": f"Import Rankings for {chart.name}",
            "chart": chart,
            "opts": self.model._meta,
            "has_change_permission": self.has_change_permission(request),
            "has_add_permission": self.has_add_permission(request),
            "has_delete_permission": self.has_delete_permission(request),
            "has_view_permission": self.has_view_permission(request),
        }
        return TemplateResponse(
            request, "admin/soundcharts/chart_import_rankings.html", context
        )

    @csrf_exempt
    def fetch_rankings_api(self, request, object_id):
        """API endpoint to fetch chart rankings"""
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        try:
            chart = get_object_or_404(Chart, id=object_id)
            data = json.loads(request.body)
            ranking_date = data.get("ranking_date")

            if not chart.slug:
                return JsonResponse({"error": "Chart has no slug"}, status=400)

            service = SoundchartsService()
            rankings = service.get_song_ranking_for_date(chart.slug, ranking_date)

            if rankings:
                # Parse the API response structure
                if isinstance(rankings, dict):
                    chart_data = rankings.get("related", {}).get("chart", {})
                    ranking_date_str = rankings.get("related", {}).get("date")
                    items = rankings.get("items", [])

                    # Parse the ranking date
                    try:
                        if ranking_date_str:
                            api_ranking_date = datetime.fromisoformat(
                                ranking_date_str.replace("Z", "+00:00")
                            )
                        else:
                            api_ranking_date = datetime.now()
                    except (ValueError, TypeError) as e:
                        logger.warning(
                            f"Could not parse ranking date '{ranking_date_str}': {e}"
                        )
                        api_ranking_date = datetime.now()

                    # Check if ranking already exists
                    existing_ranking = ChartRanking.objects.filter(
                        chart=chart, ranking_date=api_ranking_date
                    ).first()

                    return JsonResponse(
                        {
                            "success": True,
                            "data": {
                                "chart_name": chart.name,
                                "platform": chart.platform.name
                                if chart.platform
                                else "Unknown",
                                "ranking_date": api_ranking_date.isoformat(),
                                "total_entries": len(items),
                                "items": items,
                                "already_exists": existing_ranking is not None,
                                "existing_ranking_id": existing_ranking.id
                                if existing_ranking
                                else None,
                            },
                        }
                    )
                else:
                    return JsonResponse(
                        {"error": "Unexpected API response format"}, status=400
                    )
            else:
                return JsonResponse(
                    {"error": "Failed to fetch rankings from API"}, status=400
                )

        except Exception as e:
            logger.error(f"Error fetching rankings for chart {object_id}: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    @csrf_exempt
    def add_chart_api(self, request):
        """API endpoint to add a single chart"""
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        try:
            data = json.loads(request.body)
            chart_slug = data.get('slug')
            
            if not chart_slug:
                return JsonResponse({"error": "Chart slug is required"}, status=400)
            
            # Check if chart already exists
            existing_chart = Chart.objects.filter(slug=chart_slug).first()
            if existing_chart:
                return JsonResponse({
                    "success": False,
                    "error": "Chart already exists",
                    "chart_id": existing_chart.id
                })
            
            # Get chart data from session (stored during fetch)
            session_key = f"fetched_charts_{request.session.session_key}"
            fetched_charts = request.session.get(session_key, {})
            
            if chart_slug not in fetched_charts:
                return JsonResponse({
                    "success": False,
                    "error": "Chart data not found. Please fetch charts first."
                })
            
            chart_data = fetched_charts[chart_slug]
            
            # Get or create platform
            platform = Platform.objects.filter(slug=chart_data.get('platform_code')).first()
            if not platform:
                return JsonResponse({
                    "success": False,
                    "error": "Platform not found"
                })
            
            # Create the chart
            chart = Chart.objects.create(
                name=chart_data.get('name', ''),
                slug=chart_data.get('slug', ''),
                type=chart_data.get('type', 'song'),
                frequency=chart_data.get('frequency', 'weekly'),
                country_code=chart_data.get('country_code', 'IT'),
                platform=platform
            )
            
            # Remove from session after successful creation
            del fetched_charts[chart_slug]
            request.session[session_key] = fetched_charts
            request.session.modified = True
            
            logger.info(f"Successfully added chart: {chart.name} for platform {platform.slug}")
            
            return JsonResponse({
                "success": True,
                "chart_id": chart.id,
                "message": f"Chart '{chart.name}' added successfully"
            })
                
        except Exception as e:
            logger.error(f"Error adding chart: {e}")
            return JsonResponse({
                "success": False,
                "error": f"Error adding chart: {str(e)}"
            }, status=500)

    @csrf_exempt
    def store_rankings_api(self, request, object_id):
        """API endpoint to store chart rankings in database"""
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        try:
            chart = get_object_or_404(Chart, id=object_id)
            data = json.loads(request.body)
            ranking_date_str = data.get("ranking_date")
            items = data.get("items", [])

            if not chart.slug:
                return JsonResponse({"error": "Chart has no slug"}, status=400)

            # Parse the ranking date
            try:
                if ranking_date_str:
                    ranking_date = datetime.fromisoformat(ranking_date_str)
                else:
                    ranking_date = datetime.now()
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Could not parse ranking date '{ranking_date_str}': {e}"
                )
                ranking_date = datetime.now()

            # Create or update the chart ranking
            ranking, created = ChartRanking.objects.get_or_create(
                chart=chart,
                ranking_date=ranking_date,
                defaults={
                    "total_entries": len(items),
                    "api_version": "v2.14",
                },
            )

            # Clear existing entries and create new ones
            ranking.entries.all().delete()

            # Create ranking entries
            entries_created = 0
            for item_data in items:
                if isinstance(item_data, dict):
                    # Extract song data from the item
                    song_data = item_data.get("song", {})
                    track_uuid = song_data.get("uuid")
                    track_name = song_data.get("name", "Unknown")
                    credit_name = song_data.get("creditName", "")
                    image_url = song_data.get("imageUrl", "")

                    if track_uuid:
                        # Get or create the Track object
                        track, track_created = Track.objects.get_or_create(
                            uuid=track_uuid,
                            defaults={
                                "name": track_name,
                                "credit_name": credit_name,
                                "image_url": image_url,
                            },
                        )

                        # Update track if it already exists
                        if not track_created:
                            track.name = track_name
                            track.credit_name = credit_name
                            track.image_url = image_url
                            track.save()
                    else:
                        # If no UUID, try to find by name or create new
                        track, track_created = Track.objects.get_or_create(
                            name=track_name,
                            defaults={
                                "uuid": f"generated-{track_name.lower().replace(' ', '-')}",
                                "credit_name": credit_name,
                                "image_url": image_url,
                            },
                        )

                    # Create the ranking entry
                    entry = ChartRankingEntry.objects.create(
                        ranking=ranking,
                        track=track,
                        position=item_data.get("position", 0),
                        previous_position=item_data.get("oldPosition"),
                        position_change=item_data.get("positionEvolution"),
                        weeks_on_chart=item_data.get("timeOnChart"),
                        api_data=item_data,  # Store the complete API response
                    )
                    entries_created += 1

            logger.info(
                f"Stored {entries_created} ranking entries for chart {chart.name} ({chart.slug})"
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Successfully stored {entries_created} ranking entries for '{chart.name}'",
                    "ranking_id": ranking.id,
                    "entries_created": entries_created,
                }
            )

        except Exception as e:
            logger.error(f"Error storing rankings for chart {object_id}: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    def response_change(self, request, obj):
        """Handle custom actions in change form"""
        # This method is now simplified since we moved ranking import to a separate interface
        return super().response_change(request, obj)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Override change view to handle custom actions"""
        # This method is now simplified since we moved ranking import to a separate interface
        return super().change_view(request, object_id, form_url, extra_context)
