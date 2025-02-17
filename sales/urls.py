from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalesOrderViewSet, SalesOrderItemViewSet, ShippingViewSet

router = DefaultRouter()
router.register(r'sales-orders', SalesOrderViewSet)
router.register(r'order-items', SalesOrderItemViewSet, basename='order-items')
router.register(r'shipments', ShippingViewSet)

app_name = 'sales'

urlpatterns = [
    path('', include(router.urls)),
    path('sales-orders/<int:salesorder_pk>/items/',
         SalesOrderItemViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='salesorder-items-list'),
    path('sales-orders/<int:salesorder_pk>/items/<int:pk>/',
         SalesOrderItemViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}),
         name='salesorder-items-detail'),
] 