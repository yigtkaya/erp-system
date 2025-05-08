# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'core'

# Create a router with API version prefix
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'departments', views.DepartmentViewSet, basename='department')
router.register(r'customers', views.CustomerViewSet, basename='customer')
router.register(r'audit-logs', views.AuditLogViewSet, basename='audit-log')

# Split routes into versioned and non-versioned
urlpatterns = [
    # Versioned API endpoints 
    path('v1/', include(router.urls)),
    
    # Auth endpoints typically don't need versioning
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/permissions/', views.user_permissions, name='permissions'),
    
    # Add dashboard endpoints
    path('dashboard/overview/', views.dashboard_overview, name='dashboard-overview'),
    path('dashboard/module/<str:module>/', views.dashboard_module, name='dashboard-module'),
    path('dashboard/system-metrics/', views.system_metrics, name='system-metrics'),
    
    # API info endpoint
    path('', views.api_root, name='api-root'),
    path('health/', views.health_check, name='health-check'),
]