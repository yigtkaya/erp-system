# erp_core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from core.views import UserRegistrationView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication
    path('api/auth/register/', UserRegistrationView.as_view(), name='register'),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API routes
    path('api/v1/', include('core.urls')),
    path('api/v1/files/', include('common.urls')),
    path('api/v1/inventory/', include('inventory.urls')),
    path('api/v1/manufacturing/', include('manufacturing.urls')),
    path('api/v1/sales/', include('sales.urls')),
    path('api/v1/purchasing/', include('purchasing.urls')),
    path('api/v1/quality/', include('quality.urls')),
    path('api/v1/maintenance/', include('maintenance.urls')),
]

# Add media files serving for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)