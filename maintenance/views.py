# maintenance/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import (
    Equipment, MaintenanceWorkOrder, MaintenanceTask,
    MaintenanceLog
)
from .serializers import (
    EquipmentSerializer, WorkOrderSerializer,
    MaintenanceTaskSerializer, MaintenanceLogSerializer
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
        work_orders = MaintenanceWorkOrder.objects.filter(equipment=equipment)
        logs = MaintenanceLog.objects.filter(equipment=equipment)
        
        return Response({
            'work_orders': WorkOrderSerializer(work_orders, many=True).data,
            'logs': MaintenanceLogSerializer(logs, many=True).data
        })


class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceWorkOrder.objects.all()
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