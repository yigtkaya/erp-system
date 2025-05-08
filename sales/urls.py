# sales/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'sales'

router = DefaultRouter()
router.register(r'currencies', views.CurrencyViewSet)
router.register(r'sales-orders', views.SalesOrderViewSet)
router.register(r'sales-quotations', views.SalesQuotationViewSet)
router.register(r'customer-price-lists', views.CustomerPriceListViewSet)

urlpatterns = [
    path('', include(router.urls)),
]