from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from erp_core.throttling import CustomScopedRateThrottle
from erp_core.models import WorkOrderStatus, MachineStatus
from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import (
    WorkOrder, BOM, Machine, ManufacturingProcess,
    SubWorkOrder, BOMComponent, WorkOrderOutput,
    ProcessComponent, ProductComponent, SubWorkOrderProcess,
    BOMProcessConfig
)
from .serializers import (
    WorkOrderSerializer, BOMSerializer, MachineSerializer,
    ManufacturingProcessSerializer, SubWorkOrderSerializer,
    BOMComponentSerializer, WorkOrderOutputSerializer,
    ProcessComponentSerializer, ProductComponentSerializer,
    SubWorkOrderProcessSerializer, BOMProcessConfigSerializer,
    WorkOrderCreateUpdateSerializer, BOMCreateUpdateSerializer,
    BOMWithComponentsSerializer, ProcessComponentCreateUpdateSerializer,
    ProductComponentCreateUpdateSerializer, SubWorkOrderCreateUpdateSerializer,
    SubWorkOrderProcessCreateUpdateSerializer, WorkOrderOutputCreateUpdateSerializer,
    BOMComponentCreateSerializer
)

class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.select_related(
        'bom', 'bom__product', 'sales_order_item'
    ).prefetch_related(
        'sub_orders',
        'sub_orders__processes',
        'sub_orders__outputs'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'bom__product', 'priority']
    search_fields = ['order_number', 'notes']
    ordering_fields = ['planned_start', 'planned_end', 'priority']
    ordering = ['-planned_start']
    throttle_scope = 'manufacturing'
    throttle_classes = [CustomScopedRateThrottle]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return WorkOrderCreateUpdateSerializer
        return WorkOrderSerializer

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        work_order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in WorkOrderStatus.values:
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        work_order.status = new_status
        work_order.save()
        return Response(self.get_serializer(work_order).data)
    
    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)

class BOMViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['product', 'version', 'is_active']
    search_fields = ['product__product_code']

    def get_queryset(self):
        return BOM.objects.filter(is_active=True).select_related(
            'product'
        ).prefetch_related(
            'components__processcomponent__process_config__process',
            'components__processcomponent__raw_material',
            'components__productcomponent__product'
        )
    
    def get_serializer_class(self):
        if self.action == 'create_with_components':
            return BOMWithComponentsSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BOMCreateUpdateSerializer
        return BOMSerializer

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
    
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def create_with_components(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bom = serializer.save()
        return Response(
            BOMSerializer(bom).data,
            status=status.HTTP_201_CREATED
        )
    
    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)

class MachineViewSet(viewsets.ModelViewSet):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['machine_type', 'status', 'axis_count']
    search_fields = ['machine_code', 'brand', 'model']

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        machine = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in MachineStatus.values:
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        machine.status = new_status
        machine.save()
        return Response(self.get_serializer(machine).data)

    @action(detail=True, methods=['post'])
    def record_maintenance(self, request, pk=None):
        machine = self.get_object()
        machine.last_maintenance_date = request.data.get('maintenance_date')
        machine.maintenance_notes = request.data.get('notes')
        machine.calculate_next_maintenance()
        machine.save()
        return Response(self.get_serializer(machine).data)
    
    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)

class BOMComponentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        bom_id = self.kwargs.get('bom_pk')
        return BOMComponent.objects.filter(bom__id=bom_id).select_related(
            'bom',
            'processcomponent__process_config__process',
            'processcomponent__raw_material',
            'productcomponent__product'
        )
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BOMComponentCreateSerializer
        return BOMComponentSerializer
    
    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)

class ProcessComponentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['bom']
    
    def get_queryset(self):
        return ProcessComponent.objects.select_related(
            'bom', 'bom__product',
            'process_config', 'process_config__process',
            'raw_material'
        )
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProcessComponentCreateUpdateSerializer
        return ProcessComponentSerializer
    
    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)

class ProductComponentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['bom']
    
    def get_queryset(self):
        return ProductComponent.objects.select_related(
            'bom', 'bom__product',
            'product'
        )
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductComponentCreateUpdateSerializer
        return ProductComponentSerializer
    
    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)

class ManufacturingProcessViewSet(viewsets.ModelViewSet):
    queryset = ManufacturingProcess.objects.all()
    serializer_class = ManufacturingProcessSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['machine_type']
    search_fields = ['process_code', 'process_name']
    
    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)

class BOMProcessConfigViewSet(viewsets.ModelViewSet):
    queryset = BOMProcessConfig.objects.select_related('process')
    serializer_class = BOMProcessConfigSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['process', 'axis_count']
    
    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)

class SubWorkOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'parent_work_order']
    
    def get_queryset(self):
        return SubWorkOrder.objects.select_related(
            'parent_work_order',
            'bom_component',
            'target_category'
        ).prefetch_related(
            'processes', 
            'processes__process',
            'processes__machine',
            'outputs',
            'outputs__target_category'
        )
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SubWorkOrderCreateUpdateSerializer
        return SubWorkOrderSerializer

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        sub_work_order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in WorkOrderStatus.values:
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        sub_work_order.status = new_status
        sub_work_order.save()
        return Response(self.get_serializer(sub_work_order).data)
    
    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)

class SubWorkOrderProcessViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['sub_work_order', 'machine']

    def get_queryset(self):
        sub_work_order_pk = self.kwargs.get('sub_work_order_pk')
        queryset = SubWorkOrderProcess.objects.select_related(
            'sub_work_order', 'process', 'machine'
        )
        if sub_work_order_pk:
            queryset = queryset.filter(sub_work_order_id=sub_work_order_pk)
        return queryset
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SubWorkOrderProcessCreateUpdateSerializer
        return SubWorkOrderProcessSerializer
    
    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)

class WorkOrderOutputViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'target_category', 'inspection_required']
    
    def get_queryset(self):
        return WorkOrderOutput.objects.select_related(
            'sub_work_order', 'target_category'
        )
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return WorkOrderOutputCreateUpdateSerializer
        return WorkOrderOutputSerializer
    
    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)
