# pneumatic_actuators/actuator_selector_handler.py

import logging
from typing import Dict, Any, Tuple, Optional, List

from params.models import IpOption, ExdOption, HandWheelInstalledOption, BodyCoatingOption, StemShapes, \
    PneumaticAirSupplyPressure
from pneumatic_actuators.models import PneumaticActuatorVariety
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

    Args:
        params: словарь с выбранными параметрами
            {   'valve_type_id': int,
                'dn_id': int,
                'pn_id': int,
                'mounting_plate_id': int,
                'stem_id': int,
                'torque_without_safety': Decimal,
                'safety_factor': Decimal,
                'torque_with_safety': Decimal,
                'model_line_id': int,
                'model_line_item_id': int,
                'actuator_variety_id': int,
                'safety_position_id': int,
                'ip_id': int,
                'exd_id': int,
                'coating_id': int,
                'hand_wheel_id': int,
                'temp_min': int,
                'temp_max': int
            }

    Returns:
        Dict: результат обработки
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
    model_line_for_IP_list=PneumaticIpOption.get_model_line_for_IP(params.get('ip_id'))
    print(model_line_for_IP_list)
    # Здесь будет логика поиска подходящего привода
    return {
        'success' : True ,
        'message' : 'Параметры получены' ,
        'params_received' : params
    }


# pneumatic_actuators/actuator_selector_handler.py

def get_actuator_options_table(
        model_line_id: Optional[int] = None,
        model_line_item_id: Optional[int] = None,
        actuator_variety_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Создает внутреннюю таблицу всех доступных опций для быстрого поиска.

    Таблица содержит все возможные комбинации параметров и позволяет
    быстро найти подходящие model_line и model_line_item.

    Args:
        model_line_id: ID выбранной серии моделей (опционально)
        model_line_item_id: ID выбранной модели в серии (опционально)
        actuator_variety_id: ID выбранного вида привода (опционально)

    Returns:
        Dict: словарь с таблицами опций в формате:
        {
            'actuator_varieties': [  # все виды приводов
                {'id': 1, 'name': 'DA', 'code': 'DA', 'torque_range': {...}},
                ...
            ],
            'safety_positions': [  # все положения безопасности
                {'id': 1, 'name': 'NO', 'code': 'NO', 'applicable_for': ['SR']},
                ...
            ],
            'ip_options': [  # все IP защиты
                {'id': 1, 'name': 'IP67', 'code': '67', 'price_factor': 1.0},
                ...
            ],
            'exd_options': [...],
            'coating_options': [...],
            'hand_wheel_options': [...],
            'temperature_options': [...],
            'model_lines': [  # все серии моделей
                {
                    'id': 1,
                    'name': 'Серия A',
                    'code': 'SA',
                    'model_items': [  # модели в этой серии
                        {
                            'id': 101,
                            'name': 'SA-100',
                            'code': 'SA-100',
                            'actuator_variety_id': 1,  # DA
                            'torque_min': 10,
                            'torque_max': 100,
                            'temp_min': -20,
                            'temp_max': 80,
                            'ip_options_ids': [1, 2, 3],  # доступные IP
                            'exd_options_ids': [1, 2],
                            'coating_options_ids': [1],
                            'hand_wheel_options_ids': [1, 2],
                            'safety_positions_ids': [1, 2]  # для SR
                        },
                        ...
                    ]
                },
                ...
            ]
        }
    """
    from pneumatic_actuators.models import (
        PneumaticActuatorVariety,
        PneumaticActuatorModelLine,
        PneumaticActuatorModelLineItem
    )
    from params.models import (
        IpOption, ExdOption, HandWheelInstalledOption,
        BodyCoatingOption, SafetyPositionOption,
        DnVariety, PnVariety, MountingPlateTypes, StemSize, StemShapes, ValveTypes
    )
    from pneumatic_actuators.models.pa_options import (
        PneumaticSafetyPositionOption,
        PneumaticTemperatureOption,
        PneumaticIpOption,
        PneumaticExdOption,
        PneumaticBodyCoatingOption,
        PneumaticHandWheelOption
    )

    result = {
        # Базовые опции (не зависят от модели)
        'actuator_varieties': [],
        'safety_positions': [],
        'ip_options': [],
        'exd_options': [],
        'coating_options': [],
        'hand_wheel_options': [],
        'temperature_options': [],

        # Параметры арматуры
        'dn_varieties': [],
        'pn_varieties': [],
        'mounting_plates': [],
        'stem_shapes': [],
        'stem_sizes': [],
        'valve_types': [],

        # Модели приводов (основная таблица)
        'model_lines': [],
        'model_line_items': [],

        # Индексы для быстрого поиска
        '_index_by_id': {},  # {id: item} для всех объектов
        '_index_by_code': {},  # {code: [ids]} для поиска по коду
        '_index_by_model_line': {},  # {model_line_id: [model_line_item_ids]}
        '_index_by_variety': {},  # {actuator_variety_id: [model_line_item_ids]}
    }

    # 1. Загружаем все опции
    result['actuator_varieties'] = PneumaticActuatorVariety.get_for_select(active_only=True)
    result['safety_positions'] = SafetyPositionOption.get_for_select(active_only=True)
    result['ip_options'] = IpOption.get_for_select(active_only=True)
    result['exd_options'] = ExdOption.get_for_select(active_only=True)
    result['coating_options'] = BodyCoatingOption.get_for_select(active_only=True)
    result['hand_wheel_options'] = HandWheelInstalledOption.get_for_select(active_only=True)

    # 2. Загружаем параметры арматуры
    result['dn_varieties'] = DnVariety.get_for_select(active_only=True)
    result['pn_varieties'] = PnVariety.get_for_select(active_only=True)
    result['mounting_plates'] = MountingPlateTypes.get_for_select(active_only=True)
    result['stem_shapes'] = StemShapes.get_for_select(active_only=True)
    result['stem_sizes'] = StemSize.get_for_select(active_only=True)
    result['valve_types'] = ValveTypes.get_for_select(active_only=True)

    # 3. Загружаем все серии моделей
    model_lines = PneumaticActuatorModelLine.get_for_select(active_only=True)

    # 4. Для каждой серии загружаем модели
    for model_line in model_lines:
        model_line_dict = {
            'id': model_line['id'],
            'name': model_line['name'],
            'code': model_line.get('code', ''),
            'description': model_line.get('description', ''),
            'model_items': []
        }

        # Получаем все модели в серии
        model_items = PneumaticActuatorModelLineItem.get_for_select(
            model_line_id=model_line['id'],
            active_only=True
        )

        for item in model_items:
            # Получаем все доступные опции для этой модели
            safety_positions = PneumaticSafetyPositionOption.get_for_select(
                model_line_item_id=item['id'],
                active_only=True
            )

            ip_options = PneumaticIpOption.get_for_select(
                model_line_item_id=item['id'],
                active_only=True
            )

            exd_options = PneumaticExdOption.get_for_select(
                model_line_item_id=item['id'],
                active_only=True
            )

            coating_options = PneumaticBodyCoatingOption.get_for_select(
                model_line_item_id=item['id'],
                active_only=True
            )

            hand_wheel_options = PneumaticHandWheelOption.get_for_select(
                model_line_item_id=item['id'],
                active_only=True
            )

            temperature_options = PneumaticTemperatureOption.get_for_select(
                model_line_item_id=item['id'],
                active_only=True
            )

            item_dict = {
                'id': item['id'],
                'name': item['name'],
                'code': item.get('code', ''),
                'model_line_id': model_line['id'],
                'actuator_variety_id': item.get('actuator_variety_id'),
                'actuator_variety_code': item.get('actuator_variety_code'),

                # Технические характеристики
                'torque_min': item.get('torque_min'),
                'torque_max': item.get('torque_max'),
                'temp_min': item.get('temp_min'),
                'temp_max': item.get('temp_max'),

                # Доступные опции (списки ID)
                'safety_positions_ids': [sp['id'] for sp in safety_positions],
                'ip_options_ids': [ip['id'] for ip in ip_options],
                'exd_options_ids': [exd['id'] for exd in exd_options],
                'coating_options_ids': [coat['id'] for coat in coating_options],
                'hand_wheel_options_ids': [hw['id'] for hw in hand_wheel_options],
                'temperature_options_ids': [temp['id'] for temp in temperature_options],

                # Совместимость с параметрами арматуры
                'compatible_dn_ids': item.get('compatible_dn_ids', []),
                'compatible_pn_ids': item.get('compatible_pn_ids', []),
                'compatible_mounting_plate_ids': item.get('compatible_mounting_plate_ids', []),
                'compatible_stem_shape_ids': item.get('compatible_stem_shape_ids', []),
                'compatible_stem_ids': item.get('compatible_stem_ids', []),
                'compatible_valve_type_ids': item.get('compatible_valve_type_ids', []),
            }

            model_line_dict['model_items'].append(item_dict)

            # Добавляем в плоский список для быстрого доступа
            result['model_line_items'].append(item_dict)

            # Строим индексы
            result['_index_by_id'][item['id']] = item_dict
            result['_index_by_code'][item.get('code', '')] = result['_index_by_code'].get(item.get('code', ''), []) + [
                item['id']]
            result['_index_by_model_line'][model_line['id']] = result['_index_by_model_line'].get(model_line['id'],
                                                                                                  []) + [item['id']]

            variety_id = item.get('actuator_variety_id')
            if variety_id:
                result['_index_by_variety'][variety_id] = result['_index_by_variety'].get(variety_id, []) + [item['id']]

        result['model_lines'].append(model_line_dict)

    return result


def find_compatible_actuators(
        options_table: Dict[str, Any],
        selected_params: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Находит все подходящие модели привода на основе выбранных параметров.

    Args:
        options_table: таблица опций от get_actuator_options_table()
        selected_params: выбранные пользователем параметры
            {
                'valve_type_id': int,
                'dn_id': int,
                'pn_id': int,
                'mounting_plate_id': int,
                'stem_id': int,
                'torque_with_safety': float,
                'actuator_variety_id': int,
                'safety_position_id': int,
                'ip_id': int,
                'exd_id': int,
                'coating_id': int,
                'hand_wheel_id': int,
                'temp_min': int,
                'temp_max': int,
            }

    Returns:
        List[Dict]: список подходящих моделей с рейтингом соответствия
    """
    compatible_items = []

    for item in options_table['model_line_items']:
        score = 0
        reasons = []
        missing_features = []

        # 1. Проверка типа привода
        if selected_params.get('actuator_variety_id'):
            if item['actuator_variety_id'] != selected_params['actuator_variety_id']:
                continue  # Обязательное условие
            score += 10

        # 2. Проверка момента
        torque_needed = selected_params.get('torque_with_safety', 0)
        if torque_needed > 0:
            if item['torque_min'] is not None and torque_needed >= item['torque_min']:
                score += 5
                reasons.append(f"Момент {torque_needed} >= {item['torque_min']}")
            elif item['torque_max'] is not None and torque_needed <= item['torque_max']:
                score += 3
                reasons.append(f"Момент {torque_needed} <= {item['torque_max']}")
            else:
                missing_features.append(
                    f"Момент {torque_needed} вне диапазона ({item['torque_min']}-{item['torque_max']})")

        # 3. Проверка температуры
        temp_min = selected_params.get('temp_min')
        temp_max = selected_params.get('temp_max')
        if temp_min and item['temp_min'] is not None:
            if temp_min >= item['temp_min']:
                score += 2
            else:
                missing_features.append(f"Температура {temp_min}°C ниже минимума {item['temp_min']}°C")

        if temp_max and item['temp_max'] is not None:
            if temp_max <= item['temp_max']:
                score += 2
            else:
                missing_features.append(f"Температура {temp_max}°C выше максимума {item['temp_max']}°C")

        # 4. Проверка положения безопасности (только для SR)
        if selected_params.get('safety_position_id'):
            if selected_params['safety_position_id'] in item['safety_positions_ids']:
                score += 5
                reasons.append("Поддерживает положение безопасности")
            else:
                missing_features.append("Не поддерживает выбранное положение безопасности")

        # 5. Проверка IP защиты
        if selected_params.get('ip_id'):
            if selected_params['ip_id'] in item['ip_options_ids']:
                score += 3
                reasons.append("Поддерживает IP защиту")
            else:
                missing_features.append("Не поддерживает выбранную IP защиту")

        # 6. Проверка Exd
        if selected_params.get('exd_id'):
            if selected_params['exd_id'] in item['exd_options_ids']:
                score += 3
                reasons.append("Поддерживает Exd защиту")
            else:
                missing_features.append("Не поддерживает выбранную Exd защиту")

        # 7. Проверка покрытия
        if selected_params.get('coating_id'):
            if selected_params['coating_id'] in item['coating_options_ids']:
                score += 2
                reasons.append("Поддерживает покрытие")
            else:
                missing_features.append("Не поддерживает выбранное покрытие")

        # 8. Проверка ручного дублера
        if selected_params.get('hand_wheel_id'):
            if selected_params['hand_wheel_id'] in item['hand_wheel_options_ids']:
                score += 2
                reasons.append("Поддерживает ручной дублер")
            else:
                missing_features.append("Не поддерживает ручной дублер")

        # 9. Проверка совместимости с параметрами арматуры
        if selected_params.get('dn_id'):
            if selected_params['dn_id'] in item.get('compatible_dn_ids', []):
                score += 2

        if selected_params.get('pn_id'):
            if selected_params['pn_id'] in item.get('compatible_pn_ids', []):
                score += 2

        if selected_params.get('mounting_plate_id'):
            if selected_params['mounting_plate_id'] in item.get('compatible_mounting_plate_ids', []):
                score += 2

        if selected_params.get('stem_id'):
            if selected_params['stem_id'] in item.get('compatible_stem_ids', []):
                score += 2

        if selected_params.get('valve_type_id'):
            if selected_params['valve_type_id'] in item.get('compatible_valve_type_ids', []):
                score += 2

        # Добавляем модель в результаты, даже если есть missing_features
        compatible_items.append({
            'item': item,
            'score': score,
            'reasons': reasons,
            'missing_features': missing_features,
            'is_compatible': len(missing_features) == 0
        })

    # Сортируем по убыванию score (наиболее подходящие сверху)
    compatible_items.sort(key=lambda x: x['score'], reverse=True)

    return compatible_items