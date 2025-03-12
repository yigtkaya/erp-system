from django.core.management.base import BaseCommand
from manufacturing.models import ManufacturingProcess

class Command(BaseCommand):
    help = 'Loads manufacturing processes into the database'

    def handle(self, *args, **options):
        processes = [
            {'process_code': 'OP10', 'process_name': 'Malzeme Girişi'},
            {'process_code': 'OP10-1', 'process_name': 'Hammadde / Yarımamul Kabulü'},
            {'process_code': 'OP20', 'process_name': 'Talaşlı İmalat'},
            {'process_code': 'OP20-1', 'process_name': 'Talaşlı İmalat 1'},
            {'process_code': 'OP30', 'process_name': 'Tesviye'},
            {'process_code': 'OP30-1', 'process_name': 'Matkap Salma'},
            {'process_code': 'OP30-2', 'process_name': 'Zımparalama'},
            {'process_code': 'OP30-3', 'process_name': 'Parlatma'},
            {'process_code': 'OP40', 'process_name': 'Lazer Markalama'},
            {'process_code': 'OP50', 'process_name': 'Isıl İşlem'},
            {'process_code': 'OP60', 'process_name': 'Çapak Alma'},
            {'process_code': 'OP70', 'process_name': 'Kumlama'},
            {'process_code': 'OP80', 'process_name': 'Kaplama'},
            {'process_code': 'OP90', 'process_name': 'Boyama'},
            {'process_code': 'OP80-1', 'process_name': 'QPQ'},
            {'process_code': 'OP100', 'process_name': 'Montaj'},
            {'process_code': 'OP110', 'process_name': 'Son Kontrol & Paketleme'},
            {'process_code': 'OP120', 'process_name': 'Depolama & Sevkiyat'},
        ]

        created_count = 0
        for process in processes:
            _, created = ManufacturingProcess.objects.get_or_create(
                process_code=process['process_code'],
                defaults={
                    'process_name': process['process_name']
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {created_count} manufacturing processes')) 