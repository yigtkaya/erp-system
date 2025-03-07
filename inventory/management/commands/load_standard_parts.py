from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from inventory.models import Product, InventoryCategory
from erp_core.models import Customer

class Command(BaseCommand):
    help = 'Loads standard parts data into the database'

    def handle(self, *args, **options):
        self.stdout.write('Loading standard parts data...')

        try:
            with transaction.atomic():
                # Get or create the HAMMADDE category
                hammadde_category, _ = InventoryCategory.objects.get_or_create(
                    name='HAMMADDE',
                    defaults={'description': 'Raw Materials and Standard Parts'}
                )

                # Standard parts data
                products_data = [
                        {
        "product_code": "02.BİL.Ø02.50",
        "product_name": "Ø 2",
        "description": "A6-181",
        "current_stock": 100
    },
    {
        "product_code": "02.BİL.Ø03.00",
        "product_name": "Ø 3 Gez Yan Tambur Bilyası",
        "description": "DIN 5401",
        "current_stock": 100
    },
    {
        "product_code": "02.PİM.DÜZ.Ø01.50X06.00",
        "product_name": "1",
        "description": "207348-14",
        "current_stock": 100
    },
    {
        "product_code": "02.PİM.SPİ.Ø01.50x10.00",
        "product_name": "Ø 1",
        "description": "207348-5",
        "current_stock": 100
    },
    {
        "product_code": "02.PİM.SPİ.Ø02.00x12.00",
        "product_name": "Ø 2 X 12 mm Spiral Pim",
        "description": "DIN 7343",
        "current_stock": 100
    },
    {
        "product_code": "02.PİM.SPİ.Ø02.00x22.00",
        "product_name": "Ø 2 X 22 mm Spiral Pim",
        "description": "DIN 7343",
        "current_stock": 100
    },
    {
        "product_code": "02.PİM.SPİ.Ø02.50x14.00",
        "product_name": "Ø 2.5 x 14 mm St Spiral Pim",
        "description": "DIN 7343",
        "current_stock": 100
    },
    {
        "product_code": "02.PİM.YAR.Ø01.50x08.00",
        "product_name": "1",
        "description": "KCR5-A3-3.01.07.00",
        "current_stock": 100
    },
    {
        "product_code": "02.PİM.YAR.Ø01.50x10.00",
        "product_name": "Ø 1",
        "description": "DIN 1481",
        "current_stock": 100
    },
    {
        "product_code": "02.PİM.YAR.Ø01.50x12.00",
        "product_name": "Ø 1.5 X 12 mm Yarıklı Pim",
        "description": "DIN 1481",
        "current_stock": 100
    },
    {
        "product_code": "02.PİM.YAR.Ø01.50x14.00",
        "product_name": "Ø 1",
        "description": "KCR5-A1-3.01.00.09",
        "current_stock": 100
    },
    {
        "product_code": "02.PİM.YAR.Ø02.00x12.00",
        "product_name": "Ø 2 x 12 mm St Yarikli Pim",
        "description": "DIN 1481",
        "current_stock": 100
    },
    {
        "product_code": "02.PUL.ÇAN.Ø05.20x10x0.5",
        "product_name": "5",
        "description": "5 Çanak Pul",
        "current_stock": 100
    },
    {
        "product_code": "02.PUL.DÜZ.M4",
        "product_name": "M4 Pul",
        "description": "SP",
        "current_stock": 100
    },
    {
        "product_code": "02.PUL.TIR.M4",
        "product_name": "Tırtıllı Rondela DIN 6798-V 4",
        "description": "A6-199",
        "current_stock": 100
    },
    {
        "product_code": "02.SEG.Ø05.00",
        "product_name": "ARPACIK MİL SEGMANI - Q5 İÇİN",
        "description": "DIN 471",
        "current_stock": 100
    },
    {
        "product_code": "02.SEG.Ø07.50",
        "product_name": "ÇELİK TIRNAKLI SEGMAN - İTALYAN 07.50X15.5X0.4",
        "description": "Beneri D02 Tırnaklı Segman (İtalyan Malı)",
        "current_stock": 100
    },
    {
        "product_code": "02.SEG.Ø08.00",
        "product_name": "GEZ KULE SEGMANI - 8 LİK",
        "description": "BLN-KCR5-A1-3.01.00.16 Gez Kule Segman_Rev0",
        "current_stock": 100
    },
    {
        "product_code": "02.VİD.M2.5X05",
        "product_name": "M2",
        "description": "A6-",
        "current_stock": 100
    },
    {
        "product_code": "02.VİD.M2.5X10",
        "product_name": "M2",
        "description": "207348-4",
        "current_stock": 100
    },
    {
        "product_code": "02.VİD.M4X06",
        "product_name": "M4 X 6 mm YAN AYAR KLİK VİDASI",
        "description": "DIN 916",
        "current_stock": 100
    },
    {
        "product_code": "02.VİD.M4X08",
        "product_name": "M4 X 8 mm Vida",
        "description": "DIN965",
        "current_stock": 100
    },
    {
        "product_code": "02.VİD.M4X14",
        "product_name": "M4 X 14 mm INBUS",
        "description": "DIN 912",
        "current_stock": 100
    },
    {
        "product_code": "02.VİD.M4X30",
        "product_name": "M4X30 Sıkma Vidası",
        "description": "DIN 2076-D- Ø0.50 -1.1211",
        "current_stock": 100
    },
    {
        "product_code": "02.VİD.M5X20",
        "product_name": "M5 X 20 mm INBUS HAVSA BAŞLI",
        "description": "DIN 7991",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ00.40L05.50Dİ01.70",
        "product_name": "KLİK YAYI - GEZ İÇİN (kapsam 7)",
        "description": "KAPSAM 07",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ00.40L07.50Dİ01.55",
        "product_name": "Arpacık Ara Ayar Somunu Klik Yayı",
        "description": "KAPSAM 14",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ00.40L08.00Dİ01.70",
        "product_name": "Gez Kule Klik Yayı (Kapsam 13)",
        "description": "BLN-KCR5-A1-3.01.00.07 Gez Kule Bilya Yayı_Rev0",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ00.40L09.00Dİ01.70",
        "product_name": "YAY - GEZ UCU KONUMLAMA DİLİ İÇİN (kapsam 10)",
        "description": "KAPSAM 10",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ00.45L03.50Dİ01.90",
        "product_name": "Pul Kilit Yayı",
        "description": "KAPSAM 26",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ00.45L07.50Dİ01.90",
        "product_name": "Gez Yan Tambur Klik Yayı (Kapsam 16)",
        "description": "KAPSAM 16",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ00.45L11.00Dİ01.40",
        "product_name": "KLİK BİLYASI YAYI (kapsam 8)",
        "description": "KAPSAM 08",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ00.50L05.10Dİ01.50",
        "product_name": "0.50 BASMA YAY - KAPSAM27",
        "description": "KAPSAM 27",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ00.50L05.50Dİ01.50",
        "product_name": "Kule Kilit Dili İçin Konumlama Yayı",
        "description": "KAPSAM 21",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ00.50L08.50Dİ02.20",
        "product_name": "Kule Kilit Dili Yayı (Kapsam 15)",
        "description": " BLN-KCR5-A1-3.01.00.10 Gez Kilit Dili Yayı_Rev0",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ00.50L13.50Dİ02.20",
        "product_name": "Gez Ucu Baskı Yayı (Kapsam 4)",
        "description": "BLN-KCR5-A1-3.01.00.14 Gez Kule Yayı_Rev0",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ00.50L22.00Dİ02.30",
        "product_name": "GEZ YAYI (kapsam 6)",
        "description": "KAPSAM 06",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ00.55L25.40Dİ03.80",
        "product_name": "BASKI YAYI - ARPACIK KİLİDİ İÇİN (kapsam 3)",
        "description": "KAPSAM 03",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ00.60L05.50Dİ05.95",
        "product_name": "YAY - GEZ YAN AYAR TAMBURU İÇİN (kapsam 20)",
        "description": "KAPSAM 20",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ00.60L07.50Dİ05.25",
        "product_name": "Arpacık Klik Yayı",
        "description": "KAPSAM 25",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ00.80L07.40Dİ05.30",
        "product_name": "Arpacık Ara Ayar Somun Yayı",
        "description": "KAPSAM 28",
        "current_stock": 100
    },
    {
        "product_code": "02.YAYØ01.60L15.20Dİ11.80",
        "product_name": "Nişangah Hamili Konum Yayı",
        "description": "KAPSAM 35",
        "current_stock": 100
    },
                    {
                        'product_code': '02.BİL.Ø02.00',
                        'product_name': 'Ø 2 G80 1.3541 580-700 HV10 Bilya',
                        'description': 'DIN 5401',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.BİL.Ø02.50',
                        'product_name': 'Ø 2,5 Klik Bilyası G10',
                        'description': 'DIN 5401',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.BİL.Ø03.00',
                        'product_name': 'Ø 3 Gez Yan Tambur Bilyası',
                        'description': 'DIN 5401',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PİM.ÇEN.Ø04.00x10.00',
                        'product_name': 'Ø 4 X 10 mm Çentikli Pim',
                        'description': 'DIN 1472',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PİM.ÇEN.Ø04.00x20.00',
                        'product_name': 'Ø 4 X 20 mm Çentikli Pim',
                        'description': 'DIN 1472',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PİM.DÜZ.Ø01.50X06.00',
                        'product_name': 'Ø1,5 h8 KILITLEME KOLU İÇİN (düz)',
                        'description': 'DIN 7',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PİM.SPİ.Ø01.50x10.00',
                        'product_name': 'Ø 1,5 X 10 mm Spiral Pim',
                        'description': 'DIN 7343',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PİM.SPİ.Ø02.00x12.00',
                        'product_name': 'Ø 2 X 12 mm Spiral Pim',
                        'description': 'DIN 7343',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PİM.SPİ.Ø02.50x14.00',
                        'product_name': 'Ø 2.5 x 14 mm St Spiral Pim',
                        'description': 'DIN 7343',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PİM.YAR.Ø01.50x08.00',
                        'product_name': 'Ø 1,5 X 8 mm Yarıklı Pim',
                        'description': 'DIN 1481',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PİM.YAR.Ø01.50x10.00',
                        'product_name': 'Ø 1,5 X 10 mm Yarıklı Pim',
                        'description': 'DIN 1481',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PİM.YAR.Ø01.50x12.00',
                        'product_name': 'Ø 1.5 X 12 mm Yarıklı Pim',
                        'description': 'DIN 1481',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PİM.YAR.Ø01.50x14.00',
                        'product_name': 'Ø 1,5 X 14 mm Yarıklı Pim',
                        'description': 'DIN 1481',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PİM.YAR.Ø02.00x12.00',
                        'product_name': 'Ø 2 X 12 mm YARIKLI PİM',
                        'description': 'DIN 1481',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PİM.YAR.Ø02.00x16.00',
                        'product_name': 'Ø 2 x 16 mm H8 A2 Yarıklı Pim',
                        'description': 'DIN 1481',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PİM.YAR.Ø02.50x10.00',
                        'product_name': 'Ø 2,5 x 10 mm St Yarikli Pim',
                        'description': 'DIN 1481',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PİM.YAR.Ø04.00x16.00',
                        'product_name': 'Ø 4 x 16 mm St Yarikli Pim',
                        'description': 'DIN 1481',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PUL.ÇAN.Ø05.20x10x0.5',
                        'product_name': '5,2*10*0,5 Çanak Pul',
                        'description': 'DIN 2093-A',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PUL.DÜZ.M3',
                        'product_name': 'M3 Düz Rondela',
                        'description': 'DIN 125/A',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PUL.DÜZ.M4',
                        'product_name': 'M4 Pul',
                        'description': 'DIN 125/A',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PUL.LAY.M4',
                        'product_name': 'M4X8X050 LAYNER PUL',
                        'description': 'DIN 988',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PUL.TIR.M4',
                        'product_name': 'Tırtıllı Rondela DIN 6798-V 4,3',
                        'description': 'DIN 6798-V',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.PUL.YAY.Ø03.50x6.7X0.8',
                        'product_name': 'Ø 3.5 x 0.8 mm A2 Pul',
                        'description': 'DIN 127',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.SEG.Ø02.30',
                        'product_name': 'Ø 2.3 A2 Segman',
                        'description': 'DIN 6799',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.SEG.Ø05.00',
                        'product_name': 'ARPACIK MİL SEGMANI - Q5 İÇİN',
                        'description': 'DIN 471',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.SEG.Ø07.50',
                        'product_name': 'ÇELİK TIRNAKLI SEGMAN - İTALYAN 07.50X15.5X0.4',
                        'description': '-',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.SEG.Ø08.00',
                        'product_name': 'GEZ KULE SEGMANI - 8 LİK',
                        'description': 'DIN 471',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.VİD.M2.5X10',
                        'product_name': 'M2,5 X 10 mm A2 SETSKUR',
                        'description': 'DIN 913',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.VİD.M3X05',
                        'product_name': 'M3 x 5 mm A2 İmbus Vida',
                        'description': 'DIN 7984',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.VİD.M4X06',
                        'product_name': 'M4 X 6 mm YAN AYAR KLİK VİDASI',
                        'description': 'DIN 916',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.VİD.M4X08',
                        'product_name': 'M4 X 8 mm Vida',
                        'description': 'DIN 965',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.VİD.M4X14',
                        'product_name': 'M4 X 14 mm INBUS',
                        'description': 'DIN 912',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.VİD.M4X30',
                        'product_name': 'M4 X 30 mm GEZ - ARPACIK SIKMA VİDASI',
                        'description': 'DIN 2076',
                        'current_stock': 100
                    },
                    {
                        'product_code': '02.VİD.M5X20',
                        'product_name': 'M5 X 20 mm INBUS HAVSA BAŞLI',
                        'description': 'DIN 7991',
                        'current_stock': 100
                    }
                ]

                # Create products
                created_count = 0
                skipped_count = 0
                for product_data in products_data:
                    defaults = {
                        'product_name': product_data['product_name'],
                        'product_type': 'STANDARD_PART',
                        'description': product_data['description'],
                        'current_stock': product_data['current_stock'],
                        'inventory_category': hammadde_category,
                    }
                    
                    _, created = Product.objects.get_or_create(
                        product_code=product_data['product_code'],
                        defaults=defaults
                    )
                    if created:
                        created_count += 1
                        self.stdout.write(f"Created product: {product_data['product_code']}")
                    else:
                        skipped_count += 1
                        self.stdout.write(f"Skipped existing product: {product_data['product_code']}")

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully loaded standard parts data. '
                        f'Created: {created_count}, Skipped: {skipped_count}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading standard parts data: {str(e)}')
            )
            raise 