# Generated by Django 5.1.5 on 2025-02-19 08:26

from django.db import migrations, models

def forward_func(apps, schema_editor):
    Machine = apps.get_model('manufacturing', 'Machine')
    db_alias = schema_editor.connection.alias
    # Update all machines to have NULL in the new column
    Machine.objects.using(db_alias).all().update(internal_cooling_new=None)

def reverse_func(apps, schema_editor):
    Machine = apps.get_model('manufacturing', 'Machine')
    db_alias = schema_editor.connection.alias
    # Convert back to boolean based on whether there's a value
    Machine.objects.using(db_alias).all().update(internal_cooling=False)

class Migration(migrations.Migration):

    dependencies = [
        ('manufacturing', '0010_merge_20250219_0710'),
    ]

    operations = [
        # Add the new decimal field
        migrations.AddField(
            model_name='machine',
            name='internal_cooling_new',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                help_text='Internal cooling pressure in bars',
                null=True,
                blank=True
            ),
        ),
        # Run the data migration
        migrations.RunPython(forward_func, reverse_func),
        # Remove the old boolean field
        migrations.RemoveField(
            model_name='machine',
            name='internal_cooling',
        ),
        # Rename the new field to the original name
        migrations.RenameField(
            model_name='machine',
            old_name='internal_cooling_new',
            new_name='internal_cooling',
        ),
    ]
