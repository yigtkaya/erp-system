from django.core.management.base import BaseCommand
from django.db import transaction
from manufacturing.models import Machine, MachineType, AxisCount
from datetime import datetime

class Command(BaseCommand):
    help = 'Loads machine data from SQL file into database'

    def handle(self, *args, **options):
        self.stdout.write('Loading machine data...')

        def parse_date(date_str):
            if not date_str:
                return None
            try:
                # Handle different year formats from SQL data
                if len(date_str) == 4:  # Year-only format
                    return datetime(int(date_str), 1, 1).date()
                return datetime.strptime(date_str, '%b %y').date()
            except ValueError:
                return None

        def parse_internal_cooling(value):
            if not value or value == '-':
                return None
            try:
                # Extract numeric value from strings like '15 bar' or '5 bar'
                return float(value.split()[0])
            except (ValueError, IndexError):
                return None

        AXIS_MAPPING = {
            '5 Eksen simultene beşik tipi': AxisCount.FIVE_AXIS,
            '3 Eksen CNC İşleme Merkezi': AxisCount.THREE_AXIS,
            '2 Eksen CNC Torna': AxisCount.TWO_AXIS,
            '8,5 Eksen CNC Kayar Otomat': AxisCount.EIGHT_POINT_FIVE_AXIS,
            '9 Eksen CNC Kayar Otomat': AxisCount.NINE_AXIS,
            '4 Eksen Divizörlü': AxisCount.FOUR_AXIS
        }

        machine_data = [
            {
                'machine_code': 'CNC-01',
                'machine_type': MachineType.PROCESSING_CENTER,
                'brand': 'MAZAK',
                'model': 'VARIAXIS İ-500',
                'axis_count': '5EKSEN',
                'internal_cooling': parse_internal_cooling('15 bar'),
                'motor_power_kva': 66.0,
                'holder_type': 'BBT-40',
                'spindle_motor_power_10_percent_kw': 18.5,
                'spindle_motor_power_30_percent_kw': 15.0,
                'power_hp': 26.0,
                'spindle_speed_rpm': 18000,
                'tool_count': 30,
                'nc_control_unit': 'Mazatrol Matrix-Ⅱ',
                'serial_number': '262599',
                'machine_weight_kg': 8000.0,
                'max_part_size': '500 x 350',
                'description': None
            },
            {
                'machine_code': 'CNC-03',
                'machine_type': MachineType.PROCESSING_CENTER,
                'brand': 'MAZAK',
                'model': 'FJV-200',
                'axis_count': '3EKSEN',
                'internal_cooling': parse_internal_cooling('5 bar'),
                'motor_power_kva': 39.8,
                'holder_type': 'SK-40',
                'spindle_motor_power_10_percent_kw': 26.0,
                'spindle_motor_power_30_percent_kw': 26.0,
                'power_hp': 36.0,
                'spindle_speed_rpm': 12000,
                'tool_count': 30,
                'nc_control_unit': 'MAZATROL FUSUIN 640M',
                'serial_number': '138285',
                'machine_weight_kg': 4700.0,
                'max_part_size': '500 x 650',
                'description': None
            },
            {
                'machine_code': 'CNC-04',
                'machine_type': MachineType.PROCESSING_CENTER,
                'brand': 'MAZAK',
                'model': 'VARIAXIS 500-5X Ⅱ-2012',
                'axis_count': '5EKSEN',
                'internal_cooling': parse_internal_cooling('5 bar'),
                'motor_power_kva': 55.0,
                'holder_type': 'HSK-A63',
                'spindle_motor_power_10_percent_kw': 18.5,
                'spindle_motor_power_30_percent_kw': 15.0,
                'power_hp': 26.0,
                'spindle_speed_rpm': 18000,
                'tool_count': 30,
                'nc_control_unit': 'Mazatrol Matrix-Ⅰ',
                'serial_number': '239171',
                'machine_weight_kg': 7500.0,
                'max_part_size': '500 x 350',
                'description': None
            },
            {
                'machine_code': 'CNC-05',
                'machine_type': MachineType.PROCESSING_CENTER,
                'brand': 'MAZAK',
                'model': 'CV5-500',
                'axis_count': '5EKSEN',
                'internal_cooling': parse_internal_cooling('15 bar'),
                'motor_power_kva': 52.05,
                'holder_type': 'BT-40',
                'spindle_motor_power_10_percent_kw': 18.5,
                'spindle_motor_power_30_percent_kw': 15.0,
                'power_hp': 26.0,
                'spindle_speed_rpm': 12000,
                'tool_count': 30,
                'nc_control_unit': 'Mazatrol Smoot',
                'serial_number': '308505',
                'machine_weight_kg': 6780.0,
                'max_part_size': '500 x 320',
                'description': None
            },
            {
                'machine_code': 'CNC-07',
                'machine_type': MachineType.CNC_TORNA,
                'brand': 'MAZAK',
                'model': 'QTN-100',
                'axis_count': '2EKSEN',
                'internal_cooling': parse_internal_cooling(None),
                'motor_power_kva': 24.0,
                'holder_type': 'TURRET',
                'spindle_motor_power_10_percent_kw': 11.0,
                'spindle_motor_power_30_percent_kw': 9.0,
                'power_hp': 15.0,
                'spindle_speed_rpm': 6000,
                'tool_count': 12,
                'nc_control_unit': 'Mazatrol 640T Nexus',
                'serial_number': '311173444',
                'machine_weight_kg': 3300.0,
                'max_part_size': '300X500',
                'description': None
            },
            {
                'machine_code': 'CNC-08',
                'machine_type': MachineType.CNC_KAYAR_OTOMAT,
                'brand': 'CITIZEN',
                'model': 'L20E-2M10',
                'axis_count': '8.5EKSEN',
                'internal_cooling': parse_internal_cooling(None),
                'motor_power_kva': 7.3,
                'holder_type': None,
                'spindle_motor_power_10_percent_kw': 5.5,
                'spindle_motor_power_30_percent_kw': None,
                'power_hp': 8.0,
                'spindle_speed_rpm': 6000,
                'tool_count': 26,
                'nc_control_unit': 'Cincom',
                'serial_number': 'QF7449',
                'machine_weight_kg': 2350.0,
                'max_part_size': 'Ø 25',
                'description': None
            },
            {
                'machine_code': 'CNC-10',
                'machine_type': MachineType.CNC_KAYAR_OTOMAT,
                'brand': 'CITIZEN',
                'model': 'L20E-2M12',
                'axis_count': '9EKSEN',
                'internal_cooling': parse_internal_cooling(None),
                'motor_power_kva': 7.3,
                'holder_type': None,
                'spindle_motor_power_10_percent_kw': 5.5,
                'spindle_motor_power_30_percent_kw': None,
                'power_hp': 8.0,
                'spindle_speed_rpm': 6000,
                'tool_count': 26,
                'nc_control_unit': 'Cincom',
                'serial_number': 'QF3967',
                'machine_weight_kg': 2350.0,
                'max_part_size': 'Ø 20',
                'description': None
            },
            {
                'machine_code': 'CNC-11',
                'machine_type': MachineType.PROCESSING_CENTER,
                'brand': 'KOMATECH',
                'model': 'GMT 400 Ⅱ',
                'axis_count': '3EKSEN',
                'internal_cooling': parse_internal_cooling(None),
                'motor_power_kva': 25.0,
                'holder_type': 'BT-30',
                'spindle_motor_power_10_percent_kw': 5.5,
                'spindle_motor_power_30_percent_kw': None,
                'power_hp': 8.0,
                'spindle_speed_rpm': 15000,
                'tool_count': 14,
                'nc_control_unit': 'MITSUBISHI M70',
                'serial_number': '400II0391',
                'machine_weight_kg': 2500.0,
                'max_part_size': '300X300',
                'description': None
            },
            {
                'machine_code': 'CNC-12',
                'machine_type': MachineType.PROCESSING_CENTER,
                'brand': 'LITZ',
                'model': 'LU 620',
                'axis_count': '5EKSEN',
                'internal_cooling': parse_internal_cooling('20 bar'),
                'motor_power_kva': 25.0,
                'holder_type': 'BT-40',
                'spindle_motor_power_10_percent_kw': 21.0,
                'spindle_motor_power_30_percent_kw': 18.0,
                'power_hp': 29.0,
                'spindle_speed_rpm': 12000,
                'tool_count': 32,
                'nc_control_unit': 'HEIDENHAIN İTNC-530',
                'serial_number': '6LUD00156',
                'machine_weight_kg': 8640.0,
                'max_part_size': 'Ø 600',
                'description': None
            },
            {
                'machine_code': 'CNC-13',
                'machine_type': MachineType.PROCESSING_CENTER,
                'brand': 'YCM',
                'model': 'NXV 600A',
                'axis_count': '3EKSEN',
                'internal_cooling': parse_internal_cooling(None),
                'motor_power_kva': 14.0,
                'holder_type': 'BBT-40',
                'spindle_motor_power_10_percent_kw': 19.0,
                'spindle_motor_power_30_percent_kw': None,
                'power_hp': 26.0,
                'spindle_speed_rpm': 12000,
                'tool_count': None,
                'nc_control_unit': None,
                'serial_number': '0491',
                'machine_weight_kg': None,
                'max_part_size': None,
                'description': None
            },
            {
                'machine_code': 'CNC-14',
                'machine_type': MachineType.PROCESSING_CENTER,
                'brand': 'KOMATECH',
                'model': 'KM 450D',
                'axis_count': '4EKSEN',
                'internal_cooling': parse_internal_cooling(None),
                'motor_power_kva': 38.0,
                'holder_type': None,
                'spindle_motor_power_10_percent_kw': None,
                'spindle_motor_power_30_percent_kw': None,
                'power_hp': None,
                'spindle_speed_rpm': 12000,
                'tool_count': None,
                'nc_control_unit': None,
                'serial_number': 'W450D009',
                'machine_weight_kg': 5500.0,
                'max_part_size': None,
                'description': None
            },
            {
                'machine_code': 'CNC-15',
                'machine_type': MachineType.PROCESSING_CENTER,
                'brand': 'MAZAK',
                'model': 'VARIAXIS 500-5X Ⅱ-2007',
                'axis_count': '5EKSEN',
                'internal_cooling': parse_internal_cooling(None),
                'motor_power_kva': 44.0,
                'holder_type': None,
                'spindle_motor_power_10_percent_kw': None,
                'spindle_motor_power_30_percent_kw': None,
                'power_hp': None,
                'spindle_speed_rpm': None,
                'tool_count': None,
                'nc_control_unit': None,
                'serial_number': '203409',
                'machine_weight_kg': 7500.0,
                'max_part_size': 'Ø 500',
                'description': None
            },
            {
                'machine_code': 'CNC-16',
                'machine_type': MachineType.PROCESSING_CENTER,
                'brand': 'MAZAK',
                'model': 'VARIAXIS 500-5X Ⅱ-2006',
                'axis_count': '5EKSEN',
                'internal_cooling': parse_internal_cooling(None),
                'motor_power_kva': 51.0,
                'holder_type': None,
                'spindle_motor_power_10_percent_kw': None,
                'spindle_motor_power_30_percent_kw': None,
                'power_hp': None,
                'spindle_speed_rpm': None,
                'tool_count': None,
                'nc_control_unit': None,
                'serial_number': '189864',
                'machine_weight_kg': 7500.0,
                'max_part_size': None,
                'description': None
            }
        ]

        try:
            with transaction.atomic():
                created_count = 0
                skipped_count = 0
                
                for data in machine_data:
                    raw_axis = data.pop('axis_count', '').strip()
                    data['axis_count'] = AXIS_MAPPING.get(raw_axis, None)
                    
                    # Convert string numbers with commas to floats
                    def clean_num(value):
                        if isinstance(value, str):
                            return float(value.replace(',', '').replace(' kg', '').strip())
                        return value
                    
                    # Create machine with proper data types
                    _, created = Machine.objects.get_or_create(
                        machine_code=data['machine_code'],
                        defaults={
                            'machine_type': data['machine_type'],
                            'brand': data['brand'],
                            'model': data['model'],
                            'axis_count': data['axis_count'],
                            'internal_cooling': data['internal_cooling'],
                            'motor_power_kva': clean_num(data['motor_power_kva']),
                            'holder_type': data['holder_type'],
                            'spindle_speed_rpm': clean_num(data['spindle_speed_rpm']),
                            'tool_count': data['tool_count'],
                            'nc_control_unit': data['nc_control_unit'],
                            'serial_number': data['serial_number'],
                            'machine_weight_kg': clean_num(data['machine_weight_kg']),
                            'max_part_size': data['max_part_size'],
                            'description': data['description']
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f"Created machine: {data['machine_code']}")
                    else:
                        skipped_count += 1
                        self.stdout.write(f"Skipped existing machine: {data['machine_code']}")

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully loaded machines. Created: {created_count}, Skipped: {skipped_count}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading machine data: {str(e)}')
            )
            raise 