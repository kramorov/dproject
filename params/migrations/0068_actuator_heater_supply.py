# Generated manually — ActuatorHeaterSupply model + seed data

from django.db import migrations, models


def create_heater_supply_options(apps, schema_editor):
    ActuatorHeaterSupply = apps.get_model('params', 'ActuatorHeaterSupply')

    options = [
        {
            'name': 'Нет обогрева',
            'code': 'NO_HEATER',
            'electrical_specs': '',
            'description': 'Антиконденсатный обогрев не предусмотрен конструкцией привода.',
            'sorting_order': 10,
            'is_active': True,
        },
        {
            'name': 'От цепей питания устройства',
            'code': 'MOTOR_CIRCUIT',
            'electrical_specs': '',
            'description': (
                'Обогреватель запитан от общей линии питания электропривода '
                '(общий кабель с двигателем). Не требует отдельной кабельной линии. '
                'Напряжение обогрева совпадает с напряжением питания двигателя.'
            ),
            'sorting_order': 20,
            'is_active': True,
        },
        {
            'name': 'От отдельной линии',
            'code': 'SEPARATE_LINE',
            'electrical_specs': '',
            'description': (
                'Обогреватель запитан от отдельной выделенной линии. '
                'Требуется дополнительный кабель и автомат защиты. '
                'Напряжение обогрева может отличаться от напряжения питания двигателя. '
                'Позволяет включать обогрев независимо от подачи силового питания.'
            ),
            'sorting_order': 30,
            'is_active': True,
        },
    ]

    for opt in options:
        ActuatorHeaterSupply.objects.get_or_create(
            code=opt['code'],
            defaults=opt,
        )


def remove_heater_supply_options(apps, schema_editor):
    ActuatorHeaterSupply = apps.get_model('params', 'ActuatorHeaterSupply')
    ActuatorHeaterSupply.objects.filter(
        code__in=['NO_HEATER', 'MOTOR_CIRCUIT', 'SEPARATE_LINE']
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('params', '0067_populate_digital_signal_roles'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActuatorHeaterSupply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Например: «От цепей питания устройства»', max_length=200, verbose_name='Название')),
                ('code', models.CharField(help_text='Уникальный код, например «MOTOR_CIRCUIT»', max_length=50, unique=True, verbose_name='Код')),
                ('electrical_specs', models.CharField(blank=True, help_text='Например: «230В AC, 10 Вт» или «24В DC, 5 Вт»', max_length=255, verbose_name='Электрические характеристики')),
                ('description', models.TextField(blank=True, help_text='Примечания к варианту питания обогрева', verbose_name='Описание')),
                ('sorting_order', models.IntegerField(default=0, help_text='Порядок в списках выбора', verbose_name='Сортировка')),
                ('is_active', models.BooleanField(default=True, help_text='Показывать ли в списках выбора', verbose_name='Активно')),
            ],
            options={
                'verbose_name': 'Питание обогрева привода',
                'verbose_name_plural': 'Варианты питания обогрева привода',
                'ordering': ['sorting_order'],
            },
        ),
        migrations.RunPython(create_heater_supply_options, remove_heater_supply_options),
    ]
