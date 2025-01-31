from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MaintenanceViewSet, FaultReportViewSet

router = DefaultRouter()
router.register(r'maintenance', MaintenanceViewSet)
router.register(r'fault-reports', FaultReportViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 