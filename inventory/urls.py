# inventory/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet, RawMaterialViewSet,
    ToolViewSet, ToolUsageViewSet, HolderViewSet, FixtureViewSet, ControlGaugeViewSet
)

app_name = 'inventory'

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'raw-materials', RawMaterialViewSet)
router.register(r'tools', ToolViewSet)
router.register(r'tool-usages', ToolUsageViewSet)
router.register(r'holders', HolderViewSet)
router.register(r'fixtures', FixtureViewSet)
router.register(r'control-gauges', ControlGaugeViewSet)

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Add other URL patterns here
] 