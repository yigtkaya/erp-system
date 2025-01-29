# Generated by Django 5.1.5 on 2025-01-29 21:29

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('erp_core', '0001_initial'),
        ('inventory', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BOMProcessConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('machine_type', models.CharField(max_length=50)),
                ('estimated_duration_minutes', models.IntegerField()),
                ('tooling_requirements', models.JSONField(blank=True, null=True)),
                ('quality_checks', models.JSONField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'BOM Process Configuration',
                'verbose_name_plural': 'BOM Process Configurations',
            },
        ),
        migrations.CreateModel(
            name='BOM',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('version', models.CharField(default='1.0', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_modified', to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventory.product')),
            ],
            options={
                'verbose_name': 'Bill of Materials',
                'verbose_name_plural': 'Bills of Materials',
            },
        ),
        migrations.CreateModel(
            name='BOMComponent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('component_type', models.CharField(choices=[('SEMI_PRODUCT', 'Semi Product'), ('MANUFACTURING_PROCESS', 'Manufacturing Process'), ('RAW_MATERIAL', 'Raw Material')], max_length=30)),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=10)),
                ('sequence_order', models.IntegerField()),
                ('bom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='components', to='manufacturing.bom')),
                ('raw_material', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='inventory.rawmaterial')),
                ('semi_product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='inventory.product')),
                ('process_config', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='manufacturing.bomprocessconfig')),
            ],
            options={
                'verbose_name': 'BOM Component',
                'verbose_name_plural': 'BOM Components',
                'ordering': ['sequence_order'],
            },
        ),
        migrations.CreateModel(
            name='Machine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('machine_code', models.CharField(max_length=50, unique=True)),
                ('machine_type', models.CharField(choices=[('MILLING', 'Milling Machine'), ('LATHE', 'Lathe Machine'), ('DRILL', 'Drill Press'), ('GRINDING', 'Grinding Machine')], max_length=50)),
                ('brand', models.CharField(blank=True, max_length=50, null=True)),
                ('model', models.CharField(blank=True, max_length=50, null=True)),
                ('axis_count', models.IntegerField(blank=True, null=True)),
                ('internal_cooling', models.BooleanField(default=False)),
                ('motor_power_kva', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('holder_type', models.CharField(blank=True, max_length=50, null=True)),
                ('spindle_motor_power_10_percent_kw', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('spindle_motor_power_30_percent_kw', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('power_hp', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('spindle_speed_rpm', models.IntegerField(blank=True, null=True)),
                ('tool_count', models.IntegerField(blank=True, null=True)),
                ('nc_control_unit', models.CharField(blank=True, max_length=50, null=True)),
                ('manufacturing_year', models.IntegerField(blank=True, null=True)),
                ('serial_number', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('machine_weight_kg', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('max_part_size', models.CharField(blank=True, max_length=50, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('AVAILABLE', 'Available'), ('IN_USE', 'In Use'), ('MAINTENANCE', 'Maintenance'), ('RETIRED', 'Retired')], default='AVAILABLE', max_length=20)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ManufacturingProcess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('process_code', models.CharField(max_length=50, unique=True)),
                ('process_name', models.CharField(max_length=100)),
                ('standard_time_minutes', models.IntegerField()),
                ('machine_type', models.CharField(choices=[('MILLING', 'Milling Machine'), ('LATHE', 'Lathe Machine'), ('DRILL', 'Drill Press'), ('GRINDING', 'Grinding Machine')], max_length=50)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='approved_processes', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='bomprocessconfig',
            name='process',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='manufacturing.manufacturingprocess'),
        ),
        migrations.CreateModel(
            name='SalesOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('order_number', models.CharField(max_length=50, unique=True)),
                ('order_date', models.DateField(auto_now_add=True)),
                ('deadline_date', models.DateField()),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='approved_sales_orders', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='erp_core.customer')),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SalesOrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField()),
                ('fulfilled_quantity', models.IntegerField(default=0)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventory.product')),
                ('sales_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='manufacturing.salesorder')),
            ],
        ),
        migrations.CreateModel(
            name='SubWorkOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField()),
                ('planned_start', models.DateField()),
                ('planned_end', models.DateField()),
                ('actual_start', models.DateField(blank=True, null=True)),
                ('actual_end', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PLANNED', 'Planned'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('DELAYED', 'Delayed')], default='PLANNED', max_length=20)),
                ('bom_component', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='manufacturing.bomcomponent')),
            ],
        ),
        migrations.CreateModel(
            name='SubWorkOrderProcess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sequence_order', models.IntegerField()),
                ('planned_duration_minutes', models.IntegerField()),
                ('actual_duration_minutes', models.IntegerField(blank=True, null=True)),
                ('machine', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='manufacturing.machine')),
                ('process', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='manufacturing.manufacturingprocess')),
                ('sub_work_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='processes', to='manufacturing.subworkorder')),
            ],
            options={
                'ordering': ['sequence_order'],
            },
        ),
        migrations.CreateModel(
            name='WorkOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('order_number', models.CharField(max_length=50, unique=True)),
                ('quantity', models.IntegerField()),
                ('planned_start', models.DateField()),
                ('planned_end', models.DateField()),
                ('actual_start', models.DateField(blank=True, null=True)),
                ('actual_end', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PLANNED', 'Planned'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('DELAYED', 'Delayed')], default='PLANNED', max_length=20)),
                ('bom', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='manufacturing.bom')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_modified', to=settings.AUTH_USER_MODEL)),
                ('sales_order_item', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='manufacturing.salesorderitem')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='subworkorder',
            name='parent_work_order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sub_orders', to='manufacturing.workorder'),
        ),
        migrations.AddIndex(
            model_name='bom',
            index=models.Index(fields=['product'], name='manufacturi_product_60b29a_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='bom',
            unique_together={('product', 'version')},
        ),
    ]
