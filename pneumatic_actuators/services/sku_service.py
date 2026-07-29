# pneumatic_actuators/services/sku_service.py
"""
SKU-сервис для пневмоприводов.

Ленивое создание SKU: только при реальном заказе (корзина, счёт, конструктор).
Не при save() модели.

Использование:
    from pneumatic_actuators.services.sku_service import get_or_create_sku

    sku = get_or_create_sku(
        model_line_item=item,
        options={
            'springs_qty': spring_option,
            'temperature': temp_option,
            'safety_position': safety_option,
            'ip': ip_option,
            'exd': exd_option,
            'body_coating': coating_option,
            'hand_wheel': hw_option,
        }
    )
"""
import logging
from typing import Dict, Optional, Any

from django.db import transaction

from sku.models.sku import SKU
from pneumatic_actuators.models import PneumaticActuatorModelLineItem

logger = logging.getLogger(__name__)


def build_pa_sku_code(model_line_item: PneumaticActuatorModelLineItem, options: Dict[str, Any]) -> str:
    """
    Собрать уникальный код SKU из model_line_item + опций.

    Формат: {item_code}-{springs}-{temp}-{safety}-{ip}-{exd}-{coating}-{wheel}

    Пример: PA52SR20-12-NC-IP67-ExdIICT6-Std-NoHW
    """
    parts = [model_line_item.code or model_line_item.name]

    # Опции в фиксированном порядке
    option_keys = [
        'springs_qty', 'temperature', 'safety_position',
        'ip', 'exd', 'body_coating', 'hand_wheel',
    ]

    for key in option_keys:
        opt = options.get(key)
        if opt is None:
            continue
        code = _safe_code(opt)
        if code:
            parts.append(code)

    return '-'.join(parts)


def build_pa_sku_name(model_line_item: PneumaticActuatorModelLineItem, options: Dict[str, Any]) -> str:
    """
    Собрать читаемое наименование SKU.
    """
    ml = model_line_item.model_line
    body = model_line_item.body
    variety = model_line_item.pneumatic_actuator_variety

    name = f"{model_line_item.name or model_line_item.code}"

    if variety:
        name += f", {variety.name}"

    if body and hasattr(body, 'torque_at_6bar') and body.torque_at_6bar:
        name += f", {body.torque_at_6bar} Нм при 6 бар"

    for key, label in [
        ('springs_qty', 'пружин'),
        ('temperature', 't°'),
        ('safety_position', ''),
        ('ip', ''),
        ('exd', ''),
        ('body_coating', ''),
        ('hand_wheel', ''),
    ]:
        opt = options.get(key)
        if opt is None:
            continue
        val = str(opt) if opt else ''
        if val:
            name += f", {label} {val}" if label else f", {val}"

    return name


def get_or_create_sku(
    model_line_item: PneumaticActuatorModelLineItem,
    options: Dict[str, Any],
) -> SKU:
    """
    Получить или создать SKU для заданной конфигурации.

    Args:
        model_line_item: базовая модель (body + variety)
        options: dict с выбранными опциями (springs_qty, temperature, ...)

    Returns:
        SKU instance (созданный или существующий)
    """
    ml = model_line_item.model_line

    code = build_pa_sku_code(model_line_item, options)
    name = build_pa_sku_name(model_line_item, options)

    equipment_type = ml.equipment_type if ml else None
    brand = ml.brand if ml else None

    # Описание с параметрами
    desc_parts = [
        f"Пневмопривод {model_line_item.name}",
    ]
    for key, label in [
        ('springs_qty', 'Кол-во пружин'),
        ('temperature', 'Температура'),
        ('safety_position', 'Положение безопасности'),
        ('ip', 'IP'),
        ('exd', 'Взрывозащита'),
        ('body_coating', 'Покрытие'),
        ('hand_wheel', 'Ручной дублёр'),
    ]:
        opt = options.get(key)
        if opt is not None:
            desc_parts.append(f"{label}: {opt}")

    description = '; '.join(desc_parts)

    with transaction.atomic():
        sku, created = SKU.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': description,
                'equipment_type': equipment_type,
                'brand': brand,
                'is_active': True,
            }
        )
        if created:
            logger.info(f"SKU created: {code} — {name}")
        else:
            logger.debug(f"SKU already exists: {code}")

    return sku


def _safe_code(opt) -> str:
    """Извлечь короткий код из опции (объект, строка или ID/int)."""
    if opt is None:
        return ''
    if isinstance(opt, (int, float)):
        return str(opt)
    if hasattr(opt, 'encoding') and opt.encoding:
        return opt.encoding
    if hasattr(opt, 'code'):
        return opt.code or ''
    if hasattr(opt, 'name'):
        return opt.name or ''
    return str(opt)
