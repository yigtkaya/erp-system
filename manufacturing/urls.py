# manufacturing/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'manufacturing'

router = DefaultRouter()
router.register(r'work-orders', views.WorkOrderViewSet, basename='work-order')
router.register(r'work-order-operations', views.WorkOrderOperationViewSet, basename='work-order-operation')
router.register(r'material-allocations', views.MaterialAllocationViewSet, basename='material-allocation')
router.register(r'production-outputs', views.ProductionOutputViewSet, basename='production-output')
router.register(r'machine-downtimes', views.MachineDowntimeViewSet, basename='machine-downtime')
router.register(r'manufacturing-processes', views.ManufacturingProcessViewSet, basename='manufacturing-process')
router.register(r'product-workflows', views.ProductWorkflowViewSet, basename='product-workflow')
router.register(r'process-configs', views.ProcessConfigViewSet, basename='process-config')
router.register(r'fixtures', views.FixtureViewSet, basename='fixture')
router.register(r'control-gauges', views.ControlGaugeViewSet, basename='control-gauge')
router.register(r'sub-work-orders', views.SubWorkOrderViewSet, basename='sub-work-order')
router.register(r'machines', views.MachineViewSet, basename='machine')
router.register(r'utilities', views.ManufacturingUtilityViewSet, basename='utility')
router.register(r'boms', views.ProductBOMViewSet, basename='bom')

urlpatterns = [
    path('', include(router.urls)),
]