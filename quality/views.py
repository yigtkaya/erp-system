# quality/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from .models import (
    QualityStandard, InspectionTemplate, InspectionParameter,
    QualityInspection, InspectionResult, NonConformance,
    QualityDocument
)
from .serializers import (
    QualityStandardSerializer, InspectionTemplateSerializer,
    InspectionParameterSerializer, QualityInspectionSerializer,
    InspectionResultSerializer, NonConformanceSerializer,
    QualityDocumentSerializer
)
from core.permissions import HasRolePermission


class QualityStandardViewSet(viewsets.ModelViewSet):
    queryset = QualityStandard.objects.all()
    serializer_class = QualityStandardSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['is_active']
    search_fields = ['code', 'name']
    ordering = ['code']


class InspectionTemplateViewSet(viewsets.ModelViewSet):
    queryset = InspectionTemplate.objects.all()
    serializer_class = InspectionTemplateSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['product', 'inspection_type', 'is_active']
    search_fields = ['name', 'product__product_code']
    ordering = ['name', '-version']
    
    @action(detail=True, methods=['post'])
    def copy_template(self, request, pk=None):
        template = self.get_object()
        
        # Create a copy of the template
        new_template = InspectionTemplate.objects.create(
            name=f"{template.name} (Copy)",
            product=template.product,
            inspection_type=template.inspection_type,
            quality_standard=template.quality_standard,
            is_active=True,
            version="1.0",
            notes=f"Copied from {template.name} v{template.version}",
            created_by=request.user
        )
        
        # Copy parameters
        for param in template.parameters.all():
            InspectionParameter.objects.create(
                template=new_template,
                parameter_name=param.parameter_name,
                parameter_type=param.parameter_type,
                unit_of_measure=param.unit_of_measure,
                nominal_value=param.nominal_value,
                min_value=param.min_value,
                max_value=param.max_value,
                choices=param.choices,
                is_critical=param.is_critical,
                sequence_number=param.sequence_number
            )
        
        serializer = self.get_serializer(new_template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QualityInspectionViewSet(viewsets.ModelViewSet):
    queryset = QualityInspection.objects.all()
    serializer_class = QualityInspectionSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['inspection_type', 'result', 'product', 'work_order']
    search_fields = ['inspection_number', 'product__product_code', 'batch_number']
    ordering = ['-inspection_date']
    
    def perform_create(self, serializer):
        serializer.save(
            inspector=self.request.user,
            created_by=self.request.user
        )
    
    @action(detail=False, methods=['post'])
    def create_with_results(self, request):
        """Create inspection with results"""
        with transaction.atomic():
            results_data = request.data.pop('results', [])
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            inspection = serializer.save(
                inspector=request.user,
                created_by=request.user
            )
            
            # Create inspection results
            passed_count = 0
            failed_count = 0
            
            for result_data in results_data:
                result_data['inspection'] = inspection.id
                result_serializer = InspectionResultSerializer(data=result_data)
                result_serializer.is_valid(raise_exception=True)
                result = result_serializer.save()
                
                if result.is_passed:
                    passed_count += 1
                else:
                    failed_count += 1
            
            # Determine overall result
            if failed_count == 0:
                inspection.result = 'PASS'
            elif passed_count > 0:
                inspection.result = 'CONDITIONAL'
            else:
                inspection.result = 'FAIL'
            
            inspection.save()
            
            return Response(
                self.get_serializer(inspection).data,
                status=status.HTTP_201_CREATED
            )
    
    @action(detail=True, methods=['post'])
    def create_nonconformance(self, request, pk=None):
        inspection = self.get_object()
        
        if inspection.result == 'PASS':
            return Response(
                {'error': 'Cannot create nonconformance for passed inspection'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = request.data.copy()
        data['inspection'] = inspection.id
        data['product'] = inspection.product.id
        data['reported_by'] = request.user.id
        
        serializer = NonConformanceSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        nonconformance = serializer.save(reported_by=request.user)
        
        return Response(
            NonConformanceSerializer(nonconformance).data,
            status=status.HTTP_201_CREATED
        )


class NonConformanceViewSet(viewsets.ModelViewSet):
    queryset = NonConformance.objects.all()
    serializer_class = NonConformanceSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['severity', 'status', 'product', 'assigned_to']
    search_fields = ['nc_number', 'description', 'product__product_code']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(
            reported_by=self.request.user,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        nonconformance = self.get_object()
        
        if nonconformance.status == 'CLOSED':
            return Response(
                {'error': 'Nonconformance is already closed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        root_cause = request.data.get('root_cause')
        corrective_action = request.data.get('corrective_action')
        preventive_action = request.data.get('preventive_action')
        
        if not all([root_cause, corrective_action, preventive_action]):
            return Response(
                {'error': 'Root cause, corrective action, and preventive action are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        nonconformance.root_cause = root_cause
        nonconformance.corrective_action = corrective_action
        nonconformance.preventive_action = preventive_action
        nonconformance.status = 'RESOLVED'
        nonconformance.resolution_date = timezone.now()
        nonconformance.save()
        
        serializer = self.get_serializer(nonconformance)
        return Response(serializer.data)


class QualityDocumentViewSet(viewsets.ModelViewSet):
    queryset = QualityDocument.objects.all()
    serializer_class = QualityDocumentSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['document_type', 'is_active', 'owner']
    search_fields = ['document_number', 'title']
    ordering = ['document_number', '-version']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)