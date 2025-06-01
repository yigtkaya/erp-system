# manufacturing/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum
from django.utils import timezone
from .models import (
    ProductionLine, WorkCenter, WorkOrder, WorkOrderOperation,
    MaterialAllocation, ProductionOutput, MachineDowntime, ManufacturingProcess,
    ProductWorkflow, ProcessConfig, Fixture, ControlGauge, SubWorkOrder, Machine
)
from .serializers import (
    ProductionLineSerializer, WorkCenterSerializer, WorkOrderSerializer,
    WorkOrderOperationSerializer, MaterialAllocationSerializer,
    ProductionOutputSerializer, MachineDowntimeSerializer, ManufacturingProcessSerializer,
    ProductWorkflowSerializer, ProcessConfigSerializer, FixtureSerializer, ControlGaugeSerializer,
    SubWorkOrderSerializer, MachineSerializer, MachineListSerializer,
    MachineDetailSerializer
)
from core.permissions import HasRolePermission
from django.db import models, transaction
from django.db.models import F, Case, When, Value, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from inventory.models import Product, ProductBOM, ProductStock, StockTransaction, StockTransactionType
from inventory.stock_manager import StockManager
from datetime import timedelta
import uuid


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
        """
        Allocate materials for a work order based on the product's BOM
        """
        work_order = self.get_object()
        
        if work_order.status not in ['DRAFT', 'PLANNED']:
            return Response(
                {"detail": "Materials can only be allocated for work orders in DRAFT or PLANNED status"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find the active BOM items for the product
        bom_items = ProductBOM.objects.filter(
            parent_product=work_order.product,
            is_active=True
        )
        
        if not bom_items.exists():
            return Response(
                {"detail": "No active BOM found for this product"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create material allocations
        created_allocations = []
        
        for bom_item in bom_items:
            # Calculate required quantity based on work order quantity
            required_quantity = bom_item.quantity * work_order.quantity_ordered
            
            # Create or update material allocation
            allocation, created = MaterialAllocation.objects.update_or_create(
                work_order=work_order,
                material=bom_item.child_product,
                defaults={
                    'required_quantity': required_quantity,
                    'created_by': request.user
                }
            )
            
            created_allocations.append(allocation)
        
        serializer = MaterialAllocationSerializer(created_allocations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def issue_materials(self, request, pk=None):
        """
        Issue materials for a work order, reducing inventory
        """
        work_order = self.get_object()
        
        if work_order.status not in ['PLANNED', 'RELEASED', 'IN_PROGRESS']:
            return Response(
                {"detail": "Materials can only be issued for work orders in PLANNED, RELEASED or IN_PROGRESS status"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get material allocations
        allocations = MaterialAllocation.objects.filter(work_order=work_order)
        
        if not allocations.exists():
            return Response(
                {"detail": "No material allocations found for this work order"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        issued_materials = []
        errors = []
        
        for allocation in allocations:
            to_allocate = allocation.required_quantity - allocation.allocated_quantity
            
            if to_allocate <= 0:
                continue  # Skip already allocated materials
                
            # Find available stock
            available_stock = ProductStock.objects.filter(
                product=allocation.material,
                quantity__gt=0
            ).order_by('receipt_date')  # FIFO
            
            if not available_stock.exists():
                errors.append(f"No stock available for {allocation.material.product_code}")
                continue
                
            # Allocate from available stock locations
            allocated_qty = 0
            references = []
            
            for stock in available_stock:
                qty_from_this_stock = min(stock.quantity, to_allocate - allocated_qty)
                
                if qty_from_this_stock <= 0:
                    continue
                    
                # Create stock transaction
                transaction = StockTransaction.objects.create(
                    product=allocation.material,
                    transaction_type=StockTransactionType.PRODUCTION_ISSUE,
                    quantity=-qty_from_this_stock,  # Negative for issue
                    category=stock.category,
                    location=stock.location,
                    batch_number=stock.batch_number,
                    reference=f"WO:{work_order.work_order_number}",
                    work_order=work_order,
                    created_by=request.user
                )
                
                # Update stock
                stock.quantity -= qty_from_this_stock
                stock.save()
                
                # Track allocation reference
                references.append(f"{stock.category.name}:{qty_from_this_stock}")
                
                # Update allocated amount
                allocated_qty += qty_from_this_stock
                
                if allocated_qty >= to_allocate:
                    break
            
            # Update allocation record
            if allocated_qty > 0:
                allocation.allocated_quantity += allocated_qty
                allocation.is_allocated = allocation.allocated_quantity >= allocation.required_quantity
                allocation.allocation_date = timezone.now()
                allocation.save()
                
                issued_materials.append({
                    'material': allocation.material.product_code,
                    'allocated': allocated_qty,
                    'from': ', '.join(references)
                })
        
        # Update work order status if all materials allocated
        all_allocated = all(a.is_allocated for a in allocations)
        
        if all_allocated and work_order.status == 'PLANNED':
            work_order.status = 'RELEASED'
            work_order.save()
        
        return Response({
            'issued_materials': issued_materials,
            'errors': errors,
            'all_allocated': all_allocated
        })
    
    @action(detail=True, methods=['post'])
    def complete_operation(self, request, pk=None):
        """
        Complete an operation for a work order
        """
        work_order = self.get_object()
        operation_id = request.data.get('operation_id')
        
        if not operation_id:
            return Response(
                {"detail": "Operation ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            operation = WorkOrderOperation.objects.get(id=operation_id, work_order=work_order)
        except WorkOrderOperation.DoesNotExist:
            return Response(
                {"detail": "Operation not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update operation status
        operation.status = 'COMPLETED'
        operation.actual_end_date = timezone.now()
        operation.save()
        
        # Check if all operations are completed
        remaining_operations = WorkOrderOperation.objects.filter(
            work_order=work_order
        ).exclude(status='COMPLETED').count()
        
        if remaining_operations == 0 and work_order.status == 'IN_PROGRESS':
            work_order.status = 'COMPLETED'
            work_order.actual_end_date = timezone.now()
            work_order.save()
        
        return Response({
            'detail': f"Operation {operation.operation_name} marked as completed",
            'all_completed': remaining_operations == 0
        })
    
    @action(detail=True, methods=['post'])
    def record_production(self, request, pk=None):
        """
        Record production output for a work order
        """
        work_order = self.get_object()
        
        if work_order.status not in ['IN_PROGRESS', 'COMPLETED']:
            return Response(
                {"detail": "Production can only be recorded for work orders in IN_PROGRESS or COMPLETED status"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get required data from request
        quantity_good = request.data.get('quantity_good', 0)
        quantity_scrapped = request.data.get('quantity_scrapped', 0)
        operation_id = request.data.get('operation_id')
        batch_number = request.data.get('batch_number', f"WO-{work_order.work_order_number}")
        target_category_id = request.data.get('target_category')
        
        if operation_id:
            try:
                operation = WorkOrderOperation.objects.get(id=operation_id, work_order=work_order)
            except WorkOrderOperation.DoesNotExist:
                return Response(
                    {"detail": "Operation not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            operation = None
        
        if not target_category_id:
            return Response(
                {"detail": "Target inventory category is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from inventory.models import InventoryCategory
            target_category = InventoryCategory.objects.get(id=target_category_id)
        except InventoryCategory.DoesNotExist:
            return Response(
                {"detail": "Target category not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Record production output
        output = ProductionOutput.objects.create(
            work_order=work_order,
            operation=operation,
            quantity_good=quantity_good,
            quantity_scrapped=quantity_scrapped,
            output_date=timezone.now(),
            operator=request.user,
            batch_number=batch_number,
            notes=request.data.get('notes')
        )
        
        # Update work order quantities
        work_order.quantity_completed += quantity_good
        work_order.quantity_scrapped += quantity_scrapped
        work_order.save()
        
        # If there's good quantity, create inventory transaction
        if quantity_good > 0:
            # Create or update product stock
            stock, created = ProductStock.objects.get_or_create(
                product=work_order.product,
                category=target_category,
                batch_number=batch_number,
                defaults={
                    'quantity': 0,
                    'receipt_date': timezone.now().date()
                }
            )
            
            stock.quantity += quantity_good
            stock.save()
            
            # Create stock transaction
            StockTransaction.objects.create(
                product=work_order.product,
                transaction_type=StockTransactionType.PRODUCTION_RECEIPT,
                quantity=quantity_good,
                category=target_category,
                batch_number=batch_number,
                reference=f"WO:{work_order.work_order_number}",
                work_order=work_order,
                created_by=request.user
            )
        
        serializer = ProductionOutputSerializer(output)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def analyses(self, request):
        """
        Get work order analyses like efficiency, completion rate, etc.
        Implements functionality similar to vw_work_order_summary view
        """
        # Define the date range
        end_date = timezone.now().date()
        start_date = request.query_params.get('start_date')
        
        if start_date:
            start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            # Default to last 30 days
            start_date = end_date - timedelta(days=30)
        
        # Get completed work orders in the date range
        completed_orders = WorkOrder.objects.filter(
            actual_end_date__range=(start_date, end_date + timedelta(days=1)),
            status='COMPLETED'
        )
        
        # Calculate efficiency and other metrics
        analyses = completed_orders.aggregate(
            total_count=Count('id'),
            on_time_count=Count(
                Case(When(actual_end_date__lte=F('planned_end_date'), then=1))
            ),
            total_ordered=Sum('quantity_ordered'),
            total_completed=Sum('quantity_completed'),
            total_scrapped=Sum('quantity_scrapped')
        )
        
        # Calculate derived metrics
        if analyses['total_count'] > 0:
            analyses['on_time_percentage'] = (analyses['on_time_count'] / analyses['total_count']) * 100
        else:
            analyses['on_time_percentage'] = 0
            
        if analyses['total_ordered']:
            analyses['completion_rate'] = (analyses['total_completed'] / analyses['total_ordered']) * 100
            analyses['scrap_rate'] = (analyses['total_scrapped'] / analyses['total_ordered']) * 100
        else:
            analyses['completion_rate'] = 0
            analyses['scrap_rate'] = 0
        
        # Get metrics by product
        by_product = completed_orders.values(
            'product__product_code', 'product__name'
        ).annotate(
            count=Count('id'),
            ordered=Sum('quantity_ordered'),
            completed=Sum('quantity_completed'),
            scrapped=Sum('quantity_scrapped'),
            on_time=Count(
                Case(When(actual_end_date__lte=F('planned_end_date'), then=1))
            )
        ).order_by('-count')
        
        # Get metrics by work center
        by_work_center = completed_orders.values(
            'work_center__code', 'work_center__name'
        ).annotate(
            count=Count('id'),
            ordered=Sum('quantity_ordered'),
            completed=Sum('quantity_completed'),
            scrapped=Sum('quantity_scrapped'),
            on_time=Count(
                Case(When(actual_end_date__lte=F('planned_end_date'), then=1))
            )
        ).order_by('-count')
        
        # Calculate average lead times
        lead_times = completed_orders.filter(
            actual_start_date__isnull=False,
            actual_end_date__isnull=False
        ).annotate(
            lead_time=ExpressionWrapper(
                F('actual_end_date') - F('actual_start_date'),
                output_field=models.DurationField()
            )
        ).aggregate(
            avg_lead_time=models.Avg('lead_time'),
            min_lead_time=models.Min('lead_time'),
            max_lead_time=models.Max('lead_time')
        )
        
        return Response({
            'summary': analyses,
            'by_product': by_product,
            'by_work_center': by_work_center,
            'lead_times': lead_times,
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            }
        })


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
    search_fields = ['work_order__work_order_number', 'batch_number']
    ordering_fields = ['output_date', 'quantity_good']
    ordering = ['-output_date']
    
    def perform_create(self, serializer):
        serializer.save(operator=self.request.user)


class MaterialAllocationViewSet(viewsets.ModelViewSet):
    queryset = MaterialAllocation.objects.all()
    serializer_class = MaterialAllocationSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['work_order', 'material', 'is_allocated']
    search_fields = ['work_order__work_order_number', 'material__product_code']
    ordering_fields = ['allocation_date']
    ordering = ['-allocation_date']


class MachineDowntimeViewSet(viewsets.ModelViewSet):
    queryset = MachineDowntime.objects.all()
    serializer_class = MachineDowntimeSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['work_center', 'category', 'reported_by']
    search_fields = ['work_center__code', 'reason', 'reported_by__username']
    ordering_fields = ['start_time', 'end_time']
    ordering = ['-start_time']
    
    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)


class ManufacturingProcessViewSet(viewsets.ModelViewSet):
    queryset = ManufacturingProcess.objects.all()
    serializer_class = ManufacturingProcessSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['machine_type']
    search_fields = ['process_code', 'name', 'description', 'machine_type']
    ordering_fields = ['process_code', 'name']
    ordering = ['process_code']


class ProductWorkflowViewSet(viewsets.ModelViewSet):
    queryset = ProductWorkflow.objects.all()
    serializer_class = ProductWorkflowSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['product', 'status', 'effective_date']
    search_fields = ['product__product_code', 'version', 'revision_notes']
    ordering_fields = ['product', 'version', 'effective_date']
    ordering = ['product', '-version']
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a workflow and make it the current version"""
        workflow = self.get_object()
        
        if workflow.status == WorkflowStatus.ACTIVE:
            return Response(
                {"detail": "Workflow is already active"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        workflow.status = WorkflowStatus.ACTIVE
        workflow.approval_date = timezone.now()
        workflow.approved_by = request.user
        workflow.save()
        
        serializer = self.get_serializer(workflow)
        return Response(serializer.data)


class ProcessConfigViewSet(viewsets.ModelViewSet):
    queryset = ProcessConfig.objects.all()
    serializer_class = ProcessConfigSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['workflow', 'process', 'status', 'tool', 'fixture', 'control_gauge']
    search_fields = ['workflow__product__product_code', 'process__name', 'workflow__version']
    ordering_fields = ['workflow', 'sequence_order', 'version']
    ordering = ['workflow', 'sequence_order', '-version']
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a process configuration"""
        process_config = self.get_object()
        
        if process_config.status == ProcessConfigStatus.ACTIVE:
            return Response(
                {"detail": "Process configuration is already active"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        process_config.status = ProcessConfigStatus.ACTIVE
        process_config.save()
        
        serializer = self.get_serializer(process_config)
        return Response(serializer.data)


class FixtureViewSet(viewsets.ModelViewSet):
    queryset = Fixture.objects.all()
    serializer_class = FixtureSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['status', 'fixture_type', 'location']
    search_fields = ['code', 'name', 'description', 'location']
    ordering_fields = ['code', 'next_check_date']
    ordering = ['code']
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update fixture status"""
        fixture = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status or new_status not in dict(FixtureStatus.choices).keys():
            return Response(
                {"detail": "Valid status required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fixture.status = new_status
        fixture.save(update_fields=['status'])
        
        serializer = self.get_serializer(fixture)
        return Response(serializer.data)


class ControlGaugeViewSet(viewsets.ModelViewSet):
    queryset = ControlGauge.objects.all()
    serializer_class = ControlGaugeSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['status', 'calibration_date', 'upcoming_calibration_date']
    search_fields = ['code', 'stock_name', 'description', 'manufacturer']
    ordering_fields = ['code', 'upcoming_calibration_date']
    ordering = ['code']
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update control gauge status"""
        gauge = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status or new_status not in dict(GaugeStatus.choices).keys():
            return Response(
                {"detail": "Valid status required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        gauge.status = new_status
        gauge.save(update_fields=['status'])
        
        serializer = self.get_serializer(gauge)
        return Response(serializer.data)


class SubWorkOrderViewSet(viewsets.ModelViewSet):
    queryset = SubWorkOrder.objects.all()
    serializer_class = SubWorkOrderSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['parent_work_order', 'status', 'target_category', 'assigned_to']
    search_fields = ['work_order_number', 'parent_work_order__work_order_number', 'notes']
    ordering_fields = ['planned_start', 'completion_percentage']
    ordering = ['planned_start']
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update sub work order status"""
        sub_wo = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status or new_status not in dict(WorkOrderStatus.choices).keys():
            return Response(
                {"detail": "Valid status required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sub_wo.status = new_status
        
        # Update actual start/end dates if moving to in-progress or completed
        if new_status == WorkOrderStatus.IN_PROGRESS and not sub_wo.actual_start:
            sub_wo.actual_start = timezone.now()
        elif new_status == WorkOrderStatus.COMPLETED and not sub_wo.actual_end:
            sub_wo.actual_end = timezone.now()
        
        sub_wo.save()
        
        serializer = self.get_serializer(sub_wo)
        return Response(serializer.data)


class ManufacturingUtilityViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    
    def get_permissions(self):
        return [permission() for permission in self.permission_classes]
    
    @action(detail=False, methods=['post'], url_path='clone-bom')
    def clone_bom(self, request):
        """
        Clone a product's BOM to create a new BOM for another product
        Similar to fn_clone_bom function in SQL
        """
        source_product_id = request.data.get('source_product_id')
        target_product_id = request.data.get('target_product_id')
        new_version = request.data.get('new_version')
        
        if not source_product_id or not target_product_id:
            return Response(
                {"detail": "Source and target product IDs are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            source_product = Product.objects.get(id=source_product_id)
            target_product = Product.objects.get(id=target_product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Source or target product not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get source BOM items
        source_bom = ProductBOM.objects.filter(
            parent_product=source_product,
            is_active=True
        )
        
        if not source_bom.exists():
            return Response(
                {"detail": "No active BOM found for source product"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine new version if not provided
        if not new_version:
            latest_version = ProductBOM.objects.filter(
                parent_product=target_product
            ).order_by('-version').values_list('version', flat=True).first()
            
            if latest_version:
                # Increment the version
                try:
                    major, minor = latest_version.split('.')
                    new_version = f"{major}.{int(minor) + 1}"
                except ValueError:
                    new_version = f"{latest_version}.1"
            else:
                new_version = "1.0"
        
        # Create new BOM items for target product
        cloned_items = []
        
        with transaction.atomic():
            for bom_item in source_bom:
                # Check if this component already exists in target BOM
                existing = ProductBOM.objects.filter(
                    parent_product=target_product,
                    child_product=bom_item.child_product,
                    version=new_version
                ).first()
                
                if existing:
                    # Update existing item
                    existing.quantity = bom_item.quantity
                    existing.unit_of_measure = bom_item.unit_of_measure
                    existing.position = bom_item.position
                    existing.notes = f"Cloned from {source_product.product_code} - {bom_item.notes or ''}"
                    existing.is_active = True
                    existing.effective_date = timezone.now().date()
                    existing.save()
                    cloned_items.append(existing)
                else:
                    # Create new BOM item
                    new_item = ProductBOM.objects.create(
                        parent_product=target_product,
                        child_product=bom_item.child_product,
                        quantity=bom_item.quantity,
                        unit_of_measure=bom_item.unit_of_measure,
                        position=bom_item.position,
                        notes=f"Cloned from {source_product.product_code} - {bom_item.notes or ''}",
                        is_active=True,
                        version=new_version,
                        effective_date=timezone.now().date(),
                        created_by=request.user
                    )
                    cloned_items.append(new_item)
        
        return Response({
            'source_product': source_product.product_code,
            'target_product': target_product.product_code,
            'version': new_version,
            'items_cloned': len(cloned_items)
        })
    
    @action(detail=False, methods=['post'], url_path='create-sub-work-orders')
    def create_sub_work_orders(self, request):
        """
        Create sub-work orders for a parent work order based on BOM
        """
        parent_work_order_id = request.data.get('parent_work_order_id')
        
        if not parent_work_order_id:
            return Response(
                {"detail": "Parent work order ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            parent_work_order = WorkOrder.objects.get(id=parent_work_order_id)
        except WorkOrder.DoesNotExist:
            return Response(
                {"detail": "Parent work order not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get product BOM
        bom_items = ProductBOM.objects.filter(
            parent_product=parent_work_order.product,
            is_active=True
        ).select_related('child_product')
        
        if not bom_items.exists():
            return Response(
                {"detail": "No active BOM found for this product"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get target category
        target_category_id = request.data.get('target_category_id')
        
        if not target_category_id:
            return Response(
                {"detail": "Target category ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from inventory.models import InventoryCategory
            target_category = InventoryCategory.objects.get(id=target_category_id)
        except InventoryCategory.DoesNotExist:
            return Response(
                {"detail": "Target category not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create sub-work orders
        sub_work_orders = []
        errors = []
        
        with transaction.atomic():
            for bom_item in bom_items:
                # Skip standard parts and raw materials (only create for semi-finished and assembled products)
                if bom_item.child_product.product_type not in ['SEMI', 'MONTAGED']:
                    continue
                
                # Calculate required quantity
                required_qty = bom_item.quantity * parent_work_order.quantity_ordered
                
                # Calculate planned dates (start 1 day before parent WO, end 2 days before)
                planned_start = parent_work_order.planned_start_date - timedelta(days=1)
                planned_end = parent_work_order.planned_end_date - timedelta(days=2)
                
                # Ensure valid dates (planned end must be after planned start)
                if planned_end <= planned_start:
                    planned_end = planned_start + timedelta(hours=8)  # 8-hour default duration
                
                # Generate work order number
                wo_number = f"SUB-{parent_work_order.work_order_number}-{len(sub_work_orders) + 1}"
                
                # Validate target category based on product type
                valid_categories = []
                product_type = bom_item.child_product.product_type
                
                if product_type == 'SINGLE':
                    valid_categories = ['HAMMADDE', 'KARANTINA', 'HURDA']
                elif product_type == 'SEMI':
                    valid_categories = ['PROSES', 'MAMUL', 'KARANTINA', 'HURDA']
                elif product_type == 'MONTAGED':
                    valid_categories = ['MAMUL', 'KARANTINA', 'HURDA']
                
                if target_category.name not in valid_categories:
                    errors.append(f"Invalid target category {target_category.name} for product type {product_type}")
                    continue
                
                # Create sub work order
                sub_wo = SubWorkOrder.objects.create(
                    parent_work_order=parent_work_order,
                    bom_component=bom_item,
                    work_order_number=wo_number,
                    quantity_ordered=required_qty,
                    quantity_completed=0,
                    quantity_scrapped=0,
                    planned_start=planned_start,
                    planned_end=planned_end,
                    status='PLANNED',
                    completion_percentage=0,
                    assigned_to=request.user,
                    target_category=target_category,
                    notes=f"Sub-work order for {parent_work_order.work_order_number}",
                    created_by=request.user
                )
                
                sub_work_orders.append(sub_wo)
        
        return Response({
            'parent_work_order': parent_work_order.work_order_number,
            'sub_work_orders_created': len(sub_work_orders),
            'errors': errors
        })
    
    @action(detail=False, methods=['get'], url_path='work-order-analysis')
    def work_order_analysis(self, request):
        """
        Get detailed work order performance analysis
        Similar to vw_work_order_analysis view in SQL
        """
        # Date range filters
        end_date = timezone.now().date()
        start_date = request.query_params.get('start_date')
        
        if start_date:
            start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            # Default to last 90 days
            start_date = end_date - timedelta(days=90)
        
        # Get completed work orders in the date range
        work_orders = WorkOrder.objects.filter(
            actual_end_date__range=(start_date, end_date + timedelta(days=1))
        ).select_related('product', 'work_center')
        
        # Apply additional filters
        product_id = request.query_params.get('product_id')
        if product_id:
            work_orders = work_orders.filter(product_id=product_id)
            
        work_center_id = request.query_params.get('work_center_id')
        if work_center_id:
            work_orders = work_orders.filter(work_center_id=work_center_id)
            
        status = request.query_params.get('status')
        if status:
            work_orders = work_orders.filter(status=status)
        
        # Calculate performance metrics
        results = work_orders.annotate(
            # Time performance
            planned_duration=ExpressionWrapper(
                F('planned_end_date') - F('planned_start_date'),
                output_field=models.DurationField()
            ),
            actual_duration=ExpressionWrapper(
                F('actual_end_date') - F('actual_start_date'),
                output_field=models.DurationField()
            ),
            duration_variance=ExpressionWrapper(
                F('actual_duration') - F('planned_duration'),
                output_field=models.DurationField()
            ),
            is_on_time=Case(
                When(actual_end_date__lte=F('planned_end_date'), then=Value(True)),
                default=Value(False),
                output_field=models.BooleanField()
            ),
            
            # Quantity performance
            quantity_variance=ExpressionWrapper(
                F('quantity_completed') - F('quantity_ordered'),
                output_field=models.IntegerField()
            ),
            completion_percentage=ExpressionWrapper(
                F('quantity_completed') * 100 / F('quantity_ordered'),
                output_field=models.DecimalField(max_digits=5, decimal_places=2)
            ),
            scrap_percentage=ExpressionWrapper(
                F('quantity_scrapped') * 100 / F('quantity_ordered'),
                output_field=models.DecimalField(max_digits=5, decimal_places=2)
            )
        ).values(
            'id', 'work_order_number', 'product__product_code', 'product__name',
            'work_center__code', 'work_center__name', 'status',
            'planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date',
            'quantity_ordered', 'quantity_completed', 'quantity_scrapped',
            'planned_duration', 'actual_duration', 'duration_variance',
            'is_on_time', 'quantity_variance', 'completion_percentage', 'scrap_percentage'
        )
        
        # Calculate summary metrics
        summary = {
            'total_work_orders': work_orders.count(),
            'on_time_count': work_orders.filter(actual_end_date__lte=F('planned_end_date')).count(),
            'delayed_count': work_orders.filter(actual_end_date__gt=F('planned_end_date')).count(),
            'completed_quantity': work_orders.aggregate(total=Sum('quantity_completed'))['total'] or 0,
            'scrapped_quantity': work_orders.aggregate(total=Sum('quantity_scrapped'))['total'] or 0,
            'ordered_quantity': work_orders.aggregate(total=Sum('quantity_ordered'))['total'] or 0,
        }
        
        if summary['total_work_orders'] > 0:
            summary['on_time_percentage'] = (summary['on_time_count'] / summary['total_work_orders']) * 100
        else:
            summary['on_time_percentage'] = 0
            
        if summary['ordered_quantity'] > 0:
            summary['completion_rate'] = (summary['completed_quantity'] / summary['ordered_quantity']) * 100
            summary['scrap_rate'] = (summary['scrapped_quantity'] / summary['ordered_quantity']) * 100
        else:
            summary['completion_rate'] = 0
            summary['scrap_rate'] = 0
        
        return Response({
            'summary': summary,
            'work_orders': results,
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            }
        })


class MachineViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing machines in the manufacturing system
    """
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    filterset_fields = ['status', 'machine_type', 'work_center']
    search_fields = ['machine_code', 'brand', 'model', 'serial_number']
    ordering_fields = ['machine_code', 'status', 'machine_type', 'created_at']
    ordering = ['machine_code']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return MachineListSerializer
        elif self.action == 'retrieve':
            return MachineDetailSerializer
        return MachineSerializer

    def get_queryset(self):
        """Custom queryset with filtering options"""
        queryset = Machine.objects.select_related('work_center', 'work_center__production_line')
        
        # Filter by maintenance status
        maintenance_due = self.request.query_params.get('maintenance_due')
        if maintenance_due == 'true':
            queryset = queryset.filter(
                next_maintenance_date__lt=timezone.now().date()
            )
        elif maintenance_due == 'false':
            queryset = queryset.exclude(
                next_maintenance_date__lt=timezone.now().date()
            )
        
        # Filter by work center
        work_center_id = self.request.query_params.get('work_center')
        if work_center_id:
            queryset = queryset.filter(work_center_id=work_center_id)
        
        return queryset

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update machine status"""
        machine = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Machine.MachineStatus.choices):
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = machine.status
        machine.status = new_status
        machine.save()
        
        return Response({
            'message': f'Machine status updated from {old_status} to {new_status}',
            'machine': MachineSerializer(machine).data
        })

    @action(detail=True, methods=['post'])
    def record_maintenance(self, request, pk=None):
        """Record maintenance performed on machine"""
        machine = self.get_object()
        maintenance_date = request.data.get('maintenance_date')
        notes = request.data.get('notes', '')
        
        if not maintenance_date:
            return Response(
                {'error': 'maintenance_date is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from datetime import datetime
            maintenance_date = datetime.strptime(maintenance_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        machine.last_maintenance_date = maintenance_date
        machine.calculate_next_maintenance()
        
        if notes:
            machine.maintenance_notes = notes
        
        machine.save()
        
        return Response({
            'message': 'Maintenance recorded successfully',
            'machine': MachineSerializer(machine).data
        })

    @action(detail=True, methods=['get'])
    def maintenance_history(self, request, pk=None):
        """Get maintenance history for this machine"""
        machine = self.get_object()
        
        # This would integrate with the maintenance module
        # For now, return basic maintenance info
        maintenance_info = {
            'machine_id': machine.id,
            'machine_code': machine.machine_code,
            'last_maintenance_date': machine.last_maintenance_date,
            'next_maintenance_date': machine.next_maintenance_date,
            'maintenance_interval': machine.maintenance_interval,
            'is_overdue': machine.is_maintenance_overdue,
            'maintenance_notes': machine.maintenance_notes
        }
        
        return Response(maintenance_info)

    @action(detail=True, methods=['get'])
    def downtime_history(self, request, pk=None):
        """Get downtime history for this machine's work center"""
        machine = self.get_object()
        
        if not machine.work_center:
            return Response({'downtime_records': []})
        
        downtime_records = MachineDowntime.objects.filter(
            work_center=machine.work_center
        ).order_by('-start_time')[:20]
        
        serializer = MachineDowntimeSerializer(downtime_records, many=True)
        return Response({'downtime_records': serializer.data})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get machine statistics"""
        from django.db.models import Count, Q
        from django.utils import timezone
        
        queryset = self.get_queryset()
        
        stats = {
            'total_machines': queryset.count(),
            'by_status': dict(queryset.values_list('status').annotate(count=Count('id'))),
            'by_type': dict(queryset.values_list('machine_type').annotate(count=Count('id'))),
            'maintenance_overdue': queryset.filter(
                next_maintenance_date__lt=timezone.now().date()
            ).count(),
            'available_machines': queryset.filter(status='AVAILABLE').count(),
            'in_use_machines': queryset.filter(status='IN_USE').count(),
        }
        
        return Response(stats)