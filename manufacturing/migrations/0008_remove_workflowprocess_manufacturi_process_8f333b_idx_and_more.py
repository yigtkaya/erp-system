# Generated by Django 5.1.5 on 2025-03-11 09:05

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_alter_product_product_type_holder_tool'),
        ('manufacturing', '0007_remove_workflowprocess_axis_count_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='workflowprocess',
            name='manufacturi_process_8f333b_idx',
        ),
        migrations.AlterUniqueTogether(
            name='workflowprocess',
            unique_together={('product', 'process', 'stock_code'), ('product', 'sequence_order')},
        ),
        migrations.AddIndex(
            model_name='workflowprocess',
            index=models.Index(fields=['product', 'process', 'stock_code'], name='manufacturi_product_39f2f9_idx'),
        ),
        migrations.RemoveField(
            model_name='workflowprocess',
            name='process_number',
        ),
    ]
