# ea_control/services/cu_export.py
"""
Экспорт настроек БУ в Excel (xlsx) — вкладка «Редактор БУ».

Структура листа:

- строка-заголовок «БУ: {name} ({code})»;
- блок узлов/слотов/опций. Узел — отдельная строка, слот — отдельная
  строка, в той же строке — все опции слота. Порядок опций в строке:
  «std:» + std-значения, «opt:» + opt (по sorting_order), «na:» + na
  (по sorting_order);
- выводится ВСЁ дерево (узлы и слоты вне правил show/hide и is_active);
  для узлов/слотов/опций берётся поле ``description`` (фолбэк name/code);
- доступность резолвится из профильных строк матрицы типа БУ. Если по всем
  напряжениям доступность одинакова — один блок «Для всех напряжений
  питания привода», иначе — отдельный блок на каждое напряжение.
"""
import io

from django.db.models import Q

from ea_control.models import (CuMatrixEntry, CuMatrixMode, CuSectionNode,
                               CuSlot, CuSlotOption)
from params.models import PowerSupplies


def _text(*parts):
    """Первое непустое значение (description → name → code)."""
    for p in parts:
        if p:
            return str(p)
    return ''


def _option_description(option):
    """Описание опции: своё description → description справочной записи →
    name → code."""
    if option.description:
        return option.description
    kind = option.kind
    if kind == 'signal':
        for fk in ('control_signal', 'feedback_signal', 'protocol'):
            obj = getattr(option, fk, None)
            if obj is not None:
                return getattr(obj, 'description', '') or getattr(obj, 'name', '')
    elif kind == 'device' and option.device_id:
        return option.device.description or option.device.name
    elif kind == 'heater' and option.heater_supply_id:
        return option.heater_supply.description or option.heater_supply.name
    elif kind == 'power' and option.signal_power_id:
        return option.signal_power.description or option.signal_power.name
    elif kind == 'logic' and option.control_logic_id:
        return option.control_logic.description or option.control_logic.name
    elif kind == 'unit' and option.control_unit_id:
        return option.control_unit.description or option.control_unit.name
    elif kind == 'local_control' and option.local_control_type_id:
        return option.local_control_type.description or option.local_control_type.name
    elif kind == 'display':
        parts = [d.description or d.name
                 for d in option.display_types.all()]
        parts = [p for p in parts if p]
        if parts:
            return ' + '.join(parts)
    elif kind == 'unit_power' and option.unit_power_source_id:
        return option.unit_power_source.description or option.unit_power_source.name
    elif kind == 'cable_gland' and option.cable_gland_set_id:
        return (option.cable_gland_set.text_description
                or option.cable_gland_set.name or '')
    elif kind == 'location' and option.location_option_id:
        return option.location_option.description or option.location_option.name
    elif kind == 'access_device' and option.access_device_option_id:
        return (getattr(option.access_device_option, 'description', '')
                or option.access_device_option.name or '')
    return option.name or option.code


def _availability_map(control_unit, power_supply):
    """{(slot_id, option_id): availability} профиля БУ на напряжении.

    ``power_supply=None`` — «любое напряжение» (только строки с NULL);
    конкретное напряжение перекрывает NULL-строку.
    """
    rows = (CuMatrixEntry.objects
            .filter(control_unit=control_unit,
                    brand__isnull=True, model_line__isnull=True,
                    body__isnull=True, model_line_item__isnull=True,
                    signal_power__isnull=True, mode=CuMatrixMode.BOTH)
            .exclude(slot__code='control_unit')
            .filter(Q(power_supply=power_supply) | Q(power_supply__isnull=True))
            .select_related('slot', 'option'))
    by_pair = {}
    for r in rows:
        if not r.option_id:
            continue
        by_pair.setdefault((r.slot_id, r.option_id), []).append(r)

    ps_id = power_supply.id if power_supply is not None else None
    out = {}
    for pair, pair_rows in by_pair.items():
        exact = fallback = None
        for r in pair_rows:
            if ps_id is not None and r.power_supply_id == ps_id:
                exact = r
            elif r.power_supply_id is None:
                fallback = r
        effective = exact or fallback
        out[pair] = effective.availability if effective else 'na'
    return out


def _tree_sections():
    """Узлы в порядке дерева: [(node, depth), …]."""
    nodes = list(CuSectionNode.objects.all().order_by('sorting_order', 'code'))
    by_parent = {}
    for n in nodes:
        by_parent.setdefault(n.parent_id or 0, []).append(n)
    ordered = []

    def walk(parent_id, depth):
        for n in by_parent.get(parent_id, []):
            ordered.append((n, depth))
            walk(n.id, depth + 1)

    walk(0, 0)
    return ordered


def build_settings_xlsx(control_unit):
    """xlsx-байты выгрузки настроек типа БУ."""
    import openpyxl

    sections = _tree_sections()
    slots = (CuSlot.objects.exclude(code='control_unit')
             .select_related('section')
             .order_by('sorting_order', 'code'))
    slots_by_section = {}
    for s in slots:
        slots_by_section.setdefault(s.section_id, []).append(s)

    options = (CuSlotOption.objects.filter(is_active=True)
               .select_related('slot', 'control_signal', 'feedback_signal',
                               'protocol', 'heater_supply', 'signal_power',
                               'control_logic', 'control_unit', 'device',
                               'local_control_type', 'unit_power_source',
                               'cable_gland_set', 'location_option',
                               'access_device_option')
               .prefetch_related('display_types')
               .order_by('sorting_order', 'code'))
    options_by_slot = {}
    for o in options:
        options_by_slot.setdefault(o.slot_id, []).append(o)

    voltages = list(PowerSupplies.objects.filter(is_active=True)
                    .order_by('sorting_order', 'name'))

    base_map = _availability_map(control_unit, None)
    voltage_maps = [(ps, _availability_map(control_unit, ps))
                    for ps in voltages]
    # Сравниваем только по активным опциям (ровно то, что попадает в файл):
    # неактивная опция со строкой матрицы не должна превращать выгрузку в
    # многовольтную.
    active_pairs = set()
    for slot_id, opts in options_by_slot.items():
        active_pairs.update((slot_id, o.id) for o in opts)
    base_map = {k: v for k, v in base_map.items() if k in active_pairs}
    voltage_maps = [(ps, {k: v for k, v in m.items() if k in active_pairs})
                    for ps, m in voltage_maps]
    single = all(m == base_map for _ps, m in voltage_maps)

    def slot_row(slot, avail_map):
        row = [_text(slot.description, slot.name, slot.code)]
        std, opt, na = [], [], []
        for o in options_by_slot.get(slot.id, []):
            a = avail_map.get((slot.id, o.id), 'na')
            (std if a == 'std' else opt if a == 'opt' else na).append(o)
        row.append('std:')
        row += [_option_description(o) for o in std]
        row.append('opt:')
        if opt:
            row += [_option_description(o) for o in opt]
        else:
            row.append('none')
        row.append('na:')
        if na:
            row += [_option_description(o) for o in na]
        else:
            row.append('none')
        return row

    def write_block(ws, avail_map):
        for node, _depth in sections:
            ws.append([_text(node.description, node.name, node.code)])
            for slot in slots_by_section.get(node.id, []):
                ws.append(slot_row(slot, avail_map))
        orphans = slots_by_section.get(None, [])
        if orphans:
            ws.append(['Без раздела'])
            for slot in orphans:
                ws.append(slot_row(slot, avail_map))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'cu_settings'
    ws.append([f'БУ: {control_unit.name} ({control_unit.code})'])

    if single:
        ws.append(['Для всех напряжений питания привода'])
        write_block(ws, base_map)
    else:
        for ps, m in voltage_maps:
            ws.append([])
            ws.append([f'Напряжение: {ps.name or ps.code} ({ps.code})'])
            write_block(ws, m)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
