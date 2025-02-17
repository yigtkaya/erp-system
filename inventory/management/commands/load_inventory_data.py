from django.core.management.base import BaseCommand
from django.db import transaction
from inventory.models import InventoryCategory, UnitOfMeasure, Product, RawMaterial
from erp_core.models import ProductType, MaterialType, Customer

class Command(BaseCommand):
    help = 'Loads initial inventory data including products and raw materials'

    def handle(self, *args, **options):
        self.stdout.write('Loading inventory data...')

        try:
            with transaction.atomic():
                # Create inventory categories if they don't exist
                categories_data = [
                    ('HAMMADDE', 'Raw Materials and Standard Parts'),
                    ('PROSES', 'Unfinished/Semi Products'),
                    ('MAMUL', 'Finished and Single Products'),
                    ('KARANTINA', 'Items needing decision'),
                    ('HURDA', 'Scrap items'),
                    ('TAKIMHANE', 'Tool storage')
                ]

                categories = {}
                for name, description in categories_data:
                    category, created = InventoryCategory.objects.get_or_create(
                        name=name,
                        defaults={'description': description}
                    )
                    categories[name] = category
                    if created:
                        self.stdout.write(f'Created category: {name}')

                # Create units of measure if they don't exist
                units_data = [
                    ('PCS', 'Pieces'),
                    ('KG', 'Kilogram'),
                    ('M', 'Meter'),
                    ('M2', 'Square Meter'),
                    ('MM', 'Millimeter')
                ]

                units = {}
                for code, name in units_data:
                    unit, created = UnitOfMeasure.objects.get_or_create(
                        unit_code=code,
                        defaults={'unit_name': name}
                    )
                    units[code] = unit
                    if created:
                        self.stdout.write(f'Created unit: {code}')

                # Create raw materials
                raw_materials_data = [
                    {
                        'material_code': 'RM001',
                        'material_name': 'Steel Sheet 304',
                        'current_stock': 1000.00,
                        'unit': units['KG'],
                        'inventory_category': categories['HAMMADDE'],
                        'material_type': MaterialType.STEEL,
                        'width': 1000.0,
                        'height': 2000.0,
                        'thickness': 3.0,
                        'diameter_mm': None
                    },
                    {
                        'material_code': 'RM002',
                        'material_name': 'Aluminum Rod 6061',
                        'current_stock': 500.00,
                        'unit': units['KG'],
                        'inventory_category': categories['HAMMADDE'],
                        'material_type': MaterialType.ALUMINUM,
                        'width': None,
                        'height': None,
                        'thickness': None,
                        'diameter_mm': 25.4
                    }
                ]

                for material_data in raw_materials_data:
                    material, created = RawMaterial.objects.get_or_create(
                        material_code=material_data['material_code'],
                        defaults=material_data
                    )
                    if created:
                        self.stdout.write(f'Created raw material: {material.material_code}')

                # Create products
                products_data = [
                    {
                        'product_code': 'SP001',
                        'product_name': 'Basic Component A',
                        'product_type': ProductType.SINGLE,
                        'description': 'Basic component for various assemblies',
                        'current_stock': 100,
                        'customer': None,
                        'inventory_category': categories['HAMMADDE']
                    },
                    {
                        'product_code': 'SM001',
                        'product_name': 'Semi-Finished Assembly B',
                        'product_type': ProductType.SEMI,
                        'description': 'Semi-finished product for final assembly',
                        'current_stock': 50,
                        'customer': None,
                        'inventory_category': categories['PROSES']
                    },
                    {
                        'product_code': 'MP001',
                        'product_name': 'Final Product C',
                        'product_type': ProductType.MONTAGED,
                        'description': 'Complete assembled product',
                        'current_stock': 25,
                        'customer': None,
                        'inventory_category': categories['MAMUL']
                    }
                ]

                for product_data in products_data:
                    product, created = Product.objects.get_or_create(
                        product_code=product_data['product_code'],
                        defaults=product_data
                    )
                    if created:
                        self.stdout.write(f'Created product: {product.product_code}')

                self.stdout.write(self.style.SUCCESS('Successfully loaded all inventory data'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading inventory data: {str(e)}'))
            raise 