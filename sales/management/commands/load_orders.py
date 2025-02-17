from django.core.management.base import BaseCommand
from django.db import transaction
from sales.models import SalesOrder, SalesOrderItem
from erp_core.models import Customer
from inventory.models import Product
from datetime import datetime

class Command(BaseCommand):
    help = 'Loads orders data into the database'

    def parse_date(self, date_str):
        if not date_str or date_str == 'null':
            return None
        try:
            return datetime.strptime(date_str, '%d/%m/%y').date()
        except ValueError:
            try:
                return datetime.strptime(date_str, '%d/%m/%Y').date()
            except ValueError:
                return None

    def get_orders_data(self):
        return [
            {
                'customer_current_code': '120.100.4910018545',
                'order_no': 'AS2350423',
                'order_receiving_date': '13/10/23',
                'deadline_date': None,
                'customer_code': '14131000068',
                'stock_code': '03.0.12.0020.00.00.00',
                'stock_name': 'KMG5-P320 BESLEME MANİVELASI',
                'order_amount': 600,
                'order_delivery_amount': 0,
                'order_remaining_amount': 600,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.7510036236',
                'order_no': '4000040035',
                'order_receiving_date': '22/12/22',
                'deadline_date': '22/12/23',
                'customer_code': '207194',
                'stock_code': '03.1.17.0000.00.00.00',
                'stock_name': 'ARPACIK KOMPLESİ SAR56 JND',
                'order_amount': 7000,
                'order_delivery_amount': 6590,
                'order_remaining_amount': 410,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.7510036236',
                'order_no': '4200001325',
                'order_receiving_date': '24/10/23',
                'deadline_date': '10/11/23',
                'customer_code': 'A12-25',
                'stock_code': '03.1.20.0000.00.00.00',
                'stock_name': '556M 20S  ARPACIK KOMPLESI',
                'order_amount': 200,
                'order_delivery_amount': 36,
                'order_remaining_amount': 164,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.4910018545',
                'order_no': 'AS2455776',
                'order_receiving_date': '13/09/24',
                'deadline_date': '11/11/24',
                'customer_code': '14020001337',
                'stock_code': '03.0.00.0019.00.00.00',
                'stock_name': 'CAR816 EL KUNDAĞI ALT (TALAŞLI İMALAT İŞÇ.+TESVİYE)',
                'order_amount': 359,
                'order_delivery_amount': 199,
                'order_remaining_amount': 160,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.7510036236',
                'order_no': '4000040035',
                'order_receiving_date': '22/12/22',
                'deadline_date': '22/12/23',
                'customer_code': '207191',
                'stock_code': '03.1.16.0000.00.00.00',
                'stock_name': 'GEZ KOMPLESİ SAR56 JND',
                'order_amount': 7000,
                'order_delivery_amount': 6500,
                'order_remaining_amount': 500,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.4910018545',
                'order_no': 'AS2350822',
                'order_receiving_date': '07/03/23',
                'deadline_date': '29/02/24',
                'customer_code': '14130000063',
                'stock_code': '03.1.14.0000.00.00.00',
                'stock_name': 'KMG GEZ KOMPLESİ',
                'order_amount': 1750,
                'order_delivery_amount': 0,
                'order_remaining_amount': 1750,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.4910018545',
                'order_no': 'AS2456987',
                'order_receiving_date': '25/11/24',
                'deadline_date': '27/12/24',
                'customer_code': 'P14000000107',
                'stock_code': '03.1.26.0000.00.00.00',
                'stock_name': 'KMG762 GEZ KOMPLESİ',
                'order_amount': 20,
                'order_delivery_amount': 0,
                'order_remaining_amount': 20,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.4910018545',
                'order_no': 'AS2350823',
                'order_receiving_date': '10/11/23',
                'deadline_date': '25/10/24',
                'customer_code': '14020000864',
                'stock_code': '03.1.15.0000.00.00.00',
                'stock_name': 'KMG5-A27 ARPACIK KOMPLESİ',
                'order_amount': 1650,
                'order_delivery_amount': 20,
                'order_remaining_amount': 1630,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.7510036236',
                'order_no': 'SÖZLEŞME',
                'order_receiving_date': None,
                'deadline_date': '19/07/24',
                'customer_code': '222428',
                'stock_code': '03.1.24.0000.00.00.00',
                'stock_name': '556 HMT – ARPACIK KOMPLESİ',
                'order_amount': 1000,
                'order_delivery_amount': 0,
                'order_remaining_amount': 1000,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.4910018545',
                'order_no': 'AS2456356',
                'order_receiving_date': '15/10/24',
                'deadline_date': '31/12/24',
                'customer_code': 'F14020001617',
                'stock_code': '03.0.00.0029.00.00.00',
                'stock_name': 'OBA/MEKANİZMA TALAŞLI İMALAT İŞÇİLİĞİ',
                'order_amount': 5,
                'order_delivery_amount': 0,
                'order_remaining_amount': 5,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.4910018545',
                'order_no': 'AS2452568',
                'order_receiving_date': '04/03/24',
                'deadline_date': '31/07/24',
                'customer_code': '14020000507',
                'stock_code': '03.0.10.0001.01.00.00',
                'stock_name': 'KMG ÜST MEKANİZMA GÖVDESİ',
                'order_amount': 800,
                'order_delivery_amount': 0,
                'order_remaining_amount': 800,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.4910018545',
                'order_no': 'AS2346474',
                'order_receiving_date': '09/02/23',
                'deadline_date': '22/12/23',
                'customer_code': '14131000068',
                'stock_code': '03.0.12.0020.00.00.00',
                'stock_name': 'KMG5-P320 BESLEME MANİVELASI',
                'order_amount': 1600,
                'order_delivery_amount': 1000,
                'order_remaining_amount': 600,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.4910018545',
                'order_no': 'AS2453965',
                'order_receiving_date': '13/05/24',
                'deadline_date': '27/10/24',
                'customer_code': '14020001605',
                'stock_code': '03.1.13.0000.04.00.00',
                'stock_name': 'KMG5-A04-03-01_9 ALT MEKANİZMA PİSTON MİLİ KOMPLESİ',
                'order_amount': 1200,
                'order_delivery_amount': 0,
                'order_remaining_amount': 1200,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.7510036236',
                'order_no': '4200001291',
                'order_receiving_date': '23/06/23',
                'deadline_date': '24/07/23',
                'customer_code': 'A12-42',
                'stock_code': '03.1.21.0000.00.00.00',
                'stock_name': '556M 42S  GEZ KOMPLESI',
                'order_amount': 200,
                'order_delivery_amount': 40,
                'order_remaining_amount': 160,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.4910018545',
                'order_no': 'AS2346977',
                'order_receiving_date': '09/03/23',
                'deadline_date': '12/07/23',
                'customer_code': '14000000044',
                'stock_code': '03.1.13.0000.04.00.00',
                'stock_name': 'KMG 16" ALT MEKANİZMA PİSTON MİLİ KOMPLESİ',
                'order_amount': 600,
                'order_delivery_amount': 92,
                'order_remaining_amount': 508,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.4910018545',
                'order_no': 'AS2456656',
                'order_receiving_date': None,
                'deadline_date': None,
                'customer_code': '14020001335',
                'stock_code': '03.0.00.0020.00.00.00',
                'stock_name': 'CAR816 EL KUNDAĞI ÜST (TALAŞLI İMALAT İŞÇ.+TESVİYE)',
                'order_amount': 1487,
                'order_delivery_amount': 0,
                'order_remaining_amount': 1487,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.4910018545',
                'order_no': 'AS2456762',
                'order_receiving_date': '07/11/24',
                'deadline_date': '25/12/24',
                'customer_code': '14020001835',
                'stock_code': '03.1.25.0000.00.00.00',
                'stock_name': 'KCR556 7,5" GEZ KOMPLESİ(L-R)',
                'order_amount': 1550,
                'order_delivery_amount': 0,
                'order_remaining_amount': 1550,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.4910018545',
                'order_no': 'AS2456867',
                'order_receiving_date': '14/11/24',
                'deadline_date': '14/02/25',
                'customer_code': '140200001716',
                'stock_code': '03.1.23.0000.00.00.00',
                'stock_name': 'KCR739 11"-14,5" GEZ KOMPLESİ (İŞÇİLİK)',
                'order_amount': 1600,
                'order_delivery_amount': 1550,
                'order_remaining_amount': 50,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            },
            {
                'customer_current_code': '120.100.4910018545',
                'order_no': 'AS2456656',
                'order_receiving_date': None,
                'deadline_date': None,
                'customer_code': '14020001337',
                'stock_code': '03.0.00.0019.00.00.00',
                'stock_name': 'CAR816 EL KUNDAĞI ALT (TALAŞLI İMALAT İŞÇ.+TESVİYE)',
                'order_amount': 1440,
                'order_delivery_amount': 0,
                'order_remaining_amount': 1440,
                'status': 'open',
                'description': None,
                'kapsam_deadline_date': None
            }
        ]

    def handle(self, *args, **options):
        self.stdout.write('Loading orders data...')

        try:
            with transaction.atomic():
                created_count = 0
                skipped_count = 0
                error_count = 0

                for order_data in self.get_orders_data():
                    try:
                        # Get or create customer
                        customer, _ = Customer.objects.get_or_create(
                            code=order_data['customer_code'],
                            defaults={
                                'name': f"Customer {order_data['customer_code']}"
                            }
                        )

                        # Get or create product
                        product, _ = Product.objects.get_or_create(
                            code=order_data['stock_code'],
                            defaults={
                                'name': order_data['stock_name']
                            }
                        )

                        # Map status from 'open' to appropriate SalesOrder status
                        status_mapping = {
                            'open': 'PENDING_APPROVAL',
                            'completed': 'COMPLETED',
                            'cancelled': 'CANCELLED'
                        }
                        
                        order_status = status_mapping.get(order_data['status'].lower(), 'PENDING_APPROVAL')

                        # Create or update sales order
                        order, created = SalesOrder.objects.get_or_create(
                            order_number=order_data['order_no'],
                            defaults={
                                'customer': customer,
                                'order_date': self.parse_date(order_data['order_receiving_date']) or datetime.now().date(),
                                'deadline_date': self.parse_date(order_data['deadline_date']) or datetime.now().date(),
                                'status': order_status
                            }
                        )

                        if not created:
                            # Update existing order
                            order.customer = customer
                            order.order_date = self.parse_date(order_data['order_receiving_date']) or order.order_date
                            order.deadline_date = self.parse_date(order_data['deadline_date']) or order.deadline_date
                            order.status = order_status
                            order.save()

                        # Create or update sales order item
                        order_item, item_created = SalesOrderItem.objects.get_or_create(
                            sales_order=order,
                            product=product,
                            defaults={
                                'quantity': order_data['order_amount'],
                                'fulfilled_quantity': order_data['order_delivery_amount']
                            }
                        )

                        if not item_created:
                            # Update existing order item
                            order_item.quantity = order_data['order_amount']
                            order_item.fulfilled_quantity = order_data['order_delivery_amount']
                            order_item.save()

                        if created:
                            created_count += 1
                            self.stdout.write(f"Created order: {order_data['order_no']}")
                        else:
                            skipped_count += 1
                            self.stdout.write(f"Updated existing order: {order_data['order_no']}")

                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f"Error processing order {order_data['order_no']}: {str(e)}"
                            )
                        )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully loaded orders data. '
                        f'Created: {created_count}, Updated: {skipped_count}, Errors: {error_count}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading orders data: {str(e)}')
            )
            raise 