from django.core.management.base import BaseCommand
from django.db import transaction
from erp_core.models import Customer

class Command(BaseCommand):
    help = 'Load initial customer data'

    def handle(self, *args, **kwargs):
        customers_data = [
            {
                'code': '120.100.7510036236',
                'name': 'SARSILMAZ',
                'tax_number': '7510036236',
                'tax_office': 'Default',  # Update with actual tax office
                'address': 'Default Address',  # Update with actual address
                'phone': 'Default Phone',  # Update with actual phone
                'email': 'info@sarsilmaz.com',  # Update with actual email
            },
            {
                'code': '120.100.4910018545',
                'name': 'KALEKALIP',
                'tax_number': '4910018545',
                'tax_office': 'Default',  # Update with actual tax office
                'address': 'Default Address',  # Update with actual address
                'phone': 'Default Phone',  # Update with actual phone
                'email': 'info@kalekalip.com',  # Update with actual email
            },
        ]

        try:
            with transaction.atomic():
                for customer_data in customers_data:
                    customer, created = Customer.objects.update_or_create(
                        code=customer_data['code'],
                        defaults={
                            'name': customer_data['name'],
                            'tax_number': customer_data['tax_number'],
                            'tax_office': customer_data['tax_office'],
                            'address': customer_data['address'],
                            'phone': customer_data['phone'],
                            'email': customer_data['email'],
                        }
                    )
                    
                    action = 'Created' if created else 'Updated'
                    self.stdout.write(
                        self.style.SUCCESS(f"{action} customer: {customer.name} ({customer.code})")
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading customers: {str(e)}')
            )
            raise

        self.stdout.write(self.style.SUCCESS('Successfully loaded all customers')) 