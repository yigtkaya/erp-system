# Generated by Django 5.1.5 on 2025-02-10 19:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_alter_product_product_type'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['product_code'], 'verbose_name': 'Product', 'verbose_name_plural': 'Products'},
        ),
    ]
