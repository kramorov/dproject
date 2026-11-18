# ea_control/services/cu_code.py
"""
Системный и артикульный коды конфигурации БУ (кодировки, slots.md §4.3).

Два уровня кодировок:

- **системный код** — стабильный, единый для всех вариантов БУ; собирается
  шаблоном ``CuCodeSettings.system_code_template`` (синглтон). Плейсхолдеры:
  ``{node:X}``/``{slot:X}``/``{opt:X}`` — токен сущности (``placeholder``,
  фолбэк ``code``); ``{slots:X}`` — разворот всех активных слотов узла X в
  виде ``slot_token + opt_token`` (в порядке дерева, без show/hide). Пустой
  шаблон — фолбэк «узел.слот.опция» через «/»;

- **артикульный код** — вклад конкретного БУ в артикул модели; собирается
  шаблонами ``ControlUnit.article_code_template`` /
  ``ext_article_code_template``, значения — ``encoding``/``ext_encoding``
  выбранных опций (приоритет: строка матрицы → опция слота).
"""
import re

from ea_control.models import CuCodeSettings, CuSectionNode, CuSlot
from ea_control.models.abstract import ConfigSlotKind
from ea_control.services.cu_description import (
    _effective_snapshot, _product_type_option, _slot_chosen_options,
    visible_slots)
from ea_control.services.cu_matrix import resolve_slots

_PH_RE = re.compile(r'\{(node|slot|opt|slots):([^{}]+)\}')


def _system_code_template():
    """Шаблон системного кода из синглтона настроек (или None)."""
    return CuCodeSettings.get().system_code_template


def _token(entity):
    """Системный токен сущности (placeholder → code)."""
    return (getattr(entity, 'placeholder', '') or entity.code or '')


def _dual_key_map(entities):
    """Словарь сущностей по ``code`` и по ``placeholder`` (если задан)."""
    m = {}
    for e in entities:
        m[e.code] = e
        if getattr(e, 'placeholder', ''):
            m[e.placeholder] = e
    return m


def _all_nodes_tree():
    """Все активные узлы в порядке дерева (depth-first).

    Неактивные родители не теряют активных детей: обходим по всем узлам, но
    в результат включаем только активные.
    """
    nodes = list(CuSectionNode.objects.all().order_by('sorting_order', 'code'))
    by_parent = {}
    for n in nodes:
        by_parent.setdefault(n.parent_id or 0, []).append(n)
    ordered = []

    def walk(parent_id):
        for n in by_parent.get(parent_id, []):
            if n.is_active:
                ordered.append(n)
            walk(n.id)

    walk(0)
    return ordered


def _resolved(control_unit, snapshot, power_supply=None, mode='both',
              signal_power=None, model_line=None, body=None,
              model_line_item=None, structural=False):
    """Узлы/слоты/выбранные опции + эффективные строки матрицы.

    ``structural=True`` — полная активная структура (без show/hide) для
    системного кода; иначе — видимые слоты (show/hide) для артикула.
    """
    if structural:
        nodes = _all_nodes_tree()
        slots = list(CuSlot.objects.filter(is_active=True)
                     .exclude(slot_kind=ConfigSlotKind.SUBTYPE)
                     .select_related('section')
                     .prefetch_related('slot_options')
                     .order_by('sorting_order', 'code'))
    else:
        nodes, slots = visible_slots(control_unit, snapshot)
    merged, defaults = _effective_snapshot(
        control_unit, snapshot, power_supply=power_supply, mode=mode,
        signal_power=signal_power)
    options_by_slot = {}
    for s in slots:
        options_by_slot[s.id] = sorted(
            [o for o in s.slot_options.all() if o.is_active],
            key=lambda o: (o.sorting_order, o.code))
    chosen = {}
    for s in slots:
        chosen[s.id] = _slot_chosen_options(
            s, options_by_slot, merged, defaults)
    resolved = resolve_slots(
        control_unit, model_line=model_line, body=body,
        model_line_item=model_line_item, power_supply=power_supply,
        signal_power=signal_power, mode=mode)
    rows_by_option = {}
    for payloads in resolved.values():
        for p in payloads:
            if p.get('option_code'):
                rows_by_option[p['option_code']] = p
    return nodes, slots, chosen, options_by_slot, rows_by_option


def _eff_enc(option, rows_by_option, ext):
    """Эффективная кодировка опции (матрица → опция)."""
    if not option:
        return ''
    field = 'ext_encoding' if ext else 'encoding'
    row = rows_by_option.get(option.code)
    if row:
        return row.get(field) or ''
    return getattr(option, field) or ''


def build_system_code(control_unit, snapshot=None, *, power_supply=None,
                      mode='both', signal_power=None, model_line=None,
                      body=None, model_line_item=None):
    """Полный системный код конфигурации (структурный, без show/hide)."""
    nodes, slots, chosen, options_by_slot, _ = _resolved(
        control_unit, snapshot, power_supply, mode, signal_power,
        model_line, body, model_line_item, structural=True)
    return _system_code_string(control_unit, nodes, slots, chosen,
                               options_by_slot)


def _article_code(control_unit, snapshot, *, power_supply=None, mode='both',
                  signal_power=None, model_line=None, body=None,
                  model_line_item=None, ext=False):
    """Строка артикульного кода БУ (encoding или ext_encoding)."""
    template = (control_unit.ext_article_code_template if ext
                else control_unit.article_code_template)
    if not template:
        return ''
    _nodes, visible, chosen, options_by_slot, rows_by_option = _resolved(
        control_unit, snapshot, power_supply, mode, signal_power,
        model_line, body, model_line_item)
    return _article_code_string(control_unit, visible, chosen, options_by_slot,
                                rows_by_option, ext)


def build_article_code(control_unit, snapshot=None, *, power_supply=None,
                       mode='both', signal_power=None, model_line=None,
                       body=None, model_line_item=None):
    """Артикульный код БУ (encoding выбранных опций)."""
    return _article_code(control_unit, snapshot, power_supply=power_supply,
                         mode=mode, signal_power=signal_power,
                         model_line=model_line, body=body,
                         model_line_item=model_line_item, ext=False)


def build_ext_article_code(control_unit, snapshot=None, *, power_supply=None,
                           mode='both', signal_power=None, model_line=None,
                           body=None, model_line_item=None):
    """Ext-часть артикульного кода БУ (ext_encoding выбранных опций)."""
    return _article_code(control_unit, snapshot, power_supply=power_supply,
                         mode=mode, signal_power=signal_power,
                         model_line=model_line, body=body,
                         model_line_item=model_line_item, ext=True)


def build_codes(control_unit, snapshot=None, *, power_supply=None, mode='both',
                signal_power=None, model_line=None, body=None,
                model_line_item=None):
    """Все коды конфигурации за один вызов.

    Возвращает ``{system_code, article_code, ext_article_code}``. Системный
    код считается по полной структуре (без show/hide), артикульный — по
    видимым слотам.
    """
    s_nodes, s_slots, s_chosen, s_options, _ = _resolved(
        control_unit, snapshot, power_supply, mode, signal_power,
        model_line, body, model_line_item, structural=True)
    v_nodes, v_slots, v_chosen, v_options, rows = _resolved(
        control_unit, snapshot, power_supply, mode, signal_power,
        model_line, body, model_line_item)

    system_code = _system_code_string(
        control_unit, s_nodes, s_slots, s_chosen, s_options)
    article_code = _article_code_string(
        control_unit, v_slots, v_chosen, v_options, rows, ext=False)
    ext_article_code = _article_code_string(
        control_unit, v_slots, v_chosen, v_options, rows, ext=True)
    return {'system_code': system_code, 'article_code': article_code,
            'ext_article_code': ext_article_code}


def _system_code_string(control_unit, nodes, slots, chosen, options_by_slot):
    template = _system_code_template()
    if not template:
        unit_opt = _product_type_option(control_unit)
        parts = [unit_opt.code if unit_opt else control_unit.code]
        for s in slots:
            for o in chosen.get(s.id, []):
                node_code = s.section.code if s.section else ''
                parts.append(f'{node_code}.{s.code}.{o.code}')
        return '/'.join(parts)

    node_by_key = _dual_key_map(nodes)
    slot_by_key = _dual_key_map(slots)
    opt_by_key = {}
    for s in slots:
        for o in options_by_slot[s.id]:
            opt_by_key[o.code] = o
            if o.placeholder:
                opt_by_key[o.placeholder] = o

    def _slots_of(node):
        out = []
        for s in slots:
            if s.section_id != node.id:
                continue
            for o in chosen.get(s.id, []):
                out.append(_token(s) + _token(o))
        return ''.join(out)

    def repl(m):
        kind, code = m.group(1), m.group(2).strip()
        if kind == 'node':
            return _token(node_by_key.get(code)) if node_by_key.get(code) else ''
        if kind == 'slots':
            node = node_by_key.get(code)
            return _slots_of(node) if node else ''
        if kind == 'slot':
            return _token(slot_by_key.get(code)) if slot_by_key.get(code) else ''
        return _token(opt_by_key.get(code)) if opt_by_key.get(code) else ''

    return _PH_RE.sub(repl, template)


def _article_code_string(control_unit, visible, chosen, options_by_slot,
                         rows_by_option, ext):
    template = (control_unit.ext_article_code_template if ext
                else control_unit.article_code_template)
    if not template:
        return ''
    slot_by_key = _dual_key_map(visible)
    opt_by_key = {}
    for s in visible:
        for o in options_by_slot[s.id]:
            opt_by_key[o.code] = o
            if o.placeholder:
                opt_by_key[o.placeholder] = o
    chosen_codes = {o.code for s in visible for o in chosen.get(s.id, [])}

    def repl(m):
        kind, code = m.group(1), m.group(2).strip()
        if kind == 'slot':
            s = slot_by_key.get(code)
            opts = chosen.get(s.id, []) if s else []
            return _eff_enc(opts[0], rows_by_option, ext) if opts else ''
        o = opt_by_key.get(code)
        return _eff_enc(o, rows_by_option, ext) if (o and o.code in chosen_codes) else ''

    return _PH_RE.sub(repl, template)


def build_article_code_dicts(control_unit, snapshot=None, *, power_supply=None,
                             mode='both', signal_power=None, model_line=None,
                             body=None, model_line_item=None):
    """Плоские словари для ЭП-артикула: {placeholder: encoding} и {ext}.

    Ключи — ``placeholder`` слота/опции (фоллбэк ``code``), значения —
    encoding/ext_encoding выбранных опций. Для multi-слотов значение слота —
    конкатенация кодировок всех выбранных опций. Передаётся в
    ``_get_code_data_dict()`` / ``_get_ext_code_data_dict()`` TemplateMixin.
    """
    _nodes, visible, chosen, options_by_slot, rows_by_option = _resolved(
        control_unit, snapshot, power_supply, mode, signal_power,
        model_line, body, model_line_item)
    enc, ext = {}, {}
    for s in visible:
        opts = chosen.get(s.id, [])
        if not opts:
            continue
        slot_key = s.placeholder or s.code
        slot_enc = ''.join(_eff_enc(o, rows_by_option, False) for o in opts)
        slot_ext = ''.join(_eff_enc(o, rows_by_option, True) for o in opts)
        if slot_enc:
            enc[slot_key] = slot_enc
        if slot_ext:
            ext[slot_key] = slot_ext
        for o in opts:
            opt_key = o.placeholder or o.code
            e = _eff_enc(o, rows_by_option, False)
            x = _eff_enc(o, rows_by_option, True)
            if e:
                enc[opt_key] = e
            if x:
                ext[opt_key] = x
    return enc, ext
