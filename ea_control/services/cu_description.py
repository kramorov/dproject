# ea_control/services/cu_description.py
"""
Генератор описания, спецификации и артикула модификации БУ (2026-11-02).

Вместо шаблонов с плейсхолдерами (TemplateMixin) описание и спецификация
считаются из живых данных конфигуратора:

- **видимость** — правила: в описание/спецификацию входят все активные
  слоты, кроме тех, где для выбранного БУ сработало правило ``hide``
  (решение пользователя 2026-11-02: «всё, кроме hide»; ``show`` —
  переопределение, побеждает по priority). Профильные правила
  (``when_slot=control_unit``) применяются всегда; универсальные
  (например, «общий кабель → скрыть вводы БУ») — когда в снимке
  модификации есть значение слота-условия;
- **узел** видим, если в нём есть хотя бы один видимый слот;
- **значение слота** — из снимка модификации (опция выбрана) или
  std-дефолт профиля; устаревшие/чужие коды в снимке игнорируются —
  рассинхрон снимка с составом БУ не ломает генерацию;
- **артикул** — из кодов узла/слота/опции вместо плейсхолдеров кодировок
  (``encoding``/``ext_encoding`` не используются);
- **локализация** — узлы/слоты: ``name_i18n``/``description_i18n``;
  текстовые опции (value/none): ``description_i18n`` → имя; объектные
  опции — локализованное имя справочной записи (``localized_name``).

Хранения нет: всё считается на лету — рассинхрон между JSON и настройками
БУ невозможен по построению. Если позже добавим хранение сгенерированного
JSON на модификации — потребуется либо FK на опции, либо перегенерация
при изменении настроек (см. slots.md §4).
"""
from django.db.models import Prefetch

from core.utils.localization import pick_i18n

from ea_control.models import (CuSectionNode, CuSlot, CuSlotOption,
                               CuSlotRule)
from ea_control.services.cu_matrix import get_profile_defaults, resolve_slots
from ea_control.services.cu_rules import apply_rules

# FK полезных нагрузок CuSlotOption — для select_related в префетче опций
# (иначе value/value_description/артикул тянут справочную запись на каждую
# выбранную опцию отдельным запросом).
_PAYLOAD_FKS = ('control_signal', 'feedback_signal', 'protocol',
                'heater_supply', 'signal_power', 'control_logic',
                'control_unit', 'device', 'local_control_type',
                'unit_power_source', 'cable_gland_set', 'location_option',
                'access_device_option')


def _slot_options_prefetch():
    """Префетч опций с полезными нагрузками (FK + display M2M)."""
    return Prefetch(
        'slot_options',
        queryset=(CuSlotOption.objects.select_related(*_PAYLOAD_FKS)
                  .prefetch_related('display_types')))


def _unit_option(control_unit):
    return CuSlotOption.objects.filter(
        slot__code='control_unit', control_unit=control_unit).first()


def hidden_slot_codes(control_unit, snapshot=None):
    """Коды слотов, скрытых правилами для БУ (+ выбор из снимка).

    Профильные правила срабатывают всегда (``control_unit`` в селекции);
    универсальные — когда снимок содержит значение слота-условия.
    """
    unit_opt = _unit_option(control_unit)
    if unit_opt is None:
        return set()
    selection = {'control_unit': unit_opt.code}
    selection.update(snapshot or {})
    rules = (CuSlotRule.objects.filter(is_active=True)
             .select_related('when_slot', 'target_slot'))
    state = apply_rules(rules, selection)
    return {code for code, st in state.items() if not st['visible']}


def visible_slots(control_unit, snapshot=None):
    """Активные видимые слоты БУ в порядке дерева: (nodes, slots).

    В узлы попадают ВСЕ узлы видимых слотов, включая выключенные
    (``is_active=False``) — как в cu_report: выключенная секция не прячет
    слоты и не роняет артикул; флаг передаётся в спецификации.
    """
    hidden = hidden_slot_codes(control_unit, snapshot)
    slots = list(CuSlot.objects.filter(is_active=True)
                 .exclude(code='control_unit')
                 .select_related('section')
                 .prefetch_related(_slot_options_prefetch())
                 .order_by('sorting_order', 'code'))
    visible = [s for s in slots if s.code not in hidden]
    node_ids = {s.section_id for s in visible}
    nodes = list(CuSectionNode.objects.filter(id__in=node_ids)
                 .order_by('sorting_order', 'code'))
    return nodes, visible


def _option_text(option, locale=None):
    """Текст значения опции: для value/none — описание (i18n) → имя."""
    if option.kind in ('value', 'none'):
        text = pick_i18n(option.description_i18n, locale, fallback='')
        if text:
            return text
    if option.kind == 'none':
        # явное «Нет»: none-опция всегда выводится текстом, не кодом
        return option.localized_name(locale) or 'Нет'
    return option.localized_name(locale)


def _payload_description(obj, locale=None):
    """Описание справочной записи: description_i18n → description → ''."""
    return pick_i18n(getattr(obj, 'description_i18n', None), locale,
                     fallback=getattr(obj, 'description', '') or '')


def _option_description(option, locale=None):
    """Описание опции для колонки спецификации.

    - none — явное «Нет» (у none-опций нет описания, пусто не выводим);
    - value — собственное описание опции (description_i18n → description);
    - объектные (типизированные полезные нагрузки) — описание справочной
      записи; display — объединение описаний видов отображения через «+».
    """
    if option.kind == 'none':
        return option.localized_name(locale) or 'Нет'
    if option.kind == 'value':
        return pick_i18n(option.description_i18n, locale,
                         fallback=option.description or '')
    if option.kind == 'display':
        descs = [_payload_description(d, locale)
                 for d in option.display_types.all().order_by('sorting_order')]
        return ' + '.join(x for x in descs if x)
    for fk in ('control_signal', 'feedback_signal', 'protocol',
               'heater_supply', 'signal_power', 'control_logic',
               'control_unit', 'device', 'local_control_type',
               'unit_power_source', 'cable_gland_set', 'location_option',
               'access_device_option'):
        obj = getattr(option, fk, None)
        if obj is not None:
            return _payload_description(obj, locale)
    return pick_i18n(option.description_i18n, locale,
                     fallback=option.description or '')


def _effective_snapshot(control_unit, snapshot, *, power_supply=None,
                        mode='both', signal_power=None):
    """(снимок+дефолты, дефолты): снимок перекрывает дефолты профиля."""
    defaults = get_profile_defaults(control_unit, power_supply=power_supply,
                                    mode=mode, signal_power=signal_power)
    merged = dict(defaults)
    merged.update({k: v for k, v in (snapshot or {}).items()
                   if k != 'control_unit'})
    return merged, defaults


def _slot_chosen_options(slot, options_by_slot, merged, defaults):
    """Объекты выбранных опций слота: снимок → профильный std; чужие
    коды — отброшены."""
    options = options_by_slot.get(slot.id, [])
    codes = [o.code for o in options]
    chosen = merged.get(slot.code)
    if isinstance(chosen, (list, tuple)):
        chosen = [c for c in chosen if c in codes] or None
    else:
        chosen = [chosen] if chosen in codes else None
    if not chosen:
        d = defaults.get(slot.code)
        chosen = [d] if d and d in codes else []
    return [o for o in options if o.code in chosen]


def _slot_chosen_codes(slot, options_by_slot, merged, defaults):
    """Коды выбранных опций слота: снимок → профильный std; чужие коды —
    отброшены."""
    return [o.code for o in _slot_chosen_options(slot, options_by_slot,
                                                 merged, defaults)]


def _slot_value(slot, options_by_slot, merged, defaults, locale=None):
    """Выбранное значение слота: код(ы) → локализованный текст(ы)."""
    chosen = _slot_chosen_options(slot, options_by_slot, merged, defaults)
    if not chosen:
        return None
    texts = [_option_text(o, locale) for o in chosen]
    if len(texts) > 1:
        return texts
    return texts[0]


def _slot_value_description(slot, options_by_slot, merged, defaults,
                            locale=None):
    """Описание выбранной опции слота (колонка «Описание» спецификации)."""
    chosen = _slot_chosen_options(slot, options_by_slot, merged, defaults)
    if not chosen:
        return None
    descs = [_option_description(o, locale) for o in chosen]
    if len(descs) > 1:
        return descs
    return descs[0]


def build_specification(control_unit, *, snapshot=None, locale=None,
                        power_supply=None, mode='both', signal_power=None):
    """Спецификация модификации БУ: видимые узлы → слоты → значения.

    Возвращает {unit, sections: [{code, name, description, slots:
    [{code, name, description, selection_mode, value, value_description,
    options: [{code, name, availability}]}]}]}.
    """
    merged, defaults = _effective_snapshot(
        control_unit, snapshot, power_supply=power_supply, mode=mode,
        signal_power=signal_power)
    resolved = resolve_slots(control_unit, power_supply=power_supply,
                             signal_power=signal_power, mode=mode,
                             locale=locale)

    nodes, visible = visible_slots(control_unit, snapshot)
    options_by_slot = {}
    for s in visible:
        options_by_slot[s.id] = sorted(
            [o for o in s.slot_options.all() if o.is_active],
            key=lambda o: (o.sorting_order, o.code))

    slots_by_node = {}
    for s in visible:
        slots_by_node.setdefault(s.section_id, []).append(s)

    unit_opt = _unit_option(control_unit)
    sections = []
    for node in nodes:
        slot_payloads = []
        for s in slots_by_node.get(node.id, []):
            by_code = {p['option_code']: p
                       for p in resolved.get(s.code, [])}
            options_payload = []
            for o in options_by_slot[s.id]:
                matrix = by_code.get(o.code)
                options_payload.append({
                    'code': o.code,
                    'name': _option_text(o, locale),
                    'availability': matrix['availability'] if matrix else 'na',
                })
            slot_payloads.append({
                'code': s.code,
                'name': pick_i18n(s.name_i18n, locale,
                                  fallback=s.name or s.code),
                'description': pick_i18n(s.description_i18n, locale,
                                         fallback=''),
                'selection_mode': s.selection_mode,
                'value': _slot_value(s, options_by_slot, merged, defaults,
                                     locale),
                'value_description': _slot_value_description(
                    s, options_by_slot, merged, defaults, locale),
                'options': options_payload,
            })
        sections.append({
            'code': node.code,
            'name': pick_i18n(node.name_i18n, locale,
                              fallback=node.name or node.code),
            'description': pick_i18n(node.description_i18n, locale,
                                     fallback=''),
            'is_active': node.is_active,
            'slots': slot_payloads,
        })

    return {
        'unit': {
            'code': control_unit.code,
            'name': (pick_i18n(control_unit.name_i18n, locale,
                               fallback=control_unit.name)
                     or control_unit.code),
            'kind_display': (pick_i18n(control_unit.kind.name_i18n, locale,
                                       fallback=control_unit.kind.name)
                             if control_unit.kind_id else ''),
            'option_code': unit_opt.code if unit_opt else '',
        },
        'sections': sections,
    }


def build_description(control_unit, *, snapshot=None, locale=None,
                      power_supply=None, mode='both', signal_power=None):
    """Текстовое описание модификации БУ (локализованное).

    Структура: имя БУ, затем строки «Узел:», «- Слот: значение».
    """
    spec = build_specification(control_unit, snapshot=snapshot, locale=locale,
                               power_supply=power_supply, mode=mode,
                               signal_power=signal_power)
    lines = [spec['unit']['name']]
    for section in spec['sections']:
        lines.append(section['name'] + ':')
        for s in section['slots']:
            value = s['value']
            if isinstance(value, list):
                value = ', '.join(value)
            lines.append(f"- {s['name']}: {value or '—'}")
    return '\n'.join(lines)


def assemble_article(control_unit, *, snapshot=None, power_supply=None,
                     mode='both', signal_power=None):
    """Артикул модификации из кодов: узел.слот.опция (вместо кодировок).

    Части: код опции ``control_unit`` + для каждого видимого слота вклад
    ``{node.code}.{slot.code}.{option.code}`` выбранных (или std) опций;
    соединитель — ``/``. Устаревшие коды снимка игнорируются (fallback —
    std профиля). Кодировки ``encoding``/``ext_encoding`` не используются.
    """
    merged, defaults = _effective_snapshot(
        control_unit, snapshot, power_supply=power_supply, mode=mode,
        signal_power=signal_power)
    _nodes, visible = visible_slots(control_unit, snapshot)
    options_by_slot = {}
    for s in visible:
        options_by_slot[s.id] = sorted(
            [o for o in s.slot_options.all() if o.is_active],
            key=lambda o: (o.sorting_order, o.code))
    parts = []
    unit_opt = _unit_option(control_unit)
    parts.append(unit_opt.code if unit_opt else control_unit.code)
    for s in visible:
        chosen = _slot_chosen_codes(s, options_by_slot, merged, defaults)
        # узел может быть выключен, но слот активен и видим — берём код
        # секции напрямую (артикул не должен падать и не должен молчать)
        node_code = s.section.code if s.section else ''
        for c in chosen:
            parts.append(f'{node_code}.{s.code}.{c}')
    return '/'.join(parts)
