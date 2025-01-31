from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Maintenance, FaultReport
from .serializers import MaintenanceSerializer, FaultReportSerializer

# Create your views here.

class MaintenanceViewSet(viewsets.ModelViewSet):
    queryset = Maintenance.objects.select_related('machine', 'assigned_to')
    serializer_class = MaintenanceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['machine', 'maintenance_type', 'status']
    search_fields = ['machine__machine_code', 'notes']

class FaultReportViewSet(viewsets.ModelViewSet):
    queryset = FaultReport.objects.select_related('machine', 'reported_by')
    serializer_class = FaultReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['machine', 'severity', 'status']
    search_fields = ['machine__machine_code', 'fault_description']
