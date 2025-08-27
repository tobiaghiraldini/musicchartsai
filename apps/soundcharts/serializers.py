from rest_framework import serializers
from apps.soundcharts.models import Artist, Platform, Album, Radio


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = "__all__"


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = "__all__"


class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = "__all__"


class RadioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Radio
        fields = "__all__"
