from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'inventory'

router = DefaultRouter()
router.register(r'categories', views.InventoryCategoryViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'transactions', views.InventoryTransactionViewSet)
router.register(r'raw-materials', views.RawMaterialViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 