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

Слот-селектор типа изделия (``control_unit``, slot_kind=subtype) резолвится
отдельно (``resolve_product_types``): его строки описывают «какой БУ
доступен для серии/напряжения», а не опции конфигурации выбранного БУ.
"""
from collections import defaultdict, deque

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q

from ea_control.models import (CU_SLOT_OPTION_PAYLOAD_FKS, CuMatrixEntry,
                               CuMatrixMode, CuSlot, CuSlotOption)
from ea_control.models.abstract import ConfigSlotKind, ConfigWhenOperator


def get_product_type_slot():
    """Слот-селектор типа изделия (``slot_kind=subtype``) — ровно один.

    Инвариант: в конфигурации ровно один слот-селектор. Нарушение — ошибка
    конфигурации (не тихое деградирование): нулевой/второй такой слот ломают
    резолв доступности и выбор типа изделия.
    """
    slots = list(CuSlot.objects.filter(slot_kind=ConfigSlotKind.SUBTYPE))
    if len(slots) != 1:
        raise ImproperlyConfigured(
            f'Ожидается ровно один слот-селектор типа изделия '
            f'(slot_kind=subtype), найдено: {len(slots)}.')
    return slots[0]


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


def _context_matches(row, power_supply, mode):
    """Совпадение координат (напряжение, режим)."""
    if power_supply is not None and row.power_supply_id is not None \
            and row.power_supply_id != power_supply.id:
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
        # Артикульная кодировка — только у строки матрицы (per-БУ). Пустая
        # строка = «позиция не кодируется»; системный код опции берётся из
        # ``option.encoding`` напрямую в ``cu_code``, сюда не подмешивается.
        'encoding': row.encoding or '',
        'ext_encoding': row.ext_encoding or '',
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
    # скоуповая сортировка: (уровень, конкретное напряжение, схема, протокол)
    applicable.sort(key=lambda r: (
        _scope_level(r),
        1 if getattr(r, '_ps_requested', False) else 0,
        r.id,
    ))
    return applicable[-1]


# ── Условные строки (slots.md §6) ──────────────────────────────────────────────

def _conditional_order(rows):
    """Топологический порядок слотов по условным строкам (алгоритм Кана).

    Рёбра — ``when_slot.code → option.slot.code`` для каждой условной строки.
    Цикл — ошибка конфигурации (ImproperlyConfigured с перечнем цикла).
    """
    edges = []
    slot_codes = set()
    for row in rows:
        if row.when_slot_id and row.option_id:
            edges.append((row.when_slot.code, row.option.slot.code))
            slot_codes.add(row.when_slot.code)
            slot_codes.add(row.option.slot.code)
    indeg = defaultdict(int)
    adj = defaultdict(list)
    for f, t in edges:
        adj[f].append(t)
        indeg[t] += 1
        indeg.setdefault(f, 0)
    queue = deque(sorted(c for c in slot_codes if indeg[c] == 0))
    order = []
    while queue:
        c = queue.popleft()
        order.append(c)
        for nxt in sorted(adj[c]):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)
    if len(order) != len(slot_codes):
        cycle = ', '.join(sorted(slot_codes - set(order)))
        raise ImproperlyConfigured(
            f'Цикл в зависимостях условных строк матрицы: {cycle}')
    return order


def _when_satisfied(row, effective):
    """Выполнено ли условие условной строки по эффективным значениям слотов.

    ``effective`` — {slot_code: CuSlotOption | None}. Безусловная строка
    выполняется всегда.
    """
    if not row.when_slot_id:
        return True
    value = effective.get(row.when_slot.code)
    op = row.when_operator
    if op == ConfigWhenOperator.IS_SET:
        return value is not None
    opt_ids = {o.id for o in row.when_options.all()}
    if op == ConfigWhenOperator.IN:
        return value is not None and value.id in opt_ids
    if op == ConfigWhenOperator.NOT_IN:
        return value is None or value.id not in opt_ids
    return True


def _row_precedence(row):
    """Ключ специфичности: скоуп → напряжение → условная → priority → id."""
    return (_scope_level(row),
            1 if getattr(row, '_ps_requested', False) else 0,
            1 if row.when_slot_id else 0,
            row.priority,
            row.id)


def _snapshot_options(snapshot):
    """Развернуть снимок {slot_code: option_code} → {slot_code: CuSlotOption}.

    Мультислоты (значение — список кодов) в ``when``-резолве не участвуют
    (slots.md §6.3): их значения пропускаются, чтобы не ломать эффективное
    значение слота-условия.
    """
    if not snapshot:
        return {}
    scalar = {sc: oc for sc, oc in snapshot.items() if isinstance(oc, str)}
    if not scalar:
        return {}
    opts = (CuSlotOption.objects
            .filter(slot__code__in=list(scalar.keys()))
            .select_related('slot'))
    by_code = {(o.slot.code, o.code): o for o in opts}
    return {sc: by_code[(sc, oc)] for sc, oc in scalar.items()
            if (sc, oc) in by_code}


def _resolve_effective(rows, context, power_supply, mode, snapshot_opt):
    """Эффективные значения слотов по условным строкам (slots.md §6).

    Возвращает (defaults, effective): ``defaults[slot_code]`` — предвыбранная
    std-опция (или None), ``effective[slot_code]`` — выбор из снимка или
    std-опция. Идём по топологическому порядку — каскады A→B→C работают.
    """
    by_slot = defaultdict(list)
    for row in rows:
        if row.option_id:
            by_slot[row.option.slot.code].append(row)

    order = _conditional_order(rows)
    defaults = {}
    effective = {}

    def static_ok(row):
        return (_scope_matches(row, *context)
                and _context_matches(row, power_supply, mode))

    def slot_std(slot_code):
        cands = [r for r in by_slot.get(slot_code, [])
                 if static_ok(r) and _when_satisfied(r, effective)
                 and r.is_default]
        if not cands:
            return None
        cands.sort(key=_row_precedence)
        return cands[-1].option

    for sc in order:
        defaults[sc] = slot_std(sc)
        effective[sc] = snapshot_opt.get(sc) or defaults[sc]
    rest = sorted(set(by_slot.keys()) - set(order))
    for sc in rest:
        defaults[sc] = slot_std(sc)
        effective[sc] = snapshot_opt.get(sc) or defaults[sc]
    # when_slot без строк в by_slot (нет опций для этого БУ) — только снимок
    for sc in set(order) - set(by_slot.keys()):
        effective[sc] = snapshot_opt.get(sc)
    return defaults, effective


def _enforce_single_std(out):
    """Инвариант «не более одного std на слот» (slots.md §6.3)."""
    for payloads in out.values():
        stds = [p for p in payloads if p.get('availability') == 'std']
        if len(stds) > 1:
            stds.sort(key=lambda p: p.get('_prec', (0, 0, 0, 0, 0)))
            for p in stds[:-1]:
                p['availability'] = 'opt'


def resolve_slots(control_unit, *, model_line=None, body=None,
                  model_line_item=None, brand=None, power_supply=None,
                  mode='both', snapshot=None, locale=None):
    """Доступные опции всех слотов конфигурации выбранного БУ (slots.md §6).

    Возвращает ``{slot_code: [payload, …]}`` — список эффективных строк по
    слотам (включая none-строки «Нет»). Слот-селектор типа изделия (subtype)
    не входит: выбор типа изделия — отдельный шаг (``resolve_product_types``).

    ``snapshot`` — {slot_code: option_code}: условные строки оцениваются по
    эффективному значению слота (снимок перекрывает std-дефолт).
    """
    if brand is None and model_line is not None:
        brand = getattr(model_line, 'brand', None)
    context = (brand, model_line, body, model_line_item)

    rows_qs = (CuMatrixEntry.objects
               .filter(control_unit=control_unit, is_active=True)
               .exclude(slot__slot_kind=ConfigSlotKind.SUBTYPE)
               .select_related('slot', 'option', 'option__slot', 'when_slot',
                               *[f'option__{f}'
                                 for f in CU_SLOT_OPTION_PAYLOAD_FKS])
               .prefetch_related('conflicts__option', 'when_options',
                                 'option__display_types'))
    if power_supply is not None:
        rows_qs = rows_qs.filter(Q(power_supply=power_supply)
                                 | Q(power_supply__isnull=True))
    rows = list(rows_qs)
    for row in rows:
        row._ps_requested = (power_supply is not None
                             and row.power_supply_id == power_supply.id)

    snapshot_opt = _snapshot_options(snapshot)
    _defaults, effective = _resolve_effective(
        rows, context, power_supply, mode, snapshot_opt)

    by_slot = defaultdict(list)
    for row in rows:
        if row.option_id:
            by_slot[row.option.slot.code].append(row)

    out = defaultdict(list)
    for slot_code, slot_rows in by_slot.items():
        by_opt = defaultdict(list)
        for row in slot_rows:
            if not _scope_matches(row, *context):
                continue
            if not _context_matches(row, power_supply, mode):
                continue
            if not _when_satisfied(row, effective):
                continue
            by_opt[row.option.code].append(row)
        for opt_code, opt_rows in by_opt.items():
            opt_rows.sort(key=_row_precedence)
            row = opt_rows[-1]
            if row.availability == 'na':
                continue
            payload = _row_payload(row, locale)
            payload['_prec'] = _row_precedence(row)
            out[slot_code].append(payload)

    _enforce_single_std(out)
    for payloads in out.values():
        for p in payloads:
            p.pop('_prec', None)

    # Детерминированный порядок для фронта и тестов: стандарт → опция,
    # затем по коду опции (не зависеть от порядка строк в БД).
    _avail_rank = {'std': 0, 'opt': 1, 'na': 2}
    for payloads in out.values():
        payloads.sort(key=lambda p: (
            _avail_rank.get(p['availability'], 3),
            p['option_code'] or '',
        ))
    return dict(out)


def resolve_product_types(model_line, *, body=None, model_line_item=None,
                          power_supply=None, locale=None):
    """Доступные типы изделия для серии (слот-селектор типа, slot_kind=subtype).

    Наследование: модель → серия → бесскоуповые строки (дефолты выбора типа).
    ``na`` на специфичном уровне запрещает тип для серии/напряжения.
    Возвращает список ``{product_type_id, option_code, code, name, kind,
    encoding, is_default}`` — ``option_code`` = код опции слота-селектора
    (значение выбора в снимке и правилах).
    """
    from core.utils.localization import localized_name

    brand = getattr(model_line, 'brand', None)
    rows_qs = (CuMatrixEntry.objects
               .filter(slot__slot_kind=ConfigSlotKind.SUBTYPE)
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
            'product_type_id': unit.id,
            'option_code': effective.option.code,
            'key': unit.key,
            'code': unit.code,
            'name': localized_name(unit, locale),
            'kind': unit.kind_id,
            'encoding': effective.encoding or effective.option.encoding,
            'is_default': effective.is_default,
        })
    out.sort(key=lambda x: (not x['is_default'], x['code']))
    return out


# Обратная совместимость: прежнее имя резолвера типов изделия.
resolve_control_units = resolve_product_types


def get_profile_defaults(control_unit, *, power_supply=None, mode='both',
                         snapshot=None):
    """Дефолты слотов типа БУ: {slot_code: option_code} (slots.md §6).

    Профильные строки (весь скоуп пуст), с учётом условных строк: ``snapshot``
    перекрывает std-дефолт при оценке ``when``.
    """
    rows = (CuMatrixEntry.objects
            .filter(control_unit=control_unit, brand__isnull=True,
                    model_line__isnull=True, body__isnull=True,
                    model_line_item__isnull=True, is_active=True)
            .exclude(slot__slot_kind=ConfigSlotKind.SUBTYPE)
            .select_related('slot', 'option', 'option__slot', 'when_slot')
            .prefetch_related('when_options'))
    if power_supply is not None:
        rows = rows.filter(Q(power_supply=power_supply)
                           | Q(power_supply__isnull=True))
    rows = list(rows)
    for row in rows:
        row._ps_requested = (power_supply is not None
                             and row.power_supply_id == power_supply.id)
    context = (None, None, None, None)
    snapshot_opt = _snapshot_options(snapshot)
    defaults, _effective = _resolve_effective(
        rows, context, power_supply, mode, snapshot_opt)
    return {sc: opt.code for sc, opt in defaults.items() if opt is not None}


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

    # rule/conditional-induced na: выбранная опция больше недоступна
    if available_payloads:
        avail_by_slot = {}
        for p in available_payloads:
            avail_by_slot.setdefault(p['slot_code'], set()).add(p['option_code'])
        for p in selected.values():
            if p.get('option_code') not in avail_by_slot.get(p['slot_code'], set()):
                errors.append(
                    f'Опция {p.get("option_name") or p.get("option_code")} '
                    f'слота {p["slot_code"]} стала недоступна при текущем '
                    f'выборе.')
    return errors
