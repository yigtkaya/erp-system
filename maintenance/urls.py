# maintenance/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'maintenance'

router = DefaultRouter()
router.register(r'equipment', views.EquipmentViewSet)
router.register(r'work-orders', views.WorkOrderViewSet)
router.register(r'maintenance-tasks', views.MaintenanceTaskViewSet)
router.register(r'maintenance-logs', views.MaintenanceLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]