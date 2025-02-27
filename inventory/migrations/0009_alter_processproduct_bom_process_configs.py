# Generated by Django 5.1.5 on 2025-02-27 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0008_processproduct'),
        ('manufacturing', '0029_bomprocessconfig_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='processproduct',
            name='bom_process_configs',
            field=models.ManyToManyField(help_text='The BOM process configurations this product is associated with', related_name='related_process_products', to='manufacturing.bomprocessconfig'),
        ),
    ]
