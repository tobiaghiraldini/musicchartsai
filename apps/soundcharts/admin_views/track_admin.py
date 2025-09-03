from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.utils import timezone
from ..models import Track, MetadataFetchTask
from .soundcharts_admin_mixin import SoundchartsAdminMixin
from ..tasks import fetch_track_metadata, fetch_all_tracks_metadata
from ..service import SoundchartsService
import logging

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
        "genre",
        "metadata_fetched_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at", "metadata_fetched_at", "genre", "label")
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
                    "genre",
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

    def response_change(self, request, obj):
        """Handle custom actions in change form"""
        if "_fetch_audience" in request.POST:
            # Handle single track audience fetch
            if obj.uuid:
                try:
                    from ..audience_processor import AudienceDataProcessor
                    processor = AudienceDataProcessor()
                    
                    # Get platform from POST data or default to spotify
                    platform = request.POST.get('platform', 'spotify')
                    force_refresh = 'force_refresh' in request.POST
                    
                    result = processor.process_and_store_audience_data(
                        obj.uuid, 
                        platform, 
                        force_refresh
                    )
                    
                    if result['success']:
                        obj.audience_fetched_at = timezone.now()
                        obj.save()
                        
                        messages.success(
                            request, 
                            f"Successfully fetched audience data for '{obj.name}' on {platform}: "
                            f"{result['records_created']} created, {result['records_updated']} updated"
                        )
                        logger.info(f"Successfully fetched audience data for track {obj.uuid} on {platform}")
                    else:
                        messages.error(
                            request, 
                            f"Failed to fetch audience data for '{obj.name}' on {platform}: {result['error']}"
                        )
                        logger.error(f"Failed to fetch audience data for track {obj.uuid} on {platform}: {result['error']}")
                        
                except Exception as e:
                    messages.error(request, f"Error fetching audience data: {str(e)}")
                    logger.error(f"Error fetching audience data for track {obj.uuid}: {e}")
            else:
                messages.error(request, "Track has no UUID - cannot fetch audience data")
            
            # Redirect to prevent form resubmission
            return HttpResponseRedirect(request.get_full_path())
        
        elif "_fetch_metadata" in request.POST:
            # Handle single track metadata fetch
            if obj.uuid:
                try:
                    # Fetch metadata synchronously for immediate feedback
                    service = SoundchartsService()
                    metadata = service.get_song_metadata_enhanced(obj.uuid)
                    logger.info(f"Metadata: {metadata}")
                    if metadata and "object" in metadata:
                        track_data = metadata["object"]
                        
                        # Update track with metadata
                        if "name" in track_data:
                            obj.name = track_data["name"]
                        if "slug" in track_data:
                            obj.slug = track_data["slug"]
                        if "creditName" in track_data:
                            obj.credit_name = track_data["creditName"]
                        if "imageUrl" in track_data:
                            obj.image_url = track_data["imageUrl"]
                        
                        # Update enhanced metadata fields
                        if "releaseDate" in track_data and track_data["releaseDate"]:
                            try:
                                from datetime import datetime
                                release_date = datetime.strptime(track_data["releaseDate"], "%Y-%m-%d").date()
                                obj.release_date = release_date
                            except (ValueError, TypeError):
                                pass
                        
                        if "duration" in track_data:
                            obj.duration = track_data["duration"]
                        if "isrc" in track_data:
                            obj.isrc = track_data["isrc"]
                        if "label" in track_data and track_data["label"]:
                            obj.label = track_data["label"]["name"] if isinstance(track_data["label"], dict) else track_data["label"]
                        if "genres" in track_data and track_data["genres"]:
                            if isinstance(track_data["genres"], list) and len(track_data["genres"]) > 0:
                                genre = track_data["genres"][0]
                                if isinstance(genre, dict) and "name" in genre:
                                    obj.genre = genre["name"]
                                elif isinstance(genre, str):
                                    obj.genre = genre
                        
                        obj.metadata_fetched_at = timezone.now()
                        obj.save()
                        
                        messages.success(
                            request, 
                            f"Successfully fetched and updated metadata for '{obj.name}'"
                        )
                        logger.info(f"Successfully fetched metadata for track {obj.uuid}")
                    else:
                        messages.error(request, f"Failed to fetch metadata for '{obj.name}'")
                        logger.error(f"Failed to fetch metadata for track {obj.uuid}")
                        
                except Exception as e:
                    messages.error(request, f"Error fetching metadata: {str(e)}")
                    logger.error(f"Error fetching metadata for track {obj.uuid}: {e}")
            
            # Redirect to prevent form resubmission
            return HttpResponseRedirect(request.get_full_path())
        
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
