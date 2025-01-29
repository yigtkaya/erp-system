from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from inventory.models import RawMaterial

class Customer(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)

    class Meta:
        permissions = [
            ('view_customer_dashboard', 'Can view customer dashboard'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

class ProductType(models.TextChoices):
    MONTAGED = 'MONTAGED', 'Montaged Product'
    SEMI = 'SEMI', 'Semi-Finished'
    SINGLE = 'SINGLE', 'Single Part'

class Product(models.Model):
    product_code = models.CharField(max_length=50, unique=True)
    product_name = models.CharField(max_length=100)
    product_type = models.CharField(max_length=20, choices=ProductType.choices)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True)
    current_stock = models.IntegerField(default=0)
    unit = models.ForeignKey('inventory.UnitOfMeasure', on_delete=models.PROTECT)  # We'll create this next

    def clean(self):
        # Add validation logic here
        if self.product_type == ProductType.SINGLE and self.customer:
            raise ValidationError("Single parts shouldn't be customer-specific")
    
    def __str__(self):
        return f"{self.product_code} - {self.product_name}"


class TechnicalDrawing(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    version = models.CharField(max_length=20)
    drawing_code = models.CharField(max_length=50)
    drawing_url = models.URLField(max_length=500)
    effective_date = models.DateField()
    is_current = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    revision_notes = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = "Technical Drawing"
        verbose_name_plural = "Technical Drawings"
        unique_together = ('product', 'version')
        indexes = [
            models.Index(fields=['product', 'is_current']),
        ]

    def __str__(self):
        return f"{self.drawing_code} v{self.version}"


class ComponentType(models.TextChoices):
    SEMI_PRODUCT = 'SEMI_PRODUCT', 'Semi-Product'
    MANUFACTURING_PROCESS = 'MANUFACTURING_PROCESS', 'Manufacturing Process'
    RAW_MATERIAL = 'RAW_MATERIAL', 'Raw Material'

class BOM(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    version = models.CharField(max_length=20, default='1.0')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Bill of Materials"
        verbose_name_plural = "Bills of Materials"
        unique_together = ('product', 'version')
        indexes = [
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f"BOM {self.product} v{self.version}"

class BOMComponent(models.Model):
    id = models.AutoField(primary_key=True)
    bom = models.ForeignKey(BOM, on_delete=models.CASCADE)
    component_type = models.CharField(max_length=25, choices=ComponentType.choices)
    semi_product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE, null=True, blank=True)
    process_config = models.ForeignKey('BOMProcessConfig', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    sequence_order = models.IntegerField()

    class Meta:
        verbose_name = "BOM Component"
        verbose_name_plural = "BOM Components"
        ordering = ['sequence_order']

    def clean(self):
        # Validation logic will be added later
        pass

    def __str__(self):
        return f"{self.bom} - Component {self.sequence_order}"

class BOMProcessConfig(models.Model):
    id = models.AutoField(primary_key=True)
    process = models.ForeignKey('ManufacturingProcess', on_delete=models.CASCADE)
    machine_type = models.CharField(max_length=50)
    estimated_duration_minutes = models.IntegerField()
    tooling_requirements = models.JSONField()
    quality_checks = models.JSONField()

    class Meta:
        verbose_name = "BOM Process Configuration"
        verbose_name_plural = "BOM Process Configurations"

    def __str__(self):
        return f"{self.process} Configuration"

class ManufacturingProcess(models.Model):
    process_code = models.CharField(max_length=50, unique=True)
    process_name = models.CharField(max_length=100)
    standard_time_minutes = models.IntegerField()
    machine_type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.process_code} - {self.process_name}"

class MachineStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    IN_USE = 'IN_USE', 'In Use'
    MAINTENANCE = 'MAINTENANCE', 'Maintenance'
    RETIRED = 'RETIRED', 'Retired'

class MachineType(models.TextChoices):
    MILLING = 'MILLING', 'Milling Machine'
    LATHE = 'LATHE', 'Lathe Machine'
    DRILL = 'DRILL', 'Drill Press'  # TODO
    GRINDING = 'GRINDING', 'Grinding Machine'