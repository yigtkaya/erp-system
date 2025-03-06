from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'orders', views.SalesOrderViewSet)
router.register(r'order-items', views.SalesOrderItemViewSet)
router.register(r'shipments', views.ShippingViewSet)

app_name = 'sales'

urlpatterns = [
    path('', include(router.urls)),
    # Custom endpoints
    path('orders/<str:order_number>/create-shipment/', 
         views.CreateShipmentView.as_view(), 
         name='create-shipment'),
    path('shipments/<str:shipping_no>/update-status/',
         views.UpdateShipmentStatusView.as_view(),
         name='update-shipment-status'),
] 