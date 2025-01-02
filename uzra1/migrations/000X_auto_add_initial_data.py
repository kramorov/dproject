# migrations/000X_auto_add_initial_data.py
from django.db import migrations


def add_initial_data(apps, schema_editor):
    IPChoice = apps.get_model('uzra1', 'IPChoice')
    print(IPChoice)
    TempChoice = apps.get_model('uzra1', 'TempChoice')

    # Добавляем начальные значения в таблицы
    IPChoice.objects.get_or_create(ip_value='IP67')
    IPChoice.objects.get_or_create(ip_value='IP68')

    # Добавляем начальные значения в TempChoice с min и max
    TempChoice.objects.get_or_create(temp_value='NONE', min=10, max=70)
    TempChoice.objects.get_or_create(temp_value='LT', min=5, max=70)
    TempChoice.objects.get_or_create(temp_value='VLT', min=0, max=100)


class Migration(migrations.Migration):
    dependencies = [
        # Укажите зависимости для вашей миграции, например:
        #('uzra1', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_initial_data),
    ]
