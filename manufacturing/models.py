from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from inventory.models.core import Product, RawMaterial
from erp_core.models import ProductType, ComponentType, MachineStatus, Customer

from .models.core import (
    Machine,
    ManufacturingProcess,
    MachineType
)

from .models.bom import (
    BOMProcessConfig,
    BOM,
    BOMComponent
)

from .models.production import (
    SalesOrder,
    SalesOrderItem,
    WorkOrder,
    SubWorkOrder,
    SubWorkOrderProcess
)

__all__ = [
    'Machine',
    'ManufacturingProcess',
    'MachineStatus',
    'MachineType',
    'BOMProcessConfig',
    'BOM',
    'BOMComponent',
    'SalesOrder',
    'SalesOrderItem',
    'WorkOrder',
    'SubWorkOrder',
    'SubWorkOrderProcess'
] 