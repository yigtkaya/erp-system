# manufacturing/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum
from django.utils import timezone
from .models import (
    ProductionLine, WorkCenter, WorkOrder, WorkOrderOperation,
    MaterialAllocation, ProductionOutput, MachineDowntime
)
from .serializers import (
    ProductionLineSerializer, WorkCenterSerializer, WorkOrderSerializer,
    WorkOrderOperationSerializer, MaterialAllocationSerializer,
    ProductionOutputSerializer, MachineDowntimeSerializer
)
from core.permissions import HasRolePermission


class ProductionLineViewSet(viewsets.ModelViewSet):
    queryset = ProductionLine.objects.all()
    serializer_class = ProductionLineSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['is_active']
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name']
    ordering = ['code']


class WorkCenterViewSet(viewsets.ModelViewSet):
    queryset = WorkCenter.objects.all()
    serializer_class = WorkCenterSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['production_line', 'is_active']
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name']
    ordering = ['code']
    
    @action(detail=True, methods=['get'])
    def downtime_history(self, request, pk=None):
        work_center = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        downtimes = MachineDowntime.objects.filter(work_center=work_center)
        
        if start_date:
            downtimes = downtimes.filter(start_time__gte=start_date)
        if end_date:
            downtimes = downtimes.filter(start_time__lte=end_date)
        
        serializer = MachineDowntimeSerializer(downtimes, many=True)
        return Response(serializer.data)


class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all()
    serializer_class = WorkOrderSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['status', 'priority', 'product', 'work_center']
    search_fields = ['work_order_number', 'product__product_code', 'product__product_name']
    ordering_fields = ['created_at', 'planned_start_date', 'priority']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start_production(self, request, pk=None):
        work_order = self.get_object()
        
        if work_order.status != 'RELEASED':
            return Response(
                {'error': 'Work order must be in RELEASED status to start production'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        work_order.status = 'IN_PROGRESS'
        work_order.actual_start_date = timezone.now()
        work_order.save()
        
        serializer = self.get_serializer(work_order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete_production(self, request, pk=None):
        work_order = self.get_object()
        
        if work_order.status != 'IN_PROGRESS':
            return Response(
                {'error': 'Work order must be in IN_PROGRESS status to complete'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        work_order.status = 'COMPLETED'
        work_order.actual_end_date = timezone.now()
        work_order.save()
        
        serializer = self.get_serializer(work_order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def allocate_materials(self, request, pk=None):
        work_order = self.get_object()
        
        # Auto-allocate materials based on BOM
        from inventory.models import ProductBOM
        bom_items = ProductBOM.objects.filter(parent_product=work_order.product)
        
        for bom_item in bom_items:
            required_qty = bom_item.quantity * work_order.quantity_ordered
            
            MaterialAllocation.objects.update_or_create(
                work_order=work_order,
                material=bom_item.child_product,
                defaults={
                    'required_quantity': required_qty,
                    'allocated_quantity': min(required_qty, bom_item.child_product.available_stock),
                    'is_allocated': True,
                    'allocation_date': timezone.now()
                }
            )
        
        serializer = self.get_serializer(work_order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def record_output(self, request, pk=None):
        work_order = self.get_object()
        
        serializer = ProductionOutputSerializer(data=request.data)
        if serializer.is_valid():
            output = serializer.save(
                work_order=work_order,
                operator=request.user
            )
            
            # Update work order quantities
            work_order.quantity_completed += output.quantity_good
            work_order.quantity_scrapped += output.quantity_scrapped
            work_order.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkOrderOperationViewSet(viewsets.ModelViewSet):
    queryset = WorkOrderOperation.objects.all()
    serializer_class = WorkOrderOperationSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['work_order', 'status', 'work_center']
    ordering = ['operation_sequence']
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        operation = self.get_object()
        operation.status = 'IN_PROGRESS'
        operation.actual_start_date = timezone.now()
        operation.save()
        
        serializer = self.get_serializer(operation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        operation = self.get_object()
        operation.status = 'COMPLETED'
        operation.actual_end_date = timezone.now()
        operation.save()
        
        serializer = self.get_serializer(operation)
        return Response(serializer.data)


class ProductionOutputViewSet(viewsets.ModelViewSet):
    queryset = ProductionOutput.objects.all()
    serializer_class = ProductionOutputSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['work_order', 'operator', 'output_date']
    ordering = ['-output_date']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MachineDowntimeViewSet(viewsets.ModelViewSet):
    queryset = MachineDowntime.objects.all()
    serializer_class = MachineDowntimeSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['work_center', 'category', 'start_time']
    ordering = ['-start_time']
    
    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)