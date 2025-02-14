from django.core.management.base import BaseCommand
from django.utils import timezone
from inventory.models import Product
from manufacturing.models import BOM, BOMComponent, BOMProcessConfig, ManufacturingProcess

class Command(BaseCommand):
    help = 'Add a sample BOM and BOM components for a semi-finished product.'

    def handle(self, *args, **options):
        # Retrieve a sample semi-finished product
        semi_product = Product.objects.filter(product_type='SEMI').first()
        if not semi_product:
            self.stdout.write(
                self.style.ERROR("No semi-finished product found. Please add one before running this command.")
            )
            return

        # Create a BOM for the semi-finished product
        bom, created = BOM.objects.get_or_create(
            product=semi_product,
            defaults={
                'version': '1.0',
                'created_at': timezone.now(),
                'modified_at': timezone.now(),
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created BOM for product: {semi_product.product_code}"))
        else:
            self.stdout.write(f"BOM already exists for product: {semi_product.product_code}")

        # Retrieve a specific manufacturing process for the BOM component (e.g., Cutting – PR001)
        process = ManufacturingProcess.objects.filter(process_code='PR001').first()
        if not process:
            self.stdout.write(
                self.style.ERROR("No manufacturing process with code 'PR001' found. Please add one before running this command.")
            )
            return

        # Create a BOM process configuration if needed (assumes BOMProcessConfig exists)
        bom_process_config, created_config = BOMProcessConfig.objects.get_or_create(
            process=process,
            defaults={
                'setup_time': 5,
                'run_time': 20,
                'quantity': "100.00",
                'additional_notes': "Sample configuration",
            }
        )
        if created_config:
            self.stdout.write(self.style.SUCCESS(f"Created BOM Process Config for process: {process.process_code}"))
        else:
            self.stdout.write(f"BOM Process Config already exists for process: {process.process_code}")

        # Create a BOM component linking the BOM, the semi-finished product, and the BOM process configuration
        bom_component, created_comp = BOMComponent.objects.get_or_create(
            bom=bom,
            semi_product=semi_product,
            process_config=bom_process_config,
            defaults={
                'component_type': 'SEMI_PRODUCT',
                'quantity': "100.00",
                'sequence_order': 1,
            }
        )
        if created_comp:
            self.stdout.write(self.style.SUCCESS("Created BOM component for the BOM."))
        else:
            self.stdout.write("BOM component already exists for the BOM.") 