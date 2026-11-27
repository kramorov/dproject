# ea_control/services/cu_code.py
"""
Системный и артикульный коды конфигурации БУ (кодировки, slots.md §4.3).

Терминология TemplateMixin: шаблон с плейсхолдерами в фигурных скобках,
подстановка по словарям «ключ → сущность»; для узлов/слотов роль
плейсхолдера-ключа играет их поле ``code`` (глобально уникально в БД —
никакого рассинхрона между ключом и значением).

Два уровня кодировок:

- **системный код** — структурный «хэш» конфигурации, единый для всех
  производителей: код модели БУ (``{model_code}`` → ``ControlUnit.code``),
  коды всех активных узлов и слотов (``{node:X}``/``{slot:X}``/
  ``{slots:X}``, X — ``code`` сущности — адрес-плейсхолдер в шаблоне;
  подставляется ``encoding`` сущности, пусто — фолбэк на ``code``) и
  кодировки (``encoding``) выбранных опций: одна опция — одна кодировка,
  multi — все выбранные в порядке сортировки; слоты внутри ``{slots:X}``
  разделяются ``.``; слот без выбранного (или с пустыми кодировками) —
  «голый» код слота. Пустой шаблон — фолбэк
  ``model_code/узел.слот+кодировки`` через ``/``.
  ``decode_system_code`` разбирает код обратно в набор выбранных опций
  (best effort: неоднозначность/неизвестные фрагменты — честный отчёт);

- **артикульный код** — вклад конкретного БУ в артикул производителя;
  собирается шаблонами ``ControlUnit.article_code_template`` /
  ``ext_article_code_template``, значения — ``encoding``/``ext_encoding``
  выбранных опций (приоритет: строка матрицы → опция слота). Пусто —
  позиция не кодируется.
"""
import re
from collections import defaultdict

from ea_control.models import (CuCodeSettings, CuSectionNode, CuSlot,
                               CuSlotOption, ControlUnit)
from core.models import ConfigSlotKind
from ea_control.services.cu_description import (
    _effective_snapshot, _slot_chosen_options, visible_slots)
from ea_control.services.cu_matrix import get_profile_defaults, resolve_slots

_PH_RE = re.compile(r'\{(model_code|node|slot|opt|slots)(?::([^{}]+))?\}')


def _token(entity):
    """Кодировка сущности в системном коде (encoding → фолбэк code)."""
    if entity is None:
        return ''
    return (getattr(entity, 'encoding', '') or entity.code or '')


def _system_code_template():
    """Шаблон системного кода из синглтона настроек (или None)."""
    return CuCodeSettings.get().system_code_template


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


def _structural_slots(nodes):
    """Активные слоты (без subtype) активных узлов — узел по дереву → слот.

    Слоты выключенных узлов (и безузловые сироты) в системный код не
    входят — дерево кода строится только по активным узлам.
    """
    slots = list(CuSlot.objects.filter(is_active=True, section__is_active=True)
                 .exclude(slot_kind=ConfigSlotKind.SUBTYPE)
                 .select_related('section')
                 .prefetch_related('slot_options')
                 .order_by('sorting_order', 'code'))
    node_pos = {n.id: i for i, n in enumerate(nodes)}
    slots.sort(key=lambda s: (
        node_pos.get(s.section_id, len(nodes)),
        s.sorting_order, s.code))
    return slots


def _resolved(control_unit, snapshot, power_supply=None, mode='both',
              model_line=None, body=None,
              model_line_item=None, structural=False,
              resolved=None, defaults=None):
    """Узлы/слоты/выбранные опции + эффективные строки матрицы.

    ``structural=True`` — полная активная структура (без show/hide) для
    системного кода; иначе — видимые слоты (show/hide) для артикула.
    ``resolved``/``defaults`` — предвычисленные resolve_slots/
    get_profile_defaults (slots.md §6.6 п.2).
    """
    if structural:
        nodes = _all_nodes_tree()
        slots = _structural_slots(nodes)
    else:
        nodes, slots = visible_slots(control_unit, snapshot)
    merged, defaults = _effective_snapshot(
        control_unit, snapshot, power_supply=power_supply, mode=mode,
        defaults=defaults)
    options_by_slot = {}
    for s in slots:
        options_by_slot[s.id] = sorted(
            [o for o in s.slot_options.all() if o.is_active],
            key=lambda o: (o.sorting_order, o.code))
    chosen = {}
    for s in slots:
        chosen[s.id] = _slot_chosen_options(
            s, options_by_slot, merged, defaults)
    if resolved is None:
        resolved = resolve_slots(
            control_unit, model_line=model_line, body=body,
            model_line_item=model_line_item, power_supply=power_supply,
            mode=mode, snapshot=snapshot)
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


def _chosen_encodings(slot, chosen):
    """Кодировки выбранных опций слота (в порядке сортировки), подряд."""
    return ''.join(o.encoding or '' for o in chosen.get(slot.id, []))


def build_system_code(control_unit, snapshot=None, *, power_supply=None,
                      mode='both', model_line=None,
                      body=None, model_line_item=None):
    """Полный системный код конфигурации (структурный, без show/hide).

    Код модели БУ + коды всех активных узлов/слотов + кодировки выбранных
    опций (multi — все в порядке сортировки; слоты в ``{slots:X}`` — через
    ``.``). Пустой шаблон — фолбэк ``model_code/узел.слот+кодировки``.
    """
    nodes, slots, chosen, options_by_slot, _ = _resolved(
        control_unit, snapshot, power_supply, mode,
        model_line, body, model_line_item, structural=True)
    return _system_code_string(control_unit, nodes, slots, chosen)


def _system_code_string(control_unit, nodes, slots, chosen):
    template = _system_code_template()
    node_by_code = {n.code: n for n in nodes}
    slot_by_code = {s.code: s for s in slots}

    if not template:
        parts = [control_unit.code or '']
        for s in slots:
            node_token = _token(s.section) if s.section_id else ''
            parts.append(f'{node_token}.{_token(s)}'
                         + _chosen_encodings(s, chosen))
        return '/'.join(parts)

    slots_by_node = defaultdict(list)
    for s in slots:
        slots_by_node[s.section_id].append(s)

    def _slots_of(node):
        out = []
        for s in slots_by_node.get(node.id, []):
            out.append(_token(s) + _chosen_encodings(s, chosen))
        return '.'.join(out)

    def repl(m):
        kind, code = m.group(1), (m.group(2) or '').strip()
        if kind == 'model_code':
            return control_unit.code or ''
        if kind == 'node':
            node = node_by_code.get(code)
            return _token(node) if node else ''
        if kind == 'slot':
            slot = slot_by_code.get(code)
            return _token(slot) if slot else ''
        if kind == 'slots':
            node = node_by_code.get(code)
            return _slots_of(node) if node else ''
        return ''  # {opt:X} в системном коде не поддерживается

    return _PH_RE.sub(repl, template)


# ── Декодирование ───────────────────────────────────────────────────────────

def _template_pattern(template, unit_codes):
    """Шаблон → (regex, [(номер_группы, kind, arg)]).

    Литералы — как есть; ``{model_code}`` — альтернация известных кодов
    ControlUnit (longest-first — коды могут содержать ``-``/``/``);
    ``{node:X}``/``{slot:X}`` — захватывающие группы, значение сверяется
    с текущим токеном сущности X (интегральная проверка схемы);
    ``{slots:X}`` — захватывающий регион. Токены/кодировки — только
    [A-Za-z0-9] (валидация clean), поэтому литералы не конфликтуют.
    """
    out = []
    groups = []
    idx = 1
    pos = 0
    for m in _PH_RE.finditer(template):
        if m.start() > pos:
            out.append(re.escape(template[pos:m.start()]))
        kind, arg = m.group(1), (m.group(2) or '').strip()
        if kind == 'model_code':
            alts = sorted({re.escape(c) for c in unit_codes if c},
                          key=len, reverse=True)
            out.append(f'({ "|".join(alts) })' if alts else '(.+?)')
            groups.append((idx, 'model_code', None))
            idx += 1
        elif kind in ('node', 'slot'):
            out.append('(.+?)')
            groups.append((idx, kind, arg))
            idx += 1
        elif kind == 'slots':
            out.append('(.*?)')
            groups.append((idx, 'slots', arg))
            idx += 1
        else:  # {opt:X} — в системном коде нет; как литерал
            out.append(re.escape(m.group(0)))
        pos = m.end()
    if pos < len(template):
        out.append(re.escape(template[pos:]))
    return re.compile('^' + ''.join(out) + '$'), groups


def _active_slots_of_node(node):
    return list(CuSlot.objects.filter(section=node, is_active=True)
                .exclude(slot_kind=ConfigSlotKind.SUBTYPE)
                .prefetch_related('slot_options')
                .order_by('sorting_order', 'code'))


def _parse_segment(slots, seg):
    """Сегмент ``токен_слота + encodings`` → список разборов (slot_code, opts).

    ``slots`` — кандидаты (слоты узла); токен слота — ``encoding`` или
    ``code`` (longest-match); ``opts`` — список опций с непустыми
    кодировками; single/xor — не более одной. Пустой остаток — слот есть,
    выбранное с пустыми кодировками (опций не видно).
    """
    results = []
    candidates = []
    for slot in slots:
        for tok in {_token(slot), slot.code}:
            if tok:
                candidates.append((tok, slot))
    candidates.sort(key=lambda t: len(t[0]), reverse=True)
    for tok, slot in candidates:
        if not seg.startswith(tok):
            continue
        rest = seg[len(tok):]
        opts_by_enc = {}
        for o in slot.slot_options.filter(is_active=True).exclude(encoding=''):
            opts_by_enc.setdefault(o.encoding, []).append(o)

        found = []

        def dfs(pos, acc):
            if pos == len(rest):
                found.append(sorted(acc, key=lambda o: (o.sorting_order, o.code)))
                return
            for enc, opts in opts_by_enc.items():
                if rest.startswith(enc, pos):
                    for o in opts:
                        dfs(pos + len(enc), acc + [o])

        dfs(0, [])
        for opts in found:
            if slot.selection_mode != 'multi' and len(opts) > 1:
                continue  # single/xor — ровно одна кодировка
            results.append((slot.code, [o.code for o in opts]))
    # дедупликация идентичных разборов
    uniq = []
    for r in results:
        if r not in uniq:
            uniq.append(r)
    return uniq


def decode_system_code(code):
    """Разбор системного кода в набор выбранных опций (best effort).

    Возвращает::

      {'format': 'template' | 'fallback' | None,
       'model_code': str | None, 'unit': ControlUnit | None,
       'slots': {slot_code: [option_codes...]},
       'ambiguous': [...], 'unknown': [...], 'mismatch': bool}

    ``mismatch=True`` — литералы шаблона не совпали (код сгенерирован
    другой версией шаблона/схемы). ``ambiguous``/``unknown`` — честный
    отчёт о неоднозначных и нераспознанных фрагментах; пустые кодировки
    выбранных опций в коде не видны (слот декодируется без опций).
    """
    base = {
        'format': None, 'model_code': None, 'unit': None, 'slots': {},
        'ambiguous': [], 'unknown': [], 'mismatch': False,
    }
    if not isinstance(code, str) or not code.strip():
        return base

    template = _system_code_template()
    if template:
        unit_codes = list(ControlUnit.objects.values_list('code', flat=True))
        pat, groups = _template_pattern(template, unit_codes)
        m = pat.match(code)
        if not m:
            base['format'] = 'template'
            base['mismatch'] = True
            return base
        base['format'] = 'template'
        nodes = _all_nodes_tree()
        node_by_code = {n.code: n for n in nodes}
        slot_by_code = {s.code: s for s in _structural_slots(nodes)}
        for gi, kind, arg in groups:
            text = m.group(gi)
            if kind == 'model_code':
                base['model_code'] = text
                base['unit'] = ControlUnit.objects.filter(code=text).first()
            elif kind == 'slots':
                node = node_by_code.get(arg)
                if node is None:
                    if text:
                        base['unknown'].append(f'{arg}: {text}')
                    continue
                _decode_region(base, node, text)
            elif kind == 'node':
                node = node_by_code.get(arg)
                if node is None or text != _token(node):
                    base['mismatch'] = True
            elif kind == 'slot':
                slot = slot_by_code.get(arg)
                if slot is None or text != _token(slot):
                    base['mismatch'] = True
        return base

    return _decode_fallback(code, base)


def _decode_region(result, node, region):
    """Регион ``{slots:X}``: сегменты через ``.`` → разборы сегментов."""
    slots = _active_slots_of_node(node)
    for seg in region.split('.'):
        if not seg:
            continue
        parses = _parse_segment(slots, seg)
        if not parses:
            result['unknown'].append(seg)
        elif len(parses) > 1:
            result['ambiguous'].append({'segment': seg, 'parses': parses})
        else:
            slot_code, opts = parses[0]
            result['slots'][slot_code] = opts


def _decode_fallback(code, base):
    """Фолбэк-формат ``model_code/узел.слот+кодировки`` (через ``/``).

    ``model_code`` может сам содержать ``/`` (например «INT/N») — модель
    ищем по списку кодов ControlUnit (самый длинный подходящий).
    """
    base['format'] = 'fallback'
    unit_codes = list(ControlUnit.objects.values_list('code', flat=True))
    model = next((c for c in sorted(unit_codes, key=len, reverse=True)
                  if code == c or code.startswith(c + '/')), None)
    base['model_code'] = model
    base['unit'] = (ControlUnit.objects.filter(code=model).first()
                    if model else None)
    nodes = _all_nodes_tree()
    node_by_token = {}
    for n in nodes:
        node_by_token[_token(n)] = n
        node_by_token[n.code] = n
    slots_by_node = {n.id: _active_slots_of_node(n) for n in nodes}
    rest = code[len(model) + 1:] if model else code
    for part in rest.split('/'):
        if not part:
            continue
        if '.' not in part:
            base['unknown'].append(part)
            continue
        node_token, seg = part.split('.', 1)
        node = node_by_token.get(node_token)
        if node is None:
            base['unknown'].append(part)
            continue
        parses = _parse_segment(slots_by_node[node.id], seg)
        if not parses:
            base['unknown'].append(part)
        elif len(parses) > 1:
            base['ambiguous'].append({'segment': seg, 'parses': parses})
        else:
            slot_code, opts = parses[0]
            base['slots'][slot_code] = opts
    return base


# ── Артикульный код (производитель) ─────────────────────────────────────────

def _article_code(control_unit, snapshot, *, power_supply=None, mode='both',
                  model_line=None, body=None,
                  model_line_item=None, ext=False):
    """Строка артикульного кода БУ (encoding или ext_encoding)."""
    template = (control_unit.ext_article_code_template if ext
                else control_unit.article_code_template)
    if not template:
        return ''
    _nodes, visible, chosen, options_by_slot, rows_by_option = _resolved(
        control_unit, snapshot, power_supply, mode,
        model_line, body, model_line_item)
    return _article_code_string(control_unit, visible, chosen, options_by_slot,
                                rows_by_option, ext)


def build_article_code(control_unit, snapshot=None, *, power_supply=None,
                       mode='both', model_line=None,
                       body=None, model_line_item=None):
    """Артикульный код БУ (encoding выбранных опций)."""
    return _article_code(control_unit, snapshot, power_supply=power_supply,
                         mode=mode,
                         model_line=model_line, body=body,
                         model_line_item=model_line_item, ext=False)


def build_ext_article_code(control_unit, snapshot=None, *, power_supply=None,
                           mode='both', model_line=None,
                           body=None, model_line_item=None):
    """Ext-часть артикульного кода БУ (ext_encoding выбранных опций)."""
    return _article_code(control_unit, snapshot, power_supply=power_supply,
                         mode=mode,
                         model_line=model_line, body=body,
                         model_line_item=model_line_item, ext=True)


def build_codes(control_unit, snapshot=None, *, power_supply=None, mode='both',
                model_line=None, body=None,
                model_line_item=None, resolved=None, defaults=None):
    """Все коды конфигурации за один вызов.

    Возвращает ``{system_code, article_code, ext_article_code}``. Системный
    код считается по полной структуре (без show/hide), артикульный — по
    видимым слотам. ``resolved``/``defaults`` — предвычисленные
    resolve_slots/get_profile_defaults для этой же точки (slots.md §6.6 п.2).
    """
    if resolved is None:
        resolved = resolve_slots(
            control_unit, model_line=model_line, body=body,
            model_line_item=model_line_item, power_supply=power_supply,
            mode=mode, snapshot=snapshot)
    if defaults is None:
        defaults = get_profile_defaults(
            control_unit, power_supply=power_supply, mode=mode,
            snapshot=snapshot)
    s_nodes, s_slots, s_chosen, _s_options, _ = _resolved(
        control_unit, snapshot, power_supply, mode,
        model_line, body, model_line_item, structural=True,
        resolved=resolved, defaults=defaults)
    v_nodes, v_slots, v_chosen, v_options, rows = _resolved(
        control_unit, snapshot, power_supply, mode,
        model_line, body, model_line_item,
        resolved=resolved, defaults=defaults)

    system_code = _system_code_string(control_unit, s_nodes, s_slots, s_chosen)
    article_code = _article_code_string(
        control_unit, v_slots, v_chosen, v_options, rows, ext=False)
    ext_article_code = _article_code_string(
        control_unit, v_slots, v_chosen, v_options, rows, ext=True)
    return {'system_code': system_code, 'article_code': article_code,
            'ext_article_code': ext_article_code}


def _dual_key_map(entities):
    """Словарь сущностей по ``code`` и по ``placeholder`` (если задан)."""
    m = {}
    for e in entities:
        m[e.code] = e
        if getattr(e, 'placeholder', ''):
            m[e.placeholder] = e
    return m


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
        kind, code = m.group(1), (m.group(2) or '').strip()
        if kind == 'slot':
            s = slot_by_key.get(code)
            opts = chosen.get(s.id, []) if s else []
            return _eff_enc(opts[0], rows_by_option, ext) if opts else ''
        if kind == 'opt':
            o = opt_by_key.get(code)
            return (_eff_enc(o, rows_by_option, ext)
                    if (o and o.code in chosen_codes) else '')
        return ''

    return _PH_RE.sub(repl, template)


def build_article_code_dicts(control_unit, snapshot=None, *, power_supply=None,
                             mode='both', model_line=None,
                             body=None, model_line_item=None):
    """Плоские словари для ЭП-артикула: {placeholder: encoding} и {ext}.

    Ключи — ``placeholder`` слота/опции (фоллбэк ``code``), значения —
    encoding/ext_encoding выбранных опций. Для multi-слотов значение слота —
    конкатенация кодировок всех выбранных опций. Передаётся в
    ``_get_code_data_dict()`` / ``_get_ext_code_data_dict()`` TemplateMixin.
    """
    _nodes, visible, chosen, options_by_slot, rows_by_option = _resolved(
        control_unit, snapshot, power_supply, mode,
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
