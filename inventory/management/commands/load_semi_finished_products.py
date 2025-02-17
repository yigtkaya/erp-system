from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from inventory.models import Product, InventoryCategory
from erp_core.models import Customer

class Command(BaseCommand):
    help = 'Loads semi-finished products data into the database'

    def handle(self, *args, **options):
        self.stdout.write('Loading semi-finished products data...')

        try:
            with transaction.atomic():
                # Get or create the PROSES category
                proses_category, _ = InventoryCategory.objects.get_or_create(
                    name='PROSES',
                    defaults={'description': 'Unfinished/Semi Products'}
                )

                # Get or create customers
                kk_customer, _ = Customer.objects.get_or_create(
                    code='KKCO',
                    defaults={'name': 'KK Customer'}
                )
                ss_customer, _ = Customer.objects.get_or_create(
                    code='SSCO',
                    defaults={'name': 'SS Customer'}
                )

                # Semi-finished products data
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
        "product_code": "03.0.00.0035.00.00.00",
        "product_name": "KCR556 739 Gez Kamlı Tambur",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.01.0002.00.00.00",
        "product_name": "GEZ TAMBURU KAİDESi",
        "description": "A6-177",
        "current_stock": 100
    },
    {
        "product_code": "03.0.01.0003.00.00.00",
        "product_name": "GEZ TAMBURU",
        "description": "A6-178",
        "current_stock": 100
    },
    {
        "product_code": "03.0.01.0004.00.00.00",
        "product_name": "GEZ UCU",
        "description": "A6-180",
        "current_stock": 100
    },
    {
        "product_code": "03.0.01.0006.00.00.00",
        "product_name": "YÜKSEKLİK AYAR PARÇASI",
        "description": "A6-183",
        "current_stock": 100
    },
    {
        "product_code": "03.0.01.0008.00.00.00",
        "product_name": "YAN AYAR TAMBURU - GEZ İÇİN",
        "description": "A6-185",
        "current_stock": 100
    },
    {
        "product_code": "03.0.01.0009.00.00.00",
        "product_name": "KONUMLAMA YÜKSÜĞÜ - GEZ İÇİN",
        "description": "A6-186",
        "current_stock": 100
    },
    {
        "product_code": "03.0.01.0010.00.00.00",
        "product_name": "YAN AYAR YÜKSÜK KAPAĞI - GEZ İÇİN",
        "description": "A6-187",
        "current_stock": 100
    },
    {
        "product_code": "03.0.01.0011.00.00.00",
        "product_name": "YAN AYAR VİDASI - GEZ İÇİN",
        "description": "A6-188",
        "current_stock": 100
    },
    {
        "product_code": "03.0.01.0014.00.00.00",
        "product_name": "ALT KAİDE - GEZ İÇİN",
        "description": "A6-193",
        "current_stock": 100
    },
    {
        "product_code": "03.0.01.0015.00.00.00",
        "product_name": "KİLİT PABUCU - GEZ İÇİN",
        "description": "A6-194",
        "current_stock": 100
    },
    {
        "product_code": "03.0.01.0016.00.00.00",
        "product_name": "BAĞLAMA VİDASI - GEZ İÇİN",
        "description": "A6-195",
        "current_stock": 100
    },
    {
        "product_code": "03.0.01.0017.00.00.00",
        "product_name": "KONUM PARÇASI - GEZ İÇİN",
        "description": "A6-197",
        "current_stock": 100
    },
    {
        "product_code": "03.0.02.0001.00.00.00",
        "product_name": "ARPACIK HAMİLİ - KAİDESİ",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.02.0002.00.00.00",
        "product_name": "ARPACIK KİLİDİ",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.02.0003.00.00.00",
        "product_name": "ARPACIK YAY KAPAĞI",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.02.0004.00.00.00",
        "product_name": "ARPACIK",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.02.0005.00.00.00",
        "product_name": "KADEMELİ PİM",
        "description": "A6-205",
        "current_stock": 100
    },
    {
        "product_code": "03.0.02.0006.00.00.00",
        "product_name": "SABİTLEME PİMİ",
        "description": "K6-207",
        "current_stock": 100
    },
    {
        "product_code": "03.0.03.0001.00.00.00",
        "product_name": "Gez Kaide",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.03.0002.00.00.00",
        "product_name": "Gez Yan Ayar Vidası",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.03.0003.00.00.00",
        "product_name": "Kilit Dili",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.03.0004.00.00.00",
        "product_name": "Pabuç",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.03.0005.00.00.00",
        "product_name": "Gez Yan Tambur",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.03.0011.00.00.00",
        "product_name": "Kule",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.03.0012.00.00.00",
        "product_name": "Gez Kamlı Tambur",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.03.0013.00.00.00",
        "product_name": "Gez Ucu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.04.0001.00.00.00",
        "product_name": "Arpacık Kaide",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.04.0002.00.00.00",
        "product_name": "Arpacık Mil",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.04.0004.00.00.00",
        "product_name": "Arpacık Kule",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.04.0005.00.00.00",
        "product_name": "Arpacık Ucu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.04.0006.00.00.00",
        "product_name": "Arpacık Ara Ayar Somunu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.04.0007.00.00.00",
        "product_name": "Arpacık Ara Ayar Somunu Pimi",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.05.0001.00.00.00",
        "product_name": "GEZ KULE KAİDE",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.05.0002.00.00.00",
        "product_name": "GEZ UCU",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.05.0003.00.00.00",
        "product_name": "GEZ UCU KONUMLAMA DİLİ",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.05.0005.00.00.00",
        "product_name": "YAN AYAR TAMBURU",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.05.0006.00.00.00",
        "product_name": "GEZ YAN AYAR VİDA SOMUNU",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.05.0008.00.00.00",
        "product_name": "GEZ YAN AYAR VİDASI",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.05.0010.00.00.00",
        "product_name": "GEZ -  ARPACIK KAİDE",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.05.0011.00.00.00",
        "product_name": "GEZ - ARPACIK KAİDE MİLİ",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.05.0012.00.00.00",
        "product_name": "GEZ - ARPACIK KULE KAIDE KİLİT DİLİ",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.05.0014.00.00.00",
        "product_name": "GEZ - ARPACIK SIKMA VİDASI M4X30",
        "description": "SP",
        "current_stock": 100
    },
    {
        "product_code": "03.0.05.0015.00.00.00",
        "product_name": "GEZ - ARPACIK KAİDE PABUÇ",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.06.0001.00.00.00",
        "product_name": "ARPACIK KULE KAİDE",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.06.0002.00.00.00",
        "product_name": "ARPACIK UCU",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.07.0001.00.00.00",
        "product_name": "Bağlantı Bacakları",
        "description": "1101167",
        "current_stock": 100
    },
    {
        "product_code": "03.0.07.0002.00.00.00",
        "product_name": "Bağlantı Bacağı Insert",
        "description": "1101185",
        "current_stock": 100
    },
    {
        "product_code": "03.0.07.0003.00.00.00",
        "product_name": "Nişangah Hamili",
        "description": "1101168",
        "current_stock": 100
    },
    {
        "product_code": "03.0.07.0005.00.00.00",
        "product_name": "Nişangah Hamili Konum Pulu",
        "description": "1101170",
        "current_stock": 100
    },
    {
        "product_code": "03.0.07.0006.00.00.00",
        "product_name": "Nişangah Hamili Yan Ayar Mil Yatağı",
        "description": "1101171",
        "current_stock": 100
    },
    {
        "product_code": "03.0.07.0008.00.00.00",
        "product_name": "Gez",
        "description": "1101173",
        "current_stock": 100
    },
    {
        "product_code": "03.0.07.0009.00.00.00",
        "product_name": "Arpacık Hamili",
        "description": "1101174",
        "current_stock": 100
    },
    {
        "product_code": "03.0.07.0010.00.00.00",
        "product_name": "Arpacık Ucu",
        "description": "1101175",
        "current_stock": 100
    },
    {
        "product_code": "03.0.07.0012.00.00.00",
        "product_name": "Kilit Pimi",
        "description": "1101177",
        "current_stock": 100
    },
    {
        "product_code": "03.0.07.0013.00.00.00",
        "product_name": "Klik Pulu",
        "description": "1101178",
        "current_stock": 100
    },
    {
        "product_code": "03.0.07.0015.00.00.00",
        "product_name": "Yükseliş Ayar Vidası",
        "description": "1101180",
        "current_stock": 100
    },
    {
        "product_code": "03.0.07.0016.00.00.00",
        "product_name": "Dayama Makarası",
        "description": "1101181",
        "current_stock": 100
    },
    {
        "product_code": "03.0.07.0017.00.00.00",
        "product_name": "Dayama Pimi",
        "description": "1101182",
        "current_stock": 100
    },
    {
        "product_code": "03.0.07.0019.00.00.00",
        "product_name": "Gez Yan Ayar Mili",
        "description": "1101184",
        "current_stock": 100
    },
    {
        "product_code": "03.0.07.0021.00.00.00",
        "product_name": "Arpacık Pimi",
        "description": "1101186",
        "current_stock": 100
    },
    {
        "product_code": "03.0.13.0001.00.00.00",
        "product_name": "Alt Mekanizma Gövdesi",
        "description": "KMG5-A04-03-01_9",
        "current_stock": 100
    },
    {
        "product_code": "03.0.13.0002.00.00.00",
        "product_name": "Piston Mili",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.15.0001.00.00.00",
        "product_name": "Kaide",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.15.0002.00.00.00",
        "product_name": "Yan Ayar Vidası",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.15.0003.00.00.00",
        "product_name": "Arpacık Ayar Vidası Pulu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.15.0004.00.00.00",
        "product_name": "Arpacık Sabitleme Pabucu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.15.0005.00.00.00",
        "product_name": "Arpacık Ayar Pimi",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.15.0006.00.00.00",
        "product_name": "Kule",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.15.0007.00.00.00",
        "product_name": "Arpacık Ucu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.15.0008.00.00.00",
        "product_name": "Yükseklik Ayar Somunu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.16.0001.00.00.00",
        "product_name": "Kaide",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.16.0002.00.00.00",
        "product_name": "Kule",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.16.0003.00.00.00",
        "product_name": "Yükseliş Tamburu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.16.0004.00.00.00",
        "product_name": "Gez Ucu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.16.0005.00.00.00",
        "product_name": "Yan Ayar Vidası",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.16.0006.00.00.00",
        "product_name": "Yan Ayar Tamburu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.16.0007.00.00.00",
        "product_name": "Gez Yan Tambur",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.16.0008.00.00.00",
        "product_name": "Pabuç",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.17.0001.00.00.00",
        "product_name": "Kaide",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.17.0002.00.00.00",
        "product_name": "Kule",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.17.0004.00.00.00",
        "product_name": "Arpacık Ucu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.18.0001.00.00.00",
        "product_name": "Gece Arpacığı",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.18.0002.00.00.00",
        "product_name": "Gece Arpacığı Vidası",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.18.0007.00.00.00",
        "product_name": "Taşıma Kolu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.18.0008.00.00.00",
        "product_name": "Tahdit Pimi",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.18.0009.00.00.00",
        "product_name": "Kilit Sıkma Sacı",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.18.0010.00.00.00",
        "product_name": "Eksantrik Kilit Arka / Sağ",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.18.0011.00.00.00",
        "product_name": "Eksantrik Kilit Ön / Sol",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.18.0012.00.00.00",
        "product_name": "Kilit Burcu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.18.0013.00.00.00",
        "product_name": "Kilitleme Kolu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.18.0016.00.00.00",
        "product_name": "Gece Gezi",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.18.0017.00.00.00",
        "product_name": "Gece Gezi Ayar Vidası",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.19.0001.00.00.00",
        "product_name": "Gez Yan Tambur L-R\t",
        "description": " BLN-KCR5-A1-3.01.00.05 GEZ YAN TAMBUR_Rev2",
        "current_stock": 100
    },
    {
        "product_code": "03.0.20.0001.00.00.00",
        "product_name": "Arpacık Kaide",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.20.0002.00.00.00",
        "product_name": "Arpacık Yan Ayar Vidası",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.20.0003.00.00.00",
        "product_name": "Arpacık Ayar Vidası Pulu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.20.0004.00.00.00",
        "product_name": "Arpacık Sabitleme Pabucu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.20.0005.00.00.00",
        "product_name": "Arpacık Ayar Pimi",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.20.0006.00.00.00",
        "product_name": "Arpacık Kule",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.20.0007.00.00.00",
        "product_name": "Arpacık Ucu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.20.0008.00.00.00",
        "product_name": "Yükseklik Ayar Somunu",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.0.22.0001.00.00.00",
        "product_name": "Alt Mekanizma Gövdesi",
        "description": "Bize ait olmayan parça",
        "current_stock": 100
    },
    {
        "product_code": "03.0.25.0001.00.00.00",
        "product_name": "Gez Kule (L-R)",
        "description": None,
        "current_stock": 100
    },
    {
        "product_code": "03.1.13.0000.00.00.00",
        "product_name": "KMG16\" - Alt Mekanizma Piston Mili Komplesi",
        "description": None,
        "current_stock": 100
    }
]

                # Create products
                created_count = 0
                skipped_count = 0
                for product_data in products_data:
                    defaults = {
                        'product_name': product_data['product_name'],
                        'product_type': 'SEMI',
                        'description': product_data['description'],
                        'current_stock': product_data['current_stock'],
                        'inventory_category': proses_category,
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
                        f'Successfully loaded semi-finished products data. '
                        f'Created: {created_count}, Skipped: {skipped_count}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading semi-finished products data: {str(e)}')
            )
            raise 