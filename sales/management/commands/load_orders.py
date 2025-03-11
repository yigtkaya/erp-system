import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from sales.models import SalesOrder, SalesOrderItem
from erp_core.models import Customer, ProductType
from inventory.models import Product, InventoryCategory
from collections import defaultdict

class Command(BaseCommand):
    help = 'Load orders from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def parse_date(self, date_str):
        if not date_str:
            return None
        
        # Try different date formats
        date_formats = [
            '%m/%d/%y',  # 2/10/25
            '%d/%m/%y',  # 10/2/25
            '%d.%m.%Y',  # 13.05.2024
            '%m/%d/%Y',  # 2/10/2025
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str.strip(), date_format).date()
            except ValueError:
                continue
        return None

    def clean_customer_code(self, code):
        """Clean customer code to meet validation requirements"""
        # Replace commas with dots
        cleaned = code.replace(',', '.')
        # Remove any other non-alphanumeric characters except periods
        cleaned = ''.join(c for c in cleaned if c.isalnum() or c == '.')
        # Ensure it's at least 4 characters
        if len(cleaned) < 4:
            # Pad with zeros if needed
            cleaned = cleaned.zfill(4)
        return cleaned

    def create_missing_product(self, product_code):
        """Create a new product with default values"""
        try:
            # Get or create MAMUL category as default
            mamul_category, _ = InventoryCategory.objects.get_or_create(
                name='MAMUL',
                defaults={'description': 'Finished Products'}
            )

            # Create the product with default values
            product = Product.objects.create(
                product_code=product_code,
                product_name=f"Product {product_code}",  # Default name
                product_type=ProductType.MONTAGED,  # Default type
                inventory_category=mamul_category,
                current_stock=0
            )
            self.stdout.write(
                self.style.SUCCESS(f"Created new product: {product_code}")
            )
            return product
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Failed to create product {product_code}: {str(e)}")
            )
            raise

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Group orders by order number
                orders_by_number = defaultdict(list)
                total_lines = 0
                empty_lines = 0
                order_details = defaultdict(lambda: {'count': 0, 'products': set(), 'dates': set()})
                
                for row in reader:
                    total_lines += 1
                    # Skip empty rows
                    if not any(row.values()):
                        empty_lines += 1
                        continue
                    orders_by_number[row['order_number']].append(row)
                    # Collect details about each order
                    order_num = row['order_number']
                    order_details[order_num]['count'] += 1
                    order_details[order_num]['products'].add(row['product'])
                    order_details[order_num]['dates'].add(row['deadline_date'])
                
                # Store the total number of orders for progress reporting
                total_orders = len(orders_by_number)
                processed_orders = 0
                processed_lines = 0
                created_products = []  # To keep track of newly created products
                orders_with_multiple_lines = {}  # Track orders with multiple lines
                
                with transaction.atomic():
                    for order_number, order_items in orders_by_number.items():
                        try:
                            if len(order_items) > 1:
                                orders_with_multiple_lines[order_number] = len(order_items)
                            
                            # First check and create any missing products
                            for item in order_items:
                                product_code = item['product']
                                try:
                                    Product.objects.get(product_code=product_code)
                                except Product.DoesNotExist:
                                    self.create_missing_product(product_code)
                                    created_products.append(product_code)
                            
                            # Get the first item for order details
                            first_item = order_items[0]
                            
                            # Clean and prepare customer code
                            customer_code = self.clean_customer_code(first_item['customer'])
                            
                            # Get or create customer with proper code
                            customer, _ = Customer.objects.get_or_create(
                                code=customer_code,
                                defaults={
                                    'name': first_item['customer']
                                }
                            )
                            
                            # Create order
                            order = SalesOrder.objects.create(
                                order_number=order_number,
                                customer=customer,
                                created_at=self.parse_date(first_item['receiving_date']),
                                status='OPEN'
                            )
                            
                            # Process each order item
                            for item in order_items:
                                product = Product.objects.get(product_code=item['product'])
                                # Create order item
                                SalesOrderItem.objects.create(
                                    sales_order=order,
                                    product=product,
                                    ordered_quantity=int(float(item['ordered_quantity'])),
                                    deadline_date=self.parse_date(item['deadline_date']),
                                    kapsam_deadline_date=self.parse_date(item['kapsam_deadline_date']),
                                    receiving_date=self.parse_date(item['receiving_date']),
                                    fulfilled_quantity=0
                                )
                                processed_lines += 1
                            
                            processed_orders += 1
                            self.stdout.write(f"Processed {processed_orders}/{total_orders} orders", ending='\r')
                            
                        except Exception as e:
                            self.stderr.write(
                                self.style.ERROR(
                                    f'Error processing order {order_number}: {str(e)}'
                                )
                            )
                            continue
                
                # Print summary of created products
                if created_products:
                    self.stdout.write("\nThe following products were automatically created:")
                    for product_code in created_products:
                        self.stdout.write(f"  - Created product: {product_code}")
                
                # Print detailed summary of orders with multiple lines
                if orders_with_multiple_lines:
                    self.stdout.write("\nDetailed breakdown of orders with multiple lines:")
                    for order_num in sorted(orders_with_multiple_lines.keys()):
                        details = order_details[order_num]
                        self.stdout.write(
                            f"\nOrder {order_num}:"
                            f"\n  - Number of lines: {details['count']}"
                            f"\n  - Products: {', '.join(sorted(details['products']))}"
                            f"\n  - Different delivery dates: {', '.join(sorted(details['dates']))}"
                        )
                
                self.stdout.write(self.style.SUCCESS(
                    f'\nProcessing Summary:'
                    f'\n- Total CSV lines: {total_lines}'
                    f'\n- Empty lines skipped: {empty_lines}'
                    f'\n- Valid lines processed: {processed_lines}'
                    f'\n- Unique orders processed: {processed_orders}'
                    f'\n- New products created: {len(created_products)}'
                    f'\n- Orders with multiple lines: {len(orders_with_multiple_lines)}'
                ))
                
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'File not found: {csv_file}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {str(e)}')) 