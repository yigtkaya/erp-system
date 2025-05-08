# maintenance/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import (
    Equipment, MaintenancePlan, WorkOrder, MaintenanceTask,
    SparePart, MaintenancePartUsage, MaintenanceLog
)
from .serializers import (
    EquipmentSerializer, MaintenancePlanSerializer, WorkOrderSerializer,
    MaintenanceTaskSerializer, SparePartSerializer,
    MaintenancePartUsageSerializer, MaintenanceLogSerializer
)
from core.permissions import HasRolePermission


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['work_center', 'is_active']
    search_fields = ['code', 'name', 'serial_number']
    ordering = ['code']
    
    @action(detail=True, methods=['get'])
    def maintenance_history(self, request, pk=None):
        equipment = self.get_object()
        work_orders = WorkOrder.objects.filter(equipment=equipment)
        logs = MaintenanceLog.objects.filter(equipment=equipment)
        
        return Response({
            'work_orders': WorkOrderSerializer(work_orders, many=True).data,
            'logs': MaintenanceLogSerializer(logs, many=True).data
        })


class MaintenancePlanViewSet(viewsets.ModelViewSet):
    queryset = MaintenancePlan.objects.all()
    serializer_class = MaintenancePlanSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['equipment', 'maintenance_type', 'is_active']
    search_fields = ['plan_name', 'equipment__name']
    ordering = ['equipment', 'plan_name']
    
    @action(detail=False, methods=['get'])
    def due_plans(self, request):
        """Get maintenance plans that are due"""
        today = timezone.now().date()
        due_plans = MaintenancePlan.objects.filter(
            is_active=True,
            next_due_date__lte=today
        )
        
        serializer = self.get_serializer(due_plans, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def create_work_order(self, request, pk=None):
        plan = self.get_object()
        
        work_order = WorkOrder.objects.create(
            equipment=plan.equipment,
            maintenance_plan=plan,
            maintenance_type=plan.maintenance_type,
            priority='MEDIUM',
            status='SCHEDULED',
            description=f"Scheduled maintenance: {plan.plan_name}",
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=float(plan.estimated_duration_hours)),
            assigned_to=request.user,
            reported_by=request.user,
            estimated_hours=plan.estimated_duration_hours,
            created_by=request.user
        )
        
        # Create tasks from plan instructions
        MaintenanceTask.objects.create(
            work_order=work_order,
            task_name=plan.plan_name,
            description=plan.instructions,
            sequence_number=1,
            estimated_hours=plan.estimated_duration_hours
        )
        
        # Update next due date
        plan.next_due_date = plan.next_due_date + timedelta(days=plan.frequency_days)
        plan.save()
        
        serializer = WorkOrderSerializer(work_order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all()
    serializer_class = WorkOrderSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['equipment', 'maintenance_type', 'priority', 'status']
    search_fields = ['work_order_number', 'equipment__name', 'description']
    ordering = ['-scheduled_start']
    
    def perform_create(self, serializer):
        serializer.save(
            reported_by=self.request.user,
            created_by=self.request.user
        )
    
# maintenance/views.py (continued)
   @action(detail=True, methods=['post'])
   def start(self, request, pk=None):
       work_order = self.get_object()
       
       if work_order.status not in ['SCHEDULED', 'IN_PROGRESS']:
           return Response(
               {'error': 'Work order must be scheduled to start'},
               status=status.HTTP_400_BAD_REQUEST
           )
       
       work_order.status = 'IN_PROGRESS'
       work_order.actual_start = timezone.now()
       work_order.save()
       
       serializer = self.get_serializer(work_order)
       return Response(serializer.data)
   
   @action(detail=True, methods=['post'])
   def complete(self, request, pk=None):
       work_order = self.get_object()
       
       if work_order.status != 'IN_PROGRESS':
           return Response(
               {'error': 'Work order must be in progress to complete'},
               status=status.HTTP_400_BAD_REQUEST
           )
       
       # Check if all tasks are completed
       incomplete_tasks = work_order.tasks.filter(is_completed=False)
       if incomplete_tasks.exists():
           return Response(
               {'error': 'All tasks must be completed before completing work order'},
               status=status.HTTP_400_BAD_REQUEST
           )
       
       work_order.status = 'COMPLETED'
       work_order.actual_end = timezone.now()
       work_order.actual_hours = sum(task.actual_hours or 0 for task in work_order.tasks.all())
       work_order.save()
       
       # Create maintenance log
       MaintenanceLog.objects.create(
           equipment=work_order.equipment,
           work_order=work_order,
           log_type='MAINTENANCE',
           description=work_order.description,
           action_taken=f"Completed maintenance work order {work_order.work_order_number}",
           logged_by=request.user,
           downtime_hours=(work_order.actual_end - work_order.actual_start).total_seconds() / 3600
       )
       
       serializer = self.get_serializer(work_order)
       return Response(serializer.data)
   
   @action(detail=True, methods=['post'])
   def add_part_usage(self, request, pk=None):
       work_order = self.get_object()
       
       serializer = MaintenancePartUsageSerializer(data=request.data)
       if serializer.is_valid():
           part_usage = serializer.save(work_order=work_order)
           
           # Update spare part stock
           spare_part = part_usage.spare_part
           spare_part.current_stock -= part_usage.quantity_used
           spare_part.save()
           
           # Check if stock is below minimum
           if spare_part.is_below_minimum:
               # TODO: Create purchase requisition for spare part
               pass
           
           return Response(serializer.data, status=status.HTTP_201_CREATED)
       return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MaintenanceTaskViewSet(viewsets.ModelViewSet):
   queryset = MaintenanceTask.objects.all()
   serializer_class = MaintenanceTaskSerializer
   permission_classes = [IsAuthenticated, HasRolePermission]
   filterset_fields = ['work_order', 'is_completed']
   ordering = ['sequence_number']
   
   @action(detail=True, methods=['post'])
   def complete(self, request, pk=None):
       task = self.get_object()
       
       if task.is_completed:
           return Response(
               {'error': 'Task is already completed'},
               status=status.HTTP_400_BAD_REQUEST
           )
       
       task.is_completed = True
       task.completed_by = request.user
       task.completed_at = timezone.now()
       task.actual_hours = request.data.get('actual_hours', task.estimated_hours)
       task.notes = request.data.get('notes', task.notes)
       task.save()
       
       serializer = self.get_serializer(task)
       return Response(serializer.data)


class SparePartViewSet(viewsets.ModelViewSet):
   queryset = SparePart.objects.all()
   serializer_class = SparePartSerializer
   permission_classes = [IsAuthenticated, HasRolePermission]
   filterset_fields = ['supplier', 'equipment']
   search_fields = ['part_number', 'name']
   ordering = ['part_number']
   
   @action(detail=False, methods=['get'])
   def low_stock(self, request):
       """Get spare parts below minimum stock"""
       low_stock_parts = SparePart.objects.filter(
           current_stock__lt=models.F('minimum_stock')
       )
       
       serializer = self.get_serializer(low_stock_parts, many=True)
       return Response(serializer.data)
   
   @action(detail=True, methods=['post'])
   def adjust_stock(self, request, pk=None):
       spare_part = self.get_object()
       
       adjustment = request.data.get('adjustment', 0)
       reason = request.data.get('reason', '')
       
       if not adjustment or not reason:
           return Response(
               {'error': 'Adjustment amount and reason are required'},
               status=status.HTTP_400_BAD_REQUEST
           )
       
       spare_part.current_stock += int(adjustment)
       spare_part.save()
       
       # Create log entry
       MaintenanceLog.objects.create(
           equipment=None,
           log_type='OTHER',
           description=f"Stock adjustment for {spare_part.name}",
           action_taken=f"Adjusted stock by {adjustment}. Reason: {reason}",
           logged_by=request.user
       )
       
       serializer = self.get_serializer(spare_part)
       return Response(serializer.data)


class MaintenanceLogViewSet(viewsets.ModelViewSet):
   queryset = MaintenanceLog.objects.all()
   serializer_class = MaintenanceLogSerializer
   permission_classes = [IsAuthenticated, HasRolePermission]
   filterset_fields = ['equipment', 'log_type', 'work_order']
   search_fields = ['description', 'action_taken']
   ordering = ['-log_date']
   
   def perform_create(self, serializer):
       serializer.save(
           logged_by=self.request.user,
           created_by=self.request.user
       )