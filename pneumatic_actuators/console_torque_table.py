# pneumatic_actuators/console_torque_table.py
# !/usr/bin/env python
import os
import sys
import django

# Настройка Django (ЗАМЕНИТЕ 'your_project.settings' на ваше название)
os.environ.setdefault('DJANGO_SETTINGS_MODULE' , 'djangoProject1.settings')  # Пример для вашего проекта

# Добавляем корень проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Инициализируем Django
django.setup()

from pneumatic_actuators.models import (
    PneumaticActuatorBody ,
    BodyThrustTorqueTable ,
    PneumaticActuatorModelLineItem
)


def console_print_torque_table(body_id: int) :
    """
    Вывод в консоль таблицы моментов для указанного body_id
    """
    print(f"\n{'=' * 80}")
    print(f"ТАБЛИЦА МОМЕНТОВ ДЛЯ BODY ID: {body_id}")
    print(f"{'=' * 80}\n")

    # Получаем body
    try :
        body = PneumaticActuatorBody.objects.get(id=body_id)
        print(f"Модель корпуса: {body.name} (code: {body.code})")

        # Находим model_line через model_line_item
        model_line_items = PneumaticActuatorModelLineItem.objects.filter(body=body).select_related('model_line')

        if model_line_items.exists() :
            # Берем первый (или можно вывести все)
            model_line_item = model_line_items.first()
            model_line = model_line_item.model_line

            print(
                f"Серия: {model_line.name if model_line else 'N/A'} (code: {model_line.code if model_line else 'N/A'})")
            print(
                f"Модель в серии: {model_line_item.name if model_line_item else 'N/A'} (code: {model_line_item.code if model_line_item else 'N/A'})")

            # Определяем тип конструкции через model_line
            construction_variety = None
            if model_line :
                construction_variety = model_line.pneumatic_actuator_construction_variety
                print(
                    f"Тип конструкции: {construction_variety.name if construction_variety else 'N/A'} (code: {construction_variety.code if construction_variety else 'N/A'})")
        else :
            print("Серия: Не найдена (нет связи через PneumaticActuatorModelLineItem)")

        print(f"\n{'-' * 80}\n")

    except PneumaticActuatorBody.DoesNotExist :
        print(f"Body с id={body_id} не найден!")
        return

    # Получаем все записи для этого body
    records = BodyThrustTorqueTable.objects.filter(body=body).select_related(
        'pressure' , 'spring_qty'
    ).order_by('pressure__sorting_order' , 'spring_qty__sorting_order')

    if not records.exists() :
        print("Нет данных в таблице моментов для этого body")
        return

    # Выводим простую таблицу
    print(f"{'Body':<15} {'Давление':<20} {'Пружины':<15} {'BTO':<10} {'RTO':<10} {'ETO':<10}")
    print(f"{'-' * 80}")

    for record in records :
        pressure_name = record.pressure.name if record.pressure else 'Нет давления'
        pressure_code = record.pressure.code if record.pressure else 'N/A'
        spring_name = record.spring_qty.name if record.spring_qty else 'N/A'
        spring_code = record.spring_qty.code if record.spring_qty else 'N/A'

        bto_str = f"{record.bto:.1f}" if record.bto else "N/A"
        rto_str = f"{record.rto:.1f}" if record.rto else "N/A"
        eto_str = f"{record.eto:.1f}" if record.eto else "N/A"

        print(
            f"{body.code:<15} {pressure_code}({pressure_name[:15]:<15}) {spring_code}({spring_name[:10]:<10}) {bto_str:<10} {rto_str:<10} {eto_str:<10}")

    # Детальный вывод
    print(f"\n{'=' * 80}")
    print("ДЕТАЛЬНЫЙ ВЫВОД")
    print(f"{'=' * 80}\n")

    for record in records :
        print(f"\n📊 Запись ID: {record.id}")
        print(f"   Body: {record.body.name if record.body else 'N/A'}")
        print(
            f"   Давление: {record.pressure.name if record.pressure else 'N/A'} (code: {record.pressure.code if record.pressure else 'N/A'})")
        print(
            f"   Пружины: {record.spring_qty.name if record.spring_qty else 'N/A'} (code: {record.spring_qty.code if record.spring_qty else 'N/A'})")
        print(f"   📈 BTO: {record.bto:.1f} Нм" if record.bto else "   BTO: N/A")
        print(f"   📊 RTO: {record.rto:.1f} Нм" if record.rto else "   RTO: N/A")
        print(f"   📉 ETO: {record.eto:.1f} Нм" if record.eto else "   ETO: N/A")

    print(f"\n{'=' * 80}")
    print(f"Всего записей: {records.count()}")
    print(f"{'=' * 80}")


def get_body_info(body_id: int) :
    """
    Получить подробную информацию о body и его связях
    """
    try :
        body = PneumaticActuatorBody.objects.get(id=body_id)
        print(f"\n📦 ИНФОРМАЦИЯ О BODY ID: {body_id}")
        print(f"   Название: {body.name}")
        print(f"   Код: {body.code}")
        print(f"   Активен: {body.is_active}")
        print(f"   Таблица: {body.body_table.name if body.body_table else 'N/A'}")

        # Находим все model_line_item, связанные с этим body
        model_line_items = PneumaticActuatorModelLineItem.objects.filter(body=body).select_related('model_line' ,
                                                                                                   'pneumatic_actuator_variety')

        if model_line_items.exists() :
            print(f"\n   Связанные модели в сериях ({model_line_items.count()}):")
            for item in model_line_items :
                print(f"     - Модель: {item.name} (code: {item.code})")
                print(f"       Серия: {item.model_line.name if item.model_line else 'N/A'}")
                print(
                    f"       Вид привода: {item.pneumatic_actuator_variety.name if item.pneumatic_actuator_variety else 'N/A'}")
        else :
            print(f"\n   ⚠️ Нет связанных моделей в PneumaticActuatorModelLineItem")

    except PneumaticActuatorBody.DoesNotExist :
        print(f"Body с id={body_id} не найден!")


def list_all_bodies() :
    """Вывести список всех body"""
    bodies = PneumaticActuatorBody.objects.filter(is_active=True).order_by('sorting_order')

    print(f"\n{'=' * 80}")
    print("СПИСОК ВСЕХ BODY")
    print(f"{'=' * 80}\n")

    for body in bodies :
        # Находим связанные model_line_item
        model_line_items = PneumaticActuatorModelLineItem.objects.filter(body=body)
        model_count = model_line_items.count()

        print(f"ID: {body.id:3} | Код: {body.code:<10} | Название: {body.name:<30} | Моделей: {model_count}")


if __name__ == "__main__" :
    # Выводим список всех body
    list_all_bodies()

    # Выводим подробную информацию для body_id=1
    get_body_info(1)

    # Выводим таблицу моментов для body_id=1
    console_print_torque_table(1)