# Generated by Django 5.1.5 on 2025-02-28 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manufacturing', '0033_alter_bomprocessconfig_process_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bomprocessconfig',
            name='quality_checks',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='bomprocessconfig',
            name='tooling_requirements',
            field=models.TextField(blank=True, null=True),
        ),
    ]
