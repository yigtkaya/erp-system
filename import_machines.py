#!/usr/bin/env python
"""
Script to import machines from backup data into the current database
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_core.settings')
django.setup()

from manufacturing.models import Machine, MachineType, MachineStatus
from datetime import datetime, date
from django.utils import timezone
from decimal import Decimal

def map_machine_type(turkish_type):
    """Map Turkish machine types to English enums"""
    mapping = {
        'İşleme Merkezi': MachineType.CNC_MILLING,
        'CNC Torna Merkezi': MachineType.CNC_LATHE,
        'CNC Kayar Otomat': MachineType.CNC_LATHE,
    }
    return mapping.get(turkish_type, MachineType.OTHER)

def map_axis_count(axis_str):
    """Map Turkish axis descriptions to English enums"""
    if not axis_str:
        return None
    axis_mapping = {
        '2EKSEN': 'AXIS_2',
        '3EKSEN': 'AXIS_3', 
        '4EKSEN': 'AXIS_4',
        '5EKSEN': 'AXIS_5',
        '8.5EKSEN': 'MULTI',
        '9EKSEN': 'MULTI'
    }
    return axis_mapping.get(axis_str, None)

def safe_decimal(value):
    """Safely convert value to Decimal or return None"""
    if value is None or value == '' or value == '\\N':
        return None
    try:
        return Decimal(str(value))
    except:
        return None

def safe_int(value):
    """Safely convert value to int or return None"""
    if value is None or value == '' or value == '\\N':
        return None
    try:
        return int(value)
    except:
        return None

def safe_date(value):
    """Safely convert value to date or return None"""
    if value is None or value == '' or value == '\\N':
        return None
    try:
        # If it's already a date object, return it
        if isinstance(value, date):
            return value
        # Try to parse as string
        return datetime.strptime(str(value), '%Y-%m-%d').date()
    except:
        return None

def main():
    print("Starting machine import...")

    # Machine data from backup
    machines_data = [
        (1, '2025-02-19 12:14:57+00', '2025-02-19 12:20:29.185371+00', 'CNC-01', 'İşleme Merkezi', 'MAZAK', 'VARIAXIS İ-500', '5EKSEN', '66.00', 'BBT-40', None, None, None, 18000, 30, 'Mazatrol Matrix-Ⅱ', '262599', '8000.00', '500 x 350', '', 'AVAILABLE', None, None, None, 90, None, '', None, '15.00'),
        (2, '2025-02-19 12:14:57+00', '2025-02-19 12:20:38.983803+00', 'CNC-03', 'İşleme Merkezi', 'MAZAK', 'FJV-200', '3EKSEN', '39.80', 'SK-40', None, None, None, 12000, 30, 'MAZATROL FUSUIN 640M', '138285', '4700.00', '500 x 650', '', 'AVAILABLE', None, None, None, 90, None, '', None, '5.00'),
        (3, '2025-02-19 12:14:57+00', '2025-02-19 12:21:22.094298+00', 'CNC-04', 'İşleme Merkezi', 'MAZAK', 'VARIAXIS 500-5X Ⅱ-2012', '5EKSEN', '55.00', 'HSK-A63', None, None, None, 18000, 30, 'Mazatrol Matrix-Ⅰ', '239171', '7500.00', '500 x 350', '', 'AVAILABLE', None, None, None, 90, None, '', None, '5.00'),
        (4, '2025-02-19 12:14:57+00', '2025-02-19 12:21:32.093306+00', 'CNC-05', 'İşleme Merkezi', 'MAZAK', 'CV5-500', '5EKSEN', '52.05', 'BT-40', None, None, None, 12000, 30, 'Mazatrol Smoot', '308505', '6780.00', '500 x 320', '', 'AVAILABLE', None, None, None, 90, None, '', None, '15.00'),
        (5, '2025-02-19 12:14:57+00', '2025-02-19 12:22:33.40781+00', 'CNC-07', 'CNC Torna Merkezi', 'MAZAK', 'QTN-100', '2EKSEN', '24.00', 'TURRET', None, None, None, 6000, 12, 'Mazatrol 640T Nexus', '311173444', '3300.00', '300X500', '', 'AVAILABLE', None, None, None, 90, None, '', None, None),
        (6, '2025-02-19 12:14:57+00', '2025-02-19 12:22:43.454636+00', 'CNC-08', 'CNC Kayar Otomat', 'CITIZEN', 'L20E-2M10', '8.5EKSEN', '7.30', None, None, None, None, 6000, 26, 'Cincom', 'QF7449', '2350.00', 'Ø 25', '', 'AVAILABLE', None, None, None, 90, None, '', None, None),
        (7, '2025-02-19 12:14:57+00', '2025-02-19 12:23:03.27376+00', 'CNC-10', 'CNC Kayar Otomat', 'CITIZEN', 'L20E-2M12', '9EKSEN', '7.30', None, None, None, None, 6000, 26, 'Cincom', 'QF3967', '2350.00', 'Ø 20', '', 'AVAILABLE', None, None, None, 90, None, '', None, None),
        (8, '2025-02-19 12:14:57+00', '2025-02-19 12:23:24.570494+00', 'CNC-11', 'İşleme Merkezi', 'KOMATECH', 'GMT 400 Ⅱ', '3EKSEN', '25.00', 'BT-30', None, None, None, 15000, 14, 'MITSUBISHI M70', '400II0391', '2500.00', '300X300', '', 'AVAILABLE', None, None, None, 90, None, '', None, None),
        (9, '2025-02-19 12:14:57+00', '2025-02-19 12:24:22.15831+00', 'CNC-12', 'İşleme Merkezi', 'LITZ', 'LU 620', '5EKSEN', '25.00', 'BT-40', None, None, None, 12000, 32, 'HEIDENHAIN İTNC-530', '6LUD00156', '8640.00', 'Ø 600', '', 'AVAILABLE', None, None, None, 90, None, '', None, '20.00'),
        (10, '2025-02-19 12:14:57+00', '2025-02-19 12:24:36.073768+00', 'CNC-13', 'İşleme Merkezi', 'YCM', 'NXV 600A', '3EKSEN', '14.00', 'BBT-40', None, None, None, 12000, None, None, '0491', None, None, '', 'AVAILABLE', None, None, None, 90, None, '', None, None),
        (11, '2025-02-19 12:14:57+00', '2025-02-19 12:24:57.274034+00', 'CNC-14', 'İşleme Merkezi', 'KOMATECH', 'KM 450D', '4EKSEN', '38.00', None, None, None, None, 12000, None, None, 'W450D009', '5500.00', None, '', 'AVAILABLE', None, None, None, 90, None, '', None, None),
        (12, '2025-02-19 12:14:57+00', '2025-02-19 12:25:19.880125+00', 'CNC-15', 'İşleme Merkezi', 'MAZAK', 'VARIAXIS 500-5X Ⅱ-2007', '5EKSEN', '44.00', None, None, None, None, None, None, None, '203409', '7500.00', 'Ø 500', '', 'AVAILABLE', None, None, None, 90, None, '', None, None),
        (13, '2025-02-19 12:14:57+00', '2025-02-19 12:51:48.257157+00', 'CNC-16', 'İşleme Merkezi', 'MAZAK', 'VARIAXIS 500-5X Ⅱ-2006', '5EKSEN', '51.00', None, None, None, None, None, None, None, '189864', '7500.00', None, '', 'AVAILABLE', None, None, None, 90, None, '', None, None),
    ]

    imported_count = 0
    skipped_count = 0

    for machine_data in machines_data:
        (orig_id, created_at, modified_at, machine_code, machine_type_tr, brand, model, 
         axis_count_tr, motor_power_kva, holder_type, spindle_10_percent, spindle_30_percent, 
         power_hp, spindle_speed_rpm, tool_count, nc_control_unit, serial_number, 
         machine_weight_kg, max_part_size, description, status, created_by_id, modified_by_id, 
         last_maintenance_date, maintenance_interval, next_maintenance_date, maintenance_notes, 
         manufacturing_year, internal_cooling) = machine_data

        # Check if machine already exists
        if Machine.objects.filter(machine_code=machine_code).exists():
            print(f"Machine {machine_code} already exists, skipping...")
            skipped_count += 1
            continue

        try:
            machine = Machine.objects.create(
                machine_code=machine_code,
                machine_type=map_machine_type(machine_type_tr),
                brand=brand or '',
                model=model or '',
                axis_count=map_axis_count(axis_count_tr),
                internal_cooling=safe_decimal(internal_cooling),
                motor_power_kva=safe_decimal(motor_power_kva),
                holder_type=holder_type or '',
                spindle_motor_power_10_percent_kw=safe_decimal(spindle_10_percent),
                spindle_motor_power_30_percent_kw=safe_decimal(spindle_30_percent),
                power_hp=safe_decimal(power_hp),
                spindle_speed_rpm=safe_int(spindle_speed_rpm),
                tool_count=safe_int(tool_count),
                nc_control_unit=nc_control_unit or '',
                serial_number=serial_number if serial_number else None,
                machine_weight_kg=safe_decimal(machine_weight_kg),
                max_part_size=max_part_size or '',
                description=description or '',
                status=MachineStatus.AVAILABLE,
                maintenance_interval=maintenance_interval or 90,
                last_maintenance_date=safe_date(last_maintenance_date),
                next_maintenance_date=safe_date(next_maintenance_date),
                maintenance_notes=maintenance_notes or '',
                manufacturing_year=safe_date(manufacturing_year)
            )
            
            print(f"✅ Imported machine: {machine.machine_code} - {machine.brand} {machine.model}")
            imported_count += 1
            
        except Exception as e:
            print(f"❌ Error importing machine {machine_code}: {str(e)}")
            skipped_count += 1

    print(f"\n🎉 Import completed!")
    print(f"✅ Imported: {imported_count} machines")
    print(f"⏭️  Skipped: {skipped_count} machines")
    print(f"📊 Total machines in database: {Machine.objects.count()}")

if __name__ == '__main__':
    main() 