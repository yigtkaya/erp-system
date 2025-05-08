from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Department
from inventory.models import InventoryCategory, UnitOfMeasure
from sales.models import Currency

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates initial data for the ERP system'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating initial data...')
        
        # Create superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                role='ADMIN'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user'))
        
        # Create departments
        departments = [
            {'name': 'Engineering', 'description': 'Engineering and R&D'},
            {'name': 'Production', 'description': 'Manufacturing and Production'},
            {'name': 'Quality', 'description': 'Quality Control and Assurance'},
            {'name': 'Maintenance', 'description': 'Equipment Maintenance'},
            {'name': 'Sales', 'description': 'Sales and Customer Service'},
            {'name': 'Purchasing', 'description': 'Procurement and Purchasing'},
        ]
        
        for dept_data in departments:
            dept, created = Department.objects.get_or_create(
                name=dept_data['name'],
                defaults={'description': dept_data['description']}
            )
            if created:
                self.stdout.write(f'Created department: {dept.name}')
        
        # Create inventory categories
        categories = [
            ('HAMMADDE', 'Raw Materials and Standard Parts'),
            ('PROSES', 'Unfinished/Semi Products'),
            ('MAMUL', 'Finished Products'),
            ('KARANTINA', 'Items needing decision'),
            ('HURDA', 'Scrap items'),
            ('TAKIMHANE', 'Tool storage'),
        ]
        
        for name, description in categories:
            cat, created = InventoryCategory.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            if created:
                self.stdout.write(f'Created inventory category: {name}')
        
        # Create units of measure
        units = [
            ('PCS', 'Pieces', 'Count'),
            ('KG', 'Kilograms', 'Weight'),
            ('G', 'Grams', 'Weight'),
            ('M', 'Meters', 'Length'),
            ('CM', 'Centimeters', 'Length'),
            ('MM', 'Millimeters', 'Length'),
            ('L', 'Liters', 'Volume'),
            ('ML', 'Milliliters', 'Volume'),
        ]
        
        for code, name, category in units:
            unit, created = UnitOfMeasure.objects.get_or_create(
                unit_code=code,
                defaults={'unit_name': name, 'category': category}
            )
            if created:
                self.stdout.write(f'Created unit of measure: {code}')
        
        # Create currencies
        currencies = [
            ('USD', 'US Dollar', '$'),
            ('EUR', 'Euro', '€'),
            ('TRY', 'Turkish Lira', '₺'),
            ('GBP', 'British Pound', '£'),
        ]
        
        for code, name, symbol in currencies:
            currency, created = Currency.objects.get_or_create(
                code=code,
                defaults={'name': name, 'symbol': symbol}
            )
            if created:
                self.stdout.write(f'Created currency: {code}')
        
        self.stdout.write(self.style.SUCCESS('Initial data created successfully'))