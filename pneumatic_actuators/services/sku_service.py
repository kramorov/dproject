# pneumatic_actuators/services/sku_service.py
"""
SKU-сервис пневмоприводов (переработан 2026-09-01).

SKU создаётся из ЭТАЛОННОЙ модели PneumaticActuatorCatalogItem (единый путь
SKUMixin.sync_sku(), как в остальных каталогах), а не как standalone-запись:

    materialize_configuration(model_line_item, options) -> (sku, created)
        → материализует конфигурацию в PneumaticActuatorCatalogItem
          (code генерируется из model_line.model_item_code_template,
           name/description — из шаблонов серии; вес — сразу; карточка
           origin=generated + exclude_from_catalog=True)
        → item.save() → sync_sku() создаёт/подхватывает SKU по коду
        → возвращает (SKU, created) со связью source_* на item.

    get_or_create_sku(...) — backward-compat обёртка, возвращает только SKU.

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
    'body_color': 'selected_body_color',
    'manual_override': 'selected_manual_override',
}

# Ключ опции → модель реальной опции ('app_label.ModelName')
_MODEL_BY_KEY = {
    'springs_qty': 'pneumatic_actuators.PneumaticActuatorSpringsQty',
    'temperature': 'pneumatic_actuators.PneumaticTemperatureOption',
    'safety_position': 'params.SafetyPositionOption',
    'ip': 'params.IpOption',
    'exd': 'pneumatic_actuators.PneumaticExdOption',
    'body_coating': 'pneumatic_actuators.PneumaticBodyDesignOption',
    'body_color': 'pneumatic_actuators.PneumaticBodyColorOption',
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


def materialize_configuration(model_line_item, options: Optional[Dict[str, Any]] = None):
    """Материализовать конфигурацию в ``PneumaticActuatorCatalogItem`` + SKU.

    Возвращает ``(sku, created)``: ``created=True`` если карточка создана заново,
    ``False`` — если переиспользована существующая (по ``config_hash``).

    Карточки конфигуратора создаются с ``origin=generated`` и
    ``exclude_from_catalog=True`` (нестандартные конфигурации не показываем
    в листингах каталога); вес материализуется сразу (как в ``generate_pa_cards``).
    """
    from pneumatic_actuators.models.pa_item import PneumaticActuatorCatalogItem
    from pneumatic_actuators.models.pa_model_line import PneumaticActuatorModelLineItem

    options = options or {}

    if isinstance(model_line_item, PneumaticActuatorCatalogItem):
        item = model_line_item
        if not item.sku_id:
            item.save()
        item.refresh_from_db()
        return item.sku, False

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
        'origin': PneumaticActuatorCatalogItem.Origin.GENERATED,
        'exclude_from_catalog': True,
    }
    for key, field in _FIELD_BY_KEY.items():
        kwargs[field] = _resolve_option(_MODEL_BY_KEY[key], options.get(key))

    # through-опция ручного дублера — для точного веса (как from_constructor).
    if model_line_item and kwargs.get('selected_manual_override'):
        from pneumatic_actuators.models.pa_options import PneumaticManualOverrideOption
        kwargs['manual_override_option'] = PneumaticManualOverrideOption.objects.filter(
            model_line_item=model_line_item,
            hand_wheel_option=kwargs['selected_manual_override'],
        ).order_by('id').first()

    probe = PneumaticActuatorCatalogItem(**kwargs)
    try:
        probe.weight = probe.compute_weight()
    except Exception:
        logger.exception('Не удалось вычислить weight для карточки')

    config_hash = None
    try:
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
                return existing.sku, False

        try:
            probe.save()
        except (IntegrityError, ValidationError):
            # Гонка: другой поток успел создать такую же конфигурацию.
            if config_hash:
                item = PneumaticActuatorCatalogItem.objects.filter(config_hash=config_hash).first()
                if item is None:
                    raise
                item.refresh_from_db()
                return item.sku, False
            raise

        logger.info(
            f"PneumaticActuatorCatalogItem создан: {probe.code} (source={model_line_item.pk})"
        )
        probe.refresh_from_db()
        if not probe.sku_id:
            # sync_sku не привязал SKU (напр. коллизия кода) — досинхронизировать.
            probe.save()
            probe.refresh_from_db()

    return probe.sku, True


def get_or_create_sku(model_line_item, options: Optional[Dict[str, Any]] = None) -> SKU:
    """Backward-compat: вернуть только SKU (без флага created)."""
    sku, _created = materialize_configuration(model_line_item, options)
    return sku
