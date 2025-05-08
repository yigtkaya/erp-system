# inventory/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'inventory'

router = DefaultRouter()
# Register your viewsets here
# Example: router.register(r'products', views.ProductViewSet)

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Add other URL patterns here
] 