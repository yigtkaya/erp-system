from django.contrib import admin
from .models import (
    QualityDocument,
    QualityChecklist,
    QualityFormResponse,
    CalibrationRecord
)

# Register your models here.

@admin.register(QualityDocument)
class QualityDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'version', 'effective_date')
    list_filter = ('document_type', 'effective_date')
    search_fields = ('title', 'version')

@admin.register(QualityChecklist)
class QualityChecklistAdmin(admin.ModelAdmin):
    list_display = ('name', 'process')
    search_fields = ('name', 'process__process_name')

@admin.register(QualityFormResponse)
class QualityFormResponseAdmin(admin.ModelAdmin):
    list_display = ('checklist', 'work_order', 'responder', 'passed')
    list_filter = ('passed',)

@admin.register(CalibrationRecord)
class CalibrationRecordAdmin(admin.ModelAdmin):
    list_display = ('machine', 'calibration_date', 'next_calibration_date')
    list_filter = ('machine__machine_type',)
