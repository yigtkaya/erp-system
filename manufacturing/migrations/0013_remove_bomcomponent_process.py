from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('manufacturing', '0012_remove_bomprocessconfig_machine_type_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bomcomponent',
            name='process',
        ),
    ] 