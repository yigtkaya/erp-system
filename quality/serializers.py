# quality/serializers.py
from rest_framework import serializers
from .models import (
    QualityStandard, InspectionTemplate, InspectionParameter,
    QualityInspection, InspectionResult, NonConformance,
    QualityDocument
)
from core.serializers import UserListSerializer
from inventory.serializers import ProductSerializer
from manufacturing.serializers import WorkOrderSerializer
from purchasing.serializers import GoodsReceiptSerializer


class QualityStandardSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityStandard
        fields = ['id', 'code', 'name', 'description', 'is_active']


class InspectionParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionParameter
        fields = [
            'id', 'template', 'parameter_name', 'parameter_type',
            'unit_of_measure', 'nominal_value', 'min_value', 'max_value',
            'choices', 'is_critical', 'sequence_number'
        ]


class InspectionTemplateSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True,
        required=False
    )
    quality_standard = QualityStandardSerializer(read_only=True)
    quality_standard_id = serializers.PrimaryKeyRelatedField(
        queryset=QualityStandard.objects.all(),
        source='quality_standard',
        write_only=True,
        required=False
    )
    parameters = InspectionParameterSerializer(many=True, read_only=True)
    
    class Meta:
        model = InspectionTemplate
        fields = [
            'id', 'name', 'product', 'product_id', 'inspection_type',
            'quality_standard', 'quality_standard_id', 'is_active',
            'version', 'notes', 'parameters'
        ]


class InspectionResultSerializer(serializers.ModelSerializer):
    parameter = InspectionParameterSerializer(read_only=True)
    parameter_id = serializers.PrimaryKeyRelatedField(
        queryset=InspectionParameter.objects.all(),
        source='parameter',
        write_only=True
    )
    
    class Meta:
        model = InspectionResult
        fields = [
            'id', 'inspection', 'parameter', 'parameter_id',
            'measured_value', 'is_passed', 'notes'
        ]


class QualityInspectionSerializer(serializers.ModelSerializer):
    template = InspectionTemplateSerializer(read_only=True)
    template_id = serializers.PrimaryKeyRelatedField(
        queryset=InspectionTemplate.objects.all(),
        source='template',
        write_only=True
    )
    inspector = UserListSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    work_order = WorkOrderSerializer(read_only=True)
    goods_receipt = GoodsReceiptSerializer(read_only=True)
    results = InspectionResultSerializer(many=True, read_only=True)
    
    class Meta:
        model = QualityInspection
        fields = [
            'id', 'inspection_number', 'inspection_type', 'template',
            'template_id', 'inspector', 'inspection_date', 'result',
            'work_order', 'production_output', 'goods_receipt', 'product',
            'product_id', 'quantity_inspected', 'quantity_passed',
            'quantity_failed', 'batch_number', 'sample_size', 'notes',
            'results'
        ]
        read_only_fields = ['inspector']


class NonConformanceSerializer(serializers.ModelSerializer):
    inspection = QualityInspectionSerializer(read_only=True)
    inspection_id = serializers.PrimaryKeyRelatedField(
        queryset=QualityInspection.objects.all(),
        source='inspection',
        write_only=True
    )
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    reported_by = UserListSerializer(read_only=True)
    assigned_to = UserListSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assigned_to',
        write_only=True
    )
    
    class Meta:
        model = NonConformance
        fields = [
            'id', 'nc_number', 'inspection', 'inspection_id', 'product',
            'product_id', 'severity', 'status', 'description', 'root_cause',
            'corrective_action', 'preventive_action', 'reported_by',
            'assigned_to', 'assigned_to_id', 'resolution_date'
        ]
        read_only_fields = ['reported_by']


class QualityDocumentSerializer(serializers.ModelSerializer):
    owner = UserListSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='owner',
        write_only=True
    )
    approved_by = UserListSerializer(read_only=True)
    approved_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='approved_by',
        write_only=True
    )
    
    class Meta:
        model = QualityDocument
        fields = [
            'id', 'document_number', 'title', 'document_type', 'version',
            'effective_date', 'review_date', 'owner', 'owner_id',
            'approved_by', 'approved_by_id', 'is_active'
        ]