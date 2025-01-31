from django.db import models
from erp_core.models import BaseModel, User
from manufacturing.models import Machine, BOM, WorkOrder

class QualityDocumentType(models.TextChoices):
    SUPPORT = 'SUPPORT', 'Destek Dokümanı'
    MANUAL = 'MANUAL', 'El Kitabı'
    PROCEDURE = 'PROCEDURE', 'Prosedür'
    INSTRUCTION = 'INSTRUCTION', 'Talimat'
    SCHEMA = 'SCHEMA', 'Şema'

class QualityDocument(BaseModel):
    document_type = models.CharField(max_length=20, choices=QualityDocumentType.choices)
    title = models.CharField(max_length=200)
    version = models.CharField(max_length=20)
    effective_date = models.DateField()
    related_bom = models.ForeignKey(BOM, on_delete=models.SET_NULL, null=True, blank=True)
    related_product = models.ForeignKey('inventory.Product', on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to='quality_documents/')
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='approved_documents')

class QualityChecklist(BaseModel):
    name = models.CharField(max_length=200)
    description = models.TextField()
    process = models.ForeignKey('manufacturing.ManufacturingProcess', on_delete=models.CASCADE)
    items = models.JSONField()  # {question: string, type: string, options: []}

class QualityFormResponse(BaseModel):
    checklist = models.ForeignKey(QualityChecklist, on_delete=models.PROTECT)
    work_order = models.ForeignKey(WorkOrder, on_delete=models.PROTECT)
    responder = models.ForeignKey(User, on_delete=models.PROTECT)
    responses = models.JSONField()
    passed = models.BooleanField(default=False)

class CalibrationRecord(BaseModel):
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT)
    calibrated_by = models.ForeignKey(User, on_delete=models.PROTECT)
    calibration_date = models.DateField()
    next_calibration_date = models.DateField()
    certificate_url = models.URLField()
    parameters = models.JSONField()  # Store calibration parameters