from django.db import migrations

def fix_null_products(apps, schema_editor):
    BOM = apps.get_model('manufacturing', 'BOM')
    # Delete BOMs with NULL product_id as they are invalid
    BOM.objects.filter(product__isnull=True).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('manufacturing', '0001_initial'),  # Update this to your last migration
    ]

    operations = [
        migrations.RunPython(fix_null_products, reverse_code=migrations.RunPython.noop),
    ] 