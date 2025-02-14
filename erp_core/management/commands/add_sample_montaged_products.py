import random
from django.core.management.base import BaseCommand
from inventory.models import Product

class Command(BaseCommand):
    help = 'Add sample montaged products for demonstration purposes'

    def handle(self, *args, **kwargs):
        # List of sample products to add. Modify or extend as needed.
        sample_products = [
            {
                'name': 'Montaged Product 1',
                'description': 'This is an exciting sample product 1.',
                'price': 19.99,
            },
            {
                'name': 'Montaged Product 2',
                'description': 'Discover the quality of montaged product 2.',
                'price': 29.99,
            },
            {
                'name': 'Montaged Product 3',
                'description': 'Experience the design of montaged product 3.',
                'price': 39.99,
            },
            {
                'name': 'Montaged Product 4',
                'description': 'High performance montaged product 4.',
                'price': 49.99,
            },
            {
                'name': 'Montaged Product 5',
                'description': 'Affordable style in montaged product 5.',
                'price': 59.99,
            },
        ]

        # Create products in the database
        for product_data in sample_products:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults=product_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created {product.name}"))
            else:
                self.stdout.write(f"{product.name} already exists.")

        self.stdout.write(self.style.SUCCESS("Sample montaged products have been added.")) 