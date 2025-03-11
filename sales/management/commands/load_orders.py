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
        # Remove any non-alphanumeric characters except periods
        cleaned = ''.join(c for c in code if c.isalnum() or c == '.')
        # Ensure it's at least 4 characters
        if len(cleaned) < 4:
            # Pad with zeros if needed
            cleaned = cleaned.zfill(4)
        return cleaned

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Group orders by order number
                orders_by_number = defaultdict(list)
                for row in reader:
                    # Skip empty rows
                    if not any(row.values()):
                        continue
                    orders_by_number[row['order_number']].append(row)
                
                # Store the total number of orders for progress reporting
                total_orders = len(orders_by_number)
                processed_orders = 0
                skipped_orders = {}  # To keep track of skipped orders and their missing products
                
                with transaction.atomic():
                    for order_number, order_items in orders_by_number.items():
                        try:
                            # First verify all products exist
                            missing_products = []
                            for item in order_items:
                                try:
                                    Product.objects.get(product_code=item['product'])
                                except Product.DoesNotExist:
                                    missing_products.append(item['product'])
                            
                            # If any products are missing, skip the entire order
                            if missing_products:
                                skipped_orders[order_number] = missing_products
                                self.stderr.write(
                                    self.style.WARNING(
                                        f"Skipping order {order_number} - missing products: {', '.join(missing_products)}"
                                    )
                                )
                                continue
                            
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
                            
                            # Create order only if all products exist
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
                            
                            processed_orders += 1
                            self.stdout.write(f"Processed {processed_orders}/{total_orders} orders", ending='\r')
                            
                        except Exception as e:
                            self.stderr.write(
                                self.style.ERROR(
                                    f'Error processing order {order_number}: {str(e)}'
                                )
                            )
                            continue
                
                # Print summary of skipped orders
                if skipped_orders:
                    self.stderr.write("\nThe following orders were skipped due to missing products:")
                    for order_num, missing_prods in skipped_orders.items():
                        self.stderr.write(f"Order {order_num}:")
                        for prod in missing_prods:
                            self.stderr.write(f"  - Missing product: {prod}")
                
                self.stdout.write(self.style.SUCCESS(
                    f'\nSuccessfully processed {processed_orders} orders. '
                    f'Skipped {len(skipped_orders)} orders due to missing products.'
                ))
                
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'File not found: {csv_file}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {str(e)}')) 