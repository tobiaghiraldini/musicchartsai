from django.contrib import admin
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from django.urls import reverse
from datetime import datetime
import logging

from ..models import Artist, Genre
from ..service import SoundchartsService
from .soundcharts_admin_mixin import SoundchartsAdminMixin

logger = logging.getLogger(__name__)


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
                level="WARNING",
            )

        # Log detailed messages
        for message in messages:
            logger.info(f"Artist metadata fetch: {message}")

    fetch_artist_metadata.short_description = "Fetch metadata from Soundcharts API"

    def response_change(self, request, obj):
        """Handle custom actions in change form"""
        if "_fetch_metadata" in request.POST:
            # Handle single artist metadata fetch
            if obj.uuid:
                service = SoundchartsService()
                try:
                    metadata = service.get_artist_metadata(obj.uuid)
                    if metadata:
                        # Update the artist object with metadata
                        if "object" in metadata:
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
                                                artist_data["birthDate"].replace(
                                                    "Z", "+00:00"
                                                )
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
                                    # Leave birthDate as None if parsing fails
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
                                            "uuid": f"genre-{genre_name.lower().replace(' ', '-')}"
                                        },
                                    )
                                    obj.genres.add(genre)

                                    if created:
                                        logger.info(f"Created new genre: {genre_name}")
                                    else:
                                        logger.info(
                                            f"Found existing genre: {genre_name}"
                                        )
                            # Save the updated object
                            obj.save()

                            self.message_user(
                                request,
                                f"Successfully fetched and updated metadata for '{obj.name}'",
                            )
                            logger.info(
                                f"Updated artist {obj.name} with metadata: {metadata}"
                            )
                        else:
                            self.message_user(
                                request,
                                f"Invalid metadata format for '{obj.name}'",
                                level="WARNING",
                            )
                    else:
                        self.message_user(
                            request,
                            f"Failed to fetch metadata for '{obj.name}'",
                            level="WARNING",
                        )
                except Exception as e:
                    self.message_user(
                        request,
                        f"Error fetching metadata for '{obj.name}': {str(e)}",
                        level="ERROR",
                    )
                    logger.error(f"Error fetching metadata for artist {obj.name}: {e}")
            else:
                self.message_user(
                    request, f"Artist '{obj.name}' has no UUID", level="WARNING"
                )

            # Redirect back to the change form without triggering form validation
            return HttpResponseRedirect(request.get_full_path())

        # Only call super() if it's not our custom action
        return super().response_change(request, obj)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Override change view to handle custom actions"""
        if request.method == "POST" and "_fetch_metadata" in request.POST:
            # Handle metadata fetch action
            try:
                obj = self.get_object(request, object_id)
                if obj and obj.uuid:
                    service = SoundchartsService()
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
                                            artist_data["birthDate"].replace(
                                                "Z", "+00:00"
                                            )
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
                                # Leave birthDate as None if parsing fails
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
                                        "uuid": f"genre-{genre_name.lower().replace(' ', '-')}"
                                    },
                                )
                                obj.genres.add(genre)

                                if created:
                                    logger.info(f"Created new genre: {genre_name}")
                                else:
                                    logger.info(f"Found existing genre: {genre_name}")

                        # Save the updated object
                        obj.save()

                        self.message_user(
                            request,
                            f"Successfully fetched and updated metadata for '{obj.name}'",
                        )
                        logger.info(
                            f"Updated artist {obj.name} with metadata: {metadata}"
                        )
                    else:
                        self.message_user(
                            request,
                            f"Failed to fetch metadata for '{obj.name}'",
                            level="WARNING",
                        )
                else:
                    self.message_user(request, f"Artist has no UUID", level="WARNING")
            except Exception as e:
                self.message_user(
                    request, f"Error fetching metadata: {str(e)}", level="ERROR"
                )
                logger.error(f"Error fetching metadata: {e}")

            # Redirect back to the change form
            return HttpResponseRedirect(request.get_full_path())

        # Call the parent method for normal form handling
        return super().change_view(request, object_id, form_url, extra_context)
