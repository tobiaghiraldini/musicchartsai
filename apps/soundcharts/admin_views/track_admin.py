from django.contrib import admin
from django.contrib import messages
from django.urls import path
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from ..models import Genre, Track, Artist, MetadataFetchTask
from .soundcharts_admin_mixin import SoundchartsAdminMixin
from ..tasks import fetch_track_metadata
from ..service import SoundchartsService
import logging
import json

logger = logging.getLogger(__name__)


class TrackAdmin(SoundchartsAdminMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "uuid",
        "credit_name",
        "slug",
        "release_date",
        "duration",
        "isrc",
        "label",
        "primary_artist",
        "primary_genre",
        "metadata_fetched_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at", "metadata_fetched_at", "primary_artist", "primary_genre", "label", "genres", "artists")
    search_fields = ("name", "uuid", "credit_name", "slug", "isrc")
    ordering = ("name",)
    readonly_fields = ("uuid", "metadata_fetched_at", "audience_fetched_at")
    actions = ["fetch_metadata_for_selected", "create_bulk_metadata_task"]
    
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "uuid", "credit_name", "image_url")},
        ),
        (
            "Enhanced Metadata",
            {
                "fields": (
                    "slug",
                    "release_date",
                    "duration",
                    "isrc",
                    "label",
                    "primary_artist",
                    "artists",
                    "primary_genre",
                    "genres",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata Tracking",
            {
                "fields": ("metadata_fetched_at", "audience_fetched_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def fetch_metadata_for_selected(self, request, queryset):
        """Fetch metadata for selected tracks from Soundcharts API"""
        success_count = 0
        error_count = 0
        
        for track in queryset:
            if not track.uuid:
                messages.warning(request, f"Track '{track.name}' has no UUID")
                error_count += 1
                continue
            
            try:
                # Use Celery task for background processing
                task = fetch_track_metadata.delay(track.uuid)
                success_count += 1
                messages.info(request, f"Metadata fetch queued for track '{track.name}' (Task ID: {task.id})")
            except Exception as e:
                error_count += 1
                messages.error(request, f"Error queuing metadata fetch for track '{track.name}': {str(e)}")
                logger.error(f"Error queuing metadata fetch for track {track.name}: {e}")
        
        if success_count > 0:
            messages.success(request, f"Successfully queued metadata fetch for {success_count} track(s)")
        if error_count > 0:
            messages.warning(request, f"Failed to queue metadata fetch for {error_count} track(s)")
    
    fetch_metadata_for_selected.short_description = "Fetch metadata from Soundcharts API (Background)"

    def create_bulk_metadata_task(self, request, queryset):
        """Create a bulk metadata fetch task for selected tracks"""
        if queryset.count() == 0:
            messages.warning(request, "No tracks selected")
            return
        
        try:
            track_uuids = list(queryset.values_list('uuid', flat=True))
            
            # Create the task record
            task = MetadataFetchTask.objects.create(
                task_type='bulk_metadata',
                status='pending',
                track_uuids=track_uuids,
                total_tracks=len(track_uuids)
            )
            
            # Start the bulk fetch task
            from ..tasks import fetch_bulk_track_metadata
            fetch_bulk_track_metadata.delay(task.id)
            
            messages.success(
                request, 
                f"Created bulk metadata fetch task for {len(track_uuids)} tracks. Task ID: {task.id}"
            )
            
        except Exception as e:
            messages.error(request, f"Error creating bulk metadata task: {str(e)}")
            logger.error(f"Error creating bulk metadata task: {e}")
    
    create_bulk_metadata_task.short_description = "Create bulk metadata fetch task"

    def create_bulk_audience_task(self, request, queryset):
        """Create a bulk audience fetch task for selected tracks"""
        if queryset.count() == 0:
            messages.warning(request, "No tracks selected")
            return
        
        try:
            track_uuids = list(queryset.values_list('uuid', flat=True))
            
            # Create the task record
            task = MetadataFetchTask.objects.create(
                task_type='bulk_audience',
                status='pending',
                track_uuids=track_uuids,
                total_tracks=len(track_uuids)
            )
            
            # Start the bulk fetch task
            from ..tasks import fetch_bulk_audience_data
            fetch_bulk_audience_data.delay(task.id)
            
            messages.success(request, f"Created bulk audience fetch task for {len(track_uuids)} tracks. Task ID: {task.id}")
            
        except Exception as e:
            messages.error(request, f"Error creating bulk audience task: {str(e)}")
            logger.error(f"Error creating bulk audience task: {e}")
    
    create_bulk_audience_task.short_description = "Create bulk audience fetch task"

    def response_change(self, request, obj):
        """Handle custom actions in change form"""
        # Note: The actual import actions are now handled via AJAX in the JavaScript
        # This method is kept for backward compatibility but the buttons now use AJAX
        return super().response_change(request, obj)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Add custom buttons to the change view"""
        extra_context = extra_context or {}
        extra_context["show_fetch_metadata_button"] = True
        extra_context["show_fetch_audience_button"] = True
        
        # Add available platforms for audience fetching
        from ..models import Platform
        extra_context["available_platforms"] = Platform.objects.all().values_list('slug', 'name')
        
        return super().change_view(request, object_id, form_url, extra_context)

    def changelist_view(self, request, extra_context=None):
        """Add custom buttons to the changelist view"""
        extra_context = extra_context or {}
        extra_context["show_bulk_metadata_button"] = True
        return super().changelist_view(request, extra_context)

    def get_urls(self):
        """Add custom URLs for track admin actions"""
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:object_id>/fetch-metadata/",
                self.admin_site.admin_view(self.fetch_metadata_api),
                name="soundcharts_track_fetch_metadata",
            ),
            path(
                "<int:object_id>/fetch-audience/",
                self.admin_site.admin_view(self.fetch_audience_api),
                name="soundcharts_track_fetch_audience",
            ),
            path(
                "bulk-fetch-metadata/",
                self.admin_site.admin_view(self.bulk_fetch_metadata_api),
                name="soundcharts_track_bulk_fetch_metadata",
            ),
        ]
        return custom_urls + urls

    @csrf_exempt
    def fetch_metadata_api(self, request, object_id):
        """API endpoint to fetch metadata for a single track"""
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        try:
            track = get_object_or_404(Track, id=object_id)
            
            if not track.uuid:
                return JsonResponse({
                    "success": False,
                    "error": "Track has no UUID - cannot fetch metadata"
                })

            # Fetch metadata synchronously for immediate feedback
            service = SoundchartsService()
            metadata = service.get_song_metadata_enhanced(track.uuid)
            
            if metadata and "object" in metadata:
                track_data = metadata["object"]
                
                # Update track with metadata
                if "name" in track_data:
                    track.name = track_data["name"]
                if "slug" in track_data:
                    track.slug = track_data["slug"]
                if "creditName" in track_data:
                    track.credit_name = track_data["creditName"]
                if "imageUrl" in track_data:
                    track.image_url = track_data["imageUrl"]
                
                # Update enhanced metadata fields
                if "releaseDate" in track_data and track_data["releaseDate"]:
                    try:
                        from datetime import datetime
                        release_date = datetime.strptime(track_data["releaseDate"], "%Y-%m-%d").date()
                        track.release_date = release_date
                    except (ValueError, TypeError):
                        pass
                
                if "duration" in track_data:
                    track.duration = track_data["duration"]
                if "isrc" in track_data:
                    track.isrc = track_data["isrc"]
                if "label" in track_data and track_data["label"]:
                    track.label = track_data["label"]["name"] if isinstance(track_data["label"], dict) else track_data["label"]
                
                # Process genres
                if "genres" in track_data and track_data["genres"]:
                    track.genres.clear()
                    track_genres = []
                    primary_genre = None
                    
                    if isinstance(track_data["genres"], list) and len(track_data["genres"]) > 0:
                        for genre_data in track_data["genres"]:
                            if isinstance(genre_data, dict) and "root" in genre_data:
                                result = Genre.create_from_soundcharts(genre_data)
                                if result:
                                    root_genre, subgenres = result
                                    track_genres.append(root_genre)
                                    track_genres.extend(subgenres)
                                    
                                    if primary_genre is None:
                                        primary_genre = root_genre
                    
                    if track_genres:
                        track.genres.set(track_genres)
                        track.primary_genre = primary_genre

                # Process artists
                if "artists" in track_data and track_data["artists"]:
                    track.artists.clear()
                    track_artists = []
                    primary_artist = None
                    
                    if isinstance(track_data["artists"], list) and len(track_data["artists"]) > 0:
                        for artist_data in track_data["artists"]:
                            if isinstance(artist_data, dict) and "uuid" in artist_data and "name" in artist_data:
                                artist = Artist.create_from_soundcharts(artist_data)
                                if artist:
                                    track_artists.append(artist)
                                    
                                    if primary_artist is None:
                                        primary_artist = artist
                    
                    if track_artists:
                        track.artists.set(track_artists)
                        track.primary_artist = primary_artist

                track.metadata_fetched_at = timezone.now()
                track.save()
                
                logger.info(f"Successfully fetched metadata for track {track.uuid}")
                return JsonResponse({
                    "success": True,
                    "message": f"Successfully fetched and updated metadata for '{track.name}'"
                })
            else:
                return JsonResponse({
                    "success": False,
                    "error": f"Failed to fetch metadata for '{track.name}'"
                })
                
        except Exception as e:
            logger.error(f"Error fetching metadata for track {object_id}: {e}")
            return JsonResponse({
                "success": False,
                "error": f"Error fetching metadata: {str(e)}"
            }, status=500)

    @csrf_exempt
    def fetch_audience_api(self, request, object_id):
        """API endpoint to fetch audience data for a single track"""
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        try:
            track = get_object_or_404(Track, id=object_id)
            data = json.loads(request.body)
            platform = data.get('platform', 'spotify')
            force_refresh = data.get('force_refresh', False)
            
            if not track.uuid:
                return JsonResponse({
                    "success": False,
                    "error": "Track has no UUID - cannot fetch audience data"
                })

            from ..audience_processor import AudienceDataProcessor
            processor = AudienceDataProcessor()
            
            result = processor.process_and_store_audience_data(
                track.uuid, 
                platform, 
                force_refresh
            )
            
            if result['success']:
                track.audience_fetched_at = timezone.now()
                track.save()
                
                logger.info(f"Successfully fetched audience data for track {track.uuid} on {platform}")
                return JsonResponse({
                    "success": True,
                    "message": f"Successfully fetched audience data for '{track.name}' on {platform}: "
                              f"{result['records_created']} created, {result['records_updated']} updated"
                })
            else:
                return JsonResponse({
                    "success": False,
                    "error": f"Failed to fetch audience data for '{track.name}' on {platform}: {result['error']}"
                })
                
        except Exception as e:
            logger.error(f"Error fetching audience data for track {object_id}: {e}")
            return JsonResponse({
                "success": False,
                "error": f"Error fetching audience data: {str(e)}"
            }, status=500)

    @csrf_exempt
    def bulk_fetch_metadata_api(self, request):
        """API endpoint to start bulk metadata fetch for selected tracks"""
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        try:
            data = json.loads(request.body)
            track_ids = data.get('track_ids', [])
            
            if not track_ids:
                return JsonResponse({
                    "success": False,
                    "error": "No track IDs provided"
                })

            # Get the actual track UUIDs from the track IDs
            tracks = Track.objects.filter(id__in=track_ids).values_list('uuid', flat=True)
            track_uuids = [uuid for uuid in tracks if uuid]  # Filter out None values
            
            if not track_uuids:
                return JsonResponse({
                    "success": False,
                    "error": "No valid track UUIDs found for the selected tracks"
                })

            # Create the task record
            task = MetadataFetchTask.objects.create(
                task_type='bulk_metadata',
                status='pending',
                track_uuids=track_uuids,
                total_tracks=len(track_uuids)
            )
            
            # Start the bulk fetch task
            from ..tasks import fetch_bulk_track_metadata
            fetch_bulk_track_metadata.delay(task.id)
            
            logger.info(f"Created bulk metadata fetch task for {len(track_uuids)} tracks. Task ID: {task.id}")
            return JsonResponse({
                "success": True,
                "message": f"Created bulk metadata fetch task for {len(track_uuids)} tracks. Task ID: {task.id}"
            })
            
        except Exception as e:
            logger.error(f"Error creating bulk metadata task: {e}")
            return JsonResponse({
                "success": False,
                "error": f"Error creating bulk metadata task: {str(e)}"
            }, status=500)
