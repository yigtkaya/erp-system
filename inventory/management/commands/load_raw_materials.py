from django.core.management.base import BaseCommand
from django.db import transaction
from inventory.models import RawMaterial, InventoryCategory, UnitOfMeasure
from erp_core.models import MaterialType

class Command(BaseCommand):
    help = 'Loads raw materials data into the database'

    def get_materials_data_part1(self):
        return [
            {
                'material_code': '02.100Cr6.Ø10.00',
                'material_name': 'Ø10 100CR6 YUVARLAK C 9107-03',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 10.0,
                'current_stock': 100
            },
            {
                'material_code': '02.1045.40X80X60',
                'material_name': '1045 ÇELİK 40X80X60 NORMALİZASYON-ISIL İŞLEM (28-32 HRC)',
                'material_type': MaterialType.STEEL,
                'width': 40,
                'height': 80,
                'thickness': 60,
                'current_stock': 100
            },
            {
                'material_code': '02.14NiCr14.25x25',
                'material_name': '14NiCr14',
                'material_type': MaterialType.STEEL,
                'width': 25,
                'height': 25,
                'current_stock': 100
            },
            {
                'material_code': '02.14NiCr14.Ø32.00',
                'material_name': 'Ø32 14NiCr14 Yuvarlak 14 NiCr14 (C.9118-01)',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 32.0,
                'current_stock': 100
            },
            {
                'material_code': '02.6013.60X60',
                'material_name': '6013 60X60 KARE',
                'material_type': MaterialType.ALUMINUM,
                'width': 60,
                'height': 60,
                'current_stock': 100
            },
            {
                'material_code': '02.6013.80X50X600',
                'material_name': 'ALM.LAMA 6013 80X50X600',
                'material_type': MaterialType.ALUMINUM,
                'width': 80,
                'height': 50,
                'thickness': 600,
                'current_stock': 100
            },
            {
                'material_code': '02.7075-T651.40X100X270',
                'material_name': 'AL. PLAKA 7075 T651 40*100*270 MM',
                'material_type': MaterialType.ALUMINUM,
                'width': 40,
                'height': 100,
                'thickness': 270,
                'current_stock': 100
            },
            {
                'material_code': '02.7075-T651.Ø18.00',
                'material_name': 'Ø18 ALM. ÇUBUK 7075 T651',
                'material_type': MaterialType.ALUMINUM,
                'diameter_mm': 18.0,
                'current_stock': 100
            },
            {
                'material_code': '02.C45.70X120',
                'material_name': 'C45 İMALAT ÇELİĞİ LAMA',
                'material_type': MaterialType.STEEL,
                'width': 70,
                'height': 120,
                'current_stock': 100
            },
            {
                'material_code': '02.C45.Ø12.00',
                'material_name': 'C 45 Y 12',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 12.0,
                'current_stock': 100
            }
        ]

    def get_materials_data_part2(self):
        return [
            {
                'material_code': '02.14NiCr14.Ø13.00',
                'material_name': 'Ø13 14NiCr14',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 13.0,
                'current_stock': 100
            },
            {
                'material_code': '02.14NiCr14.Ø50.00',
                'material_name': 'Ø50 14NiCr14 Yuvarlak. 14 NiCr14',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 50.0,
                'current_stock': 100
            },
            {
                'material_code': '02.15NiCr13.100x20',
                'material_name': '15NiCr13 sıcak çekme',
                'material_type': MaterialType.STEEL,
                'width': 100,
                'height': 20,
                'current_stock': 100
            },
            {
                'material_code': '02.16MnCr5.Ø08.00',
                'material_name': '16MnCr5 Ø8',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 8.0,
                'current_stock': 100
            },
            {
                'material_code': '02.16MnCr5.Ø20.00',
                'material_name': 'Ø20 16MnCr5',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 20.0,
                'current_stock': 100
            },
            {
                'material_code': '02.304.200X0X155',
                'material_name': '304L-CB KLT.200X0X155',
                'material_type': MaterialType.STEEL,
                'width': 200,
                'height': 0,
                'thickness': 155,
                'current_stock': 100
            },
            {
                'material_code': '02.7075-T651.60X62X135',
                'material_name': 'AL.PLAKA 7075T651 60x62x135 MM',
                'material_type': MaterialType.ALUMINUM,
                'width': 60,
                'height': 62,
                'thickness': 135,
                'current_stock': 100
            },
            {
                'material_code': '02.7075-T651.90X80X300',
                'material_name': 'ALM LEVHA 7075 90 MM İTHAL 90X80X300',
                'material_type': MaterialType.ALUMINUM,
                'width': 90,
                'height': 80,
                'thickness': 300,
                'current_stock': 100
            },
            {
                'material_code': '02.TOOLOX 44.20X1060',
                'material_name': 'TOOLOX 44 TO44L 20X1060 MM',
                'material_type': MaterialType.STEEL,
                'width': 20,
                'height': 1060,
                'current_stock': 100
            },
            {
                'material_code': '02.TOOLOX 44.20X40X80',
                'material_name': 'TOOLOX 44 TO44P 20X40X80',
                'material_type': MaterialType.STEEL,
                'width': 20,
                'height': 40,
                'thickness': 80,
                'current_stock': 100
            }
        ]

    def get_materials_data_part3(self):
        return [
            {
                'material_code': '02.4140.Ø14.00',
                'material_name': '42CrMo4 Ø14 - 4140',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 14.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140.Ø32.00',
                'material_name': '42CrMo4 Ø32 - 4140',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 32.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140.Ø40.00',
                'material_name': '40 mm ISLAH ÇELİĞİ 4140 ASİL ÇELİK',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 40.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140-QT.Ø13.00',
                'material_name': '42CrMo4 QT Ø13 - 4140',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 13.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4340.Ø16.00',
                'material_name': 'Ø16 AISI 4340 Yuvarlak AISI 4340 (C.9134-01)',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 16.0,
                'current_stock': 100
            },
            {
                'material_code': '02.6082-T6.30X30X176',
                'material_name': 'ALM.LAMA PROFİL 6082 T6 30X30X176',
                'material_type': MaterialType.ALUMINUM,
                'width': 30,
                'height': 30,
                'thickness': 176,
                'current_stock': 100
            },
            {
                'material_code': '02.6082-T6.30X40X172',
                'material_name': 'ALM.LAMA PROFİL 6082 T6 30X40X172',
                'material_type': MaterialType.ALUMINUM,
                'width': 30,
                'height': 40,
                'thickness': 172,
                'current_stock': 100
            },
            {
                'material_code': '02.6082-T6.Ø16.00',
                'material_name': 'Ø16 ALM. ÇUBUK 6082 T6 16MM',
                'material_type': MaterialType.ALUMINUM,
                'diameter_mm': 16.0,
                'current_stock': 100
            },
            {
                'material_code': '02.7075.Ø50.00',
                'material_name': 'Ø50 ALM. LEVHA 7075',
                'material_type': MaterialType.ALUMINUM,
                'diameter_mm': 50.0,
                'current_stock': 100
            },
            {
                'material_code': '02.C40.Ø65.00',
                'material_name': 'C40 Ø65',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 65.0,
                'current_stock': 100
            }
        ]

    def get_materials_data_part4(self):
        return [
            {
                'material_code': '02.4140.20X145X195',
                'material_name': '4140 20X145X195',
                'material_type': MaterialType.STEEL,
                'width': 20,
                'height': 145,
                'thickness': 195,
                'current_stock': 100
            },
            {
                'material_code': '02.4140.20X50X190',
                'material_name': '4140 20X50X190',
                'material_type': MaterialType.STEEL,
                'width': 20,
                'height': 50,
                'thickness': 190,
                'current_stock': 100
            },
            {
                'material_code': '02.4140.20X96X120',
                'material_name': '4140 20X96X120',
                'material_type': MaterialType.STEEL,
                'width': 20,
                'height': 96,
                'thickness': 120,
                'current_stock': 100
            },
            {
                'material_code': '02.4140.Ø08.00',
                'material_name': '42CrMo4 Ø8 - 4140',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 8.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140.Ø09.00',
                'material_name': '42CrMo4 Ø9 - 4140',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 9.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140.Ø12.00',
                'material_name': '42CrMo4 Ø12 4140',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 12.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140.Ø16.00',
                'material_name': '42CrMo4 Ø16 - 4140',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 16.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140.Ø18.00',
                'material_name': '42CrMo4 Ø18 - 4140',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 18.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140.Ø20.00',
                'material_name': '42 Cr Mo 4 Ø20 - 4140',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 20.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140.Ø24.00',
                'material_name': '42CrMo4 Ø24 - 4140 Ø24 mm',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 24.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140.Ø32.00',
                'material_name': '42CrMo4 Ø32 - 4140',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 32.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140.Ø38.00',
                'material_name': '42CrMo4 Ø38 - 4140',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 38.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140.Ø40.00',
                'material_name': '40 mm ISLAH ÇELİĞİ 4140 ASİL ÇELİK',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 40.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140.Ø50.00',
                'material_name': '50 mm ISLAH ÇELİĞİ 4140 ASİL ÇELİK',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 50.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140-QT.Ø08.00',
                'material_name': '42CrMo4 Ø8 - 4140 QT',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 8.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140-QT.Ø12.00',
                'material_name': '42CrMo4 Ø12 4140 QT',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 12.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140-QT.Ø18.50',
                'material_name': '4140 QT',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 18.5,
                'current_stock': 100
            },
            {
                'material_code': '02.4140-QT.Ø21.00',
                'material_name': '4140 QT',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 21.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140S.Ø14.00',
                'material_name': '42CrMoS4 Ø12 4140S',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 14.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140S.Ø18.00',
                'material_name': '42CrMoS4 Ø18 - 4140 Ø18 mm',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 18.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4140S.Ø24.00',
                'material_name': '42CrMoS4 Ø24 - 4140 Ø24 mm',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 24.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4340.Ø16.00',
                'material_name': 'Ø16 AISI 4340 Yuvarlak AISI 4340 (C.9134-01)',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 16.0,
                'current_stock': 100
            },
            {
                'material_code': '02.4340-QT.30X60X70',
                'material_name': 'AISI E4340 QT 30*60*70 mm',
                'material_type': MaterialType.STEEL,
                'width': 30,
                'height': 60,
                'thickness': 70,
                'current_stock': 100
            },
            {
                'material_code': '02.55NiCrMoV7.115x110x175',
                'material_name': '55NiCrMoV7 115x110x175-OBA MEKANİZMA HAMMADDE',
                'material_type': MaterialType.STEEL,
                'width': 115,
                'height': 110,
                'thickness': 175,
                'current_stock': 100
            }
        ]

    def get_materials_data_part5(self):
        return [
            {
                'material_code': '02.6013.EKALT',
                'material_name': 'CAR816 EL KUNDAĞI ALT-HAMMADDE',
                'material_type': MaterialType.ALUMINUM,
                'current_stock': 100
            },
            {
                'material_code': '02.6013.EKUST',
                'material_name': 'CAR816 EL KUNDAĞI ÜST-HAMMADDE',
                'material_type': MaterialType.ALUMINUM,
                'current_stock': 100
            },
            {
                'material_code': '02.6061-T651.80X200X400',
                'material_name': 'AL.PLAKA 6061 T651 80X200X400 MM',
                'material_type': MaterialType.ALUMINUM,
                'width': 80,
                'height': 200,
                'thickness': 400,
                'current_stock': 100
            },
            {
                'material_code': '02.6082.T6.165',
                'material_name': 'AL.ÖZEL PROFİL 6082T6 165MM KALIP NO:21482',
                'material_type': MaterialType.ALUMINUM,
                'diameter_mm': 165.0,
                'current_stock': 100
            },
            {
                'material_code': '02.6082-T6.20X20X40',
                'material_name': 'ALM.LAMA PROFİL 6082 T6 20X20X40',
                'material_type': MaterialType.ALUMINUM,
                'width': 20,
                'height': 20,
                'thickness': 40,
                'current_stock': 100
            },
            {
                'material_code': '02.6082-T6.25X2500',
                'material_name': 'ALM.LAMA PROFİL 6082 T6 25X2500',
                'material_type': MaterialType.ALUMINUM,
                'width': 25,
                'height': 2500,
                'current_stock': 100
            },
            {
                'material_code': '02.6082-T6.3000',
                'material_name': 'AL.ÖZEL PROFIL 6082T6 3000 MM KALIP NO: 21482',
                'material_type': MaterialType.ALUMINUM,
                'height': 3000,
                'current_stock': 100
            },
            {
                'material_code': '02.6082-T6.3060',
                'material_name': 'ALM.ÖZEL PROFİL 6082 T6 3060 MM',
                'material_type': MaterialType.ALUMINUM,
                'height': 3060,
                'current_stock': 100
            },
            {
                'material_code': '02.7075-T651.120X120X240',
                'material_name': 'ALM.PLAKA 7075T651 120X120X240 MM',
                'material_type': MaterialType.ALUMINUM,
                'width': 120,
                'height': 120,
                'thickness': 240,
                'current_stock': 100
            },
            {
                'material_code': '02.7075-T651.15X25X36',
                'material_name': 'AL. PLAKA 7075 T651 15*25*36 MM',
                'material_type': MaterialType.ALUMINUM,
                'width': 15,
                'height': 25,
                'thickness': 36,
                'current_stock': 100
            },
            {
                'material_code': '02.7075-T651.180X3000X18',
                'material_name': 'AL. ÇUBUK 7075 T6511 180*3000*18',
                'material_type': MaterialType.ALUMINUM,
                'width': 180,
                'height': 3000,
                'thickness': 18,
                'current_stock': 100
            },
            {
                'material_code': '02.7075-T651.20X25X40',
                'material_name': 'ALM.PLAKA 7075T651 20X25X40 MM',
                'material_type': MaterialType.ALUMINUM,
                'width': 20,
                'height': 25,
                'thickness': 40,
                'current_stock': 100
            },
            {
                'material_code': '02.7075-T651.40X100X270',
                'material_name': 'AL. PLAKA 7075 T651 40*100*270 MM',
                'material_type': MaterialType.ALUMINUM,
                'width': 40,
                'height': 100,
                'thickness': 270,
                'current_stock': 100
            },
            {
                'material_code': '02.7075-T651.40X85X270',
                'material_name': 'AL.PLAKA 7075T651 40x85x270 MM',
                'material_type': MaterialType.ALUMINUM,
                'width': 40,
                'height': 85,
                'thickness': 270,
                'current_stock': 100
            },
            {
                'material_code': '02.7075-T651.40X85X271',
                'material_name': 'AL.PLAKA 7075T651 40x85x271 MM',
                'material_type': MaterialType.ALUMINUM,
                'width': 40,
                'height': 85,
                'thickness': 271,
                'current_stock': 100
            },
            {
                'material_code': '02.7075-T651.60X62X135',
                'material_name': 'AL.PLAKA 7075T651 60x62x135 MM',
                'material_type': MaterialType.ALUMINUM,
                'width': 60,
                'height': 62,
                'thickness': 135,
                'current_stock': 100
            },
            {
                'material_code': '02.7075-T651.80X108X270',
                'material_name': 'ALM PLAKA 7075 T651 80X108X270',
                'material_type': MaterialType.ALUMINUM,
                'width': 80,
                'height': 108,
                'thickness': 270,
                'current_stock': 100
            },
            {
                'material_code': '02.C15.Ø10.00',
                'material_name': 'C 15',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 10.0,
                'current_stock': 100
            },
            {
                'material_code': '02.C40.Ø12.00',
                'material_name': 'Ø12 1040',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 12.0,
                'current_stock': 100
            },
            {
                'material_code': '02.C40.Ø25.00',
                'material_name': 'K25.00/EKT/C40/00_C0/HAD/5500_6500',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 25.0,
                'current_stock': 100
            },
            {
                'material_code': '02.C40.Ø40.00',
                'material_name': 'K40.00/EKT/C40/00_C0/HAD/6000_7000',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 40.0,
                'current_stock': 100
            },
            {
                'material_code': '02.C45.100X100X60',
                'material_name': 'C45 İMALAT ÇELİĞİ LAMA',
                'material_type': MaterialType.STEEL,
                'width': 100,
                'height': 100,
                'thickness': 60,
                'current_stock': 100
            },
            {
                'material_code': '02.C45.150X130X90',
                'material_name': 'C45 İMALAT ÇELİĞİ LAMA',
                'material_type': MaterialType.STEEL,
                'width': 150,
                'height': 130,
                'thickness': 90,
                'current_stock': 100
            },
            {
                'material_code': '02.C50.Ø40.00',
                'material_name': '40 İMALAT ÇELİĞİ 1050 ASİL ÇELİK',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 40.0,
                'current_stock': 100
            }
        ]

    def get_materials_data_part6(self):
        return [
            {
                'material_code': '02.C45.40X80X60',
                'material_name': '1045 ÇELİK 40X80X60 NORMALİZASYON-ISIL İŞLEM (28-32 HRC)',
                'material_type': MaterialType.STEEL,
                'width': 40,
                'height': 80,
                'thickness': 60,
                'current_stock': 100
            },
            {
                'material_code': '02.C45.70X120',
                'material_name': 'C45 İMALAT ÇELİĞİ LAMA',
                'material_type': MaterialType.STEEL,
                'width': 70,
                'height': 120,
                'current_stock': 100
            },
            {
                'material_code': '02.16MnCr5.Ø06.00',
                'material_name': 'Ø6 16MnCr5',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 6.0,
                'current_stock': 100
            },
            {
                'material_code': '02.16MnCr14.Ø14.00',
                'material_name': '16MnCr14 Ø14',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 14.0,
                'current_stock': 100
            },
            {
                'material_code': '02.16CrMo5.Ø14.00',
                'material_name': 'Ø14 16CrMo5 Ø14',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 14.0,
                'current_stock': 100
            },
            {
                'material_code': '02.16CrMo5.Ø15.00',
                'material_name': 'Ø154 16CrMo5 Ø15',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 15.0,
                'current_stock': 100
            },
            {
                'material_code': '02.15S20.Ø15.00',
                'material_name': '10S20K-15S20K',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 15.0,
                'current_stock': 100
            },
            {
                'material_code': '02.10S20K.Ø10.00',
                'material_name': '10S20K-15S20K',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 10.0,
                'current_stock': 100
            },
            {
                'material_code': '02.39NiCrMo3.Ø27.00',
                'material_name': '39NiCrMo3 Ø 27 mm',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 27.0,
                'current_stock': 100
            },
            {
                'material_code': '02.39NiCrMo3-QT.Ø25.00',
                'material_name': '39CrNiMo3-QT',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 25.0,
                'current_stock': 100
            },
            {
                'material_code': '02.39NiCrMo3-QT.Ø25.60',
                'material_name': '39NiCrMo3 QT Ø 25.60',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 25.6,
                'current_stock': 100
            },
            {
                'material_code': '02.39NiCrMo3-QT-SH.Ø25.30',
                'material_name': 'Ø25.30 / EN 10277-5 / 39NiCrMo3+QT+SH',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 25.3,
                'current_stock': 100
            },
            {
                'material_code': '02.303.Ø10.00',
                'material_name': 'ÇUBUK 303 KLT 10 MM PASLANMAZ',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 10.0,
                'current_stock': 100
            },
            {
                'material_code': '02.304.200X0X155',
                'material_name': '304L-CB KLT.200X0X155',
                'material_type': MaterialType.STEEL,
                'width': 200,
                'height': 0,
                'thickness': 155,
                'current_stock': 100
            },
            {
                'material_code': '02.304.Ø10.00',
                'material_name': '304 Ø 10 paslanmaz',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 10.0,
                'current_stock': 100
            },
            {
                'material_code': '02.6082-T6.Ø18.00',
                'material_name': 'Ø18 ALM. ÇUBUK 6082 T6',
                'material_type': MaterialType.ALUMINUM,
                'diameter_mm': 18.0,
                'current_stock': 100
            },
            {
                'material_code': '02.6082-T6.30X30X177',
                'material_name': 'AL.LAMA PROFİL 6082T6 30X40X177 MM',
                'material_type': MaterialType.ALUMINUM,
                'width': 30,
                'height': 40,
                'thickness': 177,
                'current_stock': 100
            },
            {
                'material_code': '02.6013.EKALT.YERLI',
                'material_name': 'CAR816 EL KUNDAĞI ALT-HAMMADDE-YERLI',
                'material_type': MaterialType.ALUMINUM,
                'current_stock': 100
            },
            {
                'material_code': '02.6013.EKUST.YERLI',
                'material_name': 'CAR816 EL KUNDAĞI ÜST-HAMMADDE-YERLI',
                'material_type': MaterialType.ALUMINUM,
                'current_stock': 100
            },
            {
                'material_code': '02.14NiCr14.Ø55.00',
                'material_name': 'Ø55 14NiCr14 Yuvarlak 14 NiCr14 (C.9115-01)',
                'material_type': MaterialType.STEEL,
                'diameter_mm': 55.0,
                'current_stock': 100
            }
        ]

    def handle(self, *args, **options):
        self.stdout.write('Loading raw materials data...')

        try:
            with transaction.atomic():
                # Get or create the HAMMADDE category
                hammadde_category, _ = InventoryCategory.objects.get_or_create(
                    name='HAMMADDE',
                    defaults={'description': 'Raw Materials and Standard Parts'}
                )

                # Get or create the kg unit
                kg_unit, _ = UnitOfMeasure.objects.get_or_create(
                    unit_code='kg',
                    defaults={'unit_name': 'Kilogram'}
                )

                # Get all materials data
                all_materials = (
                    self.get_materials_data_part1() +
                    self.get_materials_data_part2() +
                    self.get_materials_data_part3() +
                    self.get_materials_data_part4() +
                    self.get_materials_data_part5() +
                    self.get_materials_data_part6()
                )

                # Create materials
                created_count = 0
                skipped_count = 0
                for material_data in all_materials:
                    defaults = {
                        'material_name': material_data['material_name'],
                        'material_type': material_data['material_type'],
                        'current_stock': material_data['current_stock'],
                        'inventory_category': hammadde_category,
                        'unit': kg_unit
                    }

                    # Add optional dimensional fields if they exist
                    for field in ['width', 'height', 'thickness', 'diameter_mm']:
                        if field in material_data:
                            defaults[field] = material_data[field]
                    
                    _, created = RawMaterial.objects.get_or_create(
                        material_code=material_data['material_code'],
                        defaults=defaults
                    )
                    if created:
                        created_count += 1
                        self.stdout.write(f"Created material: {material_data['material_code']}")
                    else:
                        skipped_count += 1
                        self.stdout.write(f"Skipped existing material: {material_data['material_code']}")

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully loaded raw materials data. '
                        f'Created: {created_count}, Skipped: {skipped_count}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading raw materials data: {str(e)}')
            )
            raise 