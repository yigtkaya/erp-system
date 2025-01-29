from django.db import models
from django.core.exceptions import ValidationError
from erp_core.models import BaseModel, User, WorkOrderStatus
from inventory.models.core import Product
from .bom import BOM, BOMComponent
from .core import ManufacturingProcess, Machine

class SalesOrder(BaseModel):
    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey('erp_core.Customer', on_delete=models.PROTECT)
    order_date = models.DateField(auto_now_add=True)
    deadline_date = models.DateField()
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='approved_sales_orders')

    def __str__(self):
        return f"{self.order_number} - {self.customer.name}"

class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    fulfilled_quantity = models.IntegerField(default=0)

    def clean(self):
        if self.fulfilled_quantity > self.quantity:
            raise ValidationError("Fulfilled quantity cannot exceed ordered quantity")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sales_order.order_number} - {self.product.product_code}"

class WorkOrder(BaseModel):
    order_number = models.CharField(max_length=50, unique=True)
    sales_order_item = models.ForeignKey(SalesOrderItem, on_delete=models.PROTECT)
    bom = models.ForeignKey(BOM, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    planned_start = models.DateField()
    planned_end = models.DateField()
    actual_start = models.DateField(null=True, blank=True)
    actual_end = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=WorkOrderStatus.choices, default=WorkOrderStatus.PLANNED)

    def __str__(self):
        return f"{self.order_number} - {self.bom.product.product_code}"

class SubWorkOrder(models.Model):
    parent_work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='sub_orders')
    bom_component = models.ForeignKey(BOMComponent, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    planned_start = models.DateField()
    planned_end = models.DateField()
    actual_start = models.DateField(null=True, blank=True)
    actual_end = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=WorkOrderStatus.choices, default=WorkOrderStatus.PLANNED)

    def __str__(self):
        return f"{self.parent_work_order.order_number} - {self.bom_component}"

class SubWorkOrderProcess(models.Model):
    sub_work_order = models.ForeignKey(SubWorkOrder, on_delete=models.CASCADE, related_name='processes')
    process = models.ForeignKey(ManufacturingProcess, on_delete=models.PROTECT)
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT)
    sequence_order = models.IntegerField()
    planned_duration_minutes = models.IntegerField()
    actual_duration_minutes = models.IntegerField(null=True, blank=True)

    def clean(self):
        if self.machine.machine_type != self.process.machine_type:
            raise ValidationError("Machine type does not match process requirements")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sub_work_order} - {self.process.process_code}"

    class Meta:
        ordering = ['sequence_order'] 