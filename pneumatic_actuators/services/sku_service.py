# pneumatic_actuators/services/sku_service.py
"""
SKU-сервис пневмоприводов (переработан 2026-09-01).

SKU создаётся из ЭТАЛОННОЙ модели PneumaticActuatorItem (единый путь
SKUMixin.sync_sku(), как в остальных каталогах), а не как standalone-запись:

    get_or_create_sku(model_line_item, options)
        → материализует конфигурацию в PneumaticActuatorItem
          (code генерируется из model_line.model_item_code_template,
           name/description — из шаблонов серии)
        → item.save() → sync_sku() создаёт/подхватывает SKU по коду
        → возвращает SKU (со связью source_* на item).

Повторный вызов с теми же опциями возвращает ТУ ЖЕ SKU (item ищется
по source_model_line_item + выбранным опциям).

Старый API (build_pa_sku_code/build_pa_sku_name/_safe_code) удалён —
логика артикула теперь живёт в PneumaticActuatorItem.generated_model_item_code.
"""

import logging
from typing import Any, Dict, Optional

from django.apps import apps
from django.db import IntegrityError, transaction

from sku.models import SKU

logger = logging.getLogger(__name__)

# Ключ опции (из фронтенда) → поле эталонной модели
_FIELD_BY_KEY = {
    'springs_qty': 'selected_springs_qty',
    'temperature': 'selected_temperature',
    'safety_position': 'selected_safety_position',
    'ip': 'selected_ip',
    'exd': 'selected_exd',
    'body_coating': 'selected_body_coating',
    'hand_wheel': 'selected_hand_wheel',
}

# Ключ опции → модель реальной опции ('app_label.ModelName')
_MODEL_BY_KEY = {
    'springs_qty': 'pneumatic_actuators.PneumaticActuatorSpringsQty',
    'temperature': 'pneumatic_actuators.PneumaticTemperatureOption',
    'safety_position': 'params.SafetyPositionOption',
    'ip': 'params.IpOption',
    'exd': 'params.ExdOption',
    'body_coating': 'params.BodyCoatingOption',
    'hand_wheel': 'params.HandWheelInstalledOption',
}


def _resolve_option(model_path: str, value: Any) -> Optional[Any]:
    """Разрешить значение опции в объект реальной опции (или None).

    Принимает: None/'' → None; экземпляр модели → как есть; id (int/str) → объект.
    """
    if value is None or value == '':
        return None
    model = apps.get_model(*model_path.rsplit('.', 1))
    if isinstance(value, model):
        return value
    try:
        return model.objects.filter(pk=value).first()
    except (ValueError, TypeError):
        logger.warning(f"Не удалось разрешить опцию {model_path} по значению {value!r}")
        return None


def get_or_create_sku(model_line_item, options: Optional[Dict[str, Any]] = None) -> SKU:
    """
    Получить или создать SKU для конфигурации пневмопривода.

    Args:
        model_line_item: PneumaticActuatorModelLineItem (legacy, из create-sku
            endpoint) либо уже созданный PneumaticActuatorItem.
        options: {'springs_qty': id, 'temperature': id, 'safety_position': id,
                  'ip': id, 'exd': id, 'body_coating': id, 'hand_wheel': id}
                 — ID реальных опций (как шлёт фронтенд).

    Returns:
        SKU, привязанный к эталонной модели (source_* → PneumaticActuatorItem).
    """
    from pneumatic_actuators.models.pa_item import PneumaticActuatorItem
    from pneumatic_actuators.models.pa_model_line import PneumaticActuatorModelLineItem

    options = options or {}

    if isinstance(model_line_item, PneumaticActuatorItem):
        item = model_line_item
        if not item.sku_id:
            item.save()
        item.refresh_from_db()
        return item.sku

    if not isinstance(model_line_item, PneumaticActuatorModelLineItem):
        raise TypeError(
            'model_line_item должен быть PneumaticActuatorModelLineItem '
            'или PneumaticActuatorItem'
        )

    kwargs = {
        'source_model_line_item': model_line_item,
        'model_line': model_line_item.model_line,
        'body': model_line_item.body,
        'pneumatic_actuator_variety': model_line_item.pneumatic_actuator_variety,
    }
    for key, field in _FIELD_BY_KEY.items():
        kwargs[field] = _resolve_option(_MODEL_BY_KEY[key], options.get(key))

    # Артикул однозначно определяет SKU. Разные пути входа (сохранение формы
    # конструктора с автодефолтами vs create-sku с частичным набором опций)
    # могут давать одинаковый code при разных наборах опций — дедуплицируем
    # СНАЧАЛА по коду, а не по kwargs (иначе второй item попытается привязать
    # уже занятую OneToOne SKU → UNIQUE violation).
    code = None
    try:
        probe = PneumaticActuatorItem(**kwargs)
        code = probe.generated_model_item_code or None
    except Exception:
        logger.exception('Не удалось вычислить артикул для дедупликации')
        code = None

    with transaction.atomic():
        if code:
            existing = PneumaticActuatorItem.objects.filter(code=code).first()
            if existing:
                if not existing.sku_id:
                    existing.save()
                existing.refresh_from_db()
                return existing.sku

        try:
            # get_or_create вызывает item.save() → автогенерация code/name/description
            # + sync_sku() (SKUMixin). Тот же набор опций → тот же item → та же SKU.
            item, created = PneumaticActuatorItem.objects.get_or_create(**kwargs)
        except IntegrityError:
            # Конкуренция/повторный code: другой item уже занял SKU — берём его
            if code:
                item = PneumaticActuatorItem.objects.filter(code=code).first()
                if item is None:
                    raise
            else:
                raise

        if created:
            logger.info(f"PneumaticActuatorItem создан: {item.code} (source={model_line_item.pk})")
        if not item.sku_id:
            # item без SKU (например, сохранён со skip) — досинхронизировать
            try:
                item.save()
            except IntegrityError:
                # SKU с таким code уже привязана к другому item'у — берём его
                if code:
                    item = PneumaticActuatorItem.objects.filter(code=code).first()
                    if item is None:
                        raise
                else:
                    raise

    item.refresh_from_db()
    return item.sku
