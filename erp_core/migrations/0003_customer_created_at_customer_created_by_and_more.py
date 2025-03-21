# Generated by Django 5.1.5 on 2025-01-31 10:17

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erp_core', '0002_department_user_departments_userprofile_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='customer',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='customer',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='customer',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_modified', to=settings.AUTH_USER_MODEL),
        ),
    ]
