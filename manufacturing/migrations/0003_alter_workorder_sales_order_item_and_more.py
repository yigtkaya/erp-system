# Generated by Django 5.1.5 on 2025-01-30 08:08

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_inventorycategory_and_more'),
        ('manufacturing', '0002_workorderoutput_remove_salesorder_approved_by_and_more'),
        ('sales', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='workorder',
            name='sales_order_item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='sales.salesorderitem'),
        ),
        migrations.AddField(
            model_name='subworkorder',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='subworkorder',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='subworkorder',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='subworkorder',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='subworkorder',
            name='notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='subworkorder',
            name='output_quantity',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='subworkorder',
            name='scrap_quantity',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='subworkorder',
            name='target_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='inventory.inventorycategory'),
        ),
        migrations.AddField(
            model_name='workorder',
            name='notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='workorder',
            name='priority',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='workorderoutput',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='workorderoutput',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='workorderoutput',
            name='sub_work_order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='outputs', to='manufacturing.subworkorder'),
        ),
        migrations.AddField(
            model_name='workorderoutput',
            name='target_category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventory.inventorycategory'),
        ),
        migrations.DeleteModel(
            name='SalesOrder',
        ),
        migrations.DeleteModel(
            name='SalesOrderItem',
        ),
    ]
