# electric_actuators/services/ea_signal_resolver.py
"""
Резолвер матрицы сигналов ЭП (фаза 4 плана переезда).

Правила (см. `ea_signal_matrix.py` и разд. 4 финальной схемы):

- **Наследование скоупа:** brand → model_line → model_line_item; более
  специфичный уровень перекрывает менее специфичный по ключу
  (слот × сигнал/протокол/обогрев); `availability='na'` на специфичном уровне
  удаляет унаследованную строку.
- **Режим:** строка применима, если `row.mode` совпадает с режимом привода или
  равна `both`.
- **Слоты:** в пределах слота выбирается не более одной строки; `is_default` —
  предвыбор.
- **Пакеты (bundle):** строки с общим кодом пакета атомарны — если хоть одна
  строка пакета недоступна, пакет удаляется из результата целиком.
- **Конфликты:** парные (M2M `conflicts`) — симметричный запрет.
- **Схема:** `find_diagram_binding` ищет привязку по скоупу/БУ/напряжению/режиму
  и подписи (match_type exact/superset); нет совпадения — схемы нет.

Выход — структура для конфигуратора (слоты со строками, предвыборы, пакеты,
конфликты); отдельная функция `validate_selection` проверяет выбранный набор.
"""
from collections import defaultdict

from electric_actuators.models import (
    EaSignalMatrixEntry, EaWiringDiagramBinding, EaSignalSlot,
)
from electric_actuators.models.ea_signal_matrix import (
    EaAvailability, EaMatrixMode, EaDiagramMatchType,
)


def _row_key(row):
    """Ключ перекрытия строки внутри слота."""
    if row.control_signal_id:
        return ('control', row.control_signal_id)
    if row.feedback_signal_id:
        return ('feedback', row.feedback_signal_id)
    if row.protocol_id:
        return ('protocol', row.protocol_id)
    if row.heater_supply_id:
        return ('heater', row.heater_supply_id)
    return ('none', row.id)


def resolve_matrix(model_line_item, control_unit, power_supply, mode,
                   locale=None):
    """Доступные опции матрицы для пары (модель, БУ, напряжение, режим).

    Возвращает словарь:
        slots: [{slot_id, code, name, required, rows: [{id, name, availability,
                 is_default, bundle, conflict_ids}]}]
        defaults: {slot_id: row_id}          — предвыборы
        bundles: {code: [row_id, ...]}       — пакеты (атомарные наборы)
        conflicts: [(row_id, row_id), ...]   — парные запреты
        warnings: [str, ...]
    """
    brand = model_line_item.model_line.brand
    line = model_line_item.model_line
    scope_levels = [
        {'brand': brand, 'model_line': None, 'body': None, 'model_line_item': None},
        {'brand': None, 'model_line': line, 'body': None, 'model_line_item': None},
        {'brand': None, 'model_line': None, 'body': model_line_item.body, 'model_line_item': None},
        {'brand': None, 'model_line': None, 'body': None, 'model_line_item': model_line_item},
    ]

    effective = {}   # (slot_id, signal_key) -> row
    warnings = []
    for scope in scope_levels:
        qs = EaSignalMatrixEntry.objects.filter(
            control_unit=control_unit, power_supply=power_supply,
            **{k: v for k, v in scope.items() if v is not None})
        for row in qs.select_related('slot', 'control_signal',
                                     'feedback_signal', 'protocol',
                                     'device', 'heater_supply'):
            if row.mode not in (EaMatrixMode.BOTH, mode):
                continue
            key = (row.slot_id, _row_key(row))
            if row.availability == EaAvailability.NA:
                if key in effective:
                    del effective[key]
                else:
                    warnings.append(
                        f'Строка na без унаследованной пары: {row} (id={row.pk})')
            else:
                effective[key] = row

    # Пакеты: атомарность — если часть строк пакета отсутствует, убираем пакет.
    bundle_codes = {r.bundle for r in effective.values() if r.bundle}
    for code in bundle_codes:
        members = list(EaSignalMatrixEntry.objects.filter(
            bundle=code, control_unit=control_unit, power_supply=power_supply,
            availability__in=(EaAvailability.STD, EaAvailability.OPT)))
        members = [m for m in members
                   if m.mode in (EaMatrixMode.BOTH, mode)]
        present = {_row_key(m) for m in members}
        effective_keys = {_row_key(r) for r in effective.values()}
        if not present.issubset(effective_keys):
            warnings.append(f'Пакет {code} недоступен целиком — удалён.')
            for key, row in list(effective.items()):
                if row.bundle == code:
                    del effective[key]

    # Группировка по слотам
    slots = []
    defaults = {}
    bundles = defaultdict(list)
    conflicts = []
    by_id = {r.pk: r for r in effective.values()}
    for slot in EaSignalSlot.objects.filter(is_active=True).order_by(
            'sorting_order', 'code'):
        rows = [r for (sid, _), r in effective.items() if sid == slot.pk]
        if not rows:
            continue
        rows.sort(key=lambda r: (not r.is_default, r.sorting_order, r.pk))
        slot_rows = []
        for row in rows:
            if row.is_default and slot.pk not in defaults:
                defaults[slot.pk] = row.pk
            slot_rows.append({
                'id': row.pk,
                'name': row.localized_name(locale),
                'availability': row.availability,
                'is_default': row.is_default,
                'bundle': row.bundle,
                'encoding': row.encoding,
                'ext_encoding': row.ext_encoding,
            })
            if row.bundle:
                bundles[row.bundle].append(row.pk)
        slots.append({
            'slot_id': slot.pk, 'code': slot.code,
            'name': slot.name, 'required': slot.required,
            'rows': slot_rows,
        })

    # Парные конфликты среди доступных строк
    for row in effective.values():
        for other in row.conflicts.all():
            if other.pk in by_id and row.pk < other.pk:
                conflicts.append((row.pk, other.pk))

    return {
        'slots': slots,
        'defaults': defaults,
        'bundles': dict(bundles),
        'conflicts': conflicts,
        'warnings': warnings,
    }


def validate_selection(selected_row_ids, resolved=None, matrix_kwargs=None):
    """Проверка выбранного набора строк.

    Параметры: либо готовый `resolved` (результат resolve_matrix), либо
    `matrix_kwargs` — аргументы resolve_matrix (model_line_item, control_unit,
    power_supply, mode). Возвращает список ошибок (пусто — корректно).
    """
    if resolved is None:
        if matrix_kwargs is None:
            raise ValueError('Нужен resolved или matrix_kwargs')
        resolved = resolve_matrix(**matrix_kwargs)
    errors = []
    selected = set(selected_row_ids)
    row_by_slot = defaultdict(list)
    for slot in resolved['slots']:
        for row in slot['rows']:
            if row['id'] in selected:
                row_by_slot[slot['slot_id']].append(row['id'])
    for slot_id, rows in row_by_slot.items():
        if len(rows) > 1:
            errors.append(f'В слоте {slot_id} выбрано больше одной строки: {rows}')
    for (a, b) in resolved['conflicts']:
        if a in selected and b in selected:
            errors.append(f'Конфликт строк {a} и {b}')
    for code, members in resolved['bundles'].items():
        chosen = set(members) & selected
        if chosen and chosen != set(members):
            errors.append(f'Пакет {code} должен выбираться целиком: {sorted(members)}')
    return errors


def find_diagram_binding(model_line_item, control_unit, power_supply, mode,
                         selected_row_ids):
    """Поиск привязки схемы для выбранного набора (или None — схемы нет)."""
    from django.db.models import Q

    selected = set(selected_row_ids)
    candidates = EaWiringDiagramBinding.objects.filter(is_active=True).filter(
        Q(model_line__isnull=True) | Q(model_line=model_line_item.model_line),
        Q(body__isnull=True) | Q(body=model_line_item.body),
        Q(model_line_item__isnull=True) | Q(model_line_item=model_line_item),
        Q(control_unit__isnull=True) | Q(control_unit=control_unit),
        Q(power_supply__isnull=True) | Q(power_supply=power_supply),
    )
    # Специфичнее скоуп — выше приоритет
    ordered = sorted(
        candidates,
        key=lambda b: (b.model_line_item_id is not None,
                       b.body_id is not None,
                       b.model_line_id is not None,
                       b.control_unit_id is not None,
                       b.power_supply_id is not None),
        reverse=True)
    for binding in ordered:
        if binding.mode and binding.mode not in (EaMatrixMode.BOTH, mode):
            continue
        sig = set(binding.signals.values_list('pk', flat=True))
        if binding.match_type == EaDiagramMatchType.EXACT and sig == selected:
            return binding
        if binding.match_type == EaDiagramMatchType.SUPERSET and sig.issubset(selected):
            return binding
    return None
