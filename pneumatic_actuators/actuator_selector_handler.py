# pneumatic_actuators/actuator_selector_handler.py

import logging
from typing import Dict, List, Optional, Any

from pneumatic_actuators.models import PneumaticActuatorVariety

logger = logging.getLogger(__name__)


def get_actuator_options(model_line_id: Optional[int] = None,
                         model_line_item_id: Optional[int] = None,
                         actuator_variety_id: Optional[int] = None) -> Dict[str, Any]:
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
        PneumaticSafetyPositionOption,
        PneumaticTemperatureOption,
        PneumaticIpOption,
        PneumaticExdOption,
        PneumaticBodyCoatingOption,
        PneumaticHandWheelOption
    )

    result = {
        'actuator_varieties': [],
        'safety_positions': [],
        'temperature_options': [],
        'ip_options': [],
        'exd_options': [],
        'coating_options': [],
        'hand_wheel_options': []
    }

    # 1. Виды приводов (DA/SR) - не зависят от model_line
    result['actuator_varieties'] = PneumaticActuatorVariety.get_for_select(active_only=True)

    # 2. Положения безопасности - с учетом всех параметров
    result['safety_positions'] = get_safety_positions(
        model_line_id=model_line_id,
        model_line_item_id=model_line_item_id,
        actuator_variety_id=actuator_variety_id,
        active_only=True
    )

    # 3. Остальные опции - единообразный вызов
    option_classes = {
        'temperature_options': PneumaticTemperatureOption,
        'ip_options': PneumaticIpOption,
        'exd_options': PneumaticExdOption,
        'coating_options': PneumaticBodyCoatingOption,
        'hand_wheel_options': PneumaticHandWheelOption
    }

    for key, option_class in option_classes.items():
        result[key] = option_class.get_for_select(
            model_line_id=model_line_id,
            model_line_item_id=model_line_item_id,
            active_only=True
        )

    return result


def get_safety_positions(model_line_id: Optional[int] = None,
                         model_line_item_id: Optional[int] = None,
                         actuator_variety_id: Optional[int] = None,
                         active_only: bool = True) -> List[Dict]:
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
    if model_line_item_id:
        logger.debug(f"Getting safety positions for model_line_item_id={model_line_item_id}")
        return PneumaticSafetyPositionOption.get_for_select(
            model_line_item_id=model_line_item_id,
            active_only=active_only
        )

    # Вариант 2: серия моделей
    if model_line_id:
        logger.debug(f"Getting safety positions for model_line_id={model_line_id}")

        # Если указан вид привода, сначала фильтруем модели
        if actuator_variety_id:
            logger.debug(f"Filtering by actuator_variety_id={actuator_variety_id}")
            # Получаем model_line_item_id для данной серии и вида привода
            model_line_item_ids = PneumaticActuatorModelLineItem.objects.filter(
                model_line_id=model_line_id,
                pneumatic_actuator_variety_id=actuator_variety_id
            ).values_list('id', flat=True)

            if not model_line_item_ids:
                logger.warning(
                    f"No model line items found for model_line_id={model_line_id}, actuator_variety_id={actuator_variety_id}")
                return []

            return PneumaticSafetyPositionOption.get_for_select(
                model_line_item_ids=list(model_line_item_ids),
                active_only=active_only
            )

        # Без фильтрации по виду привода
        return PneumaticSafetyPositionOption.get_for_select(
            model_line_id=model_line_id,
            active_only=active_only
        )

    # Вариант 3: только вид привода (без серии)
    if actuator_variety_id:
        logger.debug(f"Getting safety positions for actuator_variety_id={actuator_variety_id}")

        model_line_item_ids = PneumaticActuatorModelLineItem.objects.filter(
            pneumatic_actuator_variety_id=actuator_variety_id
        ).values_list('id', flat=True)

        if not model_line_item_ids:
            logger.warning(f"No model line items found for actuator_variety_id={actuator_variety_id}")
            return []

        return PneumaticSafetyPositionOption.get_for_select(
            model_line_item_ids=list(model_line_item_ids),
            active_only=active_only
        )

    # Вариант 4: базовые опции
    logger.debug("Getting base safety positions from params.SafetyPositionOption")
    queryset = SafetyPositionOption.objects.all()
    if active_only:
        queryset = queryset.filter(is_active=True)

    return [{'id': obj.id, 'name': obj.name, 'code': obj.code} for obj in queryset]


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

    # Используем правильные имена параметров
    return PneumaticActuatorModelLineItem.get_for_select(
        model_line_id=model_line_id,
        actuator_variety_code=actuator_variety_id,  # ← изменили имя параметра
        active_only=True
    )

def get_initial_data() -> Dict[str, Any]:
    """
    Возвращает начальные данные для загрузки страницы
    """
    from pneumatic_actuators.models import PneumaticActuatorModelLine
    from params.models import DnVariety, PnVariety, MountingPlateTypes, StemSize

    return {
        'model_lines': PneumaticActuatorModelLine.get_for_select(active_only=True),
        'dn_varieties': DnVariety.get_for_select(active_only=True),
        'pn_varieties': PnVariety.get_for_select(active_only=True),
        'mounting_plates': MountingPlateTypes.get_for_select(active_only=True),
        'stem_sizes': StemSize.get_for_select(active_only=True),
    }