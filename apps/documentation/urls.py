from django.urls import path, re_path
from . import views

app_name = 'documentation'

urlpatterns = [
    path('', views.docs_view, name='docs'),
    path('rebuild/', views.rebuild_docs, name='rebuild_docs'),
    re_path(r'^(?P<path>.*)$', views.docs_static, name='docs_static'),
]
