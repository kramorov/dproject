# migrations/000X_auto_add_initial_data.py
from django.db import migrations


def producers_create_initial_data(apps, schema_editor):
    Brands = apps.get_model('producers', 'Brands')
    Producer = apps.get_model('producers', 'Producer')

    # Создаем начальные бренды
    brand_ARH = Brands.objects.create(name='Архимед')
    brand_Artorq = Brands.objects.create(name='Artorq')

    # Создаем начального производителя
    producer = Producer.objects.create(organization='ООО "Архимед"')
    producer.brands.add(brand_ARH, brand_Artorq)

class Migration(migrations.Migration):
    dependencies = [
        ('producers', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(producers_create_initial_data),
    ]
