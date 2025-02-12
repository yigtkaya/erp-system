from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from inventory.models import Product, InventoryCategory
from erp_core.models import ProductType  # TextChoices enum

class Command(BaseCommand):
    help = "Adds sample standard parts to the database."

    def handle(self, *args, **options):
        self.stdout.write("Adding sample standard parts...")

        try:
            hammadde_category = InventoryCategory.objects.get(name='HAMMADDE')
        except InventoryCategory.DoesNotExist:
            self.stdout.write(self.style.ERROR("InventoryCategory 'HAMMADDE' does not exist. Please create it first."))
            return

        # Use the enum value from ProductType for standard parts
        standard_product_type = ProductType.STANDARD_PART

        sample_products = [
            {
                'product_code': 'SP001',
                'product_name': 'Standard Part A',
                'inventory_category': hammadde_category,
                'current_stock': 100,
                'product_type': standard_product_type,
            },
            {
                'product_code': 'SP002',
                'product_name': 'Standard Part B',
                'inventory_category': hammadde_category,
                'current_stock': 150,
                'product_type': standard_product_type,
            },
            {
                'product_code': 'SP003',
                'product_name': 'Standard Part C',
                'inventory_category': hammadde_category,
                'current_stock': 75,
                'product_type': standard_product_type,
            },
        ]

        created_count = 0
        for product_data in sample_products:
            product_code = product_data.get('product_code')
            if Product.objects.filter(product_code=product_code).exists():
                self.stdout.write(f"Product with code {product_code} already exists, skipping.")
                continue

            product = Product.objects.create(**product_data)
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"Created product {product.product_name} with code {product.product_code}"))

        self.stdout.write(self.style.SUCCESS(f"Total {created_count} standard parts added successfully.")) 