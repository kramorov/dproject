#params/populate_exd_models.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
django.setup()

from params.exd_models import (
    GasGroup, DustGroup, TemperatureClass, 
    ExplosionProtectionType, ExplosionProtectionLevel
)

def populate():
    from params.exd_models import (
        GasGroup, DustGroup, TemperatureClass,
        ExplosionProtectionType, ExplosionProtectionLevel
    )
    from django.utils.translation import gettext_lazy as _

    def populate_base_models():
        """Заполняет базовые модели справочников"""

        print("=" * 60)
        print("Заполнение справочников взрывозащиты")
        print("=" * 60)

        # 1. Группы газов
        print("\n1. Заполнение GasGroup...")
        gas_groups = [
            {'name': 'IIA', 'code': 'IIA', 'description': 'пропан, метан, аммиак (наименее опасная)'},
            {'name': 'IIB', 'code': 'IIB', 'description': 'этилен, коксовый газ (средняя опасность)'},
            {'name': 'IIC', 'code': 'IIC', 'description': 'водород, ацетилен, сероуглерод (наиболее опасная)'},
        ]

        gas_created = 0
        for data in gas_groups:
            obj, created = GasGroup.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'description': data['description']
                }
            )
            if created:
                gas_created += 1
                print(f"  ✓ Создана: {obj.code} - {obj.name}")
            else:
                print(f"  • Уже существует: {obj.code}")

        print(f"  Итого создано: {gas_created}")

        # 2. Группы пыли
        print("\n2. Заполнение DustGroup...")
        dust_groups = [
            {'name': 'IIIA', 'code': 'IIIA', 'description': 'легковоспламеняющиеся летучие частицы (мука, зерно)'},
            {'name': 'IIIB', 'code': 'IIIB', 'description': 'непроводящая пыль (древесная, угольная)'},
            {'name': 'IIIC', 'code': 'IIIC', 'description': 'проводящая пыль (металлическая, графитовая)'},
        ]

        dust_created = 0
        for data in dust_groups:
            obj, created = DustGroup.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'description': data['description']
                }
            )
            if created:
                dust_created += 1
                print(f"  ✓ Создана: {obj.code} - {obj.name}")
            else:
                print(f"  • Уже существует: {obj.code}")

        print(f"  Итого создано: {dust_created}")

        # 3. Температурные классы
        print("\n3. Заполнение TemperatureClass...")
        temp_classes = [
            {'class': 'T1', 'max_temp': 450, 'ignition_temp': 450},
            {'class': 'T2', 'max_temp': 300, 'ignition_temp': 300},
            {'class': 'T3', 'max_temp': 200, 'ignition_temp': 200},
            {'class': 'T4', 'max_temp': 135, 'ignition_temp': 135},
            {'class': 'T5', 'max_temp': 100, 'ignition_temp': 100},
            {'class': 'T6', 'max_temp': 85, 'ignition_temp': 85},
        ]

        temp_created = 0
        for data in temp_classes:
            obj, created = TemperatureClass.objects.get_or_create(
                temperature_class=data['class'],
                defaults={
                    'max_surface_temp': data['max_temp'],
                    'gas_ignition_temp': data['ignition_temp']
                }
            )
            if created:
                temp_created += 1
                print(f"  ✓ Создан: {obj.temperature_class} (макс. температура: {obj.max_surface_temp}°C)")
            else:
                print(f"  • Уже существует: {obj.temperature_class}")

        print(f"  Итого создано: {temp_created}")

        # 4. Типы взрывозащиты
        print("\n4. Заполнение ExplosionProtectionType...")
        protection_types = [
            # Газовые типы
            {'code': 'd', 'name': 'Ex d', 'category': 'GAS',
             'description': 'Взрывонепроницаемая оболочка - оборудование выдерживает внутреннее давление взрыва'},
            {'code': 'e', 'name': 'Ex e', 'category': 'GAS',
             'description': 'Повышенная надежность - отсутствие искр и дуг в нормальном режиме'},
            {'code': 'i', 'name': 'Ex i', 'category': 'GAS',
             'description': 'Искробезопасная электрическая цепь - энергия ограничена'},
            {'code': 'ia', 'name': 'Ex ia', 'category': 'GAS',
             'description': 'Искробезопасная цепь - очень высокая степень защиты'},
            {'code': 'ib', 'name': 'Ex ib', 'category': 'GAS',
             'description': 'Искробезопасная цепь - высокая степень защиты'},
            {'code': 'n', 'name': 'Ex n', 'category': 'GAS',
             'description': 'Неискрящее оборудование для Зоны 2'},
            {'code': 'nA', 'name': 'Ex nA', 'category': 'GAS',
             'description': 'Неискрящее оборудование для Зоны 2'},
            {'code': 'm', 'name': 'Ex m', 'category': 'GAS',
             'description': 'Герметизация компаундом'},
            {'code': 'p', 'name': 'Ex p', 'category': 'GAS',
             'description': 'Заполнение или продувка оболочки под избыточным давлением'},
            # Пылевые типы
            {'code': 't', 'name': 'Ex t', 'category': 'DUST',
             'description': 'Защита оболочкой для пыли'},
            {'code': 'tb', 'name': 'Ex tb', 'category': 'DUST',
             'description': 'Защита оболочкой для пыли - высокая степень'},
            {'code': 'p', 'name': 'Ex p', 'category': 'DUST',
             'description': 'Заполнение или продувка оболочки под избыточным давлением (пыль)'},
            {'code': 'i', 'name': 'Ex i', 'category': 'DUST',
             'description': 'Искробезопасная цепь для пыли'},
        ]

        type_created = 0
        for data in protection_types:
            obj, created = ExplosionProtectionType.objects.get_or_create(
                code=data['code'],
                category=data['category'],
                defaults={
                    'name': data['name'],
                    'description': data['description']
                }
            )
            if created:
                type_created += 1
                print(f"  ✓ Создан: {obj.name} (категория: {obj.get_category_display()})")
            else:
                print(f"  • Уже существует: {obj.name}")

        print(f"  Итого создано: {type_created}")

        # 5. Уровни взрывозащиты
        print("\n5. Заполнение ExplosionProtectionLevel...")
        protection_levels = [
            # Газовые уровни
            {'code': 'Ga', 'name': 'Ga', 'category': 'SURFACE', 'zone': '0',
             'description': 'Оборудование для Зоны 0 - очень высокая степень защиты'},
            {'code': 'Gb', 'name': 'Gb', 'category': 'SURFACE', 'zone': '1',
             'description': 'Оборудование для Зоны 1 - высокая степень защиты'},
            {'code': 'Gc', 'name': 'Gc', 'category': 'SURFACE', 'zone': '2',
             'description': 'Оборудование для Зоны 2 - нормальная степень защиты'},
            # Пылевые уровни
            {'code': 'Da', 'name': 'Da', 'category': 'SURFACE', 'zone': '20',
             'description': 'Оборудование для Зоны 20 - очень высокая степень защиты'},
            {'code': 'Db', 'name': 'Db', 'category': 'SURFACE', 'zone': '21',
             'description': 'Оборудование для Зоны 21 - высокая степень защиты'},
            {'code': 'Dc', 'name': 'Dc', 'category': 'SURFACE', 'zone': '22',
             'description': 'Оборудование для Зоны 22 - нормальная степень защиты'},
        ]

        level_created = 0
        for data in protection_levels:
            obj, created = ExplosionProtectionLevel.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'equipment_category': data['category'],
                    'zone': data['zone'],
                    'description': data['description']
                }
            )
            if created:
                level_created += 1
                print(f"  ✓ Создан уровень: {obj.code} - {obj.get_equipment_category_display()} (Зона {obj.zone})")
            else:
                print(f"  • Уже существует: {obj.code}")

        print(f"  Итого создано: {level_created}")

        # Итоги
        print("\n" + "=" * 60)
        print("ЗАВЕРШЕНО!")
        print("=" * 60)
        print(f"GasGroup:                     {GasGroup.objects.count()} записей")
        print(f"DustGroup:                    {DustGroup.objects.count()} записей")
        print(f"TemperatureClass:             {TemperatureClass.objects.count()} записей")
        print(f"ExplosionProtectionType:      {ExplosionProtectionType.objects.count()} записей")
        print(f"ExplosionProtectionLevel:     {ExplosionProtectionLevel.objects.count()} записей")
        print("=" * 60)

    # Запуск заполнения
    if __name__ == "__main__":
        populate_base_models()
    pass

if __name__ == "__main__":
    populate()