# pneumatic_actuators/actuator_selector_handler.py

import logging
from typing import Dict , List , Optional , Any

logger = logging.getLogger(__name__)


def get_actuator_options(model_line_id: Optional[int] = None ,
                         model_line_item_id: Optional[int] = None) -> Dict[str , Any] :
    """
    Возвращает все доступные опции для привода на основе выбранных параметров

    Args:
        model_line_id: ID выбранной серии моделей
        model_line_item_id: ID выбранной модели в серии

    Returns:
        Dict: словарь со всеми опциями
    """

    # Импортируем модели здесь, чтобы избежать циклических импортов
    from pneumatic_actuators.models import PneumaticActuatorModelLineItem
    from pneumatic_actuators.models.pa_options import (
        PneumaticActuatorVariety ,
        PneumaticSafetyPositionOption ,
        PneumaticIpOption ,
        PneumaticExdOption ,
        PneumaticBodyCoatingOption ,
        PneumaticHandWheelOption
    )

    result = {
        'actuator_varieties' : [] ,
        'safety_positions' : [] ,
        'ip_options' : [] ,
        'exd_options' : [] ,
        'coating_options' : [] ,
        'hand_wheel_options' : []
    }

    # 1. Виды приводов (DA/SR) - не зависят от model_line
    result['actuator_varieties'] = PneumaticActuatorVariety.get_for_select(active_only=True)

    # Если есть model_line_item, получаем опции для него
    if model_line_item_id :
        try :
            model_line_item = PneumaticActuatorModelLineItem.objects.select_related(
                'model_line'
            ).get(id=model_line_item_id)

            # Положения безопасности (зависят от model_line_item)
            result['safety_positions'] = PneumaticSafetyPositionOption.get_for_select(
                model_line_item_id=model_line_item_id ,
                active_only=True
            )

            # Опции, зависящие от model_line (через model_line_item.model_line)
            if model_line_item.model_line :
                model_line = model_line_item.model_line

                result['ip_options'] = PneumaticIpOption.get_for_select(
                    model_line_id=model_line.id ,
                    active_only=True
                )

                result['exd_options'] = PneumaticExdOption.get_for_select(
                    model_line_id=model_line.id ,
                    active_only=True
                )

                result['coating_options'] = PneumaticBodyCoatingOption.get_for_select(
                    model_line_id=model_line.id ,
                    active_only=True
                )

                result['hand_wheel_options'] = PneumaticHandWheelOption.get_for_select(
                    model_line_id=model_line.id ,
                    active_only=True
                )

        except PneumaticActuatorModelLineItem.DoesNotExist :
            logger.warning(f"ModelLineItem with id {model_line_item_id} not found")

    # Если есть только model_line (без конкретной модели)
    elif model_line_id :
        from pneumatic_actuators.models import PneumaticActuatorModelLine

        try :
            model_line = PneumaticActuatorModelLine.objects.get(id=model_line_id)

            result['ip_options'] = PneumaticIpOption.get_for_select(
                model_line_id=model_line.id ,
                active_only=True
            )

            result['exd_options'] = PneumaticExdOption.get_for_select(
                model_line_id=model_line.id ,
                active_only=True
            )

            result['coating_options'] = PneumaticBodyCoatingOption.get_for_select(
                model_line_id=model_line.id ,
                active_only=True
            )

            result['hand_wheel_options'] = PneumaticHandWheelOption.get_for_select(
                model_line_id=model_line.id ,
                active_only=True
            )

        except PneumaticActuatorModelLine.DoesNotExist :
            logger.warning(f"ModelLine with id {model_line_id} not found")

    return result


def get_filtered_model_line_items(model_line_id: Optional[int] = None ,
                                  actuator_variety_code: Optional[str] = None) -> List[Dict] :
    """
    Возвращает список моделей в серии с фильтрацией по виду привода

    Args:
        model_line_id: ID серии моделей
        actuator_variety_code: код вида привода (DA или SR)

    Returns:
        List[Dict]: список моделей
    """
    from pneumatic_actuators.models import PneumaticActuatorModelLineItem

    return PneumaticActuatorModelLineItem.get_for_select(
        model_line_id=model_line_id ,
        actuator_variety_code=actuator_variety_code ,
        active_only=True
    )


def get_initial_data() -> Dict[str , Any] :
    """
    Возвращает начальные данные для загрузки страницы
    """
    from pneumatic_actuators.models import PneumaticActuatorModelLine
    from params.models import DnVariety , PnVariety , MountingPlateTypes , StemSize

    return {
        'model_lines' : PneumaticActuatorModelLine.get_for_select(active_only=True) ,
        'dn_varieties' : DnVariety.get_for_select(active_only=True) ,
        'pn_varieties' : PnVariety.get_for_select(active_only=True) ,
        'mounting_plates' : MountingPlateTypes.get_for_select(active_only=True) ,
        'stem_sizes' : StemSize.get_for_select(active_only=True) ,
    }