# quality/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'quality'

router = DefaultRouter()
router.register(r'quality-standards', views.QualityStandardViewSet)
router.register(r'inspection-templates', views.InspectionTemplateViewSet)
router.register(r'quality-inspections', views.QualityInspectionViewSet)
router.register(r'nonconformances', views.NonConformanceViewSet)
router.register(r'quality-documents', views.QualityDocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]