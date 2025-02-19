from django.core.management.base import BaseCommand
from manufacturing.models import ManufacturingProcess, MachineType

class Command(BaseCommand):
    help = 'Loads manufacturing processes into the database'

    def handle(self, *args, **options):
        processes = [
            {'process_code': 'OP10', 'process_name': 'Malzeme Girişi', 'standard_time_minutes': 15},
            {'process_code': 'OP10-1', 'process_name': 'Hammadde / Yarımamul Kabulü', 'standard_time_minutes': 30},
            {'process_code': 'OP20', 'process_name': 'Talaşlı İmalat', 'standard_time_minutes': 120},
            {'process_code': 'OP20-1', 'process_name': 'Talaşlı İmalat 1', 'standard_time_minutes': 90},
            {'process_code': 'OP30', 'process_name': 'Tesviye', 'standard_time_minutes': 45},
            {'process_code': 'OP30-1', 'process_name': 'Matkap Salma', 'standard_time_minutes': 20},
            {'process_code': 'OP30-2', 'process_name': 'Zımparalama', 'standard_time_minutes': 30},
            {'process_code': 'OP30-3', 'process_name': 'Parlatma', 'standard_time_minutes': 25},
            {'process_code': 'OP40', 'process_name': 'Lazer Markalama', 'standard_time_minutes': 10},
            {'process_code': 'OP50', 'process_name': 'Isıl İşlem', 'standard_time_minutes': 180},
            {'process_code': 'OP60', 'process_name': 'Çapak Alma', 'standard_time_minutes': 15},
            {'process_code': 'OP70', 'process_name': 'Kumlama', 'standard_time_minutes': 45},
            {'process_code': 'OP80', 'process_name': 'Kaplama', 'standard_time_minutes': 60},
            {'process_code': 'OP90', 'process_name': 'Boyama', 'standard_time_minutes': 90},
            {'process_code': 'OP80-1', 'process_name': 'QPQ', 'standard_time_minutes': 150},
            {'process_code': 'OP100', 'process_name': 'Montaj', 'standard_time_minutes': 240},
            {'process_code': 'OP110', 'process_name': 'Son Kontrol & Paketleme', 'standard_time_minutes': 30},
            {'process_code': 'OP120', 'process_name': 'Depolama & Sevkiyat', 'standard_time_minutes': 20},
        ]

        created_count = 0
        for process in processes:
            _, created = ManufacturingProcess.objects.get_or_create(
                process_code=process['process_code'],
                defaults={
                    'process_name': process['process_name'],
                    'standard_time_minutes': process['standard_time_minutes'],
                    'machine_type': MachineType.PROCESSING_CENTER
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {created_count} manufacturing processes')) 