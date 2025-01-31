from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'sales-orders', views.SalesOrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('sales-orders/<int:salesorder_pk>/items/',
         views.SalesOrderItemViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='salesorder-items-list'),
    path('sales-orders/<int:salesorder_pk>/items/<int:pk>/',
         views.SalesOrderItemViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}),
         name='salesorder-items-detail'),
] 