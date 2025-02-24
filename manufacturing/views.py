from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from erp_core.throttling import CustomScopedRateThrottle
from erp_core.models import WorkOrderStatus, MachineStatus

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
    SubWorkOrderProcessSerializer, BOMProcessConfigSerializer
)

class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.select_related(
        'bom', 'sales_order_item'
    ).prefetch_related('sub_orders')
    serializer_class = WorkOrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'bom__product', 'priority']
    search_fields = ['order_number', 'notes']
    ordering_fields = ['planned_start', 'planned_end', 'priority']
    ordering = ['-planned_start']
    throttle_scope = 'manufacturing'
    throttle_classes = [CustomScopedRateThrottle]

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

class BOMViewSet(viewsets.ModelViewSet):
    queryset = BOM.objects.filter(is_active=True).prefetch_related(
        'components',
        'components__process_component',
        'components__product_component'
    )
    serializer_class = BOMSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['product', 'version', 'is_active']
    search_fields = ['product__product_code']

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

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

class BOMComponentViewSet(viewsets.ModelViewSet):
    serializer_class = BOMComponentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        bom_id = self.kwargs.get('bom_pk')
        return BOMComponent.objects.filter(bom__id=bom_id).select_related(
            'process_component__process_config',
            'product_component__product'
        )

class ProcessComponentViewSet(viewsets.ModelViewSet):
    queryset = ProcessComponent.objects.select_related(
        'process_config', 'raw_material'
    )
    serializer_class = ProcessComponentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['bom']

class ProductComponentViewSet(viewsets.ModelViewSet):
    queryset = ProductComponent.objects.select_related('product')
    serializer_class = ProductComponentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['bom']

class ManufacturingProcessViewSet(viewsets.ModelViewSet):
    queryset = ManufacturingProcess.objects.all()
    serializer_class = ManufacturingProcessSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['machine_type']
    search_fields = ['process_code', 'process_name']

class BOMProcessConfigViewSet(viewsets.ModelViewSet):
    queryset = BOMProcessConfig.objects.select_related('process')
    serializer_class = BOMProcessConfigSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['process', 'axis_count']

class SubWorkOrderViewSet(viewsets.ModelViewSet):
    queryset = SubWorkOrder.objects.select_related(
        'parent_work_order',
        'bom_component',
        'target_category'
    ).prefetch_related('processes', 'outputs')
    serializer_class = SubWorkOrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'parent_work_order']

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

class SubWorkOrderProcessViewSet(viewsets.ModelViewSet):
    queryset = SubWorkOrderProcess.objects.select_related(
        'sub_work_order', 'process', 'machine'
    )
    serializer_class = SubWorkOrderProcessSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['sub_work_order', 'machine']

    def get_queryset(self):
        sub_work_order_pk = self.kwargs.get('sub_work_order_pk')
        queryset = super().get_queryset()
        if sub_work_order_pk:
            queryset = queryset.filter(sub_work_order_id=sub_work_order_pk)
        return queryset

class WorkOrderOutputViewSet(viewsets.ModelViewSet):
    queryset = WorkOrderOutput.objects.select_related(
        'sub_work_order', 'target_category'
    )
    serializer_class = WorkOrderOutputSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'target_category', 'inspection_required']
