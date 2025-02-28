from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('manufacturing', '0020_alter_bomcomponent_component_type_and_more'),  # Update this to your latest migration
    ]

    operations = [
        migrations.AlterField(
            model_name='machine',
            name='machine_type',
            field=models.CharField(
                choices=[
                    ('İşleme Merkezi', 'İşleme Merkezi'),
                    ('CNC Torna Merkezi', 'CNC Torna Merkezi'),
                    ('CNC Kayar Otomat', 'CNC Kayar Otomat'),
                    ('Yok', 'Yok')
                ],
                max_length=50
            ),
        ),
        migrations.AlterField(
            model_name='manufacturingprocess',
            name='machine_type',
            field=models.CharField(
                choices=[
                    ('İşleme Merkezi', 'İşleme Merkezi'),
                    ('CNC Torna Merkezi', 'CNC Torna Merkezi'),
                    ('CNC Kayar Otomat', 'CNC Kayar Otomat'),
                    ('Yok', 'Yok')
                ],
                max_length=50
            ),
        ),
    ] 