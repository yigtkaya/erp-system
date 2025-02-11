from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from inventory.models import Product, TechnicalDrawing

User = get_user_model()

class Command(BaseCommand):
    help = 'Adds sample technical drawings for sample products.'

    def handle(self, *args, **options):
        # Get a sample user to act as the approver. This assumes at least one user exists.
        approved_by = User.objects.first()
        if not approved_by:
            self.stdout.write(self.style.ERROR("No user exists to set for the approved_by field."))
            return

        # Define sample technical drawing data keyed by product code.
        sample_data = {
            "P001": [
                {
                    "version": "1.0",
                    "drawing_code": "DC001",
                    "drawing_url": "http://example.com/drawings/dc001.pdf",
                    "is_current": True,
                    "revision_notes": "Initial release",
                }
            ],
            "P002": [
                {
                    "version": "2.0",
                    "drawing_code": "DC002",
                    "drawing_url": "http://example.com/drawings/dc002.pdf",
                    "is_current": True,
                    "revision_notes": "Initial release",
                }
            ],
            # Add technical drawings for SP001 as well
            "SP001": [
                {
                    "version": "1.0",
                    "drawing_code": "DC_SP001",
                    "drawing_url": "http://example.com/drawings/dc_sp001.pdf",
                    "is_current": True,
                    "revision_notes": "Standard Bolt initial drawing",
                }
            ]
        }

        for product_code, drawings in sample_data.items():
            try:
                product = Product.objects.get(product_code=product_code)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Product with code {product_code} not found. Skipping."))
                continue

            for data in drawings:
                drawing_obj, created = TechnicalDrawing.objects.get_or_create(
                    product=product,
                    version=data["version"],
                    defaults={
                        "drawing_code": data["drawing_code"],
                        "drawing_url": data["drawing_url"],
                        "effective_date": timezone.now().date(),
                        "is_current": data["is_current"],
                        "revision_notes": data["revision_notes"],
                        "approved_by": approved_by,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f"Added Technical Drawing {drawing_obj.drawing_code} v{drawing_obj.version} for product {product.product_code}."
                    ))
                else:
                    self.stdout.write(
                        f"Technical Drawing {drawing_obj.drawing_code} v{drawing_obj.version} for product {product.product_code} already exists."
                    )