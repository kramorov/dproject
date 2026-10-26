# ea_control/services/cu_report.py
"""
Описание БУ для проверки производителем.

Все слоты выбранного типа БУ, сгруппированные по узлам дерева; каждая
опция слота — ячейка с доступностью из профильных строк матрицы:
``std`` — стандарт, ``opt`` — опция, ``na`` — недоступно (опция в каталоге,
но для этого БУ строк нет/запрет). Строки с конкретным напряжением
агрегируются: std побеждает opt, иначе opt; без строк — na.
"""
from core.utils.localization import pick_i18n

from ea_control.models import CuMatrixEntry, CuSectionNode, CuSlot


def build_description(control_unit, locale=None):
    """Структурированное описание БУ: {unit, sections[{slots[{options}]}]}.

    В отчёт входят ВСЕ узлы дерева (включая выключенные — с пометкой
    ``is_active=False``): описание предназначено для сверки с производителем,
    полнота важнее видимости в конфигураторе. Так выключенный родитель не
    скрывает активных детей (например, «Дистанционное управление» под
    выключенной секцией «Сигналы управления»).
    """
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
            sections.append({
                'code': n.code,
                'name': pick_i18n(n.name_i18n, locale,
                                  fallback=n.name or n.code),
                'depth': depth,
                'is_active': n.is_active,
                'slots': [slot_payloads[s.id]
                          for s in slots_by_section.get(n.id, [])],
            })
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
            'kind_display': control_unit.get_kind_display(),
            'location': str(control_unit.location) if control_unit.location_id else '',
            'brand_name': str(control_unit.brand) if control_unit.brand_id else '',
            'control_voltage': str(control_unit.control_voltage)
                               if control_unit.control_voltage_id else '',
        },
        'sections': sections,
    }
