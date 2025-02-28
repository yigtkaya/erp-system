# Generated by Django 5.1.5 on 2025-02-24 06:22

from django.db import migrations, models

def update_component_types(apps, schema_editor):
    BOMComponent = apps.get_model('manufacturing', 'BOMComponent')
    ProductComponent = apps.get_model('manufacturing', 'ProductComponent')
    ProcessComponent = apps.get_model('manufacturing', 'ProcessComponent')

    # Update all product components
    for component in ProductComponent.objects.all():
        component.component_type = 'PRODUCT'
        component.save()

    # Update all process components
    for component in ProcessComponent.objects.all():
        component.component_type = 'PROCESS'
        component.save()

class Migration(migrations.Migration):

    dependencies = [
        ('manufacturing', '0018_bomcomponent_component_type'),
    ]

    operations = [
        migrations.RunSQL(
            # First, copy the data from child tables to parent table
            sql="""
            UPDATE manufacturing_bomcomponent bc
            SET component_type = 'PRODUCT'
            FROM manufacturing_productcomponent pc
            WHERE bc.id = pc.bomcomponent_ptr_id;

            UPDATE manufacturing_bomcomponent bc
            SET component_type = 'PROCESS'
            FROM manufacturing_processcomponent pc
            WHERE bc.id = pc.bomcomponent_ptr_id;

            ALTER TABLE manufacturing_processcomponent DROP COLUMN IF EXISTS component_type;
            ALTER TABLE manufacturing_productcomponent DROP COLUMN IF EXISTS component_type;
            """,
            reverse_sql="""
            ALTER TABLE manufacturing_processcomponent ADD COLUMN component_type varchar(20);
            ALTER TABLE manufacturing_productcomponent ADD COLUMN component_type varchar(20);

            UPDATE manufacturing_processcomponent pc
            SET component_type = bc.component_type
            FROM manufacturing_bomcomponent bc
            WHERE pc.bomcomponent_ptr_id = bc.id;

            UPDATE manufacturing_productcomponent pc
            SET component_type = bc.component_type
            FROM manufacturing_bomcomponent bc
            WHERE pc.bomcomponent_ptr_id = bc.id;
            """
        ),
    ]
