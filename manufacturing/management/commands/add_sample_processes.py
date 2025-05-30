from django.core.management.base import BaseCommand
from manufacturing.models import ManufacturingProcess

class Command(BaseCommand):
    help = 'Add sample manufacturing processes for testing purposes.'

    def handle(self, *args, **options):
        sample_processes = [
            {
                'process_code': 'PR001',
                'process_name': 'Cutting'
            },
            {
                'process_code': 'PR002',
                'process_name': 'Welding'
            },
            {
                'process_code': 'PR003',
                'process_name': 'Quality Check'
            }
        ]

        for process_data in sample_processes:
            process, created = ManufacturingProcess.objects.get_or_create(
                process_code=process_data['process_code'],
                defaults=process_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created manufacturing process: {process}"))
            else:
                self.stdout.write(f"Manufacturing process already exists: {process}") 