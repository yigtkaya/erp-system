from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from inventory.models import Product, InventoryCategory
from erp_core.models import ProductType

class Command(BaseCommand):
    help = "Add sample products: a normal product and a standard part, for testing purposes."

    def handle(self, *args, **options):
        try:
            # Get the allowed inventory category for standard parts (e.g., HAMMADDE)
            standard_category = InventoryCategory.objects.get(name='HAMMADDE')
            # Get an inventory category for the normal product (change the category as suitable for your test data)
            normal_category = InventoryCategory.objects.get(name='MAMUL')
        except InventoryCategory.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"Required inventory category not found: {e}"))
            return

        # Create normal product (e.g., a montaged product)
        normal_product, created = Product.objects.get_or_create(
            product_code='P005',
            defaults={
                'product_name': 'Custom Wheel',
                'product_type': 'MONTAGED',  # You can also use ProductType.MONTAGED
                'current_stock': 30,
                'inventory_category': normal_category,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Normal product added: {normal_product}"))
        else:
            self.stdout.write(f"Normal product already exists: {normal_product}")

        # Create a standard part product
        standard_part, created = Product.objects.get_or_create(
            product_code='SP001',
            defaults={
                'product_name': 'Standard Bolt',
                'product_type': ProductType.STANDARD_PART,
                'current_stock': 150,
                'inventory_category': standard_category,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Standard part added: {standard_part}"))
        else:
            self.stdout.write(f"Standard part already exists: {standard_part}") 