from django.core.management.base import BaseCommand
from django.utils import timezone
from inventory.models import Product
from manufacturing.models import BOM, BOMComponent, ManufacturingProcess, WorkflowProcess

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

        # Create a workflow process if needed
        workflow_process, created_workflow = WorkflowProcess.objects.get_or_create(
            process=process,
            product=semi_product,
            defaults={
                'process_number': f"{semi_product.product_code}-PR001",
                'stock_code': f"{semi_product.product_code}-PR001",
                'estimated_duration_minutes': 25,
                'tooling_requirements': "Cutting Tool, Measuring Tool",
                'quality_checks': "Dimension Check, Surface Finish Check",
                'sequence_order': 1
            }
        )
        if created_workflow:
            self.stdout.write(self.style.SUCCESS(f"Created Workflow Process for process: {process.process_code}"))
        else:
            self.stdout.write(f"Workflow Process already exists for process: {process.process_code}")

        # Create a BOM component
        component, created_comp = BOMComponent.objects.get_or_create(
            bom=bom,
            material=workflow_process.raw_material,
            defaults={
                'quantity': "100.00",
                'sequence_order': 1,
                'notes': "Sample component"
            }
        )
        if created_comp:
            self.stdout.write(self.style.SUCCESS("Created component for the BOM."))
        else:
            self.stdout.write("Component already exists for the BOM.") 