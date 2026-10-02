# pneumatic_actuators/services/sku_service.py
"""
SKU-сервис пневмоприводов (переработан 2026-09-01).

SKU создаётся из ЭТАЛОННОЙ модели PneumaticActuatorCatalogItem (единый путь
SKUMixin.sync_sku(), как в остальных каталогах), а не как standalone-запись:

    get_or_create_sku(model_line_item, options)
        → материализует конфигурацию в PneumaticActuatorCatalogItem
          (code генерируется из model_line.model_item_code_template,
           name/description — из шаблонов серии)
        → item.save() → sync_sku() создаёт/подхватывает SKU по коду
        → возвращает SKU (со связью source_* на item).

Повторный вызов с теми же опциями возвращает ТУ ЖЕ SKU (item ищется
по config_hash — хэшу конфигурации «типоразмер + опции»).

Старый API (build_pa_sku_code/build_pa_sku_name/_safe_code) удалён —
логика артикула теперь живёт в PneumaticActuatorCatalogItem.generated_model_item_code.
"""

import logging
from typing import Any, Dict, Optional

from django.apps import apps
from django.core.exceptions import ValidationError
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
    'manual_override': 'selected_manual_override',
}

# Ключ опции → модель реальной опции ('app_label.ModelName')
_MODEL_BY_KEY = {
    'springs_qty': 'pneumatic_actuators.PneumaticActuatorSpringsQty',
    'temperature': 'pneumatic_actuators.PneumaticTemperatureOption',
    'safety_position': 'params.SafetyPositionOption',
    'ip': 'params.IpOption',
    'exd': 'params.ExdOption',
    'body_coating': 'pneumatic_actuators.PneumaticBodyDesignOption',
    'manual_override': 'params.HandWheelInstalledOption',
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
            endpoint) либо уже созданный PneumaticActuatorCatalogItem.
        options: {'springs_qty': id, 'temperature': id, 'safety_position': id,
                  'ip': id, 'exd': id, 'body_coating': id, 'manual_override': id}
                 — ID реальных опций (как шлёт фронтенд).

    Returns:
        SKU, привязанный к эталонной модели (source_* → PneumaticActuatorCatalogItem).
    """
    from pneumatic_actuators.models.pa_item import PneumaticActuatorCatalogItem
    from pneumatic_actuators.models.pa_model_line import PneumaticActuatorModelLineItem

    options = options or {}

    if isinstance(model_line_item, PneumaticActuatorCatalogItem):
        item = model_line_item
        if not item.sku_id:
            item.save()
        item.refresh_from_db()
        return item.sku

    if not isinstance(model_line_item, PneumaticActuatorModelLineItem):
        raise TypeError(
            'model_line_item должен быть PneumaticActuatorModelLineItem '
            'или PneumaticActuatorCatalogItem'
        )

    kwargs = {
        'source_model_line_item': model_line_item,
        'model_line': model_line_item.model_line,
        'body': model_line_item.body,
        'pneumatic_actuator_variety': model_line_item.pneumatic_actuator_variety,
    }
    for key, field in _FIELD_BY_KEY.items():
        kwargs[field] = _resolve_option(_MODEL_BY_KEY[key], options.get(key))

    # Идентичность карточки — config_hash (не code): code производный и может
    # меняться при смене кодировки, а хэш фиксирует конфигурацию
    # (типоразмер + опции). Дедуплицируем по хэшу, а не по kwargs/code.
    config_hash = None
    try:
        probe = PneumaticActuatorCatalogItem(**kwargs)
        config_hash = probe.compute_config_hash() or None
    except Exception:
        logger.exception('Не удалось вычислить config_hash для дедупликации')
        config_hash = None

    with transaction.atomic():
        if config_hash:
            existing = PneumaticActuatorCatalogItem.objects.filter(config_hash=config_hash).first()
            if existing:
                if not existing.sku_id:
                    existing.save()
                existing.refresh_from_db()
                return existing.sku

        try:
            # get_or_create вызывает item.save() → автогенерация code/name/description
            # + sync_sku() (SKUMixin). Тот же набор опций → тот же item → та же SKU.
            item, created = PneumaticActuatorCatalogItem.objects.get_or_create(**kwargs)
        except (IntegrityError, ValidationError):
            # Конкуренция/повторный config_hash: другой item уже занял — берём его
            if config_hash:
                item = PneumaticActuatorCatalogItem.objects.filter(config_hash=config_hash).first()
                if item is None:
                    raise
            else:
                raise

        if created:
            logger.info(f"PneumaticActuatorCatalogItem создан: {item.code} (source={model_line_item.pk})")
        if not item.sku_id:
            # item без SKU (например, сохранён со skip) — досинхронизировать
            try:
                item.save()
            except (IntegrityError, ValidationError):
                # config_hash/SKU уже заняты другим item'ом — берём его
                if config_hash:
                    item = PneumaticActuatorCatalogItem.objects.filter(config_hash=config_hash).first()
                    if item is None:
                        raise
                else:
                    raise

    item.refresh_from_db()
    return item.sku
