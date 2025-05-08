# quality/admin.py
from django.contrib import admin
from .models import (
    QualityStandard, InspectionTemplate, InspectionParameter,
    QualityInspection, InspectionResult, NonConformance,
    QualityDocument
)

@admin.register(QualityStandard)
class QualityStandardAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('is_active',)

@admin.register(InspectionTemplate)
class InspectionTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'inspection_type', 'version', 'is_active')
    search_fields = ('name', 'product__product_code')
    list_filter = ('inspection_type', 'is_active')

@admin.register(QualityInspection)
class QualityInspectionAdmin(admin.ModelAdmin):
    list_display = ('inspection_number', 'inspection_type', 'product', 'result', 'inspection_date')
    search_fields = ('inspection_number', 'product__product_code')
    list_filter = ('inspection_type', 'result')
    date_hierarchy = 'inspection_date'

@admin.register(NonConformance)
class NonConformanceAdmin(admin.ModelAdmin):
    list_display = ('nc_number', 'product', 'severity', 'status', 'reported_by')
    search_fields = ('nc_number', 'product__product_code')
    list_filter = ('severity', 'status')

@admin.register(QualityDocument)
class QualityDocumentAdmin(admin.ModelAdmin):
    list_display = ('document_number', 'title', 'document_type', 'version', 'is_active')
    search_fields = ('document_number', 'title')
    list_filter = ('document_type', 'is_active')