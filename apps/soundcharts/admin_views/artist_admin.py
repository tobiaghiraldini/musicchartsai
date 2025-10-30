from django.contrib import admin, messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import path
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime
import logging
import json

from ..models import Artist, Genre, Platform, ArtistAudienceTimeSeries
from ..service import SoundchartsService
from .soundcharts_admin_mixin import SoundchartsAdminMixin

logger = logging.getLogger(__name__)

# Default audience platforms to fetch when using the admin action/button
DEFAULT_AUDIENCE_PLATFORMS = [
    'spotify',
    'youtube',
    'tiktok',
    'airplay',
    'shazam',
]


class ArtistAdmin(SoundchartsAdminMixin, admin.ModelAdmin):
    list_display = ("name", "uuid", "slug", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "uuid", "slug")
    ordering = ("name",)
    readonly_fields = ("uuid", "slug", "appUrl", "imageUrl")

    actions = ["fetch_artist_metadata"]

    def fetch_artist_metadata(self, request, queryset):
        """Fetch metadata for selected artists from Soundcharts API"""
        service = SoundchartsService()
        success_count = 0
        error_count = 0
        messages = []

        for artist in queryset:
            if not artist.uuid:
                messages.append(f"Artist '{artist.name}' has no UUID")
                error_count += 1
                continue

            try:
                metadata = service.get_artist_metadata(artist.uuid)
                if metadata:
                    # Update artist with metadata
                    if "object" in metadata:
                        artist_data = metadata["object"]

                        # Map all available fields from the API response
                        if "name" in artist_data:
                            artist.name = artist_data["name"]
                        if "slug" in artist_data:
                            artist.slug = artist_data["slug"]
                        if "appUrl" in artist_data:
                            artist.appUrl = artist_data["appUrl"]
                        if "imageUrl" in artist_data:
                            artist.imageUrl = artist_data["imageUrl"]

                        # Save the updated artist
                        artist.save()

                        logger.debug("Metadata:", metadata)
                        messages.append(
                            f"Successfully fetched and updated metadata for '{artist.name}'"
                        )
                        success_count += 1
                    else:
                        messages.append(f"Invalid metadata format for '{artist.name}'")
                        error_count += 1
                else:
                    messages.append(f"Failed to fetch metadata for '{artist.name}'")
                    error_count += 1
            except Exception as e:
                messages.append(
                    f"Error fetching metadata for '{artist.name}': {str(e)}"
                )
                error_count += 1

        # Display results
        if success_count > 0:
            self.message_user(
                request,
                f"Successfully fetched and updated metadata for {success_count} artist(s)",
            )
        if error_count > 0:
            self.message_user(
                request,
                f"Failed to fetch metadata for {error_count} artist(s)",
                level=messages.WARNING,
            )

        # Log detailed messages
        for message in messages:
            logger.info(f"Artist metadata fetch: {message}")

    fetch_artist_metadata.short_description = "Fetch metadata from Soundcharts API"

    def response_change(self, request, obj):
        """Handle custom actions in change form - now handled in change_view"""
        # The fetch actions are now handled in change_view() before form validation
        # This method is kept for compatibility with standard Django admin flow
        return super().response_change(request, obj)
    
    def _process_artist_audience_data(self, artist, platform_slug, audience_data):
        """
        Process and store artist audience data from Soundcharts API.
        
        API Response structure:
        {
            "related": {
                "artist": {...},
                "platform": "spotify",
                "lastCrawlDate": "2025-10-15T12:00:00+00:00"
            },
            "items": [
                {"date": "2025-07-17T00:00:00+00:00", "followerCount": 3083287, ...},
                {"date": "2025-07-18T00:00:00+00:00", "followerCount": 3083873, ...},
                ...
            ],
            "page": {"offset": 0, "limit": 100, "total": 112}
        }
        """
        try:
            # Get the platform object
            platform = Platform.objects.filter(slug=platform_slug).first()
            if not platform:
                return {'success': False, 'error': f'Platform {platform_slug} not found'}
            
            # Extract the time-series data
            items = audience_data.get('items', [])
            # related = audience_data.get('related', {})  # not used currently
            
            if not items:
                return {'success': False, 'error': 'No time-series data in response'}
            
            # Get the latest follower count (last item in the list)
            latest_item = items[-1] if items else {}
            follower_count = (latest_item.get('followerCount') or 
                            latest_item.get('likeCount') or 
                            latest_item.get('viewCount'))
            
            # Store time-series data from items
            records_created = 0
            records_updated = 0
            
            for item in items:
                item_date_str = item.get('date')
                if not item_date_str:
                    continue
                
                try:
                    # Parse date (format: YYYY-MM-DDTHH:MM:SS+00:00 or YYYY-MM-DD)
                    if 'T' in item_date_str:
                        item_date = datetime.fromisoformat(item_date_str.replace('Z', '+00:00')).date()
                    else:
                        item_date = datetime.strptime(item_date_str, '%Y-%m-%d').date()
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse item date '{item_date_str}': {e}")
                    continue
                
                # Get the metric value (followerCount, likeCount, or viewCount)
                audience_value = (item.get('followerCount') or 
                                item.get('likeCount') or 
                                item.get('viewCount'))
                if audience_value is None:
                    continue
                
                # Create or update ArtistAudienceTimeSeries record
                ts_record, created = ArtistAudienceTimeSeries.objects.update_or_create(
                    artist=artist,
                    platform=platform,
                    date=item_date,
                    defaults={
                        'audience_value': audience_value,
                        'platform_identifier': '',  # Not provided in this endpoint
                        'api_data': item,
                        'fetched_at': timezone.now()
                    }
                )
                
                if created:
                    records_created += 1
                else:
                    records_updated += 1
            
            logger.info(f"Stored {records_created} new records, updated {records_updated} records for {artist.name} on {platform_slug}")
            
            return {
                'success': True,
                'records_created': records_created,
                'records_updated': records_updated,
                'latest_follower_count': follower_count,
                'total_items': len(items)
            }
            
        except Exception as e:
            logger.error(f"Error processing artist audience data: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'success': False, 'error': str(e)}

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Add custom buttons to the change view and handle fetch actions before form validation"""
        
        # Handle fetch actions BEFORE form validation
        if request.method == "POST":
            if "_fetch_metadata" in request.POST:
                # Get the object without going through form validation
                obj = self.get_object(request, object_id)
                if obj:
                    return self._handle_fetch_metadata(request, obj)
            
            elif "_fetch_audience" in request.POST:
                # Get the object without going through form validation
                obj = self.get_object(request, object_id)
                if obj:
                    return self._handle_fetch_audience(request, obj)
            elif "_fetch_audience_selected" in request.POST:
                obj = self.get_object(request, object_id)
                if obj:
                    return self._handle_fetch_audience_selected(request, obj)
        
        # Add context for template
        extra_context = extra_context or {}
        extra_context["show_fetch_metadata_button"] = True
        extra_context["show_fetch_audience_button"] = True
        
        # Note: We intentionally do NOT expose a platform selector anymore for audience fetch.
        # The audience fetch button will fetch across DEFAULT_AUDIENCE_PLATFORMS.
        
        return super().change_view(request, object_id, form_url, extra_context)
    
    def _handle_fetch_metadata(self, request, obj):
        """Handle metadata fetch action"""
        if not obj.uuid:
            self.message_user(
                request, f"Artist '{obj.name}' has no UUID", level=messages.WARNING
            )
            return HttpResponseRedirect(request.get_full_path())
        
        service = SoundchartsService()
        try:
            metadata = service.get_artist_metadata(obj.uuid)
            if metadata and "object" in metadata:
                artist_data = metadata["object"]

                logger.debug("Artist Metadata:", artist_data)
                # Map all available fields from the API response
                if "name" in artist_data:
                    obj.name = artist_data["name"]
                if "slug" in artist_data:
                    obj.slug = artist_data["slug"]
                if "appUrl" in artist_data:
                    obj.appUrl = artist_data["appUrl"]
                if "imageUrl" in artist_data:
                    obj.imageUrl = artist_data["imageUrl"]
                if "biography" in artist_data:
                    obj.biography = artist_data["biography"]
                if "isni" in artist_data:
                    obj.isni = artist_data["isni"]
                if "ipi" in artist_data:
                    obj.ipi = artist_data["ipi"]
                if "gender" in artist_data:
                    obj.gender = artist_data["gender"]
                if "type" in artist_data:
                    obj.type = artist_data["type"]
                if "birthDate" in artist_data:
                    try:
                        # Handle ISO datetime string format
                        if artist_data["birthDate"]:
                            if "T" in artist_data["birthDate"]:
                                # ISO format: "2001-12-18T00:00:00+00:00"
                                obj.birthDate = datetime.fromisoformat(
                                    artist_data["birthDate"].replace("Z", "+00:00")
                                ).date()
                            else:
                                # Simple date format: "2001-12-18"
                                obj.birthDate = datetime.strptime(
                                    artist_data["birthDate"], "%Y-%m-%d"
                                ).date()
                    except (ValueError, TypeError) as e:
                        logger.warning(
                            f"Could not parse birthDate '{artist_data['birthDate']}': {e}"
                        )
                if "careerStage" in artist_data:
                    obj.careerStage = artist_data["careerStage"]
                if "cityName" in artist_data:
                    obj.cityName = artist_data["cityName"]
                if "countryCode" in artist_data:
                    obj.countryCode = artist_data["countryCode"]
                if "genres" in artist_data:
                    # Handle genres - create or find Genre objects and link them
                    genre_names = set()
                    for genre_obj in artist_data["genres"]:
                        if "root" in genre_obj:
                            genre_names.add(genre_obj["root"])
                        if "sub" in genre_obj:
                            genre_names.update(genre_obj["sub"])

                    # Clear existing genres and add new ones
                    obj.genres.clear()

                    for genre_name in genre_names:
                        # Try to find existing genre by name, or create new one
                        genre, created = Genre.objects.get_or_create(
                            name=genre_name,
                            defaults={
                                "slug": Genre._generate_unique_slug(genre_name)
                            },
                        )
                        obj.genres.add(genre)

                        if created:
                            logger.info(f"Created new genre: {genre_name}")
                        else:
                            logger.info(f"Found existing genre: {genre_name}")
                
                # Update metadata fetch timestamp
                obj.metadata_fetched_at = timezone.now()
                # Save the updated object
                obj.save()

                self.message_user(
                    request,
                    f"Successfully fetched and updated metadata for '{obj.name}'",
                )
                logger.info(f"Updated artist {obj.name} with metadata: {metadata}")
            else:
                self.message_user(
                    request,
                    f"Invalid metadata format for '{obj.name}'",
                    level=messages.WARNING,
                )
        except Exception as e:
            self.message_user(
                request,
                f"Error fetching metadata for '{obj.name}': {str(e)}",
                level=messages.ERROR,
            )
            logger.error(f"Error fetching metadata for artist {obj.name}: {e}")
        
        return HttpResponseRedirect(request.get_full_path())

    def _handle_fetch_audience_selected(self, request, obj):
        """Handle single selected-platform audience fetch"""
        if not obj.uuid:
            self.message_user(
                request, f"Artist '{obj.name}' has no UUID", level=messages.WARNING
            )
            return HttpResponseRedirect(request.get_full_path())

        platform = request.POST.get('platform', 'spotify')
        service = SoundchartsService()
        try:
            audience_data = service.get_artist_audience_for_platform(
                obj.uuid,
                platform=platform,
            )
            if audience_data and "items" in audience_data:
                result = self._process_artist_audience_data(obj, platform, audience_data)
                if result['success']:
                    obj.audience_fetched_at = timezone.now()
                    obj.save()
                    records_msg = f"{result.get('records_created', 0)} created, {result.get('records_updated', 0)} updated"
                    follower_msg = (
                        f" Latest: {result.get('latest_follower_count', 'N/A'):,}"
                        if result.get('latest_follower_count') else ""
                    )
                    self.message_user(
                        request,
                        f"Fetched audience for '{obj.name}' on {platform}: {records_msg}.{follower_msg}",
                    )
                else:
                    self.message_user(
                        request,
                        f"Failed to process audience for '{obj.name}' on {platform}: {result.get('error', 'Unknown error')}",
                        level=messages.WARNING,
                    )
            else:
                self.message_user(
                    request,
                    f"Failed to fetch audience for '{obj.name}' on {platform}",
                    level=messages.WARNING,
                )
        except Exception as e:
            self.message_user(
                request,
                f"Error fetching audience for '{obj.name}' on {platform}: {str(e)}",
                level=messages.ERROR,
            )
            logger.error(f"Error fetching audience data for artist {obj.name} on {platform}: {e}")

        return HttpResponseRedirect(request.get_full_path())
    
    def _handle_fetch_audience(self, request, obj):
        """Handle audience fetch action - fetches across DEFAULT_AUDIENCE_PLATFORMS"""
        if not obj.uuid:
            self.message_user(
                request, f"Artist '{obj.name}' has no UUID", level=messages.WARNING
            )
            return HttpResponseRedirect(request.get_full_path())
        
        # Fetch across all default platforms
        platforms = list(DEFAULT_AUDIENCE_PLATFORMS)
        fetched_ok = 0
        fetched_fail = 0
        per_platform_msgs = []

        service = SoundchartsService()
        for platform in platforms:
            try:
                audience_data = service.get_artist_audience_for_platform(
                    obj.uuid,
                    platform=platform
                )
                if audience_data and "items" in audience_data:
                    result = self._process_artist_audience_data(obj, platform, audience_data)
                    if result['success']:
                        fetched_ok += 1
                        records_msg = f"{result.get('records_created', 0)} created, {result.get('records_updated', 0)} updated"
                        follower_msg = (
                            f" Latest: {result.get('latest_follower_count', 'N/A'):,}"
                            if result.get('latest_follower_count') else ""
                        )
                        per_platform_msgs.append(f"{platform}: OK ({records_msg}.{follower_msg})")
                        logger.info(f"Updated artist {obj.name} with audience data on {platform}: {result}")
                    else:
                        fetched_fail += 1
                        per_platform_msgs.append(
                            f"{platform}: FAIL (process - {result.get('error', 'Unknown error')})"
                        )
                else:
                    fetched_fail += 1
                    per_platform_msgs.append(f"{platform}: FAIL (fetch)")
            except Exception as e:
                fetched_fail += 1
                per_platform_msgs.append(f"{platform}: ERROR ({str(e)})")
                logger.error(f"Error fetching audience data for artist {obj.name} on {platform}: {e}")

        # Update timestamp if at least one platform succeeded
        if fetched_ok > 0:
            obj.audience_fetched_at = timezone.now()
            obj.save()

        # Summary admin message
        summary = f"Fetched audience for {obj.name}: {fetched_ok} ok, {fetched_fail} failed."
        self.message_user(request, summary, level=messages.SUCCESS if fetched_ok else messages.WARNING)
        # Detail as info
        self.message_user(request, "; ".join(per_platform_msgs), level=messages.INFO)
        
        return HttpResponseRedirect(request.get_full_path())
    
    def get_urls(self):
        """Add custom URLs for artist admin actions"""
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:object_id>/fetch-metadata/",
                self.admin_site.admin_view(self.fetch_metadata_api),
                name="soundcharts_artist_fetch_metadata",
            ),
            path(
                "<int:object_id>/fetch-audience/",
                self.admin_site.admin_view(self.fetch_audience_api),
                name="soundcharts_artist_fetch_audience",
            ),
        ]
        return custom_urls + urls
    
    @csrf_exempt
    def fetch_metadata_api(self, request, object_id):
        """API endpoint to fetch metadata for a single artist"""
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        try:
            artist = get_object_or_404(Artist, id=object_id)

            if not artist.uuid:
                return JsonResponse({
                    "success": False,
                    "error": "Artist has no UUID - cannot fetch metadata"
                })

            service = SoundchartsService()
            metadata = service.get_artist_metadata(artist.uuid)

            if metadata and "object" in metadata:
                artist_data = metadata["object"]

                if "name" in artist_data:
                    artist.name = artist_data["name"]
                if "slug" in artist_data:
                    artist.slug = artist_data["slug"]
                if "appUrl" in artist_data:
                    artist.appUrl = artist_data["appUrl"]
                if "imageUrl" in artist_data:
                    artist.imageUrl = artist_data["imageUrl"]
                if "biography" in artist_data:
                    artist.biography = artist_data["biography"]
                if "isni" in artist_data:
                    artist.isni = artist_data["isni"]
                if "ipi" in artist_data:
                    artist.ipi = artist_data["ipi"]
                if "gender" in artist_data:
                    artist.gender = artist_data["gender"]
                if "type" in artist_data:
                    artist.type = artist_data["type"]
                if "careerStage" in artist_data:
                    artist.careerStage = artist_data["careerStage"]
                if "cityName" in artist_data:
                    artist.cityName = artist_data["cityName"]
                if "countryCode" in artist_data:
                    artist.countryCode = artist_data["countryCode"]

                artist.metadata_fetched_at = timezone.now()
                artist.save()

                return JsonResponse({
                    "success": True,
                    "message": f"Successfully fetched and updated metadata for '{artist.name}'"
                })
            else:
                return JsonResponse({
                    "success": False,
                    "error": f"Failed to fetch metadata for '{artist.name}'"
                })

        except Exception as e:
            logger.error(f"Error fetching metadata for artist {object_id}: {e}")
            return JsonResponse({
                "success": False,
                "error": f"Error fetching metadata: {str(e)}"
            }, status=500)

    @csrf_exempt
    def fetch_audience_api(self, request, object_id):
        """API endpoint to fetch audience data for a single artist"""
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        try:
            artist = get_object_or_404(Artist, id=object_id)
            data = json.loads(request.body)
            platform = data.get('platform', 'spotify')
            start_date = data.get('start_date')  # Optional: format YYYY-MM-DD
            end_date = data.get('end_date')      # Optional: format YYYY-MM-DD
            
            if not artist.uuid:
                return JsonResponse({
                    "success": False,
                    "error": "Artist has no UUID - cannot fetch audience data"
                })

            service = SoundchartsService()
            audience_data = service.get_artist_audience_for_platform(
                artist.uuid, 
                platform=platform,
                start_date=start_date,
                end_date=end_date
            )
            
            if audience_data and "items" in audience_data:
                result = self._process_artist_audience_data(artist, platform, audience_data)
                
                if result['success']:
                    artist.audience_fetched_at = timezone.now()
                    artist.save()
                    
                    records_msg = f"{result.get('records_created', 0)} created, {result.get('records_updated', 0)} updated"
                    logger.info(f"Successfully fetched audience data for artist {artist.uuid} on {platform}: {result}")
                    
                    return JsonResponse({
                        "success": True,
                        "message": f"Successfully fetched audience data for '{artist.name}' on {platform}: {records_msg}",
                        "data": {
                            "records_created": result.get('records_created', 0),
                            "records_updated": result.get('records_updated', 0),
                            "latest_follower_count": result.get('latest_follower_count')
                        }
                    })
                else:
                    return JsonResponse({
                        "success": False,
                        "error": f"Failed to process audience data for '{artist.name}' on {platform}: {result.get('error', 'Unknown error')}"
                    })
            else:
                return JsonResponse({
                    "success": False,
                    "error": f"Failed to fetch audience data for '{artist.name}' on {platform}"
                })
                
        except Exception as e:
            logger.error(f"Error fetching audience data for artist {object_id}: {e}")
            return JsonResponse({
                "success": False,
                "error": f"Error fetching audience data: {str(e)}"
            }, status=500)
