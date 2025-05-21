import random
import uuid
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
# Assuming your models are in inventory.models
# Adjust the import path if your app structure is different
from inventory.models import Tool, Holder, ToolHolderStatus 
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with mock Tool and Holder data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tools',
            type=int,
            default=10,
            help='Number of mock tools to create'
        )
        parser.add_argument(
            '--holders',
            type=int,
            default=5,
            help='Number of mock holders to create'
        )

    def handle(self, *args, **options):
        num_tools = options['tools']
        num_holders = options['holders']

        self.stdout.write(self.style.SUCCESS(f'Starting to populate mock data...'))

        # Get or create a dummy user for created_by fields if they exist and are required
        # Adjust based on your BaseModel structure if created_by is handled differently
        try:
            # Check if 'created_by' attribute exists in Tool and Holder,
            # as it's inherited from BaseModel
            user_for_base_model = None
            if hasattr(Tool, 'created_by') or hasattr(Holder, 'created_by'):
                user_for_base_model, created = User.objects.get_or_create(
                    username='mock_data_creator',
                    defaults={'is_staff': True, 'is_superuser': False} # Adjust as needed
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created dummy user: {user_for_base_model.username}'))

        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not get/create dummy user. Objects might be created without a user: {e}'))
            user_for_base_model = None


        # Create Tools
        created_tools = 0
        for i in range(num_tools):
            try:
                tool_data = {
                    'stock_code': f'TOOL-MOCK-{uuid.uuid4().hex[:6]}',
                    'supplier_name': f'Supplier {random.choice(["A", "B", "C"])}',
                    'product_code': f'PCODE-{random.randint(1000, 9999)}',
                    'unit_price_tl': Decimal(random.uniform(50, 500)).quantize(Decimal('0.01')),
                    'unit_price_euro': Decimal(random.uniform(5, 50)).quantize(Decimal('0.01')),
                    'unit_price_usd': Decimal(random.uniform(6, 60)).quantize(Decimal('0.01')),
                    'tool_insert_code': f'INSERT-{random.randint(100, 999)}',
                    'tool_material': random.choice(['Carbide', 'HSS', 'Diamond']),
                    'tool_diameter': Decimal(random.uniform(1, 20)).quantize(Decimal('0.01')),
                    'tool_length': Decimal(random.uniform(20, 150)).quantize(Decimal('0.01')),
                    'tool_width': Decimal(random.uniform(0, 10)).quantize(Decimal('0.01')), # Assuming some tools might not have width
                    'tool_height': Decimal(random.uniform(0, 10)).quantize(Decimal('0.01')),# Assuming some tools might not have height
                    'tool_angle': random.uniform(0, 90),
                    'tool_radius': Decimal(random.uniform(0, 5)).quantize(Decimal('0.01')),
                    'tool_connection_diameter': Decimal(random.uniform(5, 25)).quantize(Decimal('0.01')),
                    'tool_type': random.choice(['Drill', 'EndMill', 'Reamer', 'Tap']),
                    'status': random.choice([status.value for status in ToolHolderStatus]),
                    'row': random.randint(1, 10),
                    'column': random.randint(1, 20),
                    'table_id': uuid.uuid4(),
                    'description': f'Mock tool description {i+1}. Lorem ipsum dolor sit amet.',
                    'quantity': Decimal(random.randint(1, 100))
                }
                if user_for_base_model and hasattr(Tool, 'created_by'):
                    tool_data['created_by'] = user_for_base_model
                
                tool = Tool.objects.create(**tool_data)
                created_tools += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not create Tool {i+1}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_tools} Tool(s)'))

        # Create Holders
        created_holders = 0
        for i in range(num_holders):
            try:
                holder_data = {
                    'stock_code': f'HLDR-MOCK-{uuid.uuid4().hex[:6]}',
                    'supplier_name': f'Holder Supplier {random.choice(["X", "Y", "Z"])}',
                    'product_code': f'H-PCODE-{random.randint(1000, 9999)}',
                    'unit_price_tl': Decimal(random.uniform(100, 1000)).quantize(Decimal('0.01')),
                    'unit_price_euro': Decimal(random.uniform(10, 100)).quantize(Decimal('0.01')),
                    'unit_price_usd': Decimal(random.uniform(12, 120)).quantize(Decimal('0.01')),
                    'holder_type': random.choice(['BT40', 'HSK63', 'SK40', 'CAPTO C6']),
                    'pulley_type': random.choice(['Type A', 'Type B', 'None']),
                    'water_cooling': random.choice([True, False]),
                    'distance_cooling': random.choice([True, False]),
                    'tool_connection_diameter': Decimal(random.uniform(10, 50)).quantize(Decimal('0.01')),
                    'holder_type_enum': random.choice(['ER Collet', 'Milling Chuck', 'Hydraulic']), # Assuming this is an enum-like field
                    'status': random.choice([status.value for status in ToolHolderStatus]),
                    'row': random.randint(1, 5),
                    'column': random.randint(1, 10),
                    'table_id': uuid.uuid4(),
                    'description': f'Mock holder description {i+1}. Consectetur adipiscing elit.'
                }
                if user_for_base_model and hasattr(Holder, 'created_by'):
                    holder_data['created_by'] = user_for_base_model

                holder = Holder.objects.create(**holder_data)
                created_holders +=1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not create Holder {i+1}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_holders} Holder(s)'))
        self.stdout.write(self.style.SUCCESS('Mock data population complete!')) 