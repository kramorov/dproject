# pneumatic_actuators/debug_sr_search.py
# !/usr/bin/env python
"""
Отладочный скрипт для поиска подходящих приводов
- SR приводы: torque должен быть меньше MIN(bto, eto) для spring и для рабочего давления
- DA приводы: torque должен быть меньше bto для рабочего давления (пружин нет)
"""

import os
import sys
from decimal import Decimal
from typing import List , Dict , Optional , Tuple

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE' , 'djangoProject1.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Инициализируем Django
import django

django.setup()

from django.apps import apps

PneumaticActuatorBody = apps.get_model('pneumatic_actuators' , 'PneumaticActuatorBody')
BodyThrustTorqueTable = apps.get_model('pneumatic_actuators' , 'BodyThrustTorqueTable')
PneumaticAirSupplyPressure = apps.get_model('params' , 'PneumaticAirSupplyPressure')

from pneumatic_actuators.models.py_options_constants import SPRINGS_DA_DEFAULT_CODE , SPRINGS_SR_DEFAULT_CODE


def get_pressure_by_id(pressure_id: int) -> Optional[Dict] :
    """Получить информацию о давлении по ID"""
    try :
        pressure = PneumaticAirSupplyPressure.objects.get(id=pressure_id)
        return {
            'id' : pressure.id ,
            'code' : pressure.code ,
            'name' : pressure.name ,
            'value' : float(pressure.code) if pressure.code.replace('.' , '').isdigit() else None
        }
    except PneumaticAirSupplyPressure.DoesNotExist :
        return None


def get_spring_data_sr(body_id: int) -> List[Dict] :
    """Получить данные для пружин (spring) для SR приводов"""
    spring_records = BodyThrustTorqueTable.objects.filter(
        body_id=body_id ,
        pressure__code='spring' ,
        spring_qty__is_active=True
    ).exclude(spring_qty__code=SPRINGS_DA_DEFAULT_CODE).select_related('spring_qty').order_by(
        'spring_qty__sorting_order')

    result = []
    for record in spring_records :
        if record.bto and record.eto :
            result.append({
                'id' : record.id ,
                'spring_qty_code' : record.spring_qty.code ,
                'spring_qty_name' : record.spring_qty.name ,
                'bto' : float(record.bto) ,
                'eto' : float(record.eto) ,
                'min_value' : min(float(record.bto) , float(record.eto))
            })
    return result


def get_work_pressure_data_sr(body_id: int , work_pressure_id: int) -> List[Dict] :
    """Получить данные для рабочего давления для SR приводов"""
    pressure_records = BodyThrustTorqueTable.objects.filter(
        body_id=body_id ,
        pressure_id=work_pressure_id ,
        spring_qty__is_active=True
    ).exclude(spring_qty__code=SPRINGS_DA_DEFAULT_CODE).select_related('spring_qty').order_by(
        'spring_qty__sorting_order')

    result = []
    for record in pressure_records :
        if record.bto and record.eto :
            result.append({
                'id' : record.id ,
                'spring_qty_code' : record.spring_qty.code ,
                'spring_qty_name' : record.spring_qty.name ,
                'bto' : float(record.bto) ,
                'eto' : float(record.eto) ,
                'min_value' : min(float(record.bto) , float(record.eto))
            })
    return result


def get_da_data(body_id: int , work_pressure_id: int) -> List[Dict] :
    """Получить данные для DA приводов (без пружин)"""
    da_records = BodyThrustTorqueTable.objects.filter(
        body_id=body_id ,
        pressure_id=work_pressure_id ,
        spring_qty__code=SPRINGS_DA_DEFAULT_CODE ,
        spring_qty__is_active=True
    ).select_related('spring_qty')

    result = []
    for record in da_records :
        if record.bto :
            result.append({
                'id' : record.id ,
                'spring_qty_code' : record.spring_qty.code ,
                'spring_qty_name' : record.spring_qty.name ,
                'bto' : float(record.bto) ,
                'rto' : float(record.rto) if record.rto else float(record.bto) ,
                'eto' : float(record.eto) if record.eto else float(record.bto) ,
                'value' : float(record.bto)  # Для DA все три значения одинаковы
            })
    return result


def calculate_score_sr(spring: Dict , pressure: Dict , torque_with_sf: float) -> Dict :
    """
    Рассчитывает рейтинг для SR привода
    Условие: torque < MIN(spring) и torque < MIN(pressure)
    Score = сумма абсолютных отклонений от центра
    """
    spring_min = min(spring['bto'] , spring['eto'])
    spring_max = max(spring['bto'] , spring['eto'])
    spring_center = (spring['bto'] + spring['eto']) / 2

    pressure_min = min(pressure['bto'] , pressure['eto'])
    pressure_max = max(pressure['bto'] , pressure['eto'])
    pressure_center = (pressure['bto'] + pressure['eto']) / 2

    # Проверяем обязательные условия
    if torque_with_sf >= spring_min :
        return {'total_score' : 999 , 'is_valid' : False , 'reason' : f'torque >= spring_min {spring_min}'}

    if torque_with_sf >= pressure_min :
        return {'total_score' : 999 , 'is_valid' : False , 'reason' : f'torque >= pressure_min {pressure_min}'}

    # Абсолютное отклонение от центра
    spring_deviation = abs(torque_with_sf - spring_center)
    pressure_deviation = abs(torque_with_sf - pressure_center)

    total_score = spring_deviation + pressure_deviation

    return {
        'total_score' : total_score ,
        'is_valid' : True ,
        'spring_deviation' : spring_deviation ,
        'pressure_deviation' : pressure_deviation ,
        'spring_center' : spring_center ,
        'pressure_center' : pressure_center ,
        'spring_margin' : spring_min - torque_with_sf ,
        'pressure_margin' : pressure_min - torque_with_sf
    }


def calculate_score_da(da_record: Dict , torque_with_sf: float) -> Dict :
    """
    Рассчитывает рейтинг для DA привода
    Условие: torque < bto
    Score = отклонение от bto (чем меньше, тем лучше)
    """
    bto_value = da_record['value']

    # Проверяем условие
    if torque_with_sf >= bto_value :
        return {'total_score' : 999 , 'is_valid' : False , 'reason' : f'torque >= bto {bto_value}'}

    # Отклонение от bto (чем ближе, тем лучше)
    deviation = bto_value - torque_with_sf

    return {
        'total_score' : deviation ,
        'is_valid' : True ,
        'bto_value' : bto_value ,
        'margin' : deviation
    }


def find_suitable_sr_actuators(
        torque_with_sf: float ,
        work_pressure_id: int ,
        body_ids: Optional[List[int]] = None ,
        max_bodies: int = 3
) -> List[Dict] :
    """
    Найти подходящие SR приводы
    Для каждого количества пружин берем пару: spring (давление воздуха = spring) и pressure (рабочее давление)
    """

    work_pressure = get_pressure_by_id(work_pressure_id)
    if not work_pressure :
        print(f"❌ Давление с ID={work_pressure_id} не найдено!")
        return []

    print(f"\n{'=' * 80}")
    print(f"ПОИСК SR ПРИВОДОВ")
    print(f"{'=' * 80}")
    print(f"Требуемый момент с запасом: {torque_with_sf} Нм")
    print(f"Рабочее давление: {work_pressure['name']} ({work_pressure['code']} бар)")
    print(f"{'=' * 80}\n")

    # Получаем список body
    if body_ids :
        bodies = PneumaticActuatorBody.objects.filter(id__in=body_ids , is_active=True)
    else :
        bodies = PneumaticActuatorBody.objects.filter(is_active=True)

    all_results = []

    for body in bodies :
        print(f"\n📦 Проверка BODY: {body.name} (code: {body.code}, id: {body.id})")

        # Получаем все записи для этого body
        all_records = BodyThrustTorqueTable.objects.filter(
            body_id=body.id ,
            spring_qty__is_active=True
        ).exclude(spring_qty__code=SPRINGS_DA_DEFAULT_CODE).select_related('spring_qty' , 'pressure')

        # Группируем по количеству пружин
        spring_qty_groups = {}
        for record in all_records :
            qty_code = record.spring_qty.code
            if qty_code not in spring_qty_groups :
                spring_qty_groups[qty_code] = {
                    'spring_qty_code' : qty_code ,
                    'spring_qty_name' : record.spring_qty.name ,
                    'spring_record' : None ,
                    'pressure_record' : None
                }

            # Определяем тип записи (spring или рабочее давление)
            if record.pressure and record.pressure.code == 'spring' :
                spring_qty_groups[qty_code]['spring_record'] = {
                    'bto' : float(record.bto) if record.bto else None ,
                    'eto' : float(record.eto) if record.eto else None
                }
            elif record.pressure_id == work_pressure_id :
                spring_qty_groups[qty_code]['pressure_record'] = {
                    'bto' : float(record.bto) if record.bto else None ,
                    'eto' : float(record.eto) if record.eto else None
                }

        # Проверяем каждую группу пружин
        suitable_combinations = []

        for qty_code , group in spring_qty_groups.items() :
            spring = group['spring_record']
            pressure = group['pressure_record']

            if not spring or not pressure :
                continue

            if not spring['bto'] or not spring['eto'] or not pressure['bto'] or not pressure['eto'] :
                continue

            spring_min = min(spring['bto'] , spring['eto'])
            spring_max = max(spring['bto'] , spring['eto'])
            spring_center = (spring['bto'] + spring['eto']) / 2

            pressure_min = min(pressure['bto'] , pressure['eto'])
            pressure_max = max(pressure['bto'] , pressure['eto'])
            pressure_center = (pressure['bto'] + pressure['eto']) / 2

            # Проверяем условия: torque < MIN(spring) и torque < MIN(pressure)
            if torque_with_sf >= spring_min :
                continue

            if torque_with_sf >= pressure_min :
                continue

            # Вычисляем отклонения от центра
            spring_deviation = abs(torque_with_sf - spring_center)
            pressure_deviation = abs(torque_with_sf - pressure_center)

            total_score = spring_deviation + pressure_deviation

            suitable_combinations.append({
                'spring_qty_code' : qty_code ,
                'spring_qty_name' : group['spring_qty_name'] ,
                'spring_bto' : spring['bto'] ,
                'spring_eto' : spring['eto'] ,
                'spring_min' : spring_min ,
                'spring_center' : spring_center ,
                'spring_deviation' : spring_deviation ,
                'spring_margin' : spring_min - torque_with_sf ,
                'pressure_bto' : pressure['bto'] ,
                'pressure_eto' : pressure['eto'] ,
                'pressure_min' : pressure_min ,
                'pressure_center' : pressure_center ,
                'pressure_deviation' : pressure_deviation ,
                'pressure_margin' : pressure_min - torque_with_sf ,
                'score' : total_score
            })

        if suitable_combinations :
            suitable_combinations.sort(key=lambda x : x['score'])
            best = suitable_combinations[0]

            print(f"   ✅ Найдено {len(suitable_combinations)} подходящих комбинаций")
            print(f"   Лучшая: {best['spring_qty_name']} пружин, score={best['score']:.1f}")

            all_results.append({
                'body_id' : body.id ,
                'body_code' : body.code ,
                'body_name' : body.name ,
                'type' : 'SR' ,
                'combinations' : suitable_combinations ,
                'best_combination' : best ,
                'total_combinations' : len(suitable_combinations)
            })
        else :
            print(f"   ❌ Нет подходящих комбинаций")

    # Сортируем по score
    all_results.sort(key=lambda x : x['best_combination']['score'])

    return all_results[:max_bodies]


def find_suitable_da_actuators(
        torque_with_sf: float ,
        work_pressure_id: int ,
        body_ids: Optional[List[int]] = None ,
        max_bodies: int = 3
) -> List[Dict] :
    """Найти подходящие DA приводы (без пружин)"""

    work_pressure = get_pressure_by_id(work_pressure_id)
    if not work_pressure :
        print(f"❌ Давление с ID={work_pressure_id} не найдено!")
        return []

    print(f"\n{'=' * 80}")
    print(f"ПОИСК DA ПРИВОДОВ")
    print(f"{'=' * 80}")
    print(f"Требуемый момент с запасом: {torque_with_sf} Нм")
    print(f"Рабочее давление: {work_pressure['name']} ({work_pressure['code']} бар)")
    print(f"{'=' * 80}\n")

    if body_ids :
        bodies = PneumaticActuatorBody.objects.filter(id__in=body_ids , is_active=True)
    else :
        bodies = PneumaticActuatorBody.objects.filter(is_active=True)

    all_results = []

    for body in bodies :
        # Получаем DA запись для данного давления
        da_records = BodyThrustTorqueTable.objects.filter(
            body_id=body.id ,
            pressure_id=work_pressure_id ,
            spring_qty__code=SPRINGS_DA_DEFAULT_CODE ,
            spring_qty__is_active=True
        )

        suitable = []
        for record in da_records :
            if record.bto and torque_with_sf < float(record.bto) :
                deviation = float(record.bto) - torque_with_sf
                suitable.append({
                    'bto' : float(record.bto) ,
                    'margin' : deviation ,
                    'score' : deviation
                })

        if suitable :
            suitable.sort(key=lambda x : x['score'])
            best = suitable[0]
            print(f"✅ {body.name}: BTO={best['bto']:.1f}, запас={best['margin']:.1f}")
            all_results.append({
                'body_id' : body.id ,
                'body_code' : body.code ,
                'body_name' : body.name ,
                'type' : 'DA' ,
                'best_combination' : best ,
                'total_combinations' : len(suitable)
            })

    all_results.sort(key=lambda x : x['best_combination']['score'])
    return all_results[:max_bodies]


def build_result_structure(results: List[Dict] , max_bodies: int = 3) -> List[Dict] :
    """
    Формирует структуру для отображения в браузере и дальнейшего отбора
    """
    output = []

    for res in results[:max_bodies] :
        best = res['best_combination']

        if res['type'] == 'SR' :
            item = {
                'body_id' : res['body_id'] ,
                'body_code' : res['body_code'] ,
                'body_name' : res['body_name'] ,
                'type' : 'SR' ,
                'score' : best['score'] ,
                'spring_margin' : best['spring_margin'] ,
                'model_line_items' : [{
                    'body_id' : res['body_id'] ,
                    'body_code' : res['body_code'] ,
                    'actuator_variety' : 'SR' ,
                    'spring_qty_id' : best.get('spring_qty_id') ,
                    'spring_qty_code' : best['spring_qty_code'] ,
                    'spring_qty_name' : best['spring_qty_name'] ,
                    'score' : best['score'] ,
                    'spring_bto' : best['spring_bto'] ,
                    'spring_eto' : best['spring_eto'] ,
                    'spring_min' : best['spring_min'] ,
                    'pressure_bto' : best['pressure_bto'] ,
                    'pressure_eto' : best['pressure_eto'] ,
                    'pressure_min' : best['pressure_min'] ,
                    'spring_margin' : best['spring_margin'] ,
                    'pressure_margin' : best['pressure_margin']
                }]
            }
        else :  # DA
            item = {
                'body_id' : res['body_id'] ,
                'body_code' : res['body_code'] ,
                'body_name' : res['body_name'] ,
                'type' : 'DA' ,
                'score' : best['score'] ,
                'spring_margin' : best['margin'] ,
                'model_line_items' : [{
                    'body_id' : res['body_id'] ,
                    'body_code' : res['body_code'] ,
                    'actuator_variety' : 'DA' ,
                    'spring_qty_id' : None ,
                    'spring_qty_code' : 'DA' ,
                    'spring_qty_name' : 'Без пружин' ,
                    'score' : best['score'] ,
                    'spring_bto' : best['bto'] ,
                    'spring_eto' : best['bto'] ,
                    'spring_min' : best['bto'] ,
                    'pressure_bto' : best['bto'] ,
                    'pressure_eto' : best['bto'] ,
                    'pressure_min' : best['bto'] ,
                    'spring_margin' : best['margin'] ,
                    'pressure_margin' : best['margin']
                }]
            }

        output.append(item)

    return output

def interactive_search() :
    """Интерактивный поиск с ручным вводом параметров"""

    print("\n" + "=" * 80)
    print("ПОИСК ПРИВОДОВ")
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

    # Выполняем поиск
    # Используйте:
    if actuator_variety == 'SR' :
        results = find_suitable_sr_actuators(
            torque_with_sf=torque ,
            work_pressure_id=pressure_id ,
            max_bodies=max_bodies
        )
    else :
        results = find_suitable_da_actuators(
            torque_with_sf=torque ,
            work_pressure_id=pressure_id ,
            max_bodies=max_bodies
        )

    # Выводим итоговый отчет
    print("\n" + "=" * 80)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 80)

    if results :
        print(f"\n✅ Найдено подходящих корпусов: {len(results)}")

        for i , r in enumerate(results , 1) :
            best = r['best_combination']

            if r['type'] == 'SR' :
                best = r['best_combination']
                print(f"\n{i}. {r['body_name']} (code: {r['body_code']}) - {r['type']} {best['spring_qty_name']}")
                print(f"   Score: {best['score']:.1f}")
                print(f"   Моменты на пружинах:")
                print(
                    f"     BTO={best['spring_bto']:.1f}, ETO={best['spring_eto']:.1f}, MIN={best['spring_min']:.1f} Нм")
                print(f"   Моменты по воздуху:")
                print(
                    f"     BTO={best['pressure_bto']:.1f}, ETO={best['pressure_eto']:.1f}, MIN={best['pressure_min']:.1f} Нм")
                print(f"   Запас по моменту: {best['spring_margin']:.1f} Нм")
            if r['type'] == 'DA' :
                best = r['best_combination']
                # Убрали дублирующую строку с номером и названием
                print(f"\n{i}. {r['body_name']} (code: {r['body_code']}) - {r['type']}")
                print(f"   Score: {best['score']:.1f}")
                print(f"   Момент по воздуху (BTO): {best['bto']:.1f} Нм")
                print(f"   Запас по моменту: {best['margin']:.1f} Нм")
                print(f"   Всего комбинаций: {r['total_combinations']}")

            print(f"   Всего комбинаций: {r['total_combinations']}")
    else :
        print("\n❌ Не найдено подходящих корпусов!")
    result_struct = build_result_structure(results , max_bodies)

    # Можно сохранить в session_state для использования в браузере:
    # st.session_state.search_results = result_struct

    # Или вернуть как результат функции
    return result_struct

if __name__ == "__main__" :
    interactive_search()