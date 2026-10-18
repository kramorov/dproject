# electric_actuators/services/ea_ext_code.py
"""
Расширенный код заказа ЭП (ext) — сборка, расшифровка, правила кодирования.

Система позиционная (образец — AUMA): код — цепочка блоков через «.»,
внутри блока позиции идут в фиксированном порядке, пустая позиция = стандарт.

Блоки и позиции (см. ea-signals-options-spec.md, разд. 9):

    блок БУ      : {cu}{cu_p}{ps}{mode}{proto}
    блок коммут. : {end}{way}{torq}
    блок ОС      : {pos}{hart}
    блок климата : {temp}{h_cu}{therm}
    блок опций   : {lc}{cmd}{setp}{cnt}{ind}

Коды позиций — из записей каталога (AllowedControlUnitOption.encoding,
PowerSupplies, EaCommProtocol, EaSlotOption, ElectricTemperatureOption) с
фиксированными отображениями каталог-код → ext-код (EXT_MAP ниже). Коды внутри
одной позиции попарно различимы и не являются префиксами друг друга — поэтому
расшифровка однозначна (greedy longest-match по позициям в порядке блока).

Правило cu_p: если БУ не выбран (cu=''), питание БУ не кодируется (пусто).
"""
from django.utils.translation import gettext_lazy as _

from electric_actuators.models import (
    EaCommProtocol, EaSignalSlot, EaSlotOption, ElectricActuatorModelLine,
    ElectricTemperatureOption, AllowedControlUnitOption,
)
from params.models import PowerSupplies, ControlUnitInstalledOption

# Позиции блоков (порядок важен)
BLOCKS = [
    ('bu', 'Блок управления и питания', ['cu', 'cu_p', 'ps', 'mode', 'proto']),
    ('sw', 'Коммутация', ['end', 'way', 'torq']),
    ('fb', 'Обратная связь', ['pos', 'hart']),
    ('cl', 'Климатика', ['temp', 'h_cu', 'therm']),
    ('op', 'Опции', ['lc', 'cmd', 'setp', 'cnt', 'ind']),
]
POSITION_TITLES = {
    'cu': 'Блок управления', 'cu_p': 'Питание БУ', 'ps': 'Напряжение мотора',
    'mode': 'Режим', 'proto': 'Шина', 'end': 'Концевые', 'way': 'Промежуточные',
    'torq': 'Моментные', 'pos': 'Позиционная ОС', 'hart': 'HART',
    'temp': 'Температура/обогрев привода', 'h_cu': 'Обогрев БУ',
    'therm': 'Теплозащита', 'lc': 'Органы управления', 'cmd': 'Команды',
    'setp': 'Уставка', 'cnt': 'Счётчик', 'ind': 'Индикация',
}

# ext-коды CU (фиксированные, ≥2 символов; ни один не префикс другого)
CU_EXT = {
    'none': '', 'int-o': 'IO', 'int-l': 'IL', 'int-n': 'IN',
    'int-n-mb': 'IM', 'int-n-pb': 'IP', 'int-n-hr': 'IH',
    'pote': 'PT', 'tr-4-20': 'TR', 'tr10': 'T0', 'posi-4-20': 'PR',
    'posi10': 'P0',
}
PS_EXT = {'220-AC': '', '380-AC': '3', '24-DC': '2'}
# Питание БУ отдельно: пока один код 'X' (24 V DC); специфика — позже
CU_P_EXT = {'24-DC': 'X'}
MODE_EXT = {'on_off': '', 'modulating': 'M', 'both': ''}
PROTO_EXT = {
    'MODBUS_RTU': 'MB', 'MODBUS_TCP': 'MT', 'PROFIBUS_DP': 'PB',
    'PROFINET': 'PN', 'FOUNDATION_FIELDBUS': 'FF', 'PAKSCAN': 'PS',
    'DEVICENET': 'DN', 'ETHERNET_IP': 'EI',
}
PAIR_PREFIX = {'LIMIT_SWITCHES': 'E', 'WAY_SWITCHES': 'W',
               'TORQUE_SWITCHES': 'T'}
PAIR_CONTACT = {'SPDT': '1', 'DPDT': '2'}
POS_EXT = {
    'FB_POS_4_20MA_ACTIVE': 'TA', 'FB_POS_4_20MA_ACTIVE_HART': 'TA',
    'FB_POS_4_20MA_PASSIVE': 'T', 'FB_POS_4_20MA_PASSIVE_HART': 'T',
    'FB_POS_POT_1K': 'P',
}
TEMP_BASE = {'STD': '', 'LT': 'L', 'VLT': 'V'}
HEATER_CU_EXT = {'NO_HEATER': '', 'CU_CIRCUIT': 'C', 'SEPARATE_LINE': 'S'}
THERM_EXT = {'FB_OVERHEAT_NC': 'T1', 'FB_OVERHEAT_SPDT': 'T2'}
NONE_SLOT_EXT = {
    # слот → {суффикс кода опции: ext}
    'LOCAL_CONTROL': {'BUTTONS': '', 'SELECTOR': 'S', 'NONE': 'N'},
    'INDICATOR': {'LED_SET': 'D', 'BLINKER': 'B', 'LED_SET_BLINKER': 'DB',
                  'LCD_POSITION': 'L', 'LCD_BLINKER': 'LB'},
    'TURN_COUNTER': {'NONE': '', 'MECH': 'M', 'ELECTRONIC': 'E',
                     'MECH_ELEC': 'EM', 'MECH_FB': 'MF',
                     'MECH_ELEC_FB': 'EMF'},
    'CMD': {'CMD_OCS_220AC': '', 'CMD_OCS_24DC': 'DC',
            'CMD_REMOTE_220AC': 'R', 'CMD_REMOTE_24DC': 'R2'},
    'SETPOINT': {'CMD_POS_4_20MA_ACTIVE': 'A',
                 'CMD_POS_4_20MA_PASSIVE': 'P'},
    'THERMAL_SENSOR': {'NO_SENSOR': '', 'THERMAL_NO_OUTPUT': 'T0',
                       'FB_OVERHEAT_NC': 'T1', 'FB_OVERHEAT_SPDT': 'T2'},
}


def _cu_rules(line):
    """Позиция cu: коды — из AllowedControlUnitOption.encoding серии
    (fallback — фиксированный справочник CU_EXT)."""
    opts = []
    seen = set()
    for a in AllowedControlUnitOption.objects.filter(
            model_line=line, is_active=True).select_related('control_unit'):
        code = a.ext_encoding or CU_EXT.get(a.control_unit.code, '')
        if code in seen:
            continue
        seen.add(code)
        opts.append({'code': code, 'name': a.control_unit.name,
                     'is_default': False})
    if not opts:
        for cu in ControlUnitInstalledOption.objects.all().order_by('sorting_order', 'code'):
            code = CU_EXT.get(cu.code, '')
            if code in seen:
                continue
            seen.add(code)
            opts.append({'code': code, 'name': cu.name, 'is_default': code == ''})
    return opts


def _slot_rules(slot_code, position):
    """Позиции по каталогу опций слота (EaSlotOption)."""
    opts = [{'code': '', 'name': str(_('Нет')), 'is_default': True}]
    for opt in EaSlotOption.objects.filter(
            is_active=True, slot__code=slot_code,
            slot__is_active=True).select_related('slot'):
        if position == 'hart':
            continue
        suffix = opt.code.split(':', 1)[1] if ':' in opt.code else opt.code
        if position in ('end', 'way', 'torq') and opt.kind == 'pair':
            code = (PAIR_PREFIX.get(slot_code, '') +
                    PAIR_CONTACT.get(suffix.rsplit('_', 1)[-1], ''))
            if code and not any(o['code'] == code for o in opts):
                opts.append({'code': code,
                             'name': opt.name or opt.code,
                             'is_default': False})
        elif position == 'pos' and opt.kind == 'signal' and \
                opt.feedback_signal_id:
            code = POS_EXT.get(opt.feedback_signal.code, '')
            if code and not any(o['code'] == code for o in opts):
                opts.append({'code': code,
                             'name': opt.feedback_signal.name,
                             'is_default': False})
        elif position == 'h_cu' and opt.kind == 'heater' and \
                opt.heater_supply_id:
            code = HEATER_CU_EXT.get(opt.heater_supply.code, '')
            if not any(o['code'] == code for o in opts):
                opts.append({'code': code,
                             'name': opt.heater_supply.name,
                             'is_default': code == ''})
        elif opt.kind in ('none', 'signal', 'control') and \
                slot_code in NONE_SLOT_EXT:
            ext = NONE_SLOT_EXT[slot_code].get(suffix)
            if ext is None and opt.feedback_signal_id:
                ext = THERM_EXT.get(opt.feedback_signal.code)
            if ext is not None and not any(o['code'] == ext for o in opts):
                opts.append({'code': ext, 'name': opt.name or opt.code,
                             'is_default': ext == ''})
    return opts


def coding_rules(model_line, locale=None):
    """Правила кодирования серии: блоки → позиции → коды с именами.

    locale — зарезервирован для локализованных имён (фаза 6); сейчас имена
    берутся из справочников как есть.
    """
    rules = []
    for block_key, block_title, positions in BLOCKS:
        block = {'key': block_key, 'title': block_title, 'positions': []}
        for pos in positions:
            if pos == 'cu':
                opts = _cu_rules(model_line)
            elif pos == 'cu_p':
                opts = [{'code': '', 'name': str(_('От питания привода')),
                         'is_default': True}]
                for ps in PowerSupplies.objects.all():
                    code = CU_P_EXT.get(ps.code, '')
                    if code and not any(o['code'] == code for o in opts):
                        opts.append({'code': code, 'name': ps.name,
                                     'is_default': False})
            elif pos == 'ps':
                opts = []
                for ps in PowerSupplies.objects.all().order_by('sorting_order', 'code'):
                    code = PS_EXT.get(ps.code, '')
                    if not any(o['code'] == code for o in opts):
                        opts.append({'code': code, 'name': ps.name,
                                     'is_default': code == ''})
            elif pos == 'mode':
                opts = [{'code': '', 'name': str(_('Двухпозиционный (on-off)')),
                         'is_default': True},
                        {'code': 'M', 'name': str(_('Модулирующий')),
                         'is_default': False}]
            elif pos == 'proto':
                opts = [{'code': '', 'name': str(_('Нет шины')),
                         'is_default': True}]
                for p in EaCommProtocol.objects.all().order_by('code'):
                    code = PROTO_EXT.get(p.code, '')
                    if code:
                        opts.append({'code': code, 'name': p.name,
                                     'is_default': False})
            elif pos in ('end', 'way', 'torq'):
                slot_code = {'end': 'LIMIT_SWITCHES',
                             'way': 'WAY_SWITCHES',
                             'torq': 'TORQUE_SWITCHES'}[pos]
                opts = _slot_rules(slot_code, pos)
            elif pos == 'pos':
                opts = _slot_rules('POSITION_FEEDBACK', pos)
            elif pos == 'hart':
                opts = [{'code': '', 'name': str(_('Без HART')),
                         'is_default': True},
                        {'code': 'H', 'name': 'HART', 'is_default': False}]
            elif pos == 'temp':
                opts = []
                for t in ElectricTemperatureOption.objects.filter(
                        model_line=model_line, is_active=True).order_by(
                        'sorting_order', 'id'):
                    base = TEMP_BASE.get(t.code or '', '')
                    if not base and t.code not in ('', 'STD'):
                        continue
                    code = base
                    if base and t.heater_supply_id and \
                            t.heater_supply.code == 'MOTOR_CIRCUIT':
                        code = base + 'M'
                    if not any(o['code'] == code for o in opts):
                        opts.append({
                            'code': code,
                            'name': '%s · %s' % (t.code or 'STD',
                                                t.heater_supply.name
                                                if t.heater_supply_id else ''),
                            'is_default': t.is_default,
                        })
            elif pos == 'h_cu':
                opts = _slot_rules('HEATER_CONTROL_UNIT', pos)
            elif pos == 'therm':
                opts = _slot_rules('THERMAL_SENSOR', pos)
            else:  # lc / cmd / setp / cnt / ind
                slot_code = {'lc': 'LOCAL_CONTROL', 'cmd': 'CMD',
                             'setp': 'SETPOINT', 'cnt': 'TURN_COUNTER',
                             'ind': 'INDICATOR'}[pos]
                opts = _slot_rules(slot_code, pos)
            block['positions'].append({
                'key': pos, 'title': POSITION_TITLES[pos], 'options': opts,
            })
        rules.append(block)
    return rules


def _codes_for(model_line):
    """Все правила серии в виде {позиция: {code: name}} (для сборки/декода)."""
    rules = coding_rules(model_line)
    codes = {}
    for block in rules:
        for pos in block['positions']:
            codes[pos['key']] = {o['code']: o['name'] for o in pos['options']}
    return codes


def build_ext_code(model_line, selection):
    """Сборка ext-кода из выбора {позиция: code} (пустые позиции опускаются).

    Пустые блоки кодируются пустыми сегментами (выравнивание блоков): код
    полностью стандартной конфигурации — пустая строка. Неизвестный код
    позиции — ValueError.
    """
    codes = _codes_for(model_line)
    blocks = []
    for block_key, _title, positions in BLOCKS:
        parts = []
        for pos in positions:
            code = selection.get(pos, '') or ''
            if not code:
                continue
            if pos == 'cu_p' and not selection.get('cu'):
                raise ValueError('Питание БУ задано без блока управления.')
            if code not in codes.get(pos, {}):
                raise ValueError(f'Неизвестный код позиции {pos}: {code!r}')
            parts.append(code)
        blocks.append(''.join(parts))
    if not any(blocks):
        return ''
    return '.'.join(blocks)


def decode_ext_code(model_line, ext_code):
    """Расшифровка ext-кода в {позиция: {code, name}} + warnings.

    Пустые позиции (стандарт) включаются с code=''. Неизвестный остаток блока —
    в warnings. Результат обратим: build_ext_code(decode(код)) == код.
    """
    codes = _codes_for(model_line)
    result = {}
    warnings = []
    blocks = ext_code.split('.') if ext_code else []
    for (block_key, _title, positions), text in zip(BLOCKS, blocks):
        for pos in positions:
            pos_codes = [c for c in codes.get(pos, {}) if c]
            pos_codes.sort(key=len, reverse=True)
            if pos == 'cu_p' and not result.get('cu', {}).get('code'):
                result[pos] = {'code': '', 'name': codes[pos].get('', '')}
                continue
            matched = None
            for code in pos_codes:
                if text.startswith(code):
                    matched = code
                    break
            if matched:
                result[pos] = {'code': matched,
                               'name': codes[pos].get(matched, '')}
                text = text[len(matched):]
            else:
                result[pos] = {'code': '', 'name': codes[pos].get('', '')}
        if text:
            warnings.append(f'Блок {block_key}: нераспознанный остаток {text!r}')
    # недостающие блоки/позиции — стандарт
    for block_key, _title, positions in BLOCKS[len(blocks):]:
        for pos in positions:
            result.setdefault(pos, {'code': '',
                                    'name': codes.get(pos, {}).get('', '')})
    return result, warnings


def option_position_code(option):
    """Позиция и ext-код опции слота (или None — позиции в ext нет).

    Обратное к coding_rules отображение: опция каталога (EaSlotOption) →
    (позиция, код). Используется конфигуратором при сборке ext-кода из
    выбранных матричных строк.
    """
    slot = option.slot.code
    suffix = option.code.split(':', 1)[1] if ':' in option.code else option.code
    if slot in PAIR_PREFIX and option.kind == 'pair':
        pos = {'LIMIT_SWITCHES': 'end', 'WAY_SWITCHES': 'way',
               'TORQUE_SWITCHES': 'torq'}[slot]
        code = PAIR_PREFIX[slot] + PAIR_CONTACT.get(
            suffix.rsplit('_', 1)[-1], '')
        return (pos, code)
    if slot == 'POSITION_FEEDBACK' and option.kind == 'signal' \
            and option.feedback_signal_id:
        code = POS_EXT.get(option.feedback_signal.code)
        return ('pos', code) if code else None
    if slot == 'PROTOCOL' and option.protocol_id:
        code = PROTO_EXT.get(option.protocol.code, '')
        return ('proto', code) if code else None
    if slot == 'HEATER_CONTROL_UNIT' and option.kind == 'heater':
        code = HEATER_CU_EXT.get(option.heater_supply.code, '')
        return ('h_cu', code)
    if slot in NONE_SLOT_EXT:
        pos_map = {'LOCAL_CONTROL': 'lc', 'CMD': 'cmd', 'SETPOINT': 'setp',
                   'TURN_COUNTER': 'cnt', 'INDICATOR': 'ind',
                   'THERMAL_SENSOR': 'therm'}
        ext = NONE_SLOT_EXT[slot].get(suffix)
        if ext is None and option.feedback_signal_id:
            ext = THERM_EXT.get(option.feedback_signal.code)
        if ext is not None:
            return (pos_map[slot], ext)
    return None
