from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from erp_core.throttling import CustomScopedRateThrottle

from .models import (
    WorkOrder, BOM, Machine, ManufacturingProcess,
    SubWorkOrder, BOMComponent, WorkOrderOutput
)
from .serializers import (
    WorkOrderSerializer, BOMSerializer, MachineSerializer,
    ManufacturingProcessSerializer, SubWorkOrderSerializer,
    BOMComponentSerializer, WorkOrderOutputSerializer
)

class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.select_related('bom', 'sales_order_item')
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
    queryset = BOM.objects.filter(is_active=True).prefetch_related('components')
    serializer_class = BOMSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['product', 'version']
    search_fields = ['product__product_code']

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

class MachineViewSet(viewsets.ModelViewSet):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['machine_type', 'status']
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

class BOMComponentViewSet(viewsets.ModelViewSet):
    serializer_class = BOMComponentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        bom_id = self.kwargs.get('bom_pk')
        return BOMComponent.objects.filter(bom__id=bom_id).select_related(
            'process_config__process'
        )

class ManufacturingProcessViewSet(viewsets.ModelViewSet):
    queryset = ManufacturingProcess.objects.all()
    serializer_class = ManufacturingProcessSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['machine_type']
    search_fields = ['process_code', 'process_name']

class SubWorkOrderViewSet(viewsets.ModelViewSet):
    queryset = SubWorkOrder.objects.select_related('parent_work_order', 'bom_component')
    serializer_class = SubWorkOrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'parent_work_order']

class WorkOrderOutputViewSet(viewsets.ModelViewSet):
    queryset = WorkOrderOutput.objects.select_related('sub_work_order')
    serializer_class = WorkOrderOutputSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'target_category']
