# Generated by Django 5.1.5 on 2025-03-12 07:02

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_alter_product_multicode_controlgauge_fixture'),
        ('manufacturing', '0009_alter_processconfig_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='processconfig',
            options={'ordering': ['workflow_process', 'axis_count'], 'verbose_name': 'Process Configuration', 'verbose_name_plural': 'Process Configurations'},
        ),
        migrations.RemoveConstraint(
            model_name='processconfig',
            name='unique_process_machine_config',
        ),
        migrations.RemoveIndex(
            model_name='processconfig',
            name='manufacturi_machine_462cba_idx',
        ),
        migrations.RemoveField(
            model_name='manufacturingprocess',
            name='approved_by',
        ),
        migrations.RemoveField(
            model_name='manufacturingprocess',
            name='standard_time_minutes',
        ),
        migrations.RemoveField(
            model_name='processconfig',
            name='machine_type',
        ),
        migrations.AddField(
            model_name='processconfig',
            name='axis_count',
            field=models.CharField(blank=True, choices=[('9EKSEN', '9 Eksen'), ('8.5EKSEN', '8.5 Eksen'), ('5EKSEN', '5 Eksen'), ('4EKSEN', '4 Eksen'), ('3EKSEN', '3 Eksen'), ('2EKSEN', '2 Eksen'), ('1EKSEN', '1 Eksen')], help_text='Type of machine axis required for this process', max_length=20, null=True),
        ),
        migrations.AddIndex(
            model_name='processconfig',
            index=models.Index(fields=['axis_count'], name='manufacturi_axis_co_8941db_idx'),
        ),
        migrations.AddConstraint(
            model_name='processconfig',
            constraint=models.UniqueConstraint(fields=('workflow_process', 'axis_count'), name='unique_process_machine_config'),
        ),
    ]
