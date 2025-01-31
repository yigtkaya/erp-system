from django.db import models
from django.core.exceptions import ValidationError
from erp_core.models import BaseModel, User
from manufacturing.models import Machine

class MaintenanceType(models.TextChoices):
    PREVENTIVE = 'PREVENTIVE', 'Preventive Maintenance'
    CORRECTIVE = 'CORRECTIVE', 'Corrective Maintenance'
    PREDICTIVE = 'PREDICTIVE', 'Predictive Maintenance'

class MaintenanceStatus(models.TextChoices):
    SCHEDULED = 'SCHEDULED', 'Scheduled'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    OVERDUE = 'OVERDUE', 'Overdue'

class Maintenance(BaseModel):
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT, related_name='maintenances')
    maintenance_type = models.CharField(max_length=20, choices=MaintenanceType.choices)
    scheduled_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.PROTECT, related_name='assigned_maintenances')
    status = models.CharField(max_length=20, choices=MaintenanceStatus.choices, default=MaintenanceStatus.SCHEDULED)
    checklist = models.JSONField(default=list)
    notes = models.TextField(blank=True, null=True)

    def clean(self):
        if self.completed_date and self.completed_date < self.scheduled_date:
            raise ValidationError("Completed date cannot be before scheduled date")

    def __str__(self):
        return f"{self.machine.machine_code} - {self.get_maintenance_type_display()}"

class FaultReport(BaseModel):
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT, related_name='fault_reports')
    reported_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reported_faults')
    fault_description = models.TextField()
    severity = models.CharField(max_length=20, choices=[
        ('LOW', 'Low'), 
        ('MEDIUM', 'Medium'), 
        ('HIGH', 'High')
    ])
    status = models.CharField(max_length=20, choices=[
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved')
    ], default='OPEN')
    resolution_notes = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='resolved_faults')

    def __str__(self):
        return f"{self.machine.machine_code} - {self.get_severity_display()} Fault"
