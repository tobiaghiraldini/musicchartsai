from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("starter/", views.starter, name="starter"),
    path("charts/", views.charts_list, name="charts_list"),
    path("charts/<int:chart_id>/rankings/", views.chart_rankings, name="chart_rankings"),
    path("rankings/<int:ranking_id>/songs/", views.ranking_songs, name="ranking_songs"),
]
