import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from inventory.models import ControlGauge
from io import StringIO

class Command(BaseCommand):
    help = 'Load gauge data from CSV'

    def parse_date(self, date_str):
        if not date_str or date_str == '-':
            return None
        try:
            # Try different date formats
            formats = ['%d/%m/%y', '%d/%m/%Y', '%d.%m.%Y', '%b-%y']
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def handle(self, *args, **options):
        # Clear existing data
        ControlGauge.objects.all().delete()

        csv_data = '''mastar_code,mastar_name,mastar_type,mastar_serial_name,brand,model,measuring_range,resolution,calibration_made_by,calibration_date,calibration_per_year,upcoming_calibration_date,certificate_no,status,current_location,scrap_lost_date,description
FÇ-01,Diş tarağı,Mekanik,-,-,-,Metrik / Whitworth,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
FÇ-02,Diş tarağı,Mekanik,-,-,-,Metrik / Whitworth,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
FÇ-03,Radüs Mastarı,Mekanik,-,-,-,R1-R7 mm,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
FÇ-04,Diş tarağı,Mekanik,-,-,-,-,-,-,,1 / Yıl,Dec-00,-,HURDA,-,10/9/24,
FÇ-05,Filler çakısı,Mekanik,-,-,-,"0,05 - 1,00 mm",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
HM-01,Halka mastar,15.999,362481,Ferter,,,,Ferter,28/02/25,1 / Yıl,Feb-26,0111020565,UYGUN,Laboratuvar,-,
HM-02,Halka mastar,39.999,367038,Ferter,,,,Ferter,28/02/25,1 / Yıl,Feb-26,0111020566,UYGUN,Laboratuvar,-,
HM-03,Halka mastar,24.999,369152,Ferter,,,,Ferter,28/02/25,1 / Yıl,Feb-26,0111020567,UYGUN,Laboratuvar,-,
KK-01,"M 16 X 1,5 Mastar",-,590752,Ferter,FAM-6-0072-M3,-,-,-,09/10/20,1 / Yıl,-,0112030938,KULLANILMIYOR,Laboratuvar,-,
KK-02,K6-200/L5 Ø10D10 Mastarı,Geçer/Geçmez,KK1-MPT-KLT-MST-0286-M0,-,-,"10,04-10,98 mm",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
KK-03,"K6-200/L6 Ø3,5D10 Mastarı",Geçer/Geçmez,KK1-MPT-KLT-MST-0068-M0,-,-,"3,53 - 3,578 mm",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
M-01,"A6-200-L10 14-0,15/-0,2  Mastar",Geçer/Geçmez,-,Normtam,-,-,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
M-02,"A6-200-L11 1,6 Mastar",Geçer/Geçmez,-,Normtam,-,-,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
M-03,"A6-200-L3 17-0,1 Mastar",Geçer/Geçmez,-,Normtam,-,"16,90 - 17,00 mm",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Üst kat,-,
M-04,"A6-200-L4 20-0,1 Mastar",Geçer/Geçmez,-,Normtam,-,-,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
M-05,"Ø6,52-6,59 Mastar",Geçer/Geçmez,-,Kapsam,-,"Ø6,52-6,59",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
M-06,"Ø3,52-3,59 Mastar",Geçer/Geçmez,-,Kapsam,-,"Ø3,52-3,59",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
M-07,"Ø6,54-6,60 Mastar",Geçer/Geçmez,-,Kapsam,-,"Ø6,54-6,60",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
M-08,"NT 632-1(1) 35,5 ±0,05 Mastar",Geçer/Geçmez,-,Normtam,-,"35,450-35,539",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Üst kat,-,
M-09,"NT 632-1(2) 35,5 ±0,05 Mastar",Geçer/Geçmez,-,Normtam,-,"35,450-35,539",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Üst kat,-,
M-10,Çatal mastar,-,-,-,-,"24,15-24,20",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Üst kat,-,
M-11,Halka mastar,-,ME-49/102A,Kapsam,-,22.43,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Üst kat,-,
M-12,Mastar,-,"KCR7,5 Kaide",-,-,"5,091-5,213",-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
M-13,Pikatini mastarı,Geçer/Geçmez,-,-,-,-,-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
TM-01,Tampon mastar,,,Forza,,4.92,,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
TM-02,Tampon mastar,,,Forza,,4.92,,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
TM-03,Tampon mastar,,,Forza,,5.08,,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
TM-04,Tampon mastar,,,Forza,,5.08,,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
TM-05,Tampon mastar,,,Mat 03,,"2,10-1,90",,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
TM-06,Tampon Mastar,Geçer/Geçmez,594858,Ferter,-,"M5x0,5-6H 4,459-4,599",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VHM-01,Vida Halka Mastar,Geçer,614878,Ferter,-,M39x1-6g,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Üst kat,-,
VHM-02,Vida Halka Mastar,Geçmez,614879,Ferter,-,M39x1-6g,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Üst kat,-,
VHM-03,Vida Halka Mastar,Geçer,609829,Ferter,-,"11/16""-32 UN 2A",-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VHM-04,Vida Halka Mastar,Geçmez,609830,Ferter,-,"11/16""-32 UN 2A",-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VHM-05,Vida Halka Mastar,Geçer,578657,Ferter,-,M10x1-4g/6g,-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VHM-06,Vida Halka Mastar,Geçmez,610902,Ferter,-,M10x1-4g/6g,-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VHM-07,Vida Halka Mastar,-,99635,Ferter,-,M10x1-6H,-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VHM-08,Vida Halka Mastar,-,-,Ferter,-,M3x6H,-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VHM-09,Vida Halka Mastar,Geçer,640163,Ferter,-,M4x0.7-6g,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VHM-10,Vida Halka Mastar,Geçmez,640211,Ferter,-,M4x0.7-6g,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VHM-12,Vida Halka Mastar,-,517166,Ferter,-,"M5x0,4-4G",-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VHM-13,Vida Halka Mastar,-,-,Ferter,-,"M5x0,5-6H",-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VHM-14,Vida Halka Mastar,Geçer,644105,Ferter,-,M5x0.8-6g,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VHM-15,Vida Halka Mastar,Geçmez,644106,Ferter,-,M5x0.8-6g,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VHM-16,Vida Halka Mastar,-,-,Ferter,-,M6x6H,-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VHM-17,Vida Halka Mastar,-,102850,Ferter,-,M8x1-6H,-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VHM-18,Vida Halka Mastar,-,102851,Ferter,-,M8x1-6H,-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VHM-19,Vida Halka Mastar,-,454044,-,-,M10x1-6H,-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VHM-20,Vida Halka Mastar,Geçer,516691,Ferter,-,"M4x0,4-4g",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,Ersin Bey tarafından alındı. 06/03/2025
VHM-21,Vida Halka Mastar,Geçmez,516692,Ferter,-,"M4x0,4-4g",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,Ersin Bey tarafından alındı. 06/03/2025
VHM-22,Vida Halka Mastar,Geçer,516689,Ferter,-,"M5x0,4-4g",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,,
VHM-23,Vida Halka Mastar,Geçmez,516690,Ferter,-,"M5x0,4-4g",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VHM-25,Vida Halka Mastar,-,594858,-,-,"M5x0,5-6H",-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VHM-26,Vida Halka Mastar,Geçer,113226,Ferter,-,"Tr20,6x1",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VHM-27,Vida Halka Mastar,Geçmez,113229,Ferter,-,"Tr20,6x1",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VHM-28,Vida Halka Mastar,Geçer,175836,Ferter,-,"Tr20,6x1",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VHM-29,Vida Halka Mastar,Geçmez,175837,Ferter,-,"Tr20,6x1",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-01,Vida Tampon Mastar,Geçer/Geçmez,559450,Ferter,-,1 1/4''-18 UNEF 2B,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-02,Vida Tampon Mastar,Geçer/Geçmez,507272,Ferter,-,1 3/16''-16 UN 2B,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-03,Vida Tampon Mastar,Geçer/Geçmez,514908,Ferter,-,"M7x0,75-6H LH ",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-04,Vida Tampon Mastar,Geçer/Geçmez,513828,Ferter,-,"M4x0,4-6G",-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VTM-05,Vida Tampon Mastar,Geçer/Geçmez,506157,Ferter,-,M36x1-4G,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-06,Vida Tampon Mastar,Geçer/Geçmez,508667,Ferter,-,M36x1-4G,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-07,Vida Tampon Mastar,Geçer/Geçmez,585090,Ferter,-,"M5x0,5-6H",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-08,Vida Tampon Mastar,Geçer/Geçmez,594859,Ferter,-,1 1/4''-18 UNEF 2B,-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VTM-09,Vida Tampon Mastar,Geçer/Geçmez,530069,Ferter,-,1 3/16''-16 UN 2B,-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VTM-10,Vida Tampon Mastar,Geçer/Geçmez,513827,Ferter,-,"M4x0,4-4G",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-11,Vida Tampon Mastar,Geçer/Geçmez,514907,Ferter,-,"M5x0,4-4G",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-12,Vida Tampon Mastar,Geçer/Geçmez,551080,Ferter,-,"M16x1,5-6H",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-13,Vida Tampon Mastar,Geçer/Geçmez,551081,Ferter,-,"M16x1,5-6H",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-14,Vida Tampon Mastar,Geçer/Geçmez,587494,Ferter,-,"M4x0,7-5H HELICOIL",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-15,Vida Tampon Mastar,Geçer/Geçmez,587495,Ferter,-,"M4x0,7-5H HELICOIL",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-16,Vida Tampon Mastar,Geçer/Geçmez,587496,Ferter,-,"M4x0,7-5H HELICOIL",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-17,Vida Tampon Mastar,Geçer/Geçmez,587497,Ferter,-,"M4x0,7-5H HELICOIL",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-18,Vida Tampon Mastar,Geçer/Geçmez,566456,Ferter,-,"M5x0,8-5H HELICOIL",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-19,Vida Tampon Mastar,Geçer/Geçmez,566463,Ferter,-,"M5x0,8-5H HELICOIL",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-20,Vida Tampon Mastar,Geçer/Geçmez,587492,Ferter,-,"M6x0,75-6H",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-21,Vida Tampon Mastar,Geçer/Geçmez,587493,Ferter,-,"M6x0,75-6H",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-22,Vida Tampon Mastar,Geçer/Geçmez,576305,Ferter,-,"1 1/16""-32 UN 2B",-,-,,1 / Yıl,Mar-25,-,KULLANILMIYOR,Üretim,-,
VTM-23,Vida Tampon Mastar,Geçer/Geçmez,66017,Ferter,-,1 1/4-18 UNEF 2B,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-24,Vida Tampon Mastar,Geçer/Geçmez,559449,Ferter,-,"1 3/16""-16 UN 2B ",-,-,,1 / Yıl,Dec-00,-,HURDA,Laboratuvar,-,
VTM-25,Vida Tampon Mastar,Geçer/Geçmez,513827,Ferter,-,"M4x0,4-4G",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,Ersin Bey tarafından alındı. 06/03/2025
VTM-26,Vida Tampon Mastar,Geçer/Geçmez,679578,Ferter,-,Nr.10-32 UNF 3B Helicoil,-,-,,1 / Yıl,Mar-25,-,KULLANILMIYOR,Üretim,-,
VTM-27,Vida Tampon Mastar,Geçer/Geçmez,99635,-,-,M10x1-6H,-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VTM-28,Vida Tampon Mastar,Geçer/Geçmez,102851,Ferter,-,M8x1-6H,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-29,Vida Tampon Mastar,Geçer/Geçmez,102850,Ferter,-,M8x1-6H,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-30,Vida Tampon Mastar,Geçer/Geçmez,-,-,-,M3-6H,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-31,Vida Tampon Mastar,Geçer/Geçmez,-,-,-,M3-6H,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-32,Vida Tampon Mastar,Geçer/Geçmez,454944,Ferter,-,M10x1-6H,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-33,Vida Tampon Mastar,Geçer/Geçmez,99635,Ferter,-,M10x1-6H,-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-34,Vida Tampon Mastar,Geçer/Geçmez,-,Ferter,-,M3-6H,-,-,,1 / Yıl,Dec-00,-,KAYIP,Laboratuvar,-,
VTM-35,Vida Tampon Mastar,Geçer/Geçmez,517154,Ferter,-,"M5x0,4-4G",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-36,Vida Tampon Mastar,Geçer/Geçmez,517155,Ferter,-,"M5x0,4-4G",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,
VTM-37,Vida Tampon Mastar,Geçer/Geçmez,-,-,-,"M5x0,5-6H",-,-,,1 / Yıl,Dec-00,-,KULLANILMIYOR,Laboratuvar,-,'''

        csv_file = StringIO(csv_data)
        reader = csv.DictReader(csv_file)

        for row in reader:
            # Map CSV fields to model fields
            ControlGauge.objects.create(
                stock_code=row['mastar_code'],
                stock_name=row['mastar_name'],
                stock_type=row['mastar_type'] if row['mastar_type'] != '-' else None,
                serial_number=row['mastar_serial_name'] if row['mastar_serial_name'] != '-' else None,
                brand=row['brand'] if row['brand'] != '-' else None,
                model=row['model'] if row['model'] != '-' else None,
                measuring_range=row['measuring_range'] if row['measuring_range'] != '-' else None,
                resolution=row['resolution'] if row['resolution'] != '-' else None,
                calibration_made_by=row['calibration_made_by'] if row['calibration_made_by'] != '-' else None,
                calibration_date=self.parse_date(row['calibration_date']),
                calibration_per_year=row['calibration_per_year'],
                upcoming_calibration_date=self.parse_date(row['upcoming_calibration_date']),
                certificate_no=row['certificate_no'] if row['certificate_no'] != '-' else None,
                status=row['status'],
                current_location=row['current_location'] if row['current_location'] != '-' else None,
                scrap_lost_date=self.parse_date(row['scrap_lost_date']),
                description=row['description'] if row['description'] != '-' else None
            )

        self.stdout.write(self.style.SUCCESS('Successfully loaded gauge data')) 