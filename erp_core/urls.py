"""
URL configuration for erp_core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from erp_core.views.auth import (
    UserRegistrationView, UserListView, UserProfileView,
    CustomTokenObtainPairView, logout_view
)
from erp_core.views.home import home
from django.conf import settings
from django.conf.urls.static import static

# Swagger imports
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.throttling import AnonRateThrottle

class CustomSchemaGenerator(OpenAPISchemaGenerator):
    def get_operation_id(self, operation_keys):
        operation_id = operation_keys[-1]
        if operation_id.endswith('_create'):
            operation_id = operation_id[:-7]
        elif operation_id.endswith('_list'):
            operation_id = 'list_' + operation_id[:-5]
        return operation_id

# Swagger Schema Configuration
schema_view = get_schema_view(
    openapi.Info(
        title="ERP System API",
        default_version='v1',
        description="Manufacturing and Sales API Documentation",
    ),
    public=True,
)

class LoginThrottle(AnonRateThrottle):
    rate = '5/hour'

class CustomTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginThrottle]

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    
    # Swagger URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Authentication URLs
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # User Management URLs
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/profile/', UserProfileView.as_view(), name='profile'),
    
    # Include other app URLs
    path('api/inventory/', include('inventory.urls')),
    path('api/manufacturing/', include('manufacturing.urls')),
    path('api/sales/', include('sales.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
