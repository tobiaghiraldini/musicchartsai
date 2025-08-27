from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json
import logging
from django.http import HttpResponseRedirect
from datetime import datetime

from ..models import (
    Platform,
    Artist,
    Album,
    Track,
    Venue,
    Chart,
    Genre,
    ChartRanking,
    ChartRankingEntry,
)
from ..service import SoundchartsService

logger = logging.getLogger(__name__)


class SoundchartsAdminMixin:
    """Mixin to add custom admin functionality for Soundcharts models"""

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import/",
                self.admin_site.admin_view(self.import_view),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_import",
            ),
            path(
                "api/fetch/",
                self.admin_site.admin_view(self.fetch_api_data),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_fetch_api",
            ),
            path(
                "api/add-item/",
                self.admin_site.admin_view(self.add_to_database),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_add",
            ),
            path(
                "api/add-all/",
                self.admin_site.admin_view(self.add_all_to_database),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_add_all",
            ),
        ]

        # Add artist-specific URLs
        if self.model == Artist:
            custom_urls.extend(
                [
                    # Removed the conflicting URL routing approach
                ]
            )

        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        """Override changelist view to add import button"""
        extra_context = extra_context or {}
        extra_context["show_import_button"] = True
        extra_context["import_url"] = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_import"
        )
        return super().changelist_view(request, extra_context)

    def import_view(self, request):
        """Main import view that displays the interface"""
        context = {
            "title": f"Import {self.model._meta.verbose_name_plural} from Soundcharts API",
            "model_name": self.model._meta.model_name,
            "model_verbose_name": self.model._meta.verbose_name_plural,
            "opts": self.model._meta,
            "has_change_permission": self.has_change_permission(request),
            "has_add_permission": self.has_add_permission(request),
            "has_delete_permission": self.has_delete_permission(request),
            "has_view_permission": self.has_view_permission(request),
        }
        return TemplateResponse(request, "admin/soundcharts/import_view.html", context)

    @csrf_exempt
    def fetch_api_data(self, request):
        """Fetch data from Soundcharts API"""
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        try:
            service = SoundchartsService()
            data = json.loads(request.body)
            limit = data.get("limit", 50)
            offset = data.get("offset", 0)

            logger.info(
                f"Fetching API data for {self.model._meta.model_name} with limit={limit}, offset={offset}"
            )

            # Determine which API method to call based on model
            if self.model == Platform:
                result = service.get_platforms(limit=limit, offset=offset)
            elif self.model == Artist:
                search_term = data.get("search_term", "")
                if not search_term:
                    # If no search term provided, use fallback data
                    result = service._get_sandbox_artists()
                else:
                    result = service.search_artists(
                        q=search_term, limit=limit, offset=offset
                    )
            elif self.model == Album:
                artist_uuid = data.get("artist_uuid")
                if not artist_uuid:
                    return JsonResponse(
                        {"error": "Artist UUID required for albums"}, status=400
                    )
                result = service.get_albums_by_artist(
                    artist_uuid, limit=limit, offset=offset
                )
            elif self.model == Track:
                artist_uuid = data.get("artist_uuid")
                result = service.get_tracks(
                    limit=limit, offset=offset, artist_uuid=artist_uuid
                )
            elif self.model == Venue:
                country_code = data.get("country_code")
                result = service.get_venues(
                    limit=limit, offset=offset, country_code=country_code
                )
            elif self.model == Chart:
                platform_code = data.get("platform_code")
                result = service.get_charts(
                    platform_code=platform_code, offset=offset, limit=limit
                )
            elif self.model == Genre:
                result = service.get_genres(limit=limit, offset=offset)
            else:
                return JsonResponse(
                    {"error": f"API not implemented for {self.model._meta.model_name}"},
                    status=400,
                )

            if result is None:
                return JsonResponse(
                    {"error": "Failed to fetch data from API"}, status=500
                )

            logger.info(
                f"API result type: {type(result)}, length: {len(result) if isinstance(result, list) else 'N/A'}"
            )

            # Ensure result is a list for processing
            if not isinstance(result, list):
                if isinstance(result, dict):
                    # Try to extract list from dict
                    if "data" in result:
                        result = result["data"]
                    elif "results" in result:
                        result = result["results"]
                    elif "platforms" in result:
                        result = result["platforms"]
                    else:
                        # Convert single item to list
                        result = [result]
                else:
                    return JsonResponse(
                        {"error": f"Unexpected API response format: {type(result)}"},
                        status=500,
                    )

            # Check for existing records to avoid duplicates
            existing_records = self._get_existing_records(result)
            logger.info(f"Found {len(existing_records)} existing records")

            return JsonResponse(
                {
                    "data": result,
                    "existing_records": existing_records,
                    "total_count": len(result) if isinstance(result, list) else 0,
                }
            )

        except Exception as e:
            logger.error(f"Error fetching API data: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    @csrf_exempt
    def add_to_database(self, request):
        """Add a single item to the database"""
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        try:
            data = json.loads(request.body)
            item_data = data.get("item")

            if not item_data:
                return JsonResponse({"error": "No item data provided"}, status=400)

            # Check if item already exists
            if self._item_exists(item_data):
                return JsonResponse(
                    {
                        "success": True,
                        "message": f"{self.model._meta.verbose_name} already exists",
                        "id": None,
                    }
                )

            with transaction.atomic():
                instance = self._create_instance(item_data)
                return JsonResponse(
                    {
                        "success": True,
                        "message": f"{self.model._meta.verbose_name} added successfully",
                        "id": instance.id,
                    }
                )

        except json.JSONDecodeError as e:
            return JsonResponse({"error": f"Invalid JSON: {str(e)}"}, status=400)
        except Exception as e:
            logger.error(f"Error adding item to database: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    @csrf_exempt
    def add_all_to_database(self, request):
        """Add all items to the database"""
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        try:
            data = json.loads(request.body)
            items_data = data.get("items", [])

            if not items_data:
                return JsonResponse({"error": "No items data provided"}, status=400)

            added_count = 0
            errors = []

            with transaction.atomic():
                for item_data in items_data:
                    try:
                        # Check if item already exists
                        if self._item_exists(item_data):
                            continue

                        self._create_instance(item_data)
                        added_count += 1
                    except Exception as e:
                        errors.append(
                            f"Error adding {item_data.get('name', 'Unknown')}: {str(e)}"
                        )

                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Added {added_count} {self.model._meta.verbose_name_plural}",
                        "added_count": added_count,
                        "errors": errors,
                    }
                )

        except Exception as e:
            logger.error(f"Error adding all items to database: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    def _get_existing_records(self, api_data):
        """Get list of existing records to avoid duplicates"""
        if not isinstance(api_data, list):
            return []

        print("api_data: ", api_data)
        existing_records = []
        for item in api_data:
            if self.model == Chart:
                slug = item.get("slug")
                if slug and self.model.objects.filter(slug=slug).exists():
                    existing_records.append(slug)
            if self.model == Platform:
                # Platform uses slug for duplicate checking
                slug = item.get("code")
                if slug and self.model.objects.filter(slug=slug).exists():
                    existing_records.append(slug)
            else:
                # Other models use uuid for duplicate checking
                uuid = item.get("uuid")
                if uuid and self.model.objects.filter(uuid=uuid).exists():
                    existing_records.append(uuid)

        return existing_records

    def _item_exists(self, item_data):
        """Check if item already exists in database"""
        if self.model == Platform:
            # Platform uses code for duplicate checking
            slug = item_data.get("code")
            print('platform slug')
            print(slug)
            if not slug:
                return False
            return self.model.objects.filter(slug=slug).exists()
        elif self.model == Chart:
            slug = item_data.get("slug")
            if not slug:
                return False
            return self.model.objects.filter(slug=slug).exists()
        else:
            # Other models use uuid for duplicate checking
            uuid = item_data.get("uuid")
            if not uuid:
                return False
            return self.model.objects.filter(uuid=uuid).exists()

    def _create_instance(self, item_data):
        """Create a new instance from API data"""
        if self.model == Platform:
            return Platform.objects.create(
                name=item_data.get("name", ""), slug=item_data.get("code", "")
            )
        elif self.model == Artist:
            return Artist.objects.create(
                uuid=item_data.get("uuid", ""),
                name=item_data.get("name", ""),
                slug=item_data.get("slug", ""),
                appUrl=item_data.get("appUrl", ""),
                imageUrl=item_data.get("imageUrl", ""),
            )
        elif self.model == Album:
            return Album.objects.create(
                uuid=item_data.get("uuid", ""), name=item_data.get("name", "")
            )
        elif self.model == Track:
            return Track.objects.create(
                uuid=item_data.get("uuid", ""), name=item_data.get("name", "")
            )
        elif self.model == Venue:
            return Venue.objects.create(
                uuid=item_data.get("uuid", ""), name=item_data.get("name", "")
            )
        elif self.model == Chart:
            platform_code = item_data.get("platform_code", "")
            platform = Platform.objects.get(slug=platform_code)
            return Chart.objects.create(
                name=item_data.get("name", ""),
                slug=item_data.get("slug", ""),
                platform=platform,
                frequency=item_data.get("frequency", ""),
                web_url=item_data.get("webUrl", ""),
            )
        elif self.model == Genre:
            return Genre.objects.create(
                uuid=item_data.get("uuid", ""), name=item_data.get("name", "")
            )
        else:
            raise ValueError(f"Unsupported model: {self.model}")
