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
from rest_framework import serializers
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import (
    WorkOrder, Machine, ManufacturingProcess, ProductWorkflow,
    SubWorkOrder, WorkOrderOutput, SubWorkOrderProcess,
    WorkOrderStatusChange, ProcessConfig, WorkOrderStatusTransition
)
from .serializers import (
    WorkOrderSerializer, MachineSerializer, ManufacturingProcessSerializer,
    SubWorkOrderSerializer, WorkOrderOutputSerializer, SubWorkOrderProcessSerializer,
    WorkOrderCreateUpdateSerializer, SubWorkOrderCreateUpdateSerializer,
    SubWorkOrderProcessCreateUpdateSerializer, WorkOrderOutputCreateUpdateSerializer,
    WorkOrderStatusChangeSerializer, ProcessConfigSerializer, ProductWorkflowSerializer,
    WorkflowWithConfigsSerializer
)

class ProductWorkflowViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product', 'status']
    search_fields = ['product__product_code', 'product__product_name', 'version', 'notes']
    ordering_fields = ['version', 'effective_date', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return ProductWorkflow.objects.select_related(
            'product', 'created_by', 'approved_by'
        ).prefetch_related('process_configs')

    def get_serializer_class(self):
        if self.action == 'create_with_configs':
            return WorkflowWithConfigsSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ProductWorkflowSerializer
        return ProductWorkflowSerializer

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        workflow = self.get_object()
        try:
            workflow.activate(request.user)
            return Response({'status': 'workflow activated'})
        except DjangoValidationError as e:
            raise ValidationError(detail=str(e))

    @action(detail=True, methods=['post'])
    def create_new_version(self, request, pk=None):
        workflow = self.get_object()
        try:
            new_workflow = workflow.create_new_version()
            serializer = self.get_serializer(new_workflow)
            return Response(serializer.data)
        except Exception as e:
            raise ValidationError(detail=str(e))

    @action(detail=False, methods=['post'])
    def create_with_configs(self, request):
        """
        Create a workflow with its process configurations in a single request.
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            workflow = serializer.save(created_by=self.request.user)
            
            response_serializer = ProductWorkflowSerializer(workflow)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'detail': 'An error occurred while creating the workflow'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class ProcessConfigViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProcessConfigSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'workflow': ['exact'],
        'process': ['exact'],
        'status': ['exact'],
        'axis_count': ['exact', 'isnull'],
        'tool': ['exact', 'isnull'],
        'control_gauge': ['exact', 'isnull'],
        'fixture': ['exact', 'isnull']
    }
    search_fields = [
        'workflow__product__product_code',
        'process__process_code',
        'stock_code'
    ]
    ordering_fields = ['sequence_order', 'version', 'created_at']
    ordering = ['workflow', 'sequence_order']

    def get_queryset(self):
        return ProcessConfig.objects.select_related(
            'workflow__product',
            'process',
            'tool',
            'control_gauge',
            'fixture'
        )

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        config = self.get_object()
        try:
            config.activate()
            return Response({'status': 'configuration activated'})
        except DjangoValidationError as e:
            raise ValidationError(detail=str(e))

    @action(detail=True, methods=['post'])
    def create_new_version(self, request, pk=None):
        config = self.get_object()
        try:
            new_config = config.create_new_version()
            serializer = self.get_serializer(new_config)
            return Response(serializer.data)
        except Exception as e:
            raise ValidationError(detail=str(e))

class ManufacturingProcessViewSet(viewsets.ModelViewSet):
    queryset = ManufacturingProcess.objects.all()
    serializer_class = ManufacturingProcessSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['process_code', 'process_name']

    def handle_exception(self, exc):
        if isinstance(exc, DjangoValidationError):
            return Response(
                {'detail': str(exc)},
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
        
        if not new_status or new_status not in dict(MachineStatus.choices):
            raise ValidationError({'status': 'Invalid status value'})
            
        machine.status = new_status
        machine.save()
        
        return Response({'status': 'machine status updated'})

    @action(detail=True, methods=['post'])
    def record_maintenance(self, request, pk=None):
        machine = self.get_object()
        machine.last_maintenance_date = timezone.now().date()
        machine.calculate_next_maintenance()
        machine.save()
        
        return Response({'status': 'maintenance recorded'})

class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.select_related(
        'bom', 'bom__product', 'sales_order_item', 'assigned_to'
    ).prefetch_related(
        'sub_orders',
        'sub_orders__processes',
        'sub_orders__outputs',
        'status_changes'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'bom__product', 'priority', 'assigned_to']
    search_fields = ['order_number', 'notes']
    ordering_fields = ['planned_start', 'planned_end', 'priority', 'completion_percentage']
    ordering = ['-priority', '-planned_start']
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
        
        try:
            work_order.update_status(new_status, request.user)
            return Response(self.get_serializer(work_order).data)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def create_sub_work_orders(self, request, pk=None):
        """
        Automatically create sub work orders for all components in the BOM.
        """
        work_order = self.get_object()
        
        if work_order.sub_orders.exists():
            return Response(
                {'error': 'Sub work orders already exist for this work order'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            with transaction.atomic():
                work_order.create_sub_work_orders()
            return Response(
                {'message': 'Sub work orders created successfully'},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def status_history(self, request, pk=None):
        """
        Get the status change history for a work order.
        """
        work_order = self.get_object()
        status_changes = work_order.status_changes.all().order_by('-changed_at')
        serializer = WorkOrderStatusChangeSerializer(status_changes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """
        Assign a work order to a user.
        """
        work_order = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'User ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        from erp_core.models import User
        try:
            user = User.objects.get(pk=user_id)
            work_order.assigned_to = user
            work_order.save()
            return Response(self.get_serializer(work_order).data)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
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
    filterset_fields = ['product', 'version', 'is_active', 'is_approved']
    search_fields = ['product__product_code', 'notes']
    
    def get_queryset(self):
        return BOM.objects.select_related(
            'product',
            'approved_by'
        ).prefetch_related(
            'components',
            'components__product'
        ).all()
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BOMCreateUpdateSerializer
        elif self.action == 'create_with_components':
            return BOMWithComponentsSerializer
        return BOMSerializer

    def create(self, request, *args, **kwargs):
        print("\n=== BOM Creation Debug ===")
        print("1. Request Data:", request.data)
        print("2. Request Method:", request.method)
        print("3. Content Type:", request.content_type)
        print("4. Headers:", request.headers)
        
        serializer = self.get_serializer(data=request.data)
        try:
            print("5. Attempting validation...")
            if not serializer.is_valid():
                print("6. Validation failed!")
                print("7. Validation errors:", serializer.errors)
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            print("6. Validation successful!")
            print("7. Validated data:", serializer.validated_data)
            
            print("8. Attempting to save...")
            instance = serializer.save()
            print("9. BOM created successfully with ID:", instance.id)
            
            return Response(
                BOMSerializer(instance).data,
                status=status.HTTP_201_CREATED
            )
            
        except serializers.ValidationError as e:
            print("Error: Validation error occurred!")
            print("Details:", e.detail)
            return Response(
                {"error": str(e.detail)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print("Error: Unexpected error occurred!")
            print("Type:", type(e))
            print("Details:", str(e))
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a BOM.
        """
        bom = self.get_object()
        
        if bom.is_approved:
            return Response(
                {'error': 'BOM is already approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        bom.approve(request.user)
        return Response(self.get_serializer(bom).data)
    
    @action(detail=True, methods=['post'])
    def create_new_version(self, request, pk=None):
        """
        Create a new version of a BOM.
        """
        bom = self.get_object()
        new_version = request.data.get('version')
        
        try:
            new_bom = bom.create_new_version(new_version)
            return Response(
                self.get_serializer(new_bom).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

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

class BOMComponentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['bom']
    search_fields = ['product__product_code', 'product__product_name', 'notes']

    def get_queryset(self):
        return BOMComponent.objects.select_related(
            'bom',
            'product'
        ).all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BOMComponentCreateUpdateSerializer
        return BOMComponentSerializer
    
    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)

class SubWorkOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'parent_work_order', 'assigned_to']
    search_fields = ['notes']
    ordering_fields = ['planned_start', 'planned_end', 'completion_percentage']
    ordering = ['planned_start']

    def get_queryset(self):
        return SubWorkOrder.objects.select_related(
            'parent_work_order',
            'bom_component',
            'target_category',
            'assigned_to'
        ).prefetch_related(
            'processes',
            'outputs'
        ).all()

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
            
        try:
            sub_work_order.update_status(new_status, request.user)
            return Response(self.get_serializer(sub_work_order).data)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """
        Assign a sub work order to a user.
        """
        sub_work_order = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'User ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        from erp_core.models import User
        try:
            user = User.objects.get(pk=user_id)
            sub_work_order.assigned_to = user
            sub_work_order.save()
            return Response(self.get_serializer(sub_work_order).data)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)

class SubWorkOrderProcessViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['sub_work_order', 'process_config', 'machine', 'status', 'operator']
    search_fields = ['notes']

    def get_queryset(self):
        return SubWorkOrderProcess.objects.select_related(
            'sub_work_order',
            'process_config',
            'machine',
            'operator'
        ).all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SubWorkOrderProcessCreateUpdateSerializer
        return SubWorkOrderProcessSerializer
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update the status of a process.
        """
        process = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(SubWorkOrderProcess.PROCESS_STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            process.update_status(new_status, request.user)
            return Response(self.get_serializer(process).data)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)

class WorkOrderOutputViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status', 'target_category', 'inspection_required', 'production_date']
    search_fields = ['notes', 'quarantine_reason']

    def get_queryset(self):
        return WorkOrderOutput.objects.select_related(
            'sub_work_order', 'target_category', 'created_by'
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return WorkOrderOutputCreateUpdateSerializer
        return WorkOrderOutputSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_inspected(self, request, pk=None):
        """
        Mark a quarantined output as inspected and update its status.
        """
        output = self.get_object()
        
        if not output.inspection_required:
            return Response(
                {'error': 'This output does not require inspection'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        new_status = request.data.get('status')
        if new_status not in ['GOOD', 'REWORK', 'SCRAP']:
            return Response(
                {'error': 'Invalid status. Must be GOOD, REWORK, or SCRAP'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Update the target category based on the new status
        from inventory.models import InventoryCategory
        try:
            if new_status == 'GOOD':
                if self.bom_component.material.product_type in [ProductType.SEMI, ProductType.SINGLE]:
                    target_category = InventoryCategory.objects.get(name='PROSES')
                else:
                    target_category = InventoryCategory.objects.get(name='MAMUL')
            elif new_status == 'REWORK':
                target_category = InventoryCategory.objects.get(name='KARANTINA')
            elif new_status == 'SCRAP':
                target_category = InventoryCategory.objects.get(name='HURDA')
                
            output.status = new_status
            output.target_category = target_category
            output.inspection_required = False
            output.save()
            
            return Response(self.get_serializer(output).data)
        except (InventoryCategory.DoesNotExist, ValidationError) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)
