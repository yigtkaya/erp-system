from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'manufacturing'

router = DefaultRouter()
router.register(r'work-orders', views.WorkOrderViewSet, basename='work-order')
router.register(r'boms', views.BOMViewSet, basename='bom')
router.register(r'machines', views.MachineViewSet, basename='machine')
router.register(r'manufacturing-processes', views.ManufacturingProcessViewSet, basename='manufacturing-process')
router.register(r'process-configs', views.BOMProcessConfigViewSet, basename='process-config')
router.register(r'sub-work-orders', views.SubWorkOrderViewSet, basename='sub-work-order')
router.register(r'sub-work-order-processes', views.SubWorkOrderProcessViewSet, basename='sub-work-order-process')
router.register(r'work-order-outputs', views.WorkOrderOutputViewSet, basename='work-order-output')
router.register(r'process-components', views.ProcessComponentViewSet, basename='process-component')
router.register(r'product-components', views.ProductComponentViewSet, basename='product-component')

urlpatterns = [
    path('', include(router.urls)),
    
    # Nested BOM components routes
    path('boms/<int:bom_pk>/components/',
         views.BOMComponentViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='bom-components-list'),
    path('boms/<int:bom_pk>/components/<int:pk>/',
         views.BOMComponentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}),
         name='bom-components-detail'),
         
    # Nested SubWorkOrder processes routes
    path('sub-work-orders/<int:sub_work_order_pk>/processes/',
         views.SubWorkOrderProcessViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='sub-work-order-processes-list'),
    path('sub-work-orders/<int:sub_work_order_pk>/processes/<int:pk>/',
         views.SubWorkOrderProcessViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}),
         name='sub-work-order-processes-detail'),
] 