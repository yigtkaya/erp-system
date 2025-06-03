# manufacturing/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum, F, Count, Avg
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from datetime import timedelta
import uuid

# Import models
from .models import (
    WorkOrder, WorkOrderOperation, MaterialAllocation, ProductionOutput, 
    MachineDowntime, ManufacturingProcess, ProductWorkflow, ProcessConfig, 
    Fixture, ControlGauge, SubWorkOrder, Machine, ManufacturingAuditLog
)

# Import serializers
from .serializers import (
    WorkOrderSerializer, WorkOrderOperationSerializer, MaterialAllocationSerializer,
    ProductionOutputSerializer, MachineDowntimeSerializer, ManufacturingProcessSerializer,
    ProductWorkflowSerializer, ProcessConfigSerializer, FixtureSerializer, ControlGaugeSerializer,
    SubWorkOrderSerializer, MachineSerializer, MachineListSerializer, MachineDetailSerializer,
    ProductBOMSerializer
)

# Import our custom error handling and logging
from .exceptions import (
    WorkOrderException, MachineException, MaterialAllocationException, ProductionException,
    ErrorMessages, ValidationHelpers, get_standardized_error_response
)
from .logging import ManufacturingOperationLogger, log_manufacturing_operation

# Import other dependencies
from core.permissions import HasRolePermission
from inventory.models import Product, ProductBOM, ProductStock, StockTransaction, StockTransactionType
from inventory.stock_manager import StockManager


class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.select_related('product', 'primary_machine', 'sales_order').prefetch_related(
        'operations__machine', 'material_allocations__material', 'outputs__operator'
    )
    serializer_class = WorkOrderSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['status', 'priority', 'product', 'primary_machine']
    search_fields = ['work_order_number', 'product__product_code', 'product__product_name']
    ordering_fields = ['created_at', 'planned_start_date', 'priority']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Enhanced work order creation with validation and logging"""
        try:
            # Validate business rules
            work_order_data = serializer.validated_data
            
            # Check if planned dates are valid
            if work_order_data['planned_end_date'] <= work_order_data['planned_start_date']:
                raise WorkOrderException(
                    message=ErrorMessages.WORK_ORDER_INVALID_DATES,
                    code="INVALID_DATES"
                )
            
            # Check machine availability if assigned
            if work_order_data.get('primary_machine'):
                ValidationHelpers.validate_machine_availability(work_order_data['primary_machine'])
            
            # Save the work order
            work_order = serializer.save(created_by=self.request.user)
            
            # Log the action
            ManufacturingOperationLogger.log_work_order_action(
                user=self.request.user,
                work_order=work_order,
                action='CREATE',
                details={
                    'product_code': work_order.product.product_code,
                    'quantity_ordered': work_order.quantity_ordered,
                    'priority': work_order.priority
                }
            )
            
            # Create audit log entry
            ManufacturingAuditLog.log_action(
                user=self.request.user,
                action_type='WORK_ORDER_CREATE',
                message=f"Work order {work_order.work_order_number} created",
                entity_type='WorkOrder',
                entity_id=work_order.id,
                details={
                    'product_code': work_order.product.product_code,
                    'quantity_ordered': work_order.quantity_ordered
                }
            )
            
        except Exception as e:
            # Log the error
            ManufacturingOperationLogger.log_work_order_action(
                user=self.request.user,
                work_order=None,
                action='CREATE',
                success=False,
                details={'error': str(e)}
            )
            raise
    
    def perform_update(self, serializer):
        """Enhanced work order update with validation and logging"""
        work_order = self.get_object()
        original_status = work_order.status
        
        try:
            # Validate status transitions if status is changing
            new_data = serializer.validated_data
            if 'status' in new_data and new_data['status'] != original_status:
                ValidationHelpers.validate_work_order_status_transition(
                    original_status, new_data['status']
                )
            
            # Save the changes
            updated_work_order = serializer.save()
            
            # Log the action
            ManufacturingOperationLogger.log_work_order_action(
                user=self.request.user,
                work_order=updated_work_order,
                action='UPDATE',
                details={
                    'changes': {k: v for k, v in new_data.items()},
                    'original_status': original_status
                }
            )
            
            # Create audit log entry
            ManufacturingAuditLog.log_action(
                user=self.request.user,
                action_type='WORK_ORDER_UPDATE',
                message=f"Work order {updated_work_order.work_order_number} updated",
                entity_type='WorkOrder',
                entity_id=updated_work_order.id,
                details={'changes': new_data}
            )
            
        except Exception as e:
            ManufacturingOperationLogger.log_work_order_action(
                user=self.request.user,
                work_order=work_order,
                action='UPDATE',
                success=False,
                details={'error': str(e)}
            )
            raise
    
    @action(detail=True, methods=['post'])
    @log_manufacturing_operation('WORK_ORDER_START', 'WorkOrder')
    def start_production(self, request, pk=None):
        """Enhanced start production with comprehensive validation"""
        work_order = self.get_object()
        
        try:
            # Validate current status
            if work_order.status != 'RELEASED':
                raise WorkOrderException(
                    message=ErrorMessages.WORK_ORDER_CANNOT_START,
                    code="INVALID_STATUS",
                    details={'current_status': work_order.status, 'required_status': 'RELEASED'}
                )
            
            # Check if machine is assigned and available
            if not work_order.primary_machine:
                raise WorkOrderException(
                    message=ErrorMessages.WORK_ORDER_NO_MACHINE,
                    code="NO_MACHINE"
                )
            
            ValidationHelpers.validate_machine_availability(work_order.primary_machine)
            
            # Check if materials are allocated
            material_allocations = work_order.material_allocations.filter(is_allocated=False)
            if material_allocations.exists():
                raise WorkOrderException(
                    message=ErrorMessages.WORK_ORDER_NO_MATERIALS,
                    code="NO_MATERIALS",
                    details={'unallocated_materials': material_allocations.count()}
                )
            
            # Update work order status and dates
            with transaction.atomic():
                work_order.status = 'IN_PROGRESS'
                work_order.actual_start_date = timezone.now()
                work_order.save(update_fields=['status', 'actual_start_date'])
                
                # Update machine status
                work_order.primary_machine.status = 'IN_USE'
                work_order.primary_machine.save(update_fields=['status'])
            
            # Log the action
            ManufacturingOperationLogger.log_work_order_action(
                user=request.user,
                work_order=work_order,
                action='START_PRODUCTION',
                details={'machine_code': work_order.primary_machine.machine_code}
            )
            
            # Create audit log entry
            ManufacturingAuditLog.log_action(
                user=request.user,
                action_type='WORK_ORDER_START',
                message=f"Production started for work order {work_order.work_order_number}",
                entity_type='WorkOrder',
                entity_id=work_order.id
            )
            
            serializer = self.get_serializer(work_order)
            return Response({
                'success': True,
                'message': 'Production started successfully',
                'data': serializer.data
            })
            
        except Exception as e:
            ManufacturingOperationLogger.log_work_order_action(
                user=request.user,
                work_order=work_order,
                action='START_PRODUCTION',
                success=False,
                details={'error': str(e)}
            )
            
            if isinstance(e, WorkOrderException):
                return Response(
                    get_standardized_error_response(e.code, e.message, e.details),
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    get_standardized_error_response('SYSTEM_ERROR', str(e)),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
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
            
            remaining_to_allocate = to_allocate
            
            for stock in available_stock:
                if remaining_to_allocate <= 0:
                    break
                
                # Calculate how much to allocate from this stock
                allocate_from_stock = min(remaining_to_allocate, stock.quantity)
                
                # Create stock transaction for material issue
                transaction_type = StockTransactionType.objects.get(code='ISSUE')
                StockTransaction.objects.create(
                    product=allocation.material,
                    product_stock=stock,
                    transaction_type=transaction_type,
                    quantity=-allocate_from_stock,
                    unit_cost=stock.unit_cost,
                    total_cost=allocate_from_stock * stock.unit_cost,
                    reference_type='work_order',
                    reference_id=work_order.id,
                    notes=f"Material issue for work order {work_order.work_order_number}",
                    created_by=request.user
                )
                
                # Update stock quantity
                stock.quantity -= allocate_from_stock
                stock.save()
                
                # Update allocation
                allocation.allocated_quantity += allocate_from_stock
                remaining_to_allocate -= allocate_from_stock
                
            allocation.is_allocated = (allocation.allocated_quantity >= allocation.required_quantity)
            allocation.allocation_date = timezone.now()
            allocation.save()
            
            issued_materials.append(allocation)
        
        if errors:
            return Response(
                {"detail": "Some materials could not be allocated", "errors": errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = MaterialAllocationSerializer(issued_materials, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete_operation(self, request, pk=None):
        """
        Complete an operation and record production output
        """
        work_order = self.get_object()
        operation_id = request.data.get('operation_id')
        quantity_good = request.data.get('quantity_good', 0)
        quantity_scrapped = request.data.get('quantity_scrapped', 0)
        notes = request.data.get('notes', '')
        
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
        
        if operation.status == 'COMPLETED':
            return Response(
                {"detail": "Operation is already completed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Record production output
        ProductionOutput.objects.create(
            work_order=work_order,
            operation=operation,
            quantity_good=quantity_good,
            quantity_scrapped=quantity_scrapped,
            operator=request.user,
            notes=notes
        )
        
        # Update operation
        operation.quantity_completed += quantity_good
        operation.quantity_scrapped += quantity_scrapped
        operation.actual_end_date = timezone.now()
        operation.status = 'COMPLETED'
        operation.save()
        
        # Update work order quantities
        work_order.quantity_completed += quantity_good
        work_order.quantity_scrapped += quantity_scrapped
        work_order.save()
        
        serializer = self.get_serializer(work_order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def record_production(self, request, pk=None):
        """
        Record production output for a work order
        """
        work_order = self.get_object()
        quantity_good = request.data.get('quantity_good', 0)
        quantity_scrapped = request.data.get('quantity_scrapped', 0)
        batch_number = request.data.get('batch_number')
        notes = request.data.get('notes', '')
        
        if quantity_good <= 0 and quantity_scrapped <= 0:
            return Response(
                {"detail": "At least one of quantity_good or quantity_scrapped must be greater than 0"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Record production output
        production_output = ProductionOutput.objects.create(
            work_order=work_order,
            quantity_good=quantity_good,
            quantity_scrapped=quantity_scrapped,
            batch_number=batch_number,
            operator=request.user,
            notes=notes
        )
        
        # Update work order quantities
        work_order.quantity_completed += quantity_good
        work_order.quantity_scrapped += quantity_scrapped
        work_order.save()
        
        # If work order is completed, create inventory
        if work_order.quantity_completed >= work_order.quantity_ordered:
            try:
                # Create finished goods inventory
                stock_manager = StockManager()
                stock_manager.receive_stock(
                    product=work_order.product,
                    quantity=quantity_good,
                    unit_cost=0,  # Will be calculated based on BOM costs
                    supplier=None,
                    reference_type='work_order',
                    reference_id=work_order.id,
                    notes=f"Production completion for work order {work_order.work_order_number}",
                    user=request.user
                )
                
                work_order.status = 'COMPLETED'
                work_order.actual_end_date = timezone.now()
                work_order.save()
                
            except Exception as e:
                return Response(
                    {"detail": f"Error creating inventory: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = ProductionOutputSerializer(production_output)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def analyses(self, request):
        """
        Get various analyses for work orders
        """
        # Status distribution
        status_stats = {}
        for status_choice in WorkOrder.status.field.choices:
            count = WorkOrder.objects.filter(status=status_choice[0]).count()
            status_stats[status_choice[1]] = count
        
        # Priority distribution
        priority_stats = {}
        for priority_choice in WorkOrder.priority.field.choices:
            count = WorkOrder.objects.filter(priority=priority_choice[0]).count()
            priority_stats[priority_choice[1]] = count
        
        # Overdue work orders
        overdue_count = WorkOrder.objects.filter(
            planned_end_date__lt=timezone.now(),
            status__in=['DRAFT', 'PLANNED', 'RELEASED', 'IN_PROGRESS']
        ).count()
        
        # Completed this month
        from django.utils import timezone
        from datetime import datetime
        
        now = timezone.now()
        start_of_month = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
        
        completed_this_month = WorkOrder.objects.filter(
            status='COMPLETED',
            actual_end_date__gte=start_of_month
        ).count()
        
        # Production efficiency
        completed_orders = WorkOrder.objects.filter(
            status='COMPLETED',
            actual_end_date__isnull=False,
            planned_end_date__isnull=False
        )
        
        total_efficiency = 0
        efficiency_count = 0
        
        for order in completed_orders:
            planned_duration = (order.planned_end_date - order.planned_start_date).total_seconds()
            actual_duration = (order.actual_end_date - order.actual_start_date).total_seconds()
            
            if actual_duration > 0:
                efficiency = (planned_duration / actual_duration) * 100
                total_efficiency += efficiency
                efficiency_count += 1
        
        avg_efficiency = total_efficiency / efficiency_count if efficiency_count > 0 else 0
        
        return Response({
            'status_distribution': status_stats,
            'priority_distribution': priority_stats,
            'overdue_count': overdue_count,
            'completed_this_month': completed_this_month,
            'average_efficiency': round(avg_efficiency, 2)
        })


class WorkOrderOperationViewSet(viewsets.ModelViewSet):
    queryset = WorkOrderOperation.objects.all()
    serializer_class = WorkOrderOperationSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['work_order', 'status', 'machine']
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
    filterset_fields = ['machine', 'category', 'reported_by']
    search_fields = ['machine__machine_code', 'reason', 'reported_by__username']
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
        """
        Activate a product workflow, making it the active version
        """
        workflow = self.get_object()
        
        if workflow.status == 'ACTIVE':
            return Response(
                {"detail": "Workflow is already active"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set other workflows for this product to obsolete
        ProductWorkflow.objects.filter(
            product=workflow.product,
            status='ACTIVE'
        ).update(status='OBSOLETE')
        
        # Activate this workflow
        workflow.status = 'ACTIVE'
        workflow.approved_by = request.user
        workflow.approval_date = timezone.now()
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
        """
        Activate a process config, making it the active version for this sequence
        """
        config = self.get_object()
        
        if config.status == 'ACTIVE':
            return Response(
                {"detail": "Process config is already active"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set other configs for this workflow/sequence/process to obsolete
        ProcessConfig.objects.filter(
            workflow=config.workflow,
            sequence_order=config.sequence_order,
            process=config.process,
            status='ACTIVE'
        ).update(status='OBSOLETE')
        
        # Activate this config
        config.status = 'ACTIVE'
        config.save()
        
        serializer = self.get_serializer(config)
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
        """
        Update fixture status
        """
        fixture = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {"detail": "Status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in [choice[0] for choice in fixture._meta.get_field('status').choices]:
            return Response(
                {"detail": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fixture.status = new_status
        fixture.save()
        
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
        """
        Update control gauge status
        """
        gauge = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {"detail": "Status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in [choice[0] for choice in gauge._meta.get_field('status').choices]:
            return Response(
                {"detail": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        gauge.status = new_status
        gauge.save()
        
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
        """
        Update sub work order status and completion percentage
        """
        sub_work_order = self.get_object()
        new_status = request.data.get('status')
        completion_percentage = request.data.get('completion_percentage')
        
        if new_status:
            if new_status not in [choice[0] for choice in sub_work_order._meta.get_field('status').choices]:
                return Response(
                    {"detail": "Invalid status"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            sub_work_order.status = new_status
            
            if new_status == 'COMPLETED':
                sub_work_order.completion_percentage = 100
                sub_work_order.actual_end = timezone.now()
            elif new_status == 'IN_PROGRESS' and not sub_work_order.actual_start:
                sub_work_order.actual_start = timezone.now()
        
        if completion_percentage is not None:
            if 0 <= completion_percentage <= 100:
                sub_work_order.completion_percentage = completion_percentage
            else:
                return Response(
                    {"detail": "Completion percentage must be between 0 and 100"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        sub_work_order.save()
        
        serializer = self.get_serializer(sub_work_order)
        return Response(serializer.data)


class ManufacturingUtilityViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]
    
    def get_permissions(self):
        return [permission() for permission in self.permission_classes]
    
    @action(detail=False, methods=['post'], url_path='clone-bom')
    def clone_bom(self, request):
        """
        Clone BOM from one product to another
        """
        source_product_id = request.data.get('source_product_id')
        target_product_id = request.data.get('target_product_id')
        
        if not source_product_id or not target_product_id:
            return Response(
                {"detail": "Both source_product_id and target_product_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            source_product = Product.objects.get(id=source_product_id)
            target_product = Product.objects.get(id=target_product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": "One or both products not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get source BOM items
        source_bom_items = ProductBOM.objects.filter(
            parent_product=source_product,
            is_active=True
        )
        
        if not source_bom_items.exists():
            return Response(
                {"detail": "No active BOM found for source product"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Clone BOM items
        cloned_items = []
        
        with transaction.atomic():
            # Deactivate existing BOM for target product
            ProductBOM.objects.filter(
                parent_product=target_product,
                is_active=True
            ).update(is_active=False)
            
            # Create new BOM items
            for bom_item in source_bom_items:
                cloned_item = ProductBOM.objects.create(
                    parent_product=target_product,
                    child_product=bom_item.child_product,
                    quantity=bom_item.quantity,
                    unit_of_measure=bom_item.unit_of_measure,
                    scrap_factor=bom_item.scrap_factor,
                    notes=bom_item.notes,
                    created_by=request.user,
                    is_active=True
                )
                cloned_items.append(cloned_item)
        
        return Response({
            "detail": f"Successfully cloned {len(cloned_items)} BOM items",
            "cloned_items": len(cloned_items)
        })
    
    @action(detail=False, methods=['post'], url_path='create-sub-work-orders')
    def create_sub_work_orders(self, request):
        """
        Create sub work orders for a main work order based on BOM
        """
        work_order_id = request.data.get('work_order_id')
        
        if not work_order_id:
            return Response(
                {"detail": "work_order_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            work_order = WorkOrder.objects.get(id=work_order_id)
        except WorkOrder.DoesNotExist:
            return Response(
                {"detail": "Work order not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if work_order.status not in ['DRAFT', 'PLANNED']:
            return Response(
                {"detail": "Sub work orders can only be created for work orders in DRAFT or PLANNED status"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get BOM items for the product
        bom_items = ProductBOM.objects.filter(
            parent_product=work_order.product,
            is_active=True
        )
        
        if not bom_items.exists():
            return Response(
                {"detail": "No active BOM found for this product"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_sub_orders = []
        
        with transaction.atomic():
            for bom_item in bom_items:
                # Determine target category based on product type
                component_product = bom_item.child_product
                
                if component_product.product_type == 'SINGLE':
                    target_category_name = 'HAMMADDE'
                elif component_product.product_type == 'SEMI':
                    target_category_name = 'PROSES'
                elif component_product.product_type == 'MONTAGED':
                    target_category_name = 'MAMUL'
                else:
                    continue  # Skip unknown product types
                
                try:
                    from inventory.models import InventoryCategory
                    target_category = InventoryCategory.objects.get(name=target_category_name)
                except InventoryCategory.DoesNotExist:
                    continue  # Skip if category doesn't exist
                
                # Calculate required quantity
                required_quantity = int(bom_item.quantity * work_order.quantity_ordered)
                
                if required_quantity <= 0:
                    continue
                
                # Generate sub work order number
                sub_wo_number = f"{work_order.work_order_number}-{component_product.product_code}"
                
                # Check if sub work order already exists
                if SubWorkOrder.objects.filter(work_order_number=sub_wo_number).exists():
                    continue
                
                # Calculate planned dates (start 1 day before main work order, end 1 day before main work order start)
                planned_start = work_order.planned_start_date - timedelta(days=1)
                planned_end = work_order.planned_start_date - timedelta(hours=1)
                
                # Create sub work order
                sub_work_order = SubWorkOrder.objects.create(
                    parent_work_order=work_order,
                    bom_component=bom_item,
                    work_order_number=sub_wo_number,
                    quantity_ordered=required_quantity,
                    planned_start=planned_start,
                    planned_end=planned_end,
                    target_category=target_category,
                    created_by=request.user
                )
                
                created_sub_orders.append(sub_work_order)
        
        return Response({
            "detail": f"Successfully created {len(created_sub_orders)} sub work orders",
            "sub_work_orders": SubWorkOrderSerializer(created_sub_orders, many=True).data
        })
    
    @action(detail=False, methods=['get'], url_path='work-order-analysis')
    def work_order_analysis(self, request):
        """
        Get comprehensive work order analysis
        """
        # Date range parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = WorkOrder.objects.all()
        
        if start_date:
            queryset = queryset.filter(planned_start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(planned_start_date__lte=end_date)
        
        # Basic statistics
        total_orders = queryset.count()
        completed_orders = queryset.filter(status='COMPLETED').count()
        in_progress_orders = queryset.filter(status='IN_PROGRESS').count()
        overdue_orders = queryset.filter(
            planned_end_date__lt=timezone.now(),
            status__in=['DRAFT', 'PLANNED', 'RELEASED', 'IN_PROGRESS']
        ).count()
        
        # Completion rate
        completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
        
        
        # Product analysis
        product_stats = queryset.values(
            'product__product_code',
            'product__product_name'
        ).annotate(
            total_quantity_ordered=Sum('quantity_ordered'),
            total_quantity_completed=Sum('quantity_completed'),
            order_count=models.Count('id')
        ).order_by('-total_quantity_ordered')[:10]
        
        # Monthly trend
        from django.db.models import Count
        from django.db.models.functions import TruncMonth
        
        monthly_trend = queryset.annotate(
            month=TruncMonth('planned_start_date')
        ).values('month').annotate(
            order_count=Count('id'),
            completed_count=Count('id', filter=Q(status='COMPLETED'))
        ).order_by('month')
        
        # Priority distribution
        priority_distribution = queryset.values('priority').annotate(
            count=Count('id')
        ).order_by('priority')
        
        # Average lead time for completed orders
        completed_with_dates = queryset.filter(
            status='COMPLETED',
            actual_start_date__isnull=False,
            actual_end_date__isnull=False
        )
        
        total_lead_time = 0
        lead_time_count = 0
        
        for order in completed_with_dates:
            lead_time = (order.actual_end_date - order.actual_start_date).total_seconds() / 3600  # hours
            total_lead_time += lead_time
            lead_time_count += 1
        
        avg_lead_time = total_lead_time / lead_time_count if lead_time_count > 0 else 0
        
        return Response({
            'summary': {
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'in_progress_orders': in_progress_orders,
                'overdue_orders': overdue_orders,
                'completion_rate': round(completion_rate, 2),
                'avg_lead_time_hours': round(avg_lead_time, 2)
            },
            'top_products': list(product_stats),
            'monthly_trend': list(monthly_trend),
            'priority_distribution': list(priority_distribution)
        })


class MachineViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing machines in the manufacturing system
    """
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    filterset_fields = ['status', 'machine_type', 'is_active']
    search_fields = ['machine_code', 'brand', 'model', 'serial_number']
    ordering_fields = ['machine_code', 'status', 'machine_type', 'created_at']
    ordering = ['machine_code']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MachineListSerializer
        elif self.action == 'retrieve':
            return MachineDetailSerializer
        return MachineSerializer
    
    def get_queryset(self):
        queryset = Machine.objects.all()
        
        # Filter by maintenance status
        maintenance_overdue = self.request.query_params.get('maintenance_overdue', None)
        if maintenance_overdue is not None:
            if maintenance_overdue.lower() == 'true':
                queryset = queryset.filter(
                    next_maintenance_date__lt=timezone.now().date()
                )
            elif maintenance_overdue.lower() == 'false':
                queryset = queryset.filter(
                    Q(next_maintenance_date__gte=timezone.now().date()) |
                    Q(next_maintenance_date__isnull=True)
                )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update machine status
        """
        machine = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if not new_status:
            return Response(
                {"detail": "Status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in [choice[0] for choice in machine._meta.get_field('status').choices]:
            return Response(
                {"detail": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = machine.status
        machine.status = new_status
        machine.save()
        
        # Record downtime if machine is going to maintenance or broken
        if new_status in ['MAINTENANCE', 'BROKEN'] and old_status not in ['MAINTENANCE', 'BROKEN']:
            MachineDowntime.objects.create(
                machine=machine,
                start_time=timezone.now(),
                reason=f"Status changed to {machine.get_status_display()}",
                category='MAINTENANCE' if new_status == 'MAINTENANCE' else 'BREAKDOWN',
                notes=notes,
                reported_by=request.user
            )
        
        serializer = self.get_serializer(machine)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def record_maintenance(self, request, pk=None):
        """
        Record maintenance for a machine
        """
        machine = self.get_object()
        maintenance_date = request.data.get('maintenance_date')
        notes = request.data.get('notes', '')
        
        if not maintenance_date:
            return Response(
                {"detail": "Maintenance date is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from datetime import datetime
            maintenance_date = datetime.strptime(maintenance_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update machine maintenance information
        machine.last_maintenance_date = maintenance_date
        machine.maintenance_notes = notes
        machine.status = 'AVAILABLE'  # Machine is available after maintenance
        machine.save()  # This will automatically calculate next_maintenance_date
        
        # End any ongoing downtime for maintenance
        ongoing_downtime = MachineDowntime.objects.filter(
            machine=machine,
            end_time__isnull=True,
            category='MAINTENANCE'
        ).first()
        
        if ongoing_downtime:
            ongoing_downtime.end_time = timezone.now()
            ongoing_downtime.notes += f" | Maintenance completed: {notes}" if notes else " | Maintenance completed"
            ongoing_downtime.save()
        
        serializer = self.get_serializer(machine)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def maintenance_history(self, request, pk=None):
        """
        Get maintenance history for a machine
        """
        machine = self.get_object()
        
        # Get maintenance downtimes
        maintenance_downtimes = MachineDowntime.objects.filter(
            machine=machine,
            category='MAINTENANCE'
        ).order_by('-start_time')
        
        serializer = MachineDowntimeSerializer(maintenance_downtimes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def downtime_history(self, request, pk=None):
        """
        Get downtime history for a machine
        """
        machine = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        downtimes = MachineDowntime.objects.filter(machine=machine)
        
        if start_date:
            downtimes = downtimes.filter(start_time__gte=start_date)
        if end_date:
            downtimes = downtimes.filter(start_time__lte=end_date)
        
        serializer = MachineDowntimeSerializer(downtimes.order_by('-start_time'), many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get machine statistics
        """
        total_machines = Machine.objects.count()
        available_machines = Machine.objects.filter(status='AVAILABLE').count()
        in_use_machines = Machine.objects.filter(status='IN_USE').count()
        maintenance_machines = Machine.objects.filter(status='MAINTENANCE').count()
        broken_machines = Machine.objects.filter(status='BROKEN').count()
        overdue_maintenance = Machine.objects.filter(
            next_maintenance_date__lt=timezone.now().date()
        ).count()
        
        # Machine type distribution
        machine_type_stats = Machine.objects.values('machine_type').annotate(
            count=Count('id')
        ).order_by('machine_type')
        
        
        
        return Response({
            'total_machines': total_machines,
            'status_distribution': {
                'available': available_machines,
                'in_use': in_use_machines,
                'maintenance': maintenance_machines,
                'broken': broken_machines
            },
            'overdue_maintenance': overdue_maintenance,
            'machine_type_distribution': list(machine_type_stats)
        })


class ProductBOMViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Product Bill of Materials (BOM)
    """
    queryset = ProductBOM.objects.select_related('parent_product', 'child_product').all()
    serializer_class = ProductBOMSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['parent_product', 'child_product', 'parent_product__product_type', 'child_product__product_type']
    search_fields = [
        'parent_product__stock_code', 'parent_product__product_name',
        'child_product__stock_code', 'child_product__product_name'
    ]
    ordering_fields = ['operation_sequence', 'quantity', 'created_at']
    ordering = ['parent_product__stock_code', 'operation_sequence']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by parent product if specified
        parent_product_id = self.request.query_params.get('parent_product_id', None)
        if parent_product_id:
            queryset = queryset.filter(parent_product_id=parent_product_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """
        Get BOM dashboard statistics
        """
        total_boms = ProductBOM.objects.count()
        
        # Products with BOMs
        products_with_boms = ProductBOM.objects.values('parent_product').distinct().count()
        
        # BOM complexity (average components per product)
        bom_complexity = ProductBOM.objects.values('parent_product').annotate(
            component_count=Count('child_product')
        ).aggregate(
            avg_components=Avg('component_count')
        )['avg_components'] or 0
        
        # Most complex products (top 5)
        complex_products = ProductBOM.objects.values(
            'parent_product__stock_code',
            'parent_product__product_name'
        ).annotate(
            component_count=Count('child_product')
        ).order_by('-component_count')[:5]
        
        # Component usage (most used components)
        popular_components = ProductBOM.objects.values(
            'child_product__stock_code',
            'child_product__product_name',
            'child_product__product_type'
        ).annotate(
            usage_count=Count('parent_product')
        ).order_by('-usage_count')[:10]
        
        # Product type distribution in BOMs
        product_type_distribution = ProductBOM.objects.values(
            'parent_product__product_type'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Material requirements summary
        material_summary = ProductBOM.objects.values(
            'child_product__product_type'
        ).annotate(
            total_items=Count('id'),
            total_quantity=Sum('quantity')
        ).order_by('-total_items')
        
        return Response({
            'summary': {
                'total_boms': total_boms,
                'products_with_boms': products_with_boms,
                'avg_components_per_product': round(bom_complexity, 2)
            },
            'complex_products': list(complex_products),
            'popular_components': list(popular_components),
            'product_type_distribution': list(product_type_distribution),
            'material_summary': list(material_summary)
        })
    
    @action(detail=False, methods=['get'])
    def test_action(self, request):
        """
        Simple test action to verify action registration works
        """
        return Response({'message': 'BOM actions are working correctly', 'total_boms': ProductBOM.objects.count()})
    
    @action(detail=False, methods=['get'], url_path='by-product/(?P<product_id>[^/.]+)')
    def by_product(self, request, product_id=None):
        """
        Get BOM for a specific product
        """
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        bom_items = ProductBOM.objects.filter(parent_product=product).order_by('operation_sequence', 'child_product__stock_code')
        serializer = self.get_serializer(bom_items, many=True)
        
        # Calculate total material requirements
        total_components = bom_items.count()
        total_quantity = bom_items.aggregate(total=Sum('quantity'))['total'] or 0
        
        return Response({
            'product': {
                'id': product.id,
                'product_code': product.stock_code,
                'product_name': product.product_name,
                'product_type': product.product_type
            },
            'bom_items': serializer.data,
            'summary': {
                'total_components': total_components,
                'total_quantity': total_quantity
            }
        })
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Bulk create BOM items
        """
        bom_items_data = request.data.get('bom_items', [])
        
        if not bom_items_data:
            return Response(
                {'error': 'No BOM items provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_items = []
        errors = []
        
        with transaction.atomic():
            for item_data in bom_items_data:
                serializer = self.get_serializer(data=item_data)
                if serializer.is_valid():
                    bom_item = serializer.save(created_by=request.user)
                    created_items.append(bom_item)
                else:
                    errors.append(serializer.errors)
        
        if errors:
            return Response(
                {'errors': errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': f'Successfully created {len(created_items)} BOM items',
            'created_items': self.get_serializer(created_items, many=True).data
        })
    
    @action(detail=False, methods=['post'])
    def copy_bom(self, request):
        """
        Copy BOM from one product to another
        """
        source_product_id = request.data.get('source_product_id')
        target_product_id = request.data.get('target_product_id')
        
        if not source_product_id or not target_product_id:
            return Response(
                {'error': 'Both source_product_id and target_product_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            source_product = Product.objects.get(id=source_product_id)
            target_product = Product.objects.get(id=target_product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'One or both products not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get source BOM items
        source_bom_items = ProductBOM.objects.filter(parent_product=source_product)
        
        if not source_bom_items.exists():
            return Response(
                {'error': 'No BOM found for source product'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Copy BOM items
        copied_items = []
        
        with transaction.atomic():
            # Remove existing BOM for target product
            ProductBOM.objects.filter(parent_product=target_product).delete()
            
            # Create new BOM items
            for bom_item in source_bom_items:
                copied_item = ProductBOM.objects.create(
                    parent_product=target_product,
                    child_product=bom_item.child_product,
                    quantity=bom_item.quantity,
                    scrap_percentage=bom_item.scrap_percentage,
                    operation_sequence=bom_item.operation_sequence,
                    notes=bom_item.notes,
                    created_by=request.user
                )
                copied_items.append(copied_item)
        
        return Response({
            'message': f'Successfully copied {len(copied_items)} BOM items',
            'copied_items': self.get_serializer(copied_items, many=True).data
        })