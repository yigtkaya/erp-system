# Generated by Django 5.1.5 on 2025-02-24 06:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manufacturing', '0020_alter_bomcomponent_component_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subworkorderprocess',
            name='planned_duration_minutes',
            field=models.IntegerField(),
        ),
    ]
