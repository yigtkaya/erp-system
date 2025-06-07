#!/usr/bin/env python3
"""
Dummy Data Loader for Manufacturing System
Run this script to populate your database with test data for development and testing.

Usage:
    python manage.py shell < manufacturing/load_dummy_data.py
    # OR
    python manufacturing/load_dummy_data.py (if running as standalone with Django setup)
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django environment
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import Customer
from inventory.models import (
    Product, RawMaterial, InventoryCategory, UnitOfMeasure, 
    ProductBOM, Tool, Fixture, ControlGauge
)
from manufacturing.models import (
    Machine, WorkOrder, WorkOrderOperation, MaterialAllocation,
    ManufacturingProcess, ProductWorkflow, ProcessConfig,
    ProductionOutput, MachineDowntime
)
from sales.models import SalesOrder, SalesOrderItem

User = get_user_model()

def create_dummy_data():
    print("🚀 Starting dummy data creation...")
    
    # Create or get superuser
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
    
    # Create test users
    operator_user, created = User.objects.get_or_create(
        username='operator1',
        defaults={
            'email': 'operator1@example.com',
            'first_name': 'John',
            'last_name': 'Operator'
        }
    )
    
    engineer_user, created = User.objects.get_or_create(
        username='engineer1',
        defaults={
            'email': 'engineer1@example.com',
            'first_name': 'Jane',
            'last_name': 'Engineer'
        }
    )
    
    print("✅ Users created")
    
    # Create Units of Measure
    unit_pcs, _ = UnitOfMeasure.objects.get_or_create(
        unit_code='PCS',
        defaults={'unit_name': 'Pieces', 'category': 'Quantity'}
    )
    
    unit_kg, _ = UnitOfMeasure.objects.get_or_create(
        unit_code='KG',
        defaults={'unit_name': 'Kilograms', 'category': 'Weight'}
    )
    
    unit_m, _ = UnitOfMeasure.objects.get_or_create(
        unit_code='M',
        defaults={'unit_name': 'Meters', 'category': 'Length'}
    )
    
    print("✅ Units of measure created")
    
    # Create Inventory Categories
    cat_mamul, _ = InventoryCategory.objects.get_or_create(
        name='MAMUL',
        defaults={'description': 'Finished Products'}
    )
    
    cat_hammadde, _ = InventoryCategory.objects.get_or_create(
        name='HAMMADDE',
        defaults={'description': 'Raw Materials'}
    )
    
    cat_yarimamul, _ = InventoryCategory.objects.get_or_create(
        name='YARIMAMUL',
        defaults={'description': 'Semi-Finished Products'}
    )
    
    print("✅ Inventory categories created")
    
    # Create Customer
    customer, _ = Customer.objects.get_or_create(
        name='ACME Corporation',
        defaults={
            'email': 'orders@acme.com',
            'phone': '+1-555-0123',
            'address': '123 Industrial Ave, Manufacturing City, MC 12345'
        }
    )
    
    print("✅ Customer created")
    
    # Create Products
    products_data = [
        {
            'stock_code': 'ASM001',
            'product_name': 'Main Assembly Unit',
            'product_type': 'MONTAGED',
            'current_stock': 50,
            'unit_of_measure': unit_pcs,
            'inventory_category': cat_mamul,
            'description': 'Complete main assembly with motor and brackets'
        },
        {
            'stock_code': 'PRT001',
            'product_name': 'Steel Bracket',
            'product_type': 'SINGLE',
            'current_stock': 150,
            'unit_of_measure': unit_pcs,
            'inventory_category': cat_mamul,
            'description': 'CNC machined steel bracket component'
        },
        {
            'stock_code': 'SUB001',
            'product_name': 'Motor Sub-Assembly',
            'product_type': 'SEMI',
            'current_stock': 25,
            'unit_of_measure': unit_pcs,
            'inventory_category': cat_yarimamul,
            'description': 'Motor with mounting hardware sub-assembly'
        },
        {
            'stock_code': 'MOT001',
            'product_name': 'Electric Motor 5HP',
            'product_type': 'STANDARD_PART',
            'current_stock': 30,
            'unit_of_measure': unit_pcs,
            'inventory_category': cat_hammadde,
            'description': '5HP 3-phase electric motor'
        },
        {
            'stock_code': 'BOLT001',
            'product_name': 'M8x25 Bolt',
            'product_type': 'STANDARD_PART',
            'current_stock': 1000,
            'unit_of_measure': unit_pcs,
            'inventory_category': cat_hammadde,
            'description': 'M8x25 hex head bolt'
        }
    ]
    
    products = {}
    for product_data in products_data:
        product, created = Product.objects.get_or_create(
            stock_code=product_data['stock_code'],
            defaults=product_data
        )
        products[product_data['stock_code']] = product
        if created:
            print(f"   Created product: {product.stock_code}")
    
    print("✅ Products created")
    
    # Create Raw Materials
    raw_materials_data = [
        {
            'stock_code': 'STL001',
            'material_name': 'Steel Plate 10mm',
            'current_stock': Decimal('500.00'),
            'unit': unit_kg,
            'inventory_category': cat_hammadde,
            'material_type': 'STEEL',
            'thickness': 10.0,
            'description': 'High-grade steel plate for CNC machining'
        },
        {
            'stock_code': 'ALU001',
            'material_name': 'Aluminum Bar 50mm',
            'current_stock': Decimal('200.00'),
            'unit': unit_m,
            'inventory_category': cat_hammadde,
            'material_type': 'ALUMINUM',
            'diameter_mm': 50.0,
            'description': 'Aluminum round bar stock'
        }
    ]
    
    for material_data in raw_materials_data:
        material, created = RawMaterial.objects.get_or_create(
            stock_code=material_data['stock_code'],
            defaults=material_data
        )
        if created:
            print(f"   Created raw material: {material.stock_code}")
    
    print("✅ Raw materials created")
    
    # Create Machines
    machines_data = [
        {
            'machine_code': 'CNC001',
            'machine_type': 'CNC_MILLING',
            'brand': 'Haas',
            'model': 'VF-2',
            'axis_count': 'AXIS_3',
            'spindle_speed_rpm': 8000,
            'tool_count': 20,
            'status': 'AVAILABLE',
            'manufacturing_year': datetime(2020, 1, 1).date(),
            'serial_number': 'VF2-2020-0123',
            'description': '3-axis CNC milling machine for precision parts',
            'maintenance_interval': 90
        },
        {
            'machine_code': 'CNC002',
            'machine_type': 'CNC_LATHE',
            'brand': 'Mazak',
            'model': 'QT-200',
            'axis_count': 'AXIS_2',
            'spindle_speed_rpm': 4000,
            'tool_count': 12,
            'status': 'AVAILABLE',
            'manufacturing_year': datetime(2019, 1, 1).date(),
            'serial_number': 'QT200-2019-0089',
            'description': '2-axis CNC turning center',
            'maintenance_interval': 90
        },
        {
            'machine_code': 'DRILL001',
            'machine_type': 'DRILLING',
            'brand': 'Bridgeport',
            'model': 'Series-1',
            'spindle_speed_rpm': 3000,
            'tool_count': 1,
            'status': 'AVAILABLE',
            'manufacturing_year': datetime(2018, 1, 1).date(),
            'serial_number': 'BP-2018-0045',
            'description': 'Manual drilling machine',
            'maintenance_interval': 60
        },
        {
            'machine_code': 'ASM001',
            'machine_type': 'ASSEMBLY',
            'brand': 'Custom',
            'model': 'WorkBench-1',
            'status': 'AVAILABLE',
            'description': 'Assembly workstation with pneumatic tools',
            'maintenance_interval': 30
        }
    ]
    
    machines = {}
    for machine_data in machines_data:
        machine, created = Machine.objects.get_or_create(
            machine_code=machine_data['machine_code'],
            defaults=machine_data
        )
        machines[machine_data['machine_code']] = machine
        if created:
            print(f"   Created machine: {machine.machine_code}")
    
    print("✅ Machines created")
    
    # Create Tools, Fixtures, Gauges
    tool, _ = Tool.objects.get_or_create(
        stock_code='TOOL001',
        defaults={
            'supplier_name': 'Sandvik',
            'product_code': 'R390-11T308',
            'tool_material': 'Carbide',
            'tool_diameter': Decimal('12.00'),
            'tool_type': 'End Mill',
            'status': 'AVAILABLE',
            'quantity': Decimal('5.00')
        }
    )
    
    fixture, _ = Fixture.objects.get_or_create(
        code='FIX001',
        defaults={
            'name': 'Steel Bracket Fixture',
            'status': 'ACTIVE'
        }
    )
    
    gauge, _ = ControlGauge.objects.get_or_create(
        stock_code='GAUGE001',
        defaults={
            'stock_name': 'Digital Caliper 150mm',
            'status': 'UYGUN',
            'calibration_date': timezone.now().date() - timedelta(days=30),
            'calibration_per_year': '1 / Yıl'
        }
    )
    
    print("✅ Tools, fixtures, and gauges created")
    
    # Create BOM Structure
    bom_items_data = [
        {
            'parent_product': products['ASM001'],
            'child_product': products['PRT001'],
            'quantity': Decimal('2.500'),
            'scrap_percentage': Decimal('5.00'),
            'operation_sequence': 1,
            'notes': 'Main structural component'
        },
        {
            'parent_product': products['ASM001'],
            'child_product': products['SUB001'],
            'quantity': Decimal('1.000'),
            'scrap_percentage': Decimal('2.00'),
            'operation_sequence': 2,
            'notes': 'Motor assembly component'
        },
        {
            'parent_product': products['SUB001'],
            'child_product': products['MOT001'],
            'quantity': Decimal('1.000'),
            'scrap_percentage': Decimal('0.00'),
            'operation_sequence': 1,
            'notes': 'Electric motor for sub-assembly'
        },
        {
            'parent_product': products['SUB001'],
            'child_product': products['BOLT001'],
            'quantity': Decimal('4.000'),
            'scrap_percentage': Decimal('1.00'),
            'operation_sequence': 2,
            'notes': 'Mounting bolts'
        }
    ]
    
    for bom_data in bom_items_data:
        bom_item, created = ProductBOM.objects.get_or_create(
            parent_product=bom_data['parent_product'],
            child_product=bom_data['child_product'],
            defaults=bom_data
        )
        if created:
            print(f"   Created BOM: {bom_item.parent_product.stock_code} -> {bom_item.child_product.stock_code}")
    
    print("✅ BOM structure created")
    
    # Create Manufacturing Processes
    processes_data = [
        {
            'process_code': 'MILL001',
            'name': 'CNC Milling Operation',
            'machine_type': 'CNC_MILLING',
            'standard_setup_time': 120,
            'standard_runtime': 15,
            'description': 'Precision milling operation for steel brackets'
        },
        {
            'process_code': 'TURN001',
            'name': 'CNC Turning Operation',
            'machine_type': 'CNC_LATHE',
            'standard_setup_time': 90,
            'standard_runtime': 10,
            'description': 'Turning operation for cylindrical parts'
        },
        {
            'process_code': 'ASM001',
            'name': 'Assembly Process',
            'machine_type': 'ASSEMBLY',
            'standard_setup_time': 60,
            'standard_runtime': 10,
            'description': 'Manual assembly with pneumatic tools'
        },
        {
            'process_code': 'INSP001',
            'name': 'Quality Inspection',
            'machine_type': 'INSPECTION',
            'standard_setup_time': 30,
            'standard_runtime': 5,
            'description': 'Dimensional and visual inspection'
        }
    ]
    
    processes = {}
    for process_data in processes_data:
        process, created = ManufacturingProcess.objects.get_or_create(
            process_code=process_data['process_code'],
            defaults=process_data
        )
        processes[process_data['process_code']] = process
        if created:
            print(f"   Created process: {process.process_code}")
    
    print("✅ Manufacturing processes created")
    
    # Create Product Workflows
    workflows_data = [
        {
            'product': products['ASM001'],
            'version': '2.0',
            'status': 'ACTIVE',
            'effective_date': timezone.now().date(),
            'revision_notes': 'Optimized process flow for higher efficiency'
        },
        {
            'product': products['PRT001'],
            'version': '1.0',
            'status': 'ACTIVE',
            'effective_date': timezone.now().date() - timedelta(days=30),
            'revision_notes': 'Initial process definition'
        }
    ]
    
    workflows = {}
    for workflow_data in workflows_data:
        workflow, created = ProductWorkflow.objects.get_or_create(
            product=workflow_data['product'],
            version=workflow_data['version'],
            defaults=workflow_data
        )
        workflows[f"{workflow_data['product'].stock_code}_{workflow_data['version']}"] = workflow
        if created:
            print(f"   Created workflow: {workflow.product.stock_code} v{workflow.version}")
    
    print("✅ Product workflows created")
    
    # Create Process Configurations
    process_configs_data = [
        {
            'workflow': workflows['ASM001_2.0'],
            'process': processes['MILL001'],
            'sequence_order': 1,
            'axis_count': 'AXIS_3',
            'setup_time': 120,
            'cycle_time': 300,
            'connecting_count': 15,
            'tool': tool,
            'fixture': fixture,
            'control_gauge': gauge,
            'instructions': 'Use flood coolant, check dimensions every 5 pieces'
        },
        {
            'workflow': workflows['ASM001_2.0'],
            'process': processes['ASM001'],
            'sequence_order': 2,
            'setup_time': 60,
            'cycle_time': 180,
            'connecting_count': 10,
            'instructions': 'Follow assembly drawing ASM001-DWG-001'
        },
        {
            'workflow': workflows['ASM001_2.0'],
            'process': processes['INSP001'],
            'sequence_order': 3,
            'setup_time': 30,
            'cycle_time': 120,
            'connecting_count': 5,
            'control_gauge': gauge,
            'instructions': 'Check all critical dimensions per QC checklist'
        }
    ]
    
    for config_data in process_configs_data:
        config, created = ProcessConfig.objects.get_or_create(
            workflow=config_data['workflow'],
            sequence_order=config_data['sequence_order'],
            defaults=config_data
        )
        if created:
            print(f"   Created process config: {config.workflow.product.stock_code} - Step {config.sequence_order}")
    
    print("✅ Process configurations created")
    
    # Create Sales Orders
    sales_order, created = SalesOrder.objects.get_or_create(
        order_number='SO-2024-0056',
        defaults={
            'customer': customer,
            'customer_po_number': 'PO-ACME-2024-001',
            'salesperson': admin_user,
            'shipping_address': '123 Industrial Ave, Manufacturing City, MC 12345',
            'billing_address': '123 Industrial Ave, Manufacturing City, MC 12345',
            'notes': 'Rush order for Q1 production'
        }
    )
    
    # Create Sales Order Items
    sales_order_items_data = [
        {
            'sales_order': sales_order,
            'product': products['ASM001'],
            'quantity': 10,
            'delivery_date': timezone.now().date() + timedelta(days=15),
            'status': 'CONFIRMED',
            'notes': 'High priority customer order'
        },
        {
            'sales_order': sales_order,
            'product': products['PRT001'],
            'quantity': 50,
            'delivery_date': timezone.now().date() + timedelta(days=10),
            'status': 'CONFIRMED',
            'notes': 'Extra brackets for maintenance stock'
        }
    ]
    
    sales_order_items = []
    for item_data in sales_order_items_data:
        item, created = SalesOrderItem.objects.get_or_create(
            sales_order=item_data['sales_order'],
            product=item_data['product'],
            defaults=item_data
        )
        sales_order_items.append(item)
        if created:
            print(f"   Created sales order item: {item.product.stock_code} x {item.quantity}")
    
    print("✅ Sales orders created")
    
    # Create Work Orders
    work_orders_data = [
        {
            'work_order_number': 'WO-2024-001234',
            'product': products['ASM001'],
            'quantity_ordered': 10,
            'planned_start_date': timezone.now() + timedelta(days=1),
            'planned_end_date': timezone.now() + timedelta(days=7),
            'status': 'PLANNED',
            'priority': 'HIGH',
            'sales_order': sales_order,
            'primary_machine': machines['CNC001'],
            'notes': 'Rush order for important customer'
        },
        {
            'work_order_number': 'WO-2024-001235',
            'product': products['PRT001'],
            'quantity_ordered': 50,
            'planned_start_date': timezone.now(),
            'planned_end_date': timezone.now() + timedelta(days=3),
            'status': 'RELEASED',
            'priority': 'MEDIUM',
            'sales_order': sales_order,
            'primary_machine': machines['CNC001'],
            'notes': 'Standard production run'
        }
    ]
    
    work_orders = []
    for wo_data in work_orders_data:
        work_order, created = WorkOrder.objects.get_or_create(
            work_order_number=wo_data['work_order_number'],
            defaults=wo_data
        )
        work_orders.append(work_order)
        if created:
            print(f"   Created work order: {work_order.work_order_number}")
    
    print("✅ Work orders created")
    
    # Create Work Order Operations
    operations_data = [
        {
            'work_order': work_orders[0],
            'operation_sequence': 1,
            'operation_name': 'CNC Machining - Brackets',
            'machine': machines['CNC001'],
            'planned_start_date': work_orders[0].planned_start_date,
            'planned_end_date': work_orders[0].planned_start_date + timedelta(days=3),
            'setup_time_minutes': 120,
            'run_time_minutes': 2400,
            'status': 'PLANNED',
            'assigned_to': operator_user
        },
        {
            'work_order': work_orders[0],
            'operation_sequence': 2,
            'operation_name': 'Assembly Process',
            'machine': machines['ASM001'],
            'planned_start_date': work_orders[0].planned_start_date + timedelta(days=3),
            'planned_end_date': work_orders[0].planned_end_date,
            'setup_time_minutes': 60,
            'run_time_minutes': 1800,
            'status': 'PLANNED',
            'assigned_to': operator_user
        }
    ]
    
    for op_data in operations_data:
        operation, created = WorkOrderOperation.objects.get_or_create(
            work_order=op_data['work_order'],
            operation_sequence=op_data['operation_sequence'],
            defaults=op_data
        )
        if created:
            print(f"   Created operation: {operation.work_order.work_order_number} - {operation.operation_name}")
    
    print("✅ Work order operations created")
    
    # Create Material Allocations
    allocations_data = [
        {
            'work_order': work_orders[0],
            'material': products['PRT001'],
            'required_quantity': Decimal('26.25'),  # 10 * 2.5 * 1.05 (scrap)
            'allocated_quantity': Decimal('26.25'),
            'is_allocated': True,
            'allocation_date': timezone.now()
        },
        {
            'work_order': work_orders[0],
            'material': products['SUB001'],
            'required_quantity': Decimal('10.20'),  # 10 * 1.0 * 1.02 (scrap)
            'allocated_quantity': Decimal('10.20'),
            'is_allocated': True,
            'allocation_date': timezone.now()
        }
    ]
    
    for alloc_data in allocations_data:
        allocation, created = MaterialAllocation.objects.get_or_create(
            work_order=alloc_data['work_order'],
            material=alloc_data['material'],
            defaults=alloc_data
        )
        if created:
            print(f"   Created allocation: {allocation.material.stock_code} for {allocation.work_order.work_order_number}")
    
    print("✅ Material allocations created")
    
    # Create some Machine Downtime records
    downtime_data = [
        {
            'machine': machines['CNC001'],
            'start_time': timezone.now() - timedelta(days=2, hours=4),
            'end_time': timezone.now() - timedelta(days=2, hours=2),
            'reason': 'Tool change and setup',
            'category': 'SETUP',
            'reported_by': operator_user,
            'notes': 'Routine tool change for new job'
        },
        {
            'machine': machines['CNC002'],
            'start_time': timezone.now() - timedelta(days=1, hours=8),
            'end_time': timezone.now() - timedelta(days=1, hours=6),
            'reason': 'Preventive maintenance',
            'category': 'MAINTENANCE',
            'reported_by': engineer_user,
            'notes': 'Scheduled maintenance completed'
        }
    ]
    
    for dt_data in downtime_data:
        downtime, created = MachineDowntime.objects.get_or_create(
            machine=dt_data['machine'],
            start_time=dt_data['start_time'],
            defaults=dt_data
        )
        if created:
            print(f"   Created downtime: {downtime.machine.machine_code} - {downtime.reason}")
    
    print("✅ Machine downtime records created")
    
    print("\n🎉 Dummy data creation completed successfully!")
    print("\nCreated data summary:")
    print(f"   - {User.objects.count()} Users")
    print(f"   - {Product.objects.count()} Products")
    print(f"   - {Machine.objects.count()} Machines")
    print(f"   - {ProductBOM.objects.count()} BOM Items")
    print(f"   - {WorkOrder.objects.count()} Work Orders")
    print(f"   - {WorkOrderOperation.objects.count()} Operations")
    print(f"   - {MaterialAllocation.objects.count()} Material Allocations")
    print(f"   - {ProductWorkflow.objects.count()} Product Workflows")
    print(f"   - {ProcessConfig.objects.count()} Process Configurations")
    print(f"   - {SalesOrder.objects.count()} Sales Orders")
    print(f"   - {SalesOrderItem.objects.count()} Sales Order Items")
    
    print("\n📋 Test user credentials:")
    print("   Admin: admin / admin123")
    print("   Operator: operator1 / (set password in Django admin)")
    print("   Engineer: engineer1 / (set password in Django admin)")

if __name__ == '__main__':
    create_dummy_data() 