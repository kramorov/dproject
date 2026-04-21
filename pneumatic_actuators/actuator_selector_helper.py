
# pneumatic_actuators/actuator_selector_helper.py

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