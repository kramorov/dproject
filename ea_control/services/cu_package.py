# ea_control/services/cu_package.py
"""
Пакет данных конфигуратора БУ для фронта (контракт slots.md §5).

Бэкенд — источник истины: доступность (Паттерн А), дефолты профиля и правила
(Паттерн В) резолвятся здесь; фронт отрисовывает дерево секций, слоты и
опции, применяет правила к видимости и отправляет выбор обратно.

Состав пакета: ``unit`` (тип БУ + сгенерированные тексты), ``sections``
(дерево узлов-секций), ``slots`` (слоты с опциями и доступностью),
``defaults`` (дефолты профиля), ``rules`` (активные правила).
"""
from core.utils.localization import pick_i18n

from ea_control.models import CuSlot, CuSlotRule
from ea_control.services.cu_matrix import (get_profile_defaults, resolve_slots)


def _slot_payload(slot, options_payloads, locale=None):
    """Слот + его опции с доступностью (или None — недоступно)."""
    return {
        'code': slot.code,
        'name': pick_i18n(slot.name_i18n, locale, fallback=slot.name),
        'selection_mode': slot.selection_mode,
        'slot_kind': slot.slot_kind,
        'required': slot.required,
        'section_code': slot.section.code if slot.section_id else None,
        'options': options_payloads,
    }


def build_package(control_unit, *, model_line=None, body=None,
                  model_line_item=None, power_supply=None, mode='both',
                  locale=None):
    """Собрать пакет конфигуратора для выбранного типа БУ."""
    resolved = resolve_slots(
        control_unit, model_line=model_line, body=body,
        model_line_item=model_line_item, power_supply=power_supply,
        mode=mode, locale=locale)

    # опции слотов: каталог + доступность из матрицы
    slots = list(CuSlot.objects.filter(is_active=True)
                 .exclude(code='control_unit')
                 .select_related('section')
                 .prefetch_related('slot_options')
                 .order_by('sorting_order', 'code'))
    slots_payload = []
    for slot in slots:
        slot_resolved = resolved.get(slot.code, {})
        by_code = {p['option_code']: p for p in slot_resolved}
        options_payload = []
        active_options = sorted(
            [o for o in slot.slot_options.all() if o.is_active],
            key=lambda o: (o.sorting_order, o.code))
        for option in active_options:
            matrix = by_code.get(option.code)
            options_payload.append({
                'code': option.code,
                'name': pick_i18n(option.name_i18n, locale,
                                  fallback=option.name or option.code),
                'kind': option.kind,
                'availability': matrix['availability'] if matrix else None,
                'is_default': matrix['is_default'] if matrix else False,
                'bundle': matrix['bundle'] if matrix else None,
                'conflicts': matrix['conflicts'] if matrix else [],
                'encoding': matrix['encoding'] if matrix else option.encoding,
                'ext_encoding': (matrix['ext_encoding'] if matrix
                                 else option.ext_encoding),
                'row_id': matrix['row_id'] if matrix else None,
            })
        slots_payload.append(_slot_payload(slot, options_payload, locale))

    # узлы-секции (дерево)
    from ea_control.models import CuSectionNode
    sections = []
    nodes = list(CuSectionNode.objects.filter(is_active=True)
                 .order_by('sorting_order', 'code'))
    for node in nodes:
        sections.append({
            'code': node.code,
            'name': pick_i18n(node.name_i18n, locale, fallback=node.name),
            'parent_code': node.parent.code if node.parent_id else None,
        })

    rules = list(CuSlotRule.objects.filter(is_active=True)
                 .select_related('when_slot', 'target_slot')
                 .order_by('-priority', 'id'))
    slot_codes = {s['code'] for s in slots_payload}
    rules_payload = []
    for rule in rules:
        if rule.when_slot.code not in slot_codes \
                and rule.when_slot.code != 'control_unit':
            continue
        if rule.target_slot.code not in slot_codes:
            continue
        rules_payload.append({
            'id': rule.id,
            'when_slot': rule.when_slot.code,
            'operator': rule.when_operator,
            'when_value': rule.when_value,
            'action': rule.action,
            'target_slot': rule.target_slot.code,
            'action_value': rule.action_value,
            'priority': rule.priority,
        })

    return {
        'unit': {
            'id': control_unit.id,
            'code': control_unit.code,
            'name': control_unit.generate_name(locale=locale) or control_unit.name,
            'kind': control_unit.kind,
            'kind_display': control_unit.get_kind_display(),
            'description': control_unit.generate_description(locale=locale)
                           or control_unit.description,
            'spec': control_unit.generate_spec_sections(),
            'brand_name': str(control_unit.brand) if control_unit.brand_id else '',
        },
        'sections': sections,
        'slots': slots_payload,
        'defaults': get_profile_defaults(control_unit, power_supply=power_supply,
                                         mode=mode),
        'rules': rules_payload,
    }
