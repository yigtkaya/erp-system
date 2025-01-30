from django.core.management.base import BaseCommand
from erp_core.models import Customer
from inventory.models import InventoryCategory, UnitOfMeasure, Product, RawMaterial
from manufacturing.models import Machine, ManufacturingProcess, MachineType

class Command(BaseCommand):
    help = 'Sets up initial data for the ERP system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')

        # Create inventory categories
        categories = [
            {'name': 'HAMMADDE', 'description': 'Raw Materials'},
            {'name': 'MAMUL', 'description': 'Finished Products'},
            {'name': 'PROSES', 'description': 'Work in Progress'},
            {'name': 'KARANTINA', 'description': 'Items needing decision'},
            {'name': 'HURDA', 'description': 'Scrap items'},
            {'name': 'TAKIMHANE', 'description': 'Tool storage'},
        ]

        for category in categories:
            InventoryCategory.objects.get_or_create(
                name=category['name'],
                defaults={'description': category['description']}
            )

        # Create units of measure
        units = [
            {'unit_code': 'PCS', 'unit_name': 'Pieces'},
            {'unit_code': 'KG', 'unit_name': 'Kilograms'},
            {'unit_code': 'M', 'unit_name': 'Meters'},
            {'unit_code': 'L', 'unit_name': 'Liters'},
        ]

        for unit in units:
            UnitOfMeasure.objects.get_or_create(
                unit_code=unit['unit_code'],
                defaults={'unit_name': unit['unit_name']}
            )

        # Create raw materials
        hammadde_category = InventoryCategory.objects.get(name='HAMMADDE')
        kg_unit = UnitOfMeasure.objects.get(unit_code='KG')

        raw_materials = [
            {'material_code': 'RM001', 'material_name': 'Steel Sheet', 'current_stock': 1000},
            {'material_code': 'RM002', 'material_name': 'Aluminum Bar', 'current_stock': 500},
            {'material_code': 'RM003', 'material_name': 'Plastic Granules', 'current_stock': 2000},
        ]

        for material in raw_materials:
            RawMaterial.objects.get_or_create(
                material_code=material['material_code'],
                defaults={
                    'material_name': material['material_name'],
                    'current_stock': material['current_stock'],
                    'unit': kg_unit,
                    'inventory_category': hammadde_category
                }
            )

        # Create products
        mamul_category = InventoryCategory.objects.get(name='MAMUL')
        pcs_unit = UnitOfMeasure.objects.get(unit_code='PCS')

        products = [
            {'product_code': 'P001', 'product_name': 'Metal Cabinet', 'current_stock': 50},
            {'product_code': 'P002', 'product_name': 'Aluminum Frame', 'current_stock': 100},
            {'product_code': 'P003', 'product_name': 'Plastic Container', 'current_stock': 200},
        ]

        for product in products:
            Product.objects.get_or_create(
                product_code=product['product_code'],
                defaults={
                    'product_name': product['product_name'],
                    'product_type': 'MONTAGED',
                    'current_stock': product['current_stock'],
                    'unit': pcs_unit,
                    'inventory_category': mamul_category
                }
            )

        # Create machines
        machines = [
            {'machine_code': 'M001', 'machine_type': 'MILLING', 'brand': 'DMG MORI', 'model': 'NMV5000'},
            {'machine_code': 'M002', 'machine_type': 'LATHE', 'brand': 'HAAS', 'model': 'ST-20'},
            {'machine_code': 'M003', 'machine_type': 'DRILL', 'brand': 'Makita', 'model': 'DP1500'},
        ]

        for machine in machines:
            Machine.objects.get_or_create(
                machine_code=machine['machine_code'],
                defaults={
                    'machine_type': machine['machine_type'],
                    'brand': machine['brand'],
                    'model': machine['model'],
                    'status': 'AVAILABLE'
                }
            )

        # Create manufacturing processes
        processes = [
            {'process_code': 'PR001', 'process_name': 'Cutting', 'standard_time_minutes': 30, 'machine_type': 'MILLING'},
            {'process_code': 'PR002', 'process_name': 'Assembly', 'standard_time_minutes': 45, 'machine_type': 'LATHE'},
            {'process_code': 'PR003', 'process_name': 'Quality Check', 'standard_time_minutes': 15, 'machine_type': 'DRILL'},
        ]

        for process in processes:
            ManufacturingProcess.objects.get_or_create(
                process_code=process['process_code'],
                defaults={
                    'process_name': process['process_name'],
                    'standard_time_minutes': process['standard_time_minutes'],
                    'machine_type': process['machine_type']
                }
            )

        # Create customers
        customers = [
            {'code': 'C001', 'name': 'ABC Corporation'},
            {'code': 'C002', 'name': 'XYZ Industries'},
            {'code': 'C003', 'name': 'Global Manufacturing'},
        ]

        for customer in customers:
            Customer.objects.get_or_create(
                code=customer['code'],
                name=customer['name']
            )

        self.stdout.write(self.style.SUCCESS('Successfully set up initial data')) 