# ea_control/services/cu_matrix.py
"""
Резолвер матрицы доступности БУ (Паттерн А).

Обобщение ``electric_actuators.services.ea_signal_resolver``. Семантика:

- **наследование скоупов**: специфичнее перекрывает общий —
  модель (model_line_item) → корпус (body) → серия (model_line) → бренд
  (brand) → профиль типа БУ (бесскоуповые строки);
- **напряжение**: строка с конкретным power_supply перекрывает строку с
  power_supply=null на том же уровне скоупа;
- **availability=na** на специфичном уровне запрещает унаследованную строку;
- **профиль** (весь скоуп пуст) = дефолты типа БУ; std-строки предвыбраны;
- **bundle** — строки с общим кодом выбираются атомарно (валидация —
  ``validate_selection``);
- **conflicts** — парный запрет одновременного выбора (валидация —
  ``validate_selection``).

Слот ``control_unit`` резолвится отдельно (``resolve_control_units``): его
строки описывают «какой БУ доступен для серии/напряжения», а не опции
конфигурации выбранного БУ.
"""
from django.db.models import Q

from ea_control.models import CuMatrixEntry, CuMatrixMode


def _scope_level(row):
    """Уровень специфичности скоупа строки (больше — специфичнее)."""
    if row.model_line_item_id:
        return 4
    if row.body_id:
        return 3
    if row.model_line_id:
        return 2
    if row.brand_id:
        return 1
    return 0  # профиль типа БУ


def _scope_matches(row, brand, model_line, body, model_line_item):
    """Применима ли строка к запрошенному контексту (скоуп ⊆ контекст)."""
    if row.brand_id and (brand is None or row.brand_id != brand.id):
        return False
    if row.model_line_id and (model_line is None or row.model_line_id != model_line.id):
        return False
    if row.body_id and (body is None or row.body_id != body.id):
        return False
    if row.model_line_item_id and (model_line_item is None
                                   or row.model_line_item_id != model_line_item.id):
        return False
    return True


def _context_matches(row, power_supply, mode, signal_power=None):
    """Совпадение координат (напряжение, режим, схема цепей).

    Строка с конкретной схемой цепей (``signal_power``) применяется только
    при выбранной схеме; без выбранной схемы действуют строки «любой схемы».
    """
    if power_supply is not None and row.power_supply_id is not None \
            and row.power_supply_id != power_supply.id:
        return False
    if signal_power is None:
        if row.signal_power_id is not None:
            return False
    elif row.signal_power_id is not None and row.signal_power_id != signal_power.id:
        return False
    if mode and mode != CuMatrixMode.BOTH \
            and row.mode != CuMatrixMode.BOTH and row.mode != mode:
        return False
    return True


def _row_payload(row, locale=None):
    """Портабельное описание строки матрицы для резолвера/фронта."""
    from core.utils.localization import localized_name
    option = row.option
    conflicts = []
    for conflict_row in row.conflicts.all():
        if conflict_row.option_id:
            conflicts.append(conflict_row.option.code)
    return {
        'row_id': row.id,
        'slot_code': row.slot.code,
        'option_code': option.code if option else None,
        'option_name': localized_name(option, locale) if option else row.name,
        'availability': row.availability,
        'is_default': row.is_default,
        'bundle': row.bundle,
        'conflicts': conflicts,
        # приоритет кодировки: строка матрицы → справочный код опции
        'encoding': row.encoding or (option.encoding if option else ''),
        'ext_encoding': row.ext_encoding or (option.ext_encoding if option else ''),
    }


def _effective_row(rows, context):
    """Эффективная строка для опции: самая специфичная из применимых.

    ``rows`` — строки одной пары (слот, опция) для одного БУ, уже
    отфильтрованные по напряжению/режиму. Приоритет: уровень скоупа, затем
    конкретное напряжение перед null. ``availability=na`` считается
    применённым (запрет).
    """
    brand, model_line, body, item = context
    applicable = [r for r in rows if _scope_matches(r, brand, model_line, body, item)]
    if not applicable:
        return None
    power_supply_id = None
    # скоуповая сортировка: (уровень, есть ли конкретное напряжение, схема)
    applicable.sort(key=lambda r: (
        _scope_level(r),
        1 if getattr(r, '_ps_requested', False) else 0,
        1 if getattr(r, '_sp_requested', False) else 0,
        r.id,
    ))
    return applicable[-1]


def resolve_slots(control_unit, *, model_line=None, body=None,
                  model_line_item=None, brand=None, power_supply=None,
                  signal_power=None, mode='both', locale=None):
    """Доступные опции всех слотов конфигурации выбранного БУ.

    Возвращает ``{slot_code: [payload, …]}`` — список эффективных строк по
    слотам (включая none-строки «Нет»). Слот ``control_unit`` не входит:
    выбор БУ — отдельный шаг (``resolve_control_units``).

    ``signal_power`` — выбранная схема цепей управления (CuSignalPower):
    строки с конкретной схемой перекрывают строки «любой схемы» — так
    «набор сигналов дистанционного управления» зависит от опции CMD_WIRING.
    """
    if brand is None and model_line is not None:
        brand = getattr(model_line, 'brand', None)
    context = (brand, model_line, body, model_line_item)

    rows_qs = (CuMatrixEntry.objects
               .filter(control_unit=control_unit)
               .exclude(slot__code='control_unit')
               .select_related('slot', 'option')
               .prefetch_related('conflicts__option'))
    if power_supply is not None:
        rows_qs = rows_qs.filter(Q(power_supply=power_supply)
                                 | Q(power_supply__isnull=True))
    if signal_power is not None:
        rows_qs = rows_qs.filter(Q(signal_power=signal_power)
                                 | Q(signal_power__isnull=True))
    rows = list(rows_qs)

    result = {}
    for row in rows:
        row._ps_requested = (
            power_supply is not None and row.power_supply_id == power_supply.id)
        row._sp_requested = (
            signal_power is not None
            and row.signal_power_id == signal_power.id)
        if not _context_matches(row, power_supply, mode, signal_power):
            continue
        key = (row.slot.code, row.option.code if row.option_id else row.name)
        result.setdefault(key, []).append(row)

    out = {}
    for (slot_code, _option_key), option_rows in result.items():
        effective = _effective_row(option_rows, context)
        if effective is None:
            continue
        if effective.availability == 'na':
            continue
        payload = _row_payload(effective, locale)
        out.setdefault(slot_code, []).append(payload)
    return out


def resolve_control_units(model_line, *, body=None, model_line_item=None,
                          power_supply=None, locale=None):
    """Доступные типы БУ для серии (слот control_unit, опции kind=unit).

    Наследование: модель → серия → бесскоуповые строки (дефолты выбора БУ).
    ``na`` на специфичном уровне запрещает БУ для серии/напряжения.
    Возвращает список ``{unit_id, option_code, code, name, kind, encoding,
    is_default}`` — ``option_code`` = код опции слота control_unit (значение
    выбора в снимке и правилах).
    """
    from core.utils.localization import localized_name

    brand = getattr(model_line, 'brand', None)
    rows_qs = (CuMatrixEntry.objects
               .filter(slot__code='control_unit')
               .select_related('option', 'option__control_unit'))
    if power_supply is not None:
        rows_qs = rows_qs.filter(Q(power_supply=power_supply)
                                 | Q(power_supply__isnull=True))
    rows = list(rows_qs)

    by_unit = {}
    for row in rows:
        option = row.option
        if not option or not option.control_unit_id:
            continue
        row._ps_requested = (
            power_supply is not None and row.power_supply_id == power_supply.id)
        if not _context_matches(row, power_supply, 'both'):
            continue
        if not _scope_matches(row, brand, model_line, body, model_line_item):
            continue
        key = option.control_unit_id
        by_unit.setdefault(key, []).append(row)

    out = []
    for unit_id, unit_rows in by_unit.items():
        context = (brand, model_line, body, model_line_item)
        effective = _effective_row(unit_rows, context)
        if effective is None or effective.availability == 'na':
            continue
        unit = effective.option.control_unit
        out.append({
            'unit_id': unit.id,
            'option_code': effective.option.code,
            'code': unit.code,
            'name': localized_name(unit, locale),
            'kind': unit.kind,
            'encoding': effective.encoding or effective.option.encoding,
            'is_default': effective.is_default,
        })
    out.sort(key=lambda x: (not x['is_default'], x['code']))
    return out


def get_profile_defaults(control_unit, *, power_supply=None, mode='both',
                         signal_power=None):
    """Дефолты слотов типа БУ: {slot_code: option_code} из профильных строк.

    Профильные строки — весь скоуп пуст; берутся предвыбранные (std →
    is_default). Используется снимком (AbstractConfigSnapshot.apply_defaults).
    """
    rows = (CuMatrixEntry.objects
            .filter(control_unit=control_unit, brand__isnull=True,
                    model_line__isnull=True, body__isnull=True,
                    model_line_item__isnull=True)
            .exclude(slot__code='control_unit'))
    if power_supply is not None:
        rows = rows.filter(Q(power_supply=power_supply)
                           | Q(power_supply__isnull=True))
    if signal_power is not None:
        rows = rows.filter(Q(signal_power=signal_power)
                           | Q(signal_power__isnull=True))
    defaults = {}
    for row in rows:
        if not row.option_id:
            continue
        if not _context_matches(row, power_supply, mode, signal_power):
            continue
        if row.is_default:
            defaults[row.slot.code] = row.option.code
    return defaults


def validate_selection(selected_payloads, available_payloads=None):
    """Валидация выбора строк: атомарность bundle и парные конфликты.

    ``selected_payloads`` — выбранные payload'ы из ``resolve_slots``.
    ``available_payloads`` — все доступные payload'ы конфигурации (тот же
    формат); нужен для проверки полноты пакетов (если не передан — проверка
    пакетов не выполняется). Возвращает список сообщений об ошибках (пусто —
    выбор валиден).
    """
    errors = []
    selected = {p['row_id']: p for p in selected_payloads if p.get('row_id')}

    # bundle: выбрана строка пакета → все доступные строки пакета выбраны
    if available_payloads:
        avail = {p['row_id']: p for p in available_payloads if p.get('row_id')}
        bundle_full = {}
        for p in avail.values():
            if p.get('bundle'):
                bundle_full.setdefault(p['bundle'], set()).add(p['row_id'])
        selected_bundles = {p.get('bundle') for p in selected.values()
                            if p.get('bundle')}
        for bundle in selected_bundles:
            missing = bundle_full.get(bundle, set()) - set(selected.keys())
            if missing:
                codes = ', '.join(sorted({avail[r]['slot_code'] for r in missing}))
                errors.append(
                    f'Пакет {bundle}: не выбраны обязательные слоты '
                    f'{codes} (пакет атомарен).')

    # conflicts: выбранная пара конфликтующих строк
    by_option = {}
    for p in selected.values():
        by_option.setdefault(p.get('option_code'), []).append(p)
    for p in selected.values():
        for conflict_code in p.get('conflicts') or []:
            if conflict_code in by_option:
                q = by_option[conflict_code][0]
                errors.append(
                    f'Конфликт: {p["option_name"]} ↔ {q["option_name"]}')
    return errors
