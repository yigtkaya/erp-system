# Generated by Django 5.1.5 on 2025-03-05 07:22

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('erp_core', '0004_alter_userprofile_options'),
        ('inventory', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SalesOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('order_number', models.CharField(max_length=50, unique=True)),
                ('order_date', models.DateField(auto_now_add=True)),
                ('deadline_date', models.DateField()),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('PENDING_APPROVAL', 'Pending Approval'), ('APPROVED', 'Approved'), ('CANCELLED', 'Cancelled'), ('COMPLETED', 'Completed')], default='DRAFT', max_length=20)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='approved_sales_orders', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='erp_core.customer')),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-order_date'],
            },
        ),
        migrations.CreateModel(
            name='SalesOrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField()),
                ('fulfilled_quantity', models.IntegerField(default=0)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventory.product')),
                ('sales_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='sales.salesorder')),
            ],
        ),
        migrations.CreateModel(
            name='Shipping',
            fields=[
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('shipping_no', models.CharField(max_length=50, unique=True)),
                ('shipping_date', models.DateField()),
                ('shipping_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('shipping_note', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('PICKED_UP', 'Picked Up'), ('IN_TRANSIT', 'In Transit'), ('OUT_FOR_DELIVERY', 'Out for Delivery'), ('DELIVERED', 'Delivered'), ('FAILED', 'Failed Delivery'), ('RETURNED', 'Returned')], default='PENDING', max_length=20)),
                ('tracking_number', models.CharField(blank=True, max_length=100, null=True)),
                ('estimated_delivery_date', models.DateField(blank=True, null=True)),
                ('actual_delivery_date', models.DateField(blank=True, null=True)),
                ('carrier', models.CharField(blank=True, max_length=100, null=True)),
                ('carrier_service', models.CharField(blank=True, max_length=100, null=True)),
                ('package_weight', models.DecimalField(blank=True, decimal_places=2, help_text='Weight in kg', max_digits=10, null=True)),
                ('package_length', models.DecimalField(blank=True, decimal_places=2, help_text='Length in cm', max_digits=10, null=True)),
                ('package_width', models.DecimalField(blank=True, decimal_places=2, help_text='Width in cm', max_digits=10, null=True)),
                ('package_height', models.DecimalField(blank=True, decimal_places=2, help_text='Height in cm', max_digits=10, null=True)),
                ('shipping_address_line1', models.CharField(blank=True, max_length=255, null=True)),
                ('shipping_address_line2', models.CharField(blank=True, max_length=255, null=True)),
                ('shipping_city', models.CharField(blank=True, max_length=100, null=True)),
                ('shipping_state', models.CharField(blank=True, max_length=100, null=True)),
                ('shipping_country', models.CharField(blank=True, max_length=100, null=True)),
                ('shipping_postal_code', models.CharField(blank=True, max_length=20, null=True)),
                ('is_insured', models.BooleanField(default=False)),
                ('insurance_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_modified', to=settings.AUTH_USER_MODEL)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='shipments', to='sales.salesorder')),
            ],
            options={
                'verbose_name': 'Shipping',
                'verbose_name_plural': 'Shippings',
                'ordering': ['-shipping_date'],
            },
        ),
    ]
