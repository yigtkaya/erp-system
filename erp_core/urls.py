from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from core.views import (
    UserRegistrationView, health_check, api_root, 
    logout_view, user_permissions, dashboard_overview,
    system_metrics
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Monitoring
    path('', include('django_prometheus.urls')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Health checks
    path('health/', health_check, name='health-check'),
    path('api/', api_root, name='api-root'),
    path('api/metrics/', system_metrics, name='system-metrics'),
    
    # Authentication
    path('api/auth/register/', UserRegistrationView.as_view(), name='register'),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/auth/logout/', logout_view, name='logout'),
    path('api/auth/permissions/', user_permissions, name='permissions'),
    
    # Dashboard
    path('api/dashboard/', dashboard_overview, name='dashboard-overview'),
    
    # API routes
    path('api/', include('core.urls')),
    path('api/files/', include('common.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/manufacturing/', include('manufacturing.urls')),
    path('api/sales/', include('sales.urls')),
    path('api/purchasing/', include('purchasing.urls')),
    path('api/quality/', include('quality.urls')),
    path('api/maintenance/', include('maintenance.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)