# pneumatic_actuators/debug_sr_search2.py
# !/usr/bin/env python
"""
Отладочный скрипт для поиска подходящих приводов
Использует classmethod find_suitable_actuators из модели BodyThrustTorqueTable
"""

import os
import sys



# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE' , 'djangoProject1.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Инициализируем Django
import django

django.setup()
from params.models import PneumaticAirSupplyPressure
from pneumatic_actuators.models import PneumaticActuatorBody , BodyThrustTorqueTable
# from django.apps import apps



def interactive_search() :
    """Интерактивный поиск с ручным вводом параметров"""

    print("\n" + "=" * 80)
    print("ПОИСК ПРИВОДОВ (через BodyThrustTorqueTable.find_suitable_actuators)")
    print("=" * 80)

    # Ввод момента
    while True :
        try :
            torque = float(input("\nВведите требуемый момент с запасом (Нм): "))
            if torque > 0 :
                break
            print("Момент должен быть больше 0!")
        except ValueError :
            print("Введите число!")

    # Выбор типа привода
    print("\nТип привода:")
    print("  1. DA (двойного действия)")
    print("  2. SR (пружинный возврат)")
    variety_choice = input("Выберите (1/2): ")
    actuator_variety = 'DA' if variety_choice == '1' else 'SR'

    # Выбор давления
    pressures = PneumaticAirSupplyPressure.objects.filter(is_active=True).order_by('sorting_order')
    print("\nДоступные давления:")
    for p in pressures :
        print(f"  {p.id}. {p.name} ({p.code} бар)")

    while True :
        try :
            pressure_id = int(input("\nВыберите ID давления: "))
            if pressures.filter(id=pressure_id).exists() :
                break
            print("Давление с таким ID не найдено!")
        except ValueError :
            print("Введите число!")

    # Выбор максимального количества body
    while True :
        try :
            max_bodies = int(input("\nМаксимальное количество body в результате (1-10): "))
            if 1 <= max_bodies <= 10 :
                break
            print("Введите число от 1 до 10!")
        except ValueError :
            print("Введите число!")

    # Выбор body (опционально)
    print("\nХотите ограничить поиск конкретными body?")
    print("  1. Все body")
    print("  2. Выбрать конкретные body")

    choice = input("Выберите (1/2): ")

    body_ids = None
    if choice == '2' :
        bodies = PneumaticActuatorBody.objects.filter(is_active=True).order_by('sorting_order')
        print("\nДоступные body:")
        for b in bodies :
            print(f"  {b.id}. {b.name} (code: {b.code})")

        ids_input = input("\nВведите ID body через запятую (например: 1,2,3): ")
        try :
            body_ids = [int(x.strip()) for x in ids_input.split(',')]
        except ValueError :
            print("Неверный ввод, будут проверены все body")
            body_ids = None

    # Выполняем поиск через classmethod модели
    print("\n" + "=" * 80)
    print("ВЫПОЛНЯЕТСЯ ПОИСК...")
    print("=" * 80)

    results = BodyThrustTorqueTable.find_suitable_actuators(
        torque_with_sf=torque ,
        work_pressure_id=pressure_id ,
        actuator_variety=actuator_variety ,
        body_ids=body_ids ,
        max_bodies=max_bodies
    )

    # Выводим итоговый отчет
    print("\n" + "=" * 80)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 80)

    if results :
        print(f"\n✅ Найдено подходящих корпусов: {len(results)}")

        for i , res in enumerate(results , 1) :
            print(f"\n{i}. {res['body_name']} (code: {res['body_code']}) - {res['type']}")
            print(f"   Score: {res['score']:.1f}")
            print(f"   Запас по моменту: {res['spring_margin']:.1f} Нм")

            for item in res['model_line_items'] :
                if res['type'] == 'SR' :
                    print(f"   Моменты на пружинах ({item['spring_qty_name']}):")
                    print(
                        f"     BTO={item['spring_bto']:.1f}, ETO={item['spring_eto']:.1f}, MIN={item['spring_min']:.1f} Нм")
                    print(f"   Моменты по воздуху ({item['spring_qty_name']}):")
                    print(
                        f"     BTO={item['pressure_bto']:.1f}, ETO={item['pressure_eto']:.1f}, MIN={item['pressure_min']:.1f} Нм")
                else :
                    print(f"   Момент по воздуху (BTO): {item['spring_bto']:.1f} Нм")

            print(f"   Всего комбинаций для этого body: {len(res['model_line_items'])}")
    else :
        print("\n❌ Не найдено подходящих корпусов!")
        print("\nВозможные причины:")
        print("  - Нет данных для указанного давления")
        print("  - Требуемый момент слишком большой")
        print("  - Нет подходящих комбинаций пружин")


def quick_test() :
    """Быстрый тест с предустановленными параметрами"""

    print("\n" + "=" * 80)
    print("БЫСТРЫЙ ТЕСТ (момент=150 Нм, давление=6 бар, SR)")
    print("=" * 80)

    results = BodyThrustTorqueTable.find_suitable_actuators(
        torque_with_sf=150.0 ,
        work_pressure_id=13 ,  # 6 бар
        actuator_variety='SR' ,
        max_bodies=3
    )

    if results :
        print(f"\n✅ Найдено подходящих корпусов: {len(results)}")
        for i , res in enumerate(results , 1) :
            print(f"\n{i}. {res['body_name']} (code: {res['body_code']}) - {res['type']}")
            print(f"   Score: {res['score']:.1f}")
            print(f"   Запас по моменту: {res['spring_margin']:.1f} Нм")
    else :
        print("\n❌ Не найдено подходящих корпусов!")


if __name__ == "__main__" :
    print("\nВыберите режим работы:")
    print("1. Интерактивный поиск")
    print("2. Быстрый тест (150 Нм, 6 бар, SR)")

    mode = input("\nВыберите (1/2): ")

    if mode == '1' :
        interactive_search()
    else :
        quick_test()