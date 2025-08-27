from django.shortcuts import render
from rest_framework import viewsets
from apps.soundcharts.models import Platform, Artist, Album
from apps.soundcharts.serializers import PlatformSerializer, ArtistSerializer, AlbumSerializer

# Create your views here.

class PlatformViewSet(viewsets.ModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer

class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer


class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer