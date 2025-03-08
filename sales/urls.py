from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views

router = DefaultRouter()
router.register(r'orders', views.SalesOrderViewSet, basename='order')

# Create nested router for order items
orders_router = routers.NestedDefaultRouter(router, r'orders', lookup='order')
orders_router.register(r'items', views.SalesOrderItemViewSet, basename='order-items')

router.register(r'shipments', views.ShippingViewSet)

app_name = 'sales'

urlpatterns = [
    path('', include(router.urls)),
    path('', include(orders_router.urls)),
    # Custom endpoints
    path('orders/by-number/<str:order_number>/', 
         views.SalesOrderByNumberView.as_view(), 
         name='order-by-number'),
    path('orders/<int:order_id>/create-shipment/', 
         views.CreateShipmentView.as_view(), 
         name='create-shipment'),
    path('shipments/<str:shipping_no>/update-status/',
         views.UpdateShipmentStatusView.as_view(),
         name='update-shipment-status'),
] 