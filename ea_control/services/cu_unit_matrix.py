# ea_control/services/cu_unit_matrix.py
"""
Редактируемая матрица профиля БУ (вкладка «Настройки» редактора БУ).

Профиль БУ — бесскоуповые строки матрицы (``brand``/``model_line``/``body``/
``model_line_item`` пусты, ``control_unit`` = тип БУ, ``mode`` = both). Здесь
пользователь для каждого слота помечает опции «стандарт / опция / недоступно»;
строка с конкретным напряжением (``power_supply``) перекрывает строку «любое
напряжение» (``power_supply=None``) — та же семантика, что в
``cu_matrix.resolve_slots``.

Семантика записи (``apply_unit_matrix_changes``):

- ``std``/``opt`` — создать/обновить профильную строку на выбранном
  напряжении; ``std`` помечает ``is_default``;
- ``na`` — «нет строки на этом напряжении»: удалить профильную строку на
  выбранном напряжении. На «любом напряжении» это «опция недоступна для БУ»,
  на конкретном — «вернуться к правилу из „любое напряжение“» (снять
  переопределение/запрет).

В отличие от «Описания БУ» (``cu_report``, только чтение, агрегат std > opt),
этот сервис возвращает эффективную доступность с привязкой к строке
(``row_id``) и умеет перезаписывать профильные строки.
"""
from ea_control.models import (CuMatrixEntry, CuMatrixMode, CuSlot,
                               CuSlotOption, CuSlotRule)
from core.utils.localization import localized_name


class MatrixValidationError(ValueError):
    """Ошибка валидации изменения матрицы (API возвращает 400)."""


def _option_name(option, locale=None):
    """Дружелюбное имя опции: из типизированной нагрузки по kind.

    ``CuSlotOption.localized_name`` раскрывает unit/local_control/unit_power/
    cable_gland/display, но для signal/heater/power/logic
    возвращает код — здесь берём имя физической сущности напрямую.
    """
    kind = option.kind
    if kind == 'signal':
        for fk in ('control_signal', 'feedback_signal', 'protocol'):
            obj = getattr(option, fk, None)
            if obj is not None:
                return localized_name(obj, locale)
    elif kind == 'heater' and option.heater_supply_id:
        return localized_name(option.heater_supply, locale)
    elif kind == 'power' and option.signal_power_id:
        return localized_name(option.signal_power, locale)
    elif kind == 'logic' and option.control_logic_id:
        return localized_name(option.control_logic, locale)
    return option.localized_name(locale)


def _profile_rows(control_unit):
    return (CuMatrixEntry.objects
            .filter(control_unit=control_unit,
                    brand__isnull=True, model_line__isnull=True,
                    body__isnull=True, model_line_item__isnull=True,
                    signal_power__isnull=True,
                    mode=CuMatrixMode.BOTH)
            .exclude(slot__code='control_unit')
            .select_related('slot', 'option'))


def _profile_row_qs(control_unit, power_supply):
    """Базовый queryset профильных строк на выбранном напряжении.

    Строки с координатой ``signal_power`` сюда не входят: это
    переопределения конкретной схемы цепей (задаются сидом/отдельным
    инструментом), а не общий профиль типа БУ.
    """
    return CuMatrixEntry.objects.filter(
        control_unit=control_unit,
        brand__isnull=True, model_line__isnull=True,
        body__isnull=True, model_line_item__isnull=True,
        signal_power__isnull=True,
        power_supply=power_supply, mode=CuMatrixMode.BOTH)


def _control_unit_option_code(control_unit):
    """Код опции слота control_unit для типа БУ (значение в снимке/правилах)."""
    opt = (CuSlotOption.objects
           .filter(slot__code='control_unit', control_unit=control_unit)
           .first())
    return opt.code if opt else None


def _unit_rules(control_unit):
    """Правила типа БУ для каждого целевого слота (exact / in / not_in).

    Возвращает {target_slot_id: CuSlotRule} — применимое правило для этого
    БУ (exact по коду опции приоритетнее списка in/not_in, содержащего код).
    """
    opt_code = _control_unit_option_code(control_unit)
    if not opt_code:
        return {}
    rules = list(CuSlotRule.objects.filter(
        when_slot__code='control_unit', is_active=True))
    out = {}
    for op in ('exact', 'in', 'not_in'):
        for r in rules:
            if r.target_slot_id in out or r.when_operator != op:
                continue
            if op == 'exact':
                if r.when_value == opt_code:
                    out[r.target_slot_id] = r
            else:
                if isinstance(r.when_value, list) and opt_code in r.when_value:
                    out[r.target_slot_id] = r
    return out


def build_unit_matrix(control_unit, power_supply=None, locale=None):
    """Эффективная матрица профиля БУ: слоты с опциями и доступностью.

    ``power_supply`` — координата напряжения (None = «любое»). Для каждой
    опции возвращается ``availability`` (std/opt/na), ``row_id`` (строка,
    определяющая доступность; None — строки нет), ``inherited`` (при просмотре
    конкретного напряжения доступность взята из строки «любое напряжение»).
    """
    rows = list(_profile_rows(control_unit))
    by_pair = {}
    for r in rows:
        if not r.option_id:
            continue
        by_pair.setdefault((r.slot_id, r.option_id), []).append(r)

    slots = list(CuSlot.objects.filter(is_active=True)
                 .exclude(code='control_unit')
                 .select_related('section')
                 .prefetch_related('slot_options')
                 .order_by('sorting_order', 'code'))

    ps_id = power_supply.id if power_supply is not None else None
    rules_by_slot = _unit_rules(control_unit)
    slots_payload = []
    for slot in slots:
        rule = rules_by_slot.get(slot.id)
        options = []
        for option in sorted(
                [o for o in slot.slot_options.all() if o.is_active],
                key=lambda o: (o.sorting_order, o.code)):
            exact = None
            fallback = None
            for r in by_pair.get((slot.id, option.id), []):
                if ps_id is not None and r.power_supply_id == ps_id:
                    exact = r
                elif r.power_supply_id is None:
                    fallback = r
            effective = exact or fallback
            options.append({
                'id': option.id,
                'code': option.code,
                'name': _option_name(option, locale),
                'kind': option.kind,
                'availability': effective.availability if effective else 'na',
                'is_default': effective.is_default if effective else False,
                'row_id': effective.id if effective else None,
                'inherited': (exact is None and effective is not None),
            })
        slots_payload.append({
            'id': slot.id,
            'code': slot.code,
            'name': localized_name(slot, locale),
            'section_id': slot.section_id,
            'section_code': slot.section.code if slot.section_id else None,
            'selection_mode': slot.selection_mode,
            'required': slot.required,
            'options': options,
            'rule': {
                'action': rule.action if rule else None,
                'action_value': rule.action_value if rule else None,
                'operator': rule.when_operator if rule else None,
                'when_value': rule.when_value if rule else None,
            },
        })

    control_unit_options = [
        {'code': o.code, 'name': o.localized_name(locale) or o.name or o.code}
        for o in CuSlotOption.objects.filter(
            slot__code='control_unit', is_active=True).order_by(
            'sorting_order', 'code')]

    return {
        'unit': {
            'id': control_unit.id,
            'code': control_unit.code,
            'name': localized_name(control_unit, locale) or control_unit.name,
            'option_code': _control_unit_option_code(control_unit),
        },
        'power_supply': ps_id,
        'slots': slots_payload,
        'control_unit_options': control_unit_options,
    }


def _validate_single_default(control_unit, power_supply, slots, valid):
    """single/xor-слот: не более одной std-опции на выбранном напряжении.

    Проверяем итоговое множество std после применения изменений: текущие
    std-строки слота (кроме изменяемых опций) плюс опции, переключаемые в
    std. Для multi/bundle-слотов несколько std допустимы.

    Bare-строки (``option=None``, наследие старой структуры «нет сигнала»)
    не считаются std-опциями: редактор и резолверы их игнорируют, а SQL
    ``NOT IN`` не отсеивает NULL — иначе одна такая строка превращала бы
    любое изменение слота в ложную ошибку «две std».
    """
    by_slot = {}
    for slot, option, availability in valid:
        if slot.selection_mode in ('single', 'xor'):
            by_slot.setdefault(slot.id, []).append((option.id, availability))

    for slot_id, items in by_slot.items():
        slot = slots[slot_id]
        changed_ids = {oid for oid, _ in items}
        existing_std = set(
            _profile_row_qs(control_unit, power_supply)
            .filter(slot_id=slot_id, availability='std',
                    option_id__isnull=False)
            .exclude(option_id__in=changed_ids)
            .values_list('option_id', flat=True))
        new_std = {oid for oid, avail in items if avail == 'std'}
        if len(existing_std | new_std) > 1:
            raise MatrixValidationError(
                f'Слот «{slot.name or slot.code}» (одиночный выбор): '
                f'только одна опция может быть стандартной (std).')


def apply_unit_matrix_changes(control_unit, power_supply, changes):
    """Перезаписать профильные строки матрицы из редактора.

    ``changes`` — список ``{slot_id, option_id, availability}``. ``std``/``opt``
    upsert строку на заданном напряжении; ``na`` удаляет строку на этом
    напряжении (на «любом» — опция недоступна, на конкретном — снятие
    переопределения). Возвращает число изменённых строк.
    """
    slot_ids = {c.get('slot_id') for c in changes}
    option_ids = {c.get('option_id') for c in changes}
    slots = {s.id: s for s in CuSlot.objects.filter(id__in=slot_ids)}
    options = {o.id: o for o in CuSlotOption.objects.filter(id__in=option_ids)}

    valid = []
    for change in changes:
        slot = slots.get(change.get('slot_id'))
        option = options.get(change.get('option_id'))
        if slot is None or option is None or option.slot_id != slot.id:
            continue
        availability = change.get('availability')
        if availability not in ('std', 'opt', 'na'):
            continue
        valid.append((slot, option, availability))

    _validate_single_default(control_unit, power_supply, slots, valid)

    saved = 0
    for slot, option, availability in valid:
        row = _profile_row_qs(control_unit, power_supply).filter(
            slot=slot, option=option).first()
        if availability == 'na':
            if row is not None:
                row.delete()
                saved += 1
            continue
        if row is None:
            CuMatrixEntry.objects.create(
                slot=slot, option=option, control_unit=control_unit,
                power_supply=power_supply, mode=CuMatrixMode.BOTH,
                availability=availability,
                is_default=(availability == 'std'))
        else:
            row.availability = availability
            row.is_default = (availability == 'std')
            row.save(update_fields=['availability', 'is_default'])
        saved += 1
    return saved


def apply_unit_rule_changes(control_unit, rule_changes):
    """Перезаписать правила типа БУ (show/hide/block/require/set_default).

    ``rule_changes`` — список ``{slot_id, action, action_value, operator,
    when_value}``. Правило привязывается к типу БУ через
    ``when_slot=control_unit``; ``operator`` — exact (только этот БУ), in
    (список кодов опций control_unit), not_in (кроме списка). ``action=None``
    удаляет правило; ``set_default`` требует ``action_value``.
    """
    opt_code = _control_unit_option_code(control_unit)
    if not opt_code:
        return 0
    control_slot = CuSlot.objects.filter(code='control_unit').first()
    if not control_slot:
        return 0
    current = _unit_rules(control_unit)  # target_slot_id -> правило
    slots = {s.id: s for s in CuSlot.objects.filter(
        id__in=[c.get('slot_id') for c in rule_changes])}

    saved = 0
    for change in rule_changes:
        slot = slots.get(change.get('slot_id'))
        if slot is None:
            continue
        action = change.get('action') or None
        action_value = change.get('action_value') or None
        if action not in (None, 'show', 'hide', 'block', 'require',
                          'set_default'):
            continue
        if action == 'set_default' and not action_value:
            continue

        operator = change.get('operator') or 'exact'
        raw_wv = change.get('when_value')
        if operator == 'exact':
            when_value = opt_code
        elif operator in ('in', 'not_in'):
            when_value = raw_wv if isinstance(raw_wv, list) else (
                [raw_wv] if raw_wv else [])
            if operator == 'in' and opt_code not in when_value:
                when_value = when_value + [opt_code]
            elif operator == 'not_in' and opt_code in when_value:
                when_value = [x for x in when_value if x != opt_code]
        else:
            continue

        old = current.get(slot.id)
        if action is None:
            if old is not None:
                old.delete()
                saved += 1
            continue
        priority = old.priority if old is not None else 0
        description = old.description if old is not None else ''
        if old is not None and (old.when_operator != operator
                                or old.when_value != when_value):
            old.delete()
            old = None
        if old is None:
            CuSlotRule.objects.create(
                when_slot=control_slot, target_slot=slot,
                when_operator=operator, when_value=when_value,
                action=action, action_value=action_value,
                priority=priority, description=description, is_active=True)
        else:
            old.action = action
            old.action_value = action_value
            old.is_active = True
            old.save(update_fields=['action', 'action_value', 'is_active'])
        saved += 1
    return saved
