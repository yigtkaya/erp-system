# Generated by Django 5.1.5 on 2025-01-30 08:08

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manufacturing', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkOrderOutput',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('quantity', models.IntegerField()),
                ('status', models.CharField(choices=[('GOOD', 'Good Quality'), ('REWORK', 'Needs Rework'), ('SCRAP', 'Scrap')], max_length=20)),
                ('notes', models.TextField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='salesorder',
            name='approved_by',
        ),
        migrations.RemoveField(
            model_name='salesorder',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='salesorder',
            name='customer',
        ),
        migrations.RemoveField(
            model_name='salesorder',
            name='modified_by',
        ),
        migrations.RemoveField(
            model_name='salesorderitem',
            name='sales_order',
        ),
        migrations.RemoveField(
            model_name='salesorderitem',
            name='product',
        ),
    ]
