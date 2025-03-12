from django.core.management.base import BaseCommand
from inventory.models import ControlGauge

class Command(BaseCommand):
    help = 'Load sample gauge data'

    def handle(self, *args, **kwargs):
        # Clear existing data
        ControlGauge.objects.all().delete()

        # Sample gauge data
        gauges = [
            {
                'stock_code': 'G001',
                'stock_name': 'Digital Caliper',
                'stock_type': 'CALIPER',
                'stock_description': '0-150mm digital caliper with 0.01mm resolution. Calibration due: 2024-07-15'
            },
            {
                'stock_code': 'G002',
                'stock_name': 'Micrometer',
                'stock_type': 'MICROMETER',
                'stock_description': '0-25mm digital micrometer with 0.001mm resolution. Calibration due: 2024-08-01'
            },
            {
                'stock_code': 'G003',
                'stock_name': 'Height Gauge',
                'stock_type': 'HEIGHT_GAUGE',
                'stock_description': '0-300mm digital height gauge with 0.01mm resolution. Calibration due: 2024-07-20'
            },
            {
                'stock_code': 'G004',
                'stock_name': 'Dial Indicator',
                'stock_type': 'DIAL_INDICATOR',
                'stock_description': '0-10mm dial indicator with magnetic base, 0.01mm resolution. Calibration due: 2024-08-15'
            },
            {
                'stock_code': 'G005',
                'stock_name': 'Thread Gauge Set',
                'stock_type': 'THREAD_GAUGE',
                'stock_description': 'Metric thread pitch gauge set, 0.25-6.0mm range. Calibration due: 2024-09-01'
            }
        ]

        for gauge_data in gauges:
            ControlGauge.objects.create(**gauge_data)

        self.stdout.write(self.style.SUCCESS('Successfully loaded sample gauge data')) 