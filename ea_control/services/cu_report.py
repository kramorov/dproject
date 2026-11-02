# ea_control/services/cu_report.py
"""
Описание БУ для проверки производителем.

Все слоты выбранного типа БУ, сгруппированные по узлам дерева; каждая
опция слота — ячейка с доступностью из профильных строк матрицы:
``std`` — стандарт, ``opt`` — опция, ``na`` — недоступно (опция в каталоге,
но для этого БУ строк нет/запрет). Строки с конкретным напряжением
агрегируются: std побеждает opt, иначе opt; без строк — na.

Видимость — правила профиля БУ (решение 2026-11-02): в отчёт входят
слоты, кроме скрытых правилом ``hide`` (см. ``cu_description``).
Выключенные узлы/слоты остаются с пометкой ``is_active=False`` — полнота
для сверки с производителем важнее видимости в конфигураторе.
"""
from core.utils.localization import pick_i18n

from ea_control.models import CuMatrixEntry, CuSectionNode, CuSlot
from ea_control.services.cu_description import hidden_slot_codes


def build_description(control_unit, locale=None):
    """Структурированное описание БУ: {unit, sections[{slots[{options}]}]}.

    В отчёт входят все узлы дерева с видимыми слотами (видимость — правила
    ``hide`` профиля БУ). Выключенные родители не скрывают активных детей
    (например, «Дистанционное управление» под выключенной секцией
    «Сигналы управления») — помечаются ``is_active=False``.
    """
    hidden = hidden_slot_codes(control_unit)
    rows = (CuMatrixEntry.objects
            .filter(control_unit=control_unit)
            .exclude(slot__code='control_unit')
            .select_related('slot', 'option'))
    by_slot = {}
    for r in rows:
        if not r.option_id:
            continue
        marks = by_slot.setdefault(r.slot_id, {})
        if r.availability == 'std':
            marks[r.option_id] = 'std'
        elif marks.get(r.option_id) != 'std':
            marks.setdefault(r.option_id, 'opt')

    slots = (CuSlot.objects.filter(is_active=True)
             .exclude(code='control_unit')
             .exclude(code__in=hidden)
             .select_related('section')
             .prefetch_related('slot_options')
             .order_by('sorting_order', 'code'))

    slot_payloads = {}
    slots_by_section = {}
    for s in slots:
        marks = by_slot.get(s.id, {})
        options = []
        for o in sorted([o for o in s.slot_options.all() if o.is_active],
                        key=lambda o: (o.sorting_order, o.code)):
            options.append({
                'code': o.code,
                'name': o.localized_name(locale),
                'availability': marks.get(o.id, 'na'),
            })
        slot_payloads[s.id] = {
            'code': s.code,
            'name': pick_i18n(s.name_i18n, locale, fallback=s.name or s.code),
            'options': options,
        }
        slots_by_section.setdefault(s.section_id, []).append(s)

    nodes = list(CuSectionNode.objects.all().order_by('sorting_order', 'code'))
    by_parent = {}
    for n in nodes:
        by_parent.setdefault(n.parent_id or 0, []).append(n)

    sections = []

    def walk(parent_id, depth):
        for n in by_parent.get(parent_id, []):
            node_slots = [slot_payloads[s.id]
                          for s in slots_by_section.get(n.id, [])]
            if node_slots:
                sections.append({
                    'code': n.code,
                    'name': pick_i18n(n.name_i18n, locale,
                                      fallback=n.name or n.code),
                    'depth': depth,
                    'is_active': n.is_active,
                    'slots': node_slots,
                })
            # узел без видимых слотов не печатаем, но детей обходим:
            # выключенный/пустой родитель не скрывает активных детей
            walk(n.id, depth + 1)

    walk(0, 0)
    orphans = slots_by_section.get(None, [])
    if orphans:
        sections.append({
            'code': '',
            'name': 'Без раздела',
            'depth': 0,
            'is_active': True,
            'slots': [slot_payloads[s.id] for s in orphans],
        })

    return {
        'unit': {
            'id': control_unit.id,
            'code': control_unit.code,
            'name': control_unit.generate_name(locale=locale) or control_unit.name,
            'kind_display': (pick_i18n(control_unit.kind.name_i18n, locale,
                                       fallback=control_unit.kind.name)
                             if control_unit.kind_id else ''),
            'brand_name': str(control_unit.brand) if control_unit.brand_id else '',
        },
        'sections': sections,
    }
