# pneumatic_actuators/actuator_selector_handler.py

import logging
from typing import Dict, Any, Tuple, Optional, List

from params.models import IpOption, ExdOption, HandWheelInstalledOption, BodyCoatingOption, StemShapes, \
    PneumaticAirSupplyPressure
from pneumatic_actuators.models import BodyThrustTorqueTable, PneumaticActuatorVariety
from pneumatic_actuators.models.pa_options import PneumaticIpOption

logger = logging.getLogger(__name__)


def get_actuator_options(model_line_id: Optional[int] = None ,
                         model_line_item_id: Optional[int] = None ,
                         actuator_variety_id: Optional[int] = None) -> Dict[str , Any] :
    """
    Возвращает все доступные опции для привода на основе выбранных параметров

    Args:
        model_line_id: ID выбранной серии моделей
        model_line_item_id: ID выбранной модели в серии
        actuator_variety_id: ID выбранного вида привода (DA/SR)

    Returns:
        Dict: словарь со всеми опциями
    """
    from pneumatic_actuators.models.pa_options import (
        PneumaticSafetyPositionOption ,
        PneumaticTemperatureOption ,
        PneumaticIpOption ,
        PneumaticExdOption ,
        PneumaticBodyCoatingOption ,
        PneumaticHandWheelOption
    )

    result = {
        'actuator_varieties' : [] ,
        'safety_positions' : [] ,
        'temperature_options' : [] ,
        'ip_options' : [] ,
        'exd_options' : [] ,
        'coating_options' : [] ,
        'hand_wheel_options' : []
    }

    # 1. Виды приводов (DA/SR) - не зависят от model_line
    result['actuator_varieties'] = PneumaticActuatorVariety.get_for_select(active_only=True)

    # 2. Положения безопасности - с учетом всех параметров
    result['safety_positions'] = get_safety_positions(
        model_line_id=model_line_id ,
        model_line_item_id=model_line_item_id ,
        actuator_variety_id=actuator_variety_id ,
        active_only=True
    )

    # 3. Температурные опции - задаются вручную, НЕ зависят от модели привода
    # result['temperature_options'] = PneumaticTemperatureOption.get_for_select(active_only=True)

    # 4. Остальные опции (IP, Exd, покрытие, ручной дублер) - зависят от model_line
    # option_classes = {
    #     'ip_options' : PneumaticIpOption ,
    #     'exd_options' : PneumaticExdOption ,
    #     'coating_options' : PneumaticBodyCoatingOption ,
    #     'hand_wheel_options' : PneumaticHandWheelOption
    # }

    # for key , option_class in option_classes.items() :
    #     result[key] = option_class.get_for_select(
    #         model_line_id=model_line_id ,
    #         model_line_item_id=model_line_item_id ,
    #         active_only=True
    #     )
    #
    # return result
    option_classes = {
        'ip_options' : IpOption ,
        'exd_options' : ExdOption ,
        'coating_options' : BodyCoatingOption ,
        'hand_wheel_options' : HandWheelInstalledOption
    }
    for key , option_class in option_classes.items() :
        result[key] = option_class.get_for_select(
            active_only=True
        )

    return result

def get_safety_positions(model_line_id: Optional[int] = None ,
                         model_line_item_id: Optional[int] = None ,
                         actuator_variety_id: Optional[int] = None ,
                         active_only: bool = True) -> List[Dict] :
    """
    Получить опции положения безопасности с учетом всех параметров

    Логика отбора:
    1. Если есть model_line_item_id - берем опции для конкретной модели
    2. Если есть model_line_id - берем опции для всех моделей в серии
       (с учетом actuator_variety_id, если указан)
    3. Если есть actuator_variety_id - берем опции для всех моделей с таким видом привода
    4. Если ничего нет - берем базовые опции из params.SafetyPositionOption
    """
    from pneumatic_actuators.models import PneumaticActuatorModelLineItem
    from pneumatic_actuators.models.pa_options import PneumaticSafetyPositionOption
    from params.models import SafetyPositionOption

    # Приоритет: model_line_item_id > model_line_id > actuator_variety_id > базовые опции

    # Вариант 1: конкретная модель
    if model_line_item_id :
        logger.debug(f"Getting safety positions for model_line_item_id={model_line_item_id}")
        return PneumaticSafetyPositionOption.get_for_select(
            model_line_item_id=model_line_item_id ,
            active_only=active_only
        )

    # Вариант 2: серия моделей
    if model_line_id :
        logger.debug(f"Getting safety positions for model_line_id={model_line_id}")

        # Если указан вид привода, сначала фильтруем модели
        if actuator_variety_id :
            logger.debug(f"Filtering by actuator_variety_id={actuator_variety_id}")
            # Получаем model_line_item_id для данной серии и вида привода
            model_line_item_ids = PneumaticActuatorModelLineItem.objects.filter(
                model_line_id=model_line_id ,
                pneumatic_actuator_variety_id=actuator_variety_id
            ).values_list('id' , flat=True)

            if not model_line_item_ids :
                logger.warning(
                    f"No model line items found for model_line_id={model_line_id}, actuator_variety_id={actuator_variety_id}")
                return []

            return PneumaticSafetyPositionOption.get_for_select(
                model_line_item_ids=list(model_line_item_ids) ,
                active_only=active_only
            )

        # Без фильтрации по виду привода
        return PneumaticSafetyPositionOption.get_for_select(
            model_line_id=model_line_id ,
            active_only=active_only
        )

    # Вариант 3: только вид привода (без серии)
    if actuator_variety_id :
        logger.debug(f"Getting safety positions for actuator_variety_id={actuator_variety_id}")

        model_line_item_ids = PneumaticActuatorModelLineItem.objects.filter(
            pneumatic_actuator_variety_id=actuator_variety_id
        ).values_list('id' , flat=True)

        if not model_line_item_ids :
            logger.warning(f"No model line items found for actuator_variety_id={actuator_variety_id}")
            return []

        return PneumaticSafetyPositionOption.get_for_select(
            model_line_item_ids=list(model_line_item_ids) ,
            active_only=active_only
        )

    # Вариант 4: базовые опции
    logger.debug("Getting base safety positions from params.SafetyPositionOption")
    queryset = SafetyPositionOption.objects.all()
    if active_only :
        queryset = queryset.filter(is_active=True)

    return [{'id' : obj.id , 'name' : obj.name , 'code' : obj.code} for obj in queryset]


def get_filtered_model_line_items(model_line_id: Optional[int] = None,
                                  actuator_variety_id: Optional[int] = None) -> List[Dict]:
    """
    Возвращает список моделей в серии с фильтрацией по виду привода

    Args:
        model_line_id: ID серии моделей
        actuator_variety_id: ID вида привода (DA или SR)

    Returns:
        List[Dict]: список моделей
    """
    from pneumatic_actuators.models import PneumaticActuatorModelLineItem

    return PneumaticActuatorModelLineItem.get_for_select(
        model_line_id=model_line_id,
        actuator_variety_id=actuator_variety_id,
        active_only=True
    )

def get_initial_data() -> Dict[str, Any]:
    """
    Возвращает начальные данные для загрузки страницы
    """
    from pneumatic_actuators.models import PneumaticActuatorModelLine
    from params.models import DnVariety, PnVariety, MountingPlateTypes, StemSize, ValveTypes

    return {
        'model_lines': PneumaticActuatorModelLine.get_for_select(active_only=True),
        'dn_varieties': DnVariety.get_for_select(active_only=True),
        'pn_varieties': PnVariety.get_for_select(active_only=True),
        'air_pressure': PneumaticAirSupplyPressure.get_for_select(active_only=True),
        'mounting_plates': MountingPlateTypes.get_for_select(active_only=True),
        'stem_shapes': StemShapes.get_for_select(active_only=True),
        'stem_sizes': StemSize.get_for_select(active_only=True),
        'valve_types': ValveTypes.get_for_select(active_only=True),  # <-- добавить
    }


def validate_selection_params(params: Dict[str , Any]) -> Tuple[bool , Optional[str] , Optional[str] , List[str]] :
    """
    Валидация параметров подбора привода

    Args:
        params: словарь с параметрами

    Returns:
        Tuple[bool, Optional[str], Optional[str], List[str]]:
            - is_valid: результат валидации
            - error_field: имя поля с ошибкой
            - error_message: сообщение об ошибке
            - error_fields: список всех полей с ошибками
    """
    errors = []
    error_fields = []

    # 1. Проверка типа арматуры
    if not params.get('valve_type_id') or params.get('valve_type_id') == 0 :
        errors.append("Не выбран тип арматуры")
        error_fields.append('valve_type_id')

    # 2. Проверка момента с запасом
    torque_with_safety = params.get('torque_with_safety' , 0)
    if not torque_with_safety or torque_with_safety <= 0 :
        errors.append("Не указан момент с запасом (должен быть больше 0)")
        error_fields.append('torque_with_safety')

    # 2A. Проверка управляющего давления
    if not params.get('air_pressure_id') or params.get('air_pressure_id') == 0:
        errors.append("Не указано давление в пневмосистеме")
        error_fields.append('air_pressure_id')

    # 3. Проверка типа привода DA/SR
    actuator_variety_id = params.get('actuator_variety_id')
    if not actuator_variety_id or actuator_variety_id == 0 :
        errors.append("Не выбран тип привода (DA/SR)")
        error_fields.append('actuator_variety_id')

    # 4. Если привод SR - проверка положения безопасности
    actuator_variety_code = params.get('actuator_variety_code')
    safety_position_id = params.get('safety_position_id')

    if actuator_variety_code == 'SR' :
        if not safety_position_id or safety_position_id == 0 :
            errors.append("Для привода SR обязательно выбор положения безопасности (NO/NC)")
            error_fields.append('safety_position_id')

    if errors :
        return False , error_fields[0] if error_fields else None , errors[0] , error_fields

    return True , None , None , []

# def find_apppropriate_model_line(params: Dict[str , Any]) -> Dict[str , Any] :

def process_selection_params(params: Dict[str , Any]) -> Dict[str , Any] :
    """
    Обрабатывает параметры выбранные на странице подбора привода
    """
    import json
    from datetime import datetime

    # Валидация
    is_valid , error_field , error_message , error_fields = validate_selection_params(params)

    if not is_valid :
        print(f"\n❌ ОШИБКА ВАЛИДАЦИИ: {error_message}")
        print(f"Поле с ошибкой: {error_field}")
        return {
            'success' : False ,
            'error' : error_message ,
            'error_field' : error_field ,
            'error_fields' : error_fields
        }

    print("\n" + "=" * 60)
    print("🔍 ПОЛУЧЕН ЗАПРОС НА ПОДБОР ПРИВОДА")
    print("=" * 60)
    print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📋 ПАРАМЕТРЫ АРМАТУРЫ:")
    print(f"  - Тип арматуры ID: {params.get('valve_type_id')}")
    print(f"  - DN ID: {params.get('dn_id')}")
    print(f"  - PN ID: {params.get('pn_id')}")
    print(f"  - Монтажная площадка ID: {params.get('mounting_plate_id')}")
    print(f"  - Шток ID: {params.get('stem_id')}")

    print("\n⚙️ РАСЧЕТНЫЕ ПАРАМЕТРЫ:")
    print(f"  - Момент без запаса: {params.get('torque_without_safety')} Нм")
    print(f"  - Коэффициент запаса: {params.get('safety_factor')}")
    print(f"  - Момент с запасом: {params.get('torque_with_safety')} Нм")

    print("\n🔧 ТРЕБОВАНИЯ К ПРИВОДУ:")
    print(f"  - Серия моделей ID: {params.get('model_line_id')}")
    print(f"  - Модель в серии ID: {params.get('model_line_item_id')}")
    print(f"  - Вид привода ID: {params.get('actuator_variety_id')}")
    print(f"  - Положение безопасности ID: {params.get('safety_position_id')}")
    print(f"  - Давление в пневмосистеме: {params.get('air_pressure_id')}")
    print(f"  - IP защита ID: {params.get('ip_id')}")
    print(f"  - Exd взрывозащита ID: {params.get('exd_id')}")
    print(f"  - Покрытие корпуса ID: {params.get('coating_id')}")
    print(f"  - Ручной дублер ID: {params.get('hand_wheel_id')}")

    print("\n🌡️ ТЕМПЕРАТУРНЫЕ ПАРАМЕТРЫ:")
    print(f"  - Мин. температура: {params.get('temp_min')} °C")
    print(f"  - Макс. температура: {params.get('temp_max')} °C")

    print("\n" + "=" * 60)
    print("✅ ПАРАМЕТРЫ УСПЕШНО ПОЛУЧЕНЫ")
    print("=" * 60 + "\n")

    work_pressure_id = params.get('air_pressure_id')
    if not work_pressure_id :
        work_pressure_id = 13  # 6 бар по умолчанию

    torque_with_safety = float(params.get('torque_with_safety' , 0))
    actuator_variety_code = params.get('actuator_variety_code' , 'DA')

    print(f"Требуемый момент с запасом: {torque_with_safety} Нм")
    print(f"Тип привода: {actuator_variety_code}")

    # Вызываем поиск подходящих приводов
    try :
        search_results = BodyThrustTorqueTable.find_suitable_actuators(
            torque_with_sf=torque_with_safety ,
            work_pressure_id=work_pressure_id ,
            actuator_variety=actuator_variety_code ,
            max_bodies=2
        )

        print(f"\n✅ Найдено подходящих серий: {len(search_results)}")

        total_items = 0
        for ml in search_results :
            items_count = len(ml.get('model_line_items' , []))
            total_items += items_count
            print(
                f"\n  Серия: {ml.get('model_line_name' , 'N/A')} ({ml.get('model_line_code' , 'N/A')}) - {items_count} моделей")

            for item in ml.get('model_line_items' , []) :
                print(
                    f"\n    Модель: {item.get('model_line_item_name' , 'N/A')} ({item.get('model_line_item_code' , 'N/A')})")
                print(f"      Корпус: {item.get('body_name' , 'N/A')} ({item.get('body_code' , 'N/A')})")
                print(f"      Тип: {item.get('actuator_variety_code' , 'DA')}")
                print(f"      Score: {item.get('score' , 0):.1f}")
                print(f"      Запас по моменту: {item.get('spring_margin' , 0):.1f} Нм")

                if item.get('actuator_variety_code') == 'SR' :
                    print(f"      Пружины: {item.get('spring_qty_name' , 'N/A')}")
                    print(
                        f"        Моменты на пружинах: BTO={item.get('spring_bto' , 0):.1f}, ETO={item.get('spring_eto' , 0):.1f}")
                    print(
                        f"        Моменты по воздуху: BTO={item.get('pressure_bto' , 0):.1f}, ETO={item.get('pressure_eto' , 0):.1f}")
                else :
                    print(f"        Момент по воздуху (BTO): {item.get('spring_bto' , 0):.1f} Нм")

        print(f"\n✅ Всего найдено моделей: {total_items}")

        return {
            'success' : True ,
            'message' : 'Параметры получены, поиск выполнен' ,
            'params_received' : params ,
            'search_results' : search_results ,
            'total_found' : total_items
        }

    except Exception as e :
        print(f"\n❌ Ошибка при поиске: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success' : False ,
            'error' : f'Ошибка при поиске приводов: {str(e)}' ,
            'params_received' : params
        }
    # model_line_for_IP_list=PneumaticIpOption.get_model_line_for_IP(params.get('ip_id'))
    # print(model_line_for_IP_list)
    # # Здесь будет логика поиска подходящего привода
    # return {
    #     'success' : True ,
    #     'message' : 'Параметры получены' ,
    #     'params_received' : params
    # }

def find_compatible_actuators_by_model_line(
        selected_params: Dict[str, Any]
        ) -> List[Dict[str, Any]]:
    ''' Ищет модель по количеству пружин, моментам, модели'''
    return []
