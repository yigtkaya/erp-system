# manufacturing/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'manufacturing'

router = DefaultRouter()
router.register(r'production-lines', views.ProductionLineViewSet)
router.register(r'work-centers', views.WorkCenterViewSet)
router.register(r'work-orders', views.WorkOrderViewSet)
router.register(r'work-order-operations', views.WorkOrderOperationViewSet)
router.register(r'production-outputs', views.ProductionOutputViewSet)
router.register(r'machine-downtimes', views.MachineDowntimeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]