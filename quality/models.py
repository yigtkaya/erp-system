# quality/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
from core.models import BaseModel
from inventory.models import Product
from manufacturing.models import WorkOrder, ProductionOutput
from purchasing.models import GoodsReceipt, GoodsReceiptItem
from common.models import FileVersionManager, ContentType


class InspectionType(models.TextChoices):
    INCOMING = 'INCOMING', 'Incoming Inspection'
    IN_PROCESS = 'IN_PROCESS', 'In-Process Inspection'
    FINAL = 'FINAL', 'Final Inspection'
    RANDOM = 'RANDOM', 'Random Inspection'


class InspectionResult(models.TextChoices):
    PASS = 'PASS', 'Pass'
    FAIL = 'FAIL', 'Fail'
    CONDITIONAL = 'CONDITIONAL', 'Conditional Pass'
    PENDING = 'PENDING', 'Pending'


class QualityStandard(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'quality_standards'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class InspectionTemplate(BaseModel):
    name = models.CharField(max_length=100)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inspection_templates', null=True, blank=True)
    inspection_type = models.CharField(max_length=20, choices=InspectionType.choices)
    quality_standard = models.ForeignKey(QualityStandard, on_delete=models.PROTECT, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=20)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'inspection_templates'
        unique_together = ['name', 'version']
        ordering = ['name', '-version']
    
    def __str__(self):
        return f"{self.name} v{self.version}"


class InspectionParameter(BaseModel):
    template = models.ForeignKey(InspectionTemplate, on_delete=models.CASCADE, related_name='parameters')
    parameter_name = models.CharField(max_length=100)
    parameter_type = models.CharField(max_length=20, choices=[
        ('NUMERIC', 'Numeric'),
        ('TEXT', 'Text'),
        ('BOOLEAN', 'Boolean'),
        ('CHOICE', 'Choice'),
    ])
    unit_of_measure = models.CharField(max_length=20, blank=True, null=True)
    nominal_value = models.CharField(max_length=100, blank=True, null=True)
    min_value = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    max_value = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    choices = models.JSONField(null=True, blank=True)  # For choice type parameters
    is_critical = models.BooleanField(default=False)
    sequence_number = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'inspection_parameters'
        ordering = ['sequence_number', 'parameter_name']
    
    def __str__(self):
        return f"{self.template.name} - {self.parameter_name}"


class QualityInspection(BaseModel):
    inspection_number = models.CharField(max_length=50, unique=True)
    inspection_type = models.CharField(max_length=20, choices=InspectionType.choices)
    template = models.ForeignKey(InspectionTemplate, on_delete=models.PROTECT)
    inspector = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='inspections')
    inspection_date = models.DateTimeField(default=timezone.now)
    result = models.CharField(max_length=20, choices=InspectionResult.choices, default=InspectionResult.PENDING)
    
    # References to what's being inspected
    work_order = models.ForeignKey(WorkOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='inspections')
    production_output = models.ForeignKey(ProductionOutput, on_delete=models.SET_NULL, null=True, blank=True)
    goods_receipt = models.ForeignKey(GoodsReceipt, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    
    quantity_inspected = models.IntegerField()
    quantity_passed = models.IntegerField(default=0)
    quantity_failed = models.IntegerField(default=0)
    
    batch_number = models.CharField(max_length=50, blank=True, null=True)
    sample_size = models.IntegerField()
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'quality_inspections'
        ordering = ['-inspection_date']
        indexes = [
            models.Index(fields=['inspection_number']),
            models.Index(fields=['inspection_type', 'result']),
            models.Index(fields=['inspection_date']),
        ]
    
    def clean(self):
        if self.quantity_passed + self.quantity_failed > self.quantity_inspected:
            raise ValidationError("Passed + Failed quantity cannot exceed inspected quantity")
    
    def __str__(self):
        return f"{self.inspection_number} - {self.product.product_code}"
    
    # File management methods
    def upload_inspection_image(self, file, notes=None, user=None):
        """Upload inspection image"""
        return FileVersionManager.create_version(
            file=file,
            content_type=ContentType.QUALITY_IMAGE,
            object_id=str(self.id),
            notes=notes,
            user=user
        )


class InspectionResult(BaseModel):
    inspection = models.ForeignKey(QualityInspection, on_delete=models.CASCADE, related_name='results')
    parameter = models.ForeignKey(InspectionParameter, on_delete=models.PROTECT)
    measured_value = models.CharField(max_length=200)
    is_passed = models.BooleanField()
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'inspection_results'
        unique_together = ['inspection', 'parameter']
    
    def __str__(self):
        return f"{self.inspection.inspection_number} - {self.parameter.parameter_name}"


class NonConformance(BaseModel):
    nc_number = models.CharField(max_length=50, unique=True)
    inspection = models.ForeignKey(QualityInspection, on_delete=models.CASCADE, related_name='nonconformances')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    severity = models.CharField(max_length=20, choices=[
        ('CRITICAL', 'Critical'),
        ('MAJOR', 'Major'),
        ('MINOR', 'Minor'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('OPEN', 'Open'),
        ('INVESTIGATING', 'Under Investigation'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ], default='OPEN')
    description = models.TextField()
    root_cause = models.TextField(blank=True, null=True)
    corrective_action = models.TextField(blank=True, null=True)
    preventive_action = models.TextField(blank=True, null=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reported_nonconformances')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='assigned_nonconformances')
    resolution_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'nonconformances'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.nc_number} - {self.product.product_code}"


class QualityDocument(BaseModel):
    document_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=50, choices=[
        ('PROCEDURE', 'Procedure'),
        ('WORK_INSTRUCTION', 'Work Instruction'),
        ('SPECIFICATION', 'Specification'),
        ('FORM', 'Form'),
        ('MANUAL', 'Manual'),
    ])
    version = models.CharField(max_length=20)
    effective_date = models.DateField()
    review_date = models.DateField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='owned_quality_documents')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='approved_quality_documents')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'quality_documents'
        unique_together = ['document_number', 'version']
        ordering = ['document_number', '-version']
    
    def __str__(self):
        return f"{self.document_number} - {self.title} v{self.version}"
    
    # File management methods
    def upload_document(self, file, notes=None, user=None):
        """Upload quality document"""
        return FileVersionManager.create_version(
            file=file,
            content_type=ContentType.QUALITY_DOCUMENT,
            object_id=str(self.id),
            notes=notes,
            user=user
        )