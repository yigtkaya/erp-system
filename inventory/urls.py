# inventory/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, RawMaterialViewSet

app_name = 'inventory'

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'raw-materials', RawMaterialViewSet)

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Add other URL patterns here
] 