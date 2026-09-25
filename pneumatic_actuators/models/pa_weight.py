# pneumatic_actuators/models/pa_weight.py
"""Расчёт веса пневмопривода.

Единая реализация для PneumaticActuatorItem / PneumaticActuatorConstructor /
PneumaticActuatorSelected. Вес хранится в PneumaticWeightParameter
(body × spring_qty). Ключ spring_qty — это ``code`` записи
PneumaticActuatorSpringsQty: 'DA' (без пружин), '05'..'12' (количество пружин)
или код пружинного блока кулисных приводов (нечисловой).

Алгоритм:
  1. DA — вес из параметра с кодом 'DA' (или 0).
  2. Пружинный привод — точное совпадение по коду выбранного количества/блока
     возвращает вес напрямую.
  3. Иначе расчёт: вес = вес_DA + N × вес_одной_пружины.
     Вес одной пружины — body.weight_spring; если его нет (или 0) — выводится
     как (вес_референсного_кол-ва − вес_DA) / референсное_кол-во.
"""
from decimal import Decimal, InvalidOperation


def _num(value) -> Decimal:
    """Безопасно привести значение к Decimal (None/ошибка → 0)."""
    if value is None:
        return Decimal('0')
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0')


def _spring_count(code) -> int | None:
    """Числовое количество пружин из кода; None для пружинного блока/DA."""
    if code is None:
        return None
    text = str(code).strip()
    if text.isdigit():
        return int(text)
    return None


def calculate_actuator_weight(body, variety_code: str, spring_code: str):
    """Вес привода в зависимости от выбранного количества пружин.

    Args:
        body: PneumaticActuatorBody.
        variety_code: код разновидности ('DA'/'SR').
        spring_code: ``code`` выбранного PneumaticActuatorSpringsQty
            ('DA', '05'..'12' или код пружинного блока).

    Returns:
        Decimal (вес, кг) или None, если данных недостаточно.
    """
    from pneumatic_actuators.models import PneumaticWeightParameter

    if body is None:
        return None

    WeightParam = PneumaticWeightParameter

    # 1) DA — без пружин
    if variety_code == 'DA':
        da = WeightParam.objects.filter(body=body, spring_qty__code='DA').first()
        return _num(da.weight) if da else Decimal('0')

    # 2) Пружинный привод — нужно знать выбранное количество/блок
    if not spring_code:
        return None

    # 2a) Точное совпадение по коду (счёт пружин или пружинный блок)
    exact = WeightParam.objects.filter(body=body, spring_qty__code=spring_code).first()
    if exact is not None:
        return _num(exact.weight)

    # 2b) Расчёт: DA + N × вес_одной_пружины
    da = WeightParam.objects.filter(body=body, spring_qty__code='DA').first()
    da_weight = _num(da.weight) if da else Decimal('0')

    one_spring = _num(getattr(body, 'weight_spring', None) or 0)
    if one_spring == 0:
        # Вес одной пружины не задан — выводим из референсного количества.
        ref = WeightParam.objects.filter(body=body) \
            .exclude(spring_qty__code='DA') \
            .order_by('-spring_qty__code') \
            .first()
        if ref is not None:
            ref_count = _spring_count(ref.spring_qty.code)
            if ref_count:
                one_spring = (_num(ref.weight) - da_weight) / ref_count

    count = _spring_count(spring_code)
    if count is None:
        # Пружинный блок без точного совпадения — посчитать не из чего.
        return None

    return da_weight + (count * one_spring)
