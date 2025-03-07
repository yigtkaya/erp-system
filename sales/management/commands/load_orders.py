from django.core.management.base import BaseCommand
from django.db import transaction
from sales.models import SalesOrder, SalesOrderItem
from erp_core.models import Customer
from inventory.models import Product
from datetime import datetime
import csv
import sys
import os

class Command(BaseCommand):
    help = 'Load sales orders from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        
        # Make path absolute if it's relative
        if not os.path.isabs(csv_file):
            csv_file = os.path.join(os.getcwd(), csv_file)
            
        self.stdout.write(self.style.SUCCESS(f"Reading CSV file from: {csv_file}"))
        
        # Customer mapping
        customer_mapping = {
            'SARSILMAZ': '120.100.7510036236',
            'KALE': '120.100.4910018545'
        }

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                with transaction.atomic():
                    for row in reader:
                        # Skip empty rows
                        if not row['Firma'] or not row['Alım Sipariş No']:
                            continue

                        # Get customer
                        customer_code = customer_mapping.get(row['Firma'])
                        if not customer_code:
                            self.stdout.write(self.style.WARNING(
                                f"Skipping row: Unknown customer {row['Firma']}"
                            ))
                            continue

                        try:
                            customer = Customer.objects.get(code=customer_code)
                        except Customer.DoesNotExist:
                            self.stdout.write(self.style.ERROR(
                                f"Customer not found with code {customer_code}"
                            ))
                            continue

                        # Parse date
                        try:
                            order_date = datetime.strptime(row['Alım Sipariş\nTarihi'], '%m/%d/%y').date()
                        except ValueError:
                            if row['Alım Sipariş\nTarihi']:  # If date exists but invalid
                                self.stdout.write(self.style.WARNING(
                                    f"Invalid date format for order {row['Alım Sipariş No']}, using current date"
                                ))
                            order_date = datetime.now().date()

                        # Create or update sales order
                        order, created = SalesOrder.objects.update_or_create(
                            order_number=row['Alım Sipariş No'].strip(),
                            defaults={
                                'customer': customer,
                                'order_receiving_date': order_date,
                                'deadline_date': order_date,  # Using same date as deadline for now
                                'status': 'OPEN'
                            }
                        )

                        # Get product
                        try:
                            product = Product.objects.get(product_code=row['Ürün Sicil Kodu'])
                        except Product.DoesNotExist:
                            self.stdout.write(self.style.ERROR(
                                f"Product not found with code {row['Ürün Sicil Kodu']}"
                            ))
                            continue

                        # Create or update order item
                        quantity = int(float(row['Sipariş\nMiktar'].replace(',', '')))
                        fulfilled = int(float(row['Sipariş Teslim Miktar'].replace(',', '') or 0))
                        
                        order_item, item_created = SalesOrderItem.objects.update_or_create(
                            sales_order=order,
                            product=product,
                            defaults={
                                'quantity': quantity,
                                'fulfilled_quantity': fulfilled
                            }
                        )

                        status = 'Created' if created else 'Updated'
                        self.stdout.write(self.style.SUCCESS(
                            f"{status} order {order.order_number} with item {product.product_code}"
                        ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {csv_file}"))
            sys.exit(1)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            sys.exit(1)

        self.stdout.write(self.style.SUCCESS('Successfully loaded sales orders')) 