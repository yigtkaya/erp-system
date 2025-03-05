from django.db import migrations

def copy_material_to_product(apps, schema_editor):
    BOMComponent = apps.get_model('manufacturing', 'BOMComponent')
    for component in BOMComponent.objects.all():
        if component.material:
            # Find the corresponding product for this material
            Product = apps.get_model('inventory', 'Product')
            try:
                product = Product.objects.get(material_code=component.material.material_code)
                component.product = product
                component.save()
            except Product.DoesNotExist:
                # If no matching product exists, we'll need to handle this case
                print(f"No matching product found for material {component.material.material_code}")

def reverse_copy_material_to_product(apps, schema_editor):
    BOMComponent = apps.get_model('manufacturing', 'BOMComponent')
    for component in BOMComponent.objects.all():
        if component.product:
            # Find the corresponding material for this product
            RawMaterial = apps.get_model('inventory', 'RawMaterial')
            try:
                material = RawMaterial.objects.get(material_code=component.product.material_code)
                component.material = material
                component.save()
            except RawMaterial.DoesNotExist:
                print(f"No matching material found for product {component.product.material_code}")

class Migration(migrations.Migration):

    dependencies = [
        ('manufacturing', '0003_bomcomponent_product_alter_bomcomponent_material'),
    ]

    operations = [
        migrations.RunPython(
            copy_material_to_product,
            reverse_copy_material_to_product
        ),
    ] 