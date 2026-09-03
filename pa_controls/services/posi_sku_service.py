# pa_controls/services/posi_sku_service.py
"""
SKU-сервис позиционеров (аналог pneumatic_actuators/services/sku_service.py).

Материализация конфигурации конструктора в ЭТАЛОННУЮ модель
PosiModelLineItem + SKU (единый путь SKUMixin.sync_sku()):

    materialize(constructor)
        → собирает kwargs item'а из выбранных опций формы
        → item.clean() — валидация комбинаций (рычаг/тип, «только общепром»)
        → дедупликация СНАЧАЛА по коду (артикул однозначно определяет SKU),
          затем get_or_create по набору опций
        → item.save() → автогенерация code/name/description + sync_sku()
        → возвращает item (с привязанным SKU).

Повторный вызов с тем же набором опций возвращает ТОТ ЖЕ item и ТУ ЖЕ SKU.
"""
import logging
from typing import Optional, Tuple

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from pa_controls.models import PosiModelLineItem

logger = logging.getLogger(__name__)


def build_item_kwargs(constructor) -> dict:
    """kwargs PosiModelLineItem из выбранных опций формы конструктора."""
    return {
        'model_line': constructor.selected_model_line,
        'acting_type': (constructor.selected_model_line.acting_type
                        if constructor.selected_model_line else None),
        'body_connection': constructor.selected_body_connection,
        'lever': constructor.selected_lever,
        'work_temp_min': constructor.work_temp_min,
        'work_temp_max': constructor.work_temp_max,
        'signal_profile': constructor.selected_signal_profile,
        'smart_capability_set': constructor.selected_smart_capability_set,
        'alarm': constructor.selected_alarm,
        'exd': constructor.selected_exd,
    }


def _probe_code(kwargs: dict) -> Optional[str]:
    """Артикул конфигурации без сохранения (для дедупликации по коду)."""
    try:
        probe = PosiModelLineItem(**kwargs)
        return probe.generated_model_item_code or None
    except Exception:
        logger.exception('Не удалось вычислить артикул позиционера для дедупликации')
        return None


def materialize(constructor) -> Tuple[PosiModelLineItem, Optional[object]]:
    """Создать или обновить PosiModelLineItem + SKU из конфигурации конструктора.

    Args:
        constructor: PositionerConstructor с заполненными опциями
            (после _ensure_valid_options()/_sync_derived_fields()).

    Returns:
        (item, sku) — эталонный PosiModelLineItem и его SKU
        (или None, если SKU не создалась).

    Raises:
        ValidationError — невалидная комбинация опций (конфликты item.clean()).
    """
    if not constructor.selected_model_line_id:
        raise ValidationError({'selected_model_line': 'Серия позиционеров не выбрана.'})

    kwargs = build_item_kwargs(constructor)

    # Валидация комбинаций ДО сохранения: рычаг/тип, «только общепром» (item.clean())
    probe = PosiModelLineItem(**kwargs)
    probe.clean()

    # Артикул однозначно определяет SKU. Дедуплицируем СНАЧАЛА по коду, а не
    # по kwargs (иначе второй item попытается привязать уже занятую OneToOne
    # SKU → UNIQUE violation) — паттерн sku_service ПП.
    code = _probe_code(kwargs)

    with transaction.atomic():
        if code:
            existing = PosiModelLineItem.objects.filter(code=code).first()
            if existing:
                if not existing.is_active:
                    existing.is_active = True
                    existing.save()
                if not existing.sku_id:
                    existing.save()
                existing.refresh_from_db()
                return existing, getattr(existing, 'sku', None)

        try:
            # get_or_create вызывает item.save() → автогенерация
            # code/name/description + sync_sku() (SKUMixin).
            item, created = PosiModelLineItem.objects.get_or_create(**kwargs)
        except IntegrityError:
            # Конкуренция/повторный code: другой item уже занял SKU — берём его
            if code:
                item = PosiModelLineItem.objects.filter(code=code).first()
                if item is None:
                    raise
            else:
                raise

        if created:
            logger.info(f"PosiModelLineItem создан: {item.code} (series={constructor.selected_model_line_id})")
        elif not item.is_active:
            item.is_active = True
            item.save()

        if not item.sku_id:
            # item без SKU (например, сохранён со skip) — досинхронизировать
            try:
                item.save()
            except IntegrityError:
                # SKU с таким code уже привязана к другому item'у — берём его
                if code:
                    item = PosiModelLineItem.objects.filter(code=code).first()
                    if item is None:
                        raise
                else:
                    raise

    item.refresh_from_db()
    return item, getattr(item, 'sku', None)
