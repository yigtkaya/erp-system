# Generated by Django 5.1.5 on 2025-01-31 11:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manufacturing', '0006_machine_last_maintenance_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='machine',
            name='maintenance_notes',
            field=models.TextField(blank=True, null=True),
        ),
    ]
