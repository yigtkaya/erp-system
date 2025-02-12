from django.core.management.base import BaseCommand
from inventory.models import UnitOfMeasure

class Command(BaseCommand):
    help = "Adds sample units (Meter and Kilos) to the database."

    def handle(self, *args, **options):
        self.stdout.write("Adding sample units...")

        units = [
            {'unit_code': 'KG', 'unit_name': 'Kilos'},
            {'unit_code': 'M', 'unit_name': 'Meter'},
        ]

        for unit in units:
            obj, created = UnitOfMeasure.objects.get_or_create(
                unit_code=unit['unit_code'],
                defaults={'unit_name': unit['unit_name']}
            )
            if created:
                self.stdout.write(f"Created unit: {obj}")
            else:
                self.stdout.write(f"Unit already exists: {obj}")

        self.stdout.write(self.style.SUCCESS("Sample units added successfully.")) 