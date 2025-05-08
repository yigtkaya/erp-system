from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'common'

router = DefaultRouter()
router.register(r'file-versions', views.FileVersionViewSet, basename='file-version')
router.register(r'allowed-file-types', views.AllowedFileTypeViewSet, basename='allowed-file-type')

urlpatterns = [
    path('', include(router.urls)),
]