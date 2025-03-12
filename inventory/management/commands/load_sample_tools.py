from django.core.management.base import BaseCommand
from inventory.models import Tool
import uuid

class Command(BaseCommand):
    help = 'Load sample tool data'

    def handle(self, *args, **kwargs):
        # Clear existing data
        Tool.objects.all().delete()

        # Generate a UUID for the table
        table_uuid = uuid.uuid4()

        # Sample tool data
        tools = [
            {
                'stock_code': 'T001',
                'product_code': 'PC001',
                'supplier_name': 'Sandvik',
                'tool_type': 'END_MILL',
                'status': 'AVAILABLE',
                'description': '4 Flute Carbide End Mill',
                'unit_price_tl': 1250.00,
                'unit_price_euro': 35.00,
                'unit_price_usd': 40.00,
                'tool_insert_code': 'IC001',
                'tool_material': 'CARBIDE',
                'tool_diameter': 12.0,
                'tool_length': 75.0,
                'tool_width': 12.0,
                'tool_height': 12.0,
                'tool_angle': 30.0,
                'tool_radius': 0.5,
                'tool_connection_diameter': 12.0,
                'row': 1,
                'column': 1,
                'table_id': table_uuid,
                'quantity': 5
            },
            {
                'stock_code': 'T002',
                'product_code': 'PC002',
                'supplier_name': 'Iscar',
                'tool_type': 'DRILL',
                'status': 'AVAILABLE',
                'description': 'Solid Carbide Drill',
                'unit_price_tl': 950.00,
                'unit_price_euro': 28.00,
                'unit_price_usd': 32.00,
                'tool_insert_code': 'IC002',
                'tool_material': 'CARBIDE',
                'tool_diameter': 8.0,
                'tool_length': 60.0,
                'tool_width': 8.0,
                'tool_height': 8.0,
                'tool_angle': 118.0,
                'tool_radius': 0.0,
                'tool_connection_diameter': 8.0,
                'row': 1,
                'column': 2,
                'table_id': table_uuid,
                'quantity': 3
            },
            {
                'stock_code': 'T003',
                'product_code': 'PC003',
                'supplier_name': 'Mitsubishi',
                'tool_type': 'FACE_MILL',
                'status': 'AVAILABLE',
                'description': 'Face Mill with Inserts',
                'unit_price_tl': 2500.00,
                'unit_price_euro': 70.00,
                'unit_price_usd': 80.00,
                'tool_insert_code': 'IC003',
                'tool_material': 'HSS',
                'tool_diameter': 50.0,
                'tool_length': 40.0,
                'tool_width': 50.0,
                'tool_height': 25.0,
                'tool_angle': 45.0,
                'tool_radius': 0.0,
                'tool_connection_diameter': 22.0,
                'row': 1,
                'column': 3,
                'table_id': table_uuid,
                'quantity': 2
            }
        ]

        for tool_data in tools:
            Tool.objects.create(**tool_data)

        self.stdout.write(self.style.SUCCESS('Successfully loaded sample tool data')) 