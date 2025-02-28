# Generated by Django 5.1.5 on 2025-02-28 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0010_remove_processproduct_bom_process_configs'),
        ('manufacturing', '0034_alter_bomprocessconfig_quality_checks_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bomprocessconfig',
            name='process_product',
        ),
        migrations.AddField(
            model_name='bomprocessconfig',
            name='process_product',
            field=models.ManyToManyField(blank=True, help_text='Process products associated with this configuration', related_name='bom_process_configs', to='inventory.processproduct'),
        ),
    ]
