# ea_control/services/cu_placeholders.py
"""
Резолвер плейсхолдеров описания БУ (Шаг A, 2026-11-13).

Шаблон описания/спецификации может ссылаться на узлы/слоты/опции по их
полю ``placeholder``:

- ``{node:CODE}`` — видимые слоты узла строками ``описание слота: описание
  выбранной опции``; скрытые правилами и пустые слоты пропускаются;
- ``{slot:CODE}`` — описание выбранной опции слота (без подписи);
  скрыт/пусто — пустая строка;
- ``{opt:CODE}`` — описание конкретной опции (статичная ссылка).

Значение плейсхолдера — поле ``description`` (фолбэк name/code), как у
генератора ``cu_description``. Видимость считается тем же механизмом
правил (``visible_slots`` → ``apply_rules``), что и в конфигураторе,
поэтому спецификация и конфигуратор не расходятся.
"""
import re

from core.utils.localization import pick_i18n

from ea_control.models import CuSlotOption
from ea_control.services.cu_description import (
    _effective_snapshot,
    _option_description,
    _slot_chosen_options,
    _slot_options_prefetch,
    visible_slots,
)

_PLACEHOLDER_RE = re.compile(r'\{(node|slot|opt):([^{}]+)\}')


def _join(value):
    if value is None:
        return ''
    if isinstance(value, (list, tuple)):
        return ', '.join(str(v) for v in value)
    return str(value)


def render_placeholders(template, control_unit, *, snapshot=None, locale=None,
                        power_supply=None, mode='both', signal_power=None):
    """Подставить ``{node:}/{slot:}/{opt:}`` в шаблон описания БУ.

    ``control_unit`` — тип БУ (ea_control.ControlUnit); ``snapshot`` —
    выбранные опции ``{slot_code: option_code}`` (перекрывают std-дефолты).
    """
    if not template:
        return ''

    merged, defaults = _effective_snapshot(
        control_unit, snapshot, power_supply=power_supply, mode=mode,
        signal_power=signal_power)
    nodes, visible = visible_slots(control_unit, snapshot)

    options_by_slot = {}
    for s in visible:
        options_by_slot[s.id] = sorted(
            [o for o in s.slot_options.all() if o.is_active],
            key=lambda o: (o.sorting_order, o.code))

    slot_by_placeholder = {s.placeholder: s for s in visible if s.placeholder}
    node_by_placeholder = {n.placeholder: n for n in nodes if n.placeholder}

    option_by_placeholder = {}
    for o in (CuSlotOption.objects.filter(is_active=True,
                                           slot__is_active=True)
              .exclude(placeholder='')):
        option_by_placeholder[o.placeholder] = o

    def slot_label(slot):
        return pick_i18n(slot.description_i18n, locale,
                         fallback=slot.description or slot.name or slot.code)

    def option_value(option):
        desc = _option_description(option, locale)
        return desc or option.localized_name(locale)

    def slot_value(slot):
        chosen = _slot_chosen_options(slot, options_by_slot, merged, defaults)
        if not chosen:
            return ''
        return ', '.join(option_value(o) for o in chosen)

    def resolve_node(code):
        node = node_by_placeholder.get(code)
        if node is None:
            return ''
        lines = []
        for s in visible:
            if s.section_id != node.id:
                continue
            value = slot_value(s)
            if not value:
                continue
            lines.append(f'{slot_label(s)}: {value}')
        return '\n'.join(lines)

    def resolve_slot(code):
        slot = slot_by_placeholder.get(code)
        return slot_value(slot) if slot is not None else ''

    def resolve_opt(code):
        option = option_by_placeholder.get(code)
        return option_value(option) if option is not None else ''

    def replace(m):
        kind, code = m.group(1), m.group(2).strip()
        if kind == 'node':
            return resolve_node(code)
        if kind == 'slot':
            return resolve_slot(code)
        return resolve_opt(code)

    return _PLACEHOLDER_RE.sub(replace, template)
