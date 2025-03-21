from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'inventory'

router = DefaultRouter()
router.register(r'categories', views.InventoryCategoryViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'technical-drawings', views.TechnicalDrawingViewSet)
router.register(r'transactions', views.InventoryTransactionViewSet)
router.register(r'raw-materials', views.RawMaterialViewSet)
router.register(r'units', views.UnitOfMeasureViewSet)
router.register(r'tools', views.ToolViewSet)
router.register(r'holders', views.HolderViewSet)
router.register(r'fixtures', views.FixtureViewSet)
router.register(r'control-gauges', views.ControlGaugeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('material-types/', views.MaterialTypeChoicesAPIView.as_view(), name='material-type-choices'),
] 