# purchasing/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'purchasing'

router = DefaultRouter()
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'purchase-orders', views.PurchaseOrderViewSet)
router.register(r'purchase-requisitions', views.PurchaseRequisitionViewSet)
router.register(r'goods-receipts', views.GoodsReceiptViewSet)
router.register(r'supplier-price-lists', views.SupplierPriceListViewSet)

urlpatterns = [
    path('', include(router.urls)),
]