# electric_actuators/services/ea_ext_code.py
"""
Расширенный код заказа ЭП (ext) — сборка, расшифровка, правила кодирования.

Система позиционная (образец — AUMA, но с ЯВНЫМИ кодами для всех вариантов —
аналог хэш-функции конфигурации): каждый вариант опции имеет свой код,
«отсутствие» тоже кодируется (N0/T0/H0/B0…). Код — цепочка блоков через «.»,
внутри блока позиции идут в фиксированном порядке.

Блоки и позиции (см. ea-signals-options-spec.md, разд. 9):

    блок БУ      : {cu}{cu_p}{ps}{mode}{proto}
    блок защиты  : {ip}{exd}
    блок коммут. : {end}{way}{torq}
    блок ОС      : {pos}{hart}
    блок климата : {temp}{h_cu}{therm}
    блок опций   : {lc}{cmd}{setp}{cnt}{ind}{bat}

Коды позиций — из записей каталога (AllowedControlUnitOption.encoding,
PowerSupplies, EaCommProtocol, EaSlotOption, ElectricTemperatureOption,
ElectricBatteryOption, IpOption/ExdOption) с фиксированными отображениями
каталог-код → ext-код (карты ниже). Коды внутри одной позиции попарно
различимы и не являются префиксами друг друга — расшифровка однозначна
(greedy longest-match по позициям в порядке блока).
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
    ('env', 'Корпус и защита', ['ip', 'exd']),
    ('sw', 'Коммутация', ['end', 'way', 'torq']),
    ('fb', 'Обратная связь', ['pos', 'hart']),
    ('cl', 'Климатика', ['temp', 'h_cu', 'therm']),
    ('op', 'Опции', ['lc', 'cmd', 'setp', 'cnt', 'ind']),
    ('ad', 'Ограничение доступа', ['ad']),
    ('sp', 'Положение безопасности', ['sp']),
]
POSITION_TITLES = {
    'cu': 'Блок управления', 'cu_p': 'Питание БУ', 'ps': 'Напряжение мотора',
    'mode': 'Режим', 'proto': 'Шина', 'ip': 'Степень защиты IP',
    'exd': 'Взрывозащита', 'end': 'Концевые', 'way': 'Промежуточные',
    'torq': 'Моментные', 'pos': 'Позиционная ОС', 'hart': 'HART',
    'temp': 'Температура/обогрев привода', 'h_cu': 'Обогрев БУ',
    'therm': 'Теплозащита', 'lc': 'Органы управления', 'cmd': 'Команды',
    'setp': 'Уставка', 'cnt': 'Счётчик', 'ind': 'Индикация',
    'sp': 'Положение безопасности', 'ad': 'Ограничение доступа',
}

# ext-коды CU (явные, ≥2 символов; ни один не префикс другого)
CU_EXT = {
    'NO': 'NO', 'basic': 'BA', 'int-o': 'LCU', 'int-l': 'INT',
    'int-n': 'AINT', 'int-n-mb': 'AINT-MB', 'int-n-pb': 'AINT-PB',
    'int-n-hr': 'AINT-HR',
    'pote': 'PT', 'tr-4-20': 'TR', 'tr10': 'T0', 'posi-4-20': 'PR',
    'posi10': 'P0',
}
PS_EXT = {'220-AC': '220AC', '380-AC': '380AC', '24-DC': '24DC'}
# Питание БУ: от привода — 'P0', отдельно 24 V DC — 'X'
CU_P_EXT = {'24-DC': 'X'}
CU_P_DEFAULT = 'P0'
MODE_EXT = {'on_off': 'O', 'modulating': 'M', 'both': 'B'}
PROTO_EXT = {
    'MODBUS_RTU': 'MB', 'MODBUS_TCP': 'MT', 'PROFIBUS_DP': 'PB',
    'PROFINET': 'PN', 'FOUNDATION_FIELDBUS': 'FF', 'PAKSCAN': 'PS',
    'DEVICENET': 'DN', 'ETHERNET_IP': 'EI',
}
PROTO_DEFAULT = 'N0'
PAIR_PREFIX = {'LIMIT_SWITCHES': 'E', 'WAY_SWITCHES': 'W',
               'TORQUE_SWITCHES': 'T'}
PAIR_CONTACT = {'SPDT': '1', 'DPDT': '2'}
PAIR_DEFAULT = '0'
POS_EXT = {
    'FB_POS_4_20MA_ACTIVE': 'TA', 'FB_POS_4_20MA_ACTIVE_HART': 'TA',
    'FB_POS_4_20MA_PASSIVE': 'T', 'FB_POS_4_20MA_PASSIVE_HART': 'T',
    'FB_POS_POT_1K': 'P', 'FB_POS_0_10V': 'TV',
}
POS_DEFAULT = 'N0'
HART_EXT = {'H': 'H'}
HART_DEFAULT = 'H0'
TEMP_BASE = {'STD': 'ST', 'LT': 'L', 'VLT': 'V'}
HEATER_CU_EXT = {'NO_HEATER': 'H0', 'CU_CIRCUIT': 'C', 'SEPARATE_LINE': 'S'}
THERM_EXT = {'FB_OVERHEAT_NC': 'T1', 'FB_OVERHEAT_SPDT': 'T2'}
SP_EXT = {'fl': 'FL', 'nc': 'NC', 'no': 'NO', 'nc-no-fl': 'BAT'}
SP_DEFAULT = 'FL'
AD_EXT = {'NO_DEVICE': 'AD0', 'DEVICE': 'AD1'}
AD_DEFAULT = 'AD0'
# Позиции multi-choice (в слоте можно выбрать несколько опций)
MULTI_POSITIONS = {'cmd'}
NONE_SLOT_EXT = {
    # слот → {суффикс кода опции: ext}
    'LOCAL_CONTROL': {'BUTTONS': 'B', 'SELECTOR': 'S', 'NONE': 'N'},
    'INDICATOR': {'NONE': 'N0', 'LED_SET': 'D', 'BLINKER': 'B',
                  'LED_SET_BLINKER': 'DB', 'LCD_POSITION': 'L',
                  'LCD_BLINKER': 'LB'},
    'TURN_COUNTER': {'NONE': 'N0', 'MECH': 'M', 'ELECTRONIC': 'E',
                     'MECH_ELEC': 'EM', 'MECH_FB': 'MF',
                     'MECH_ELEC_FB': 'EMF'},
    'CMD': {'CMD_OCS_220AC': 'O', 'CMD_OCS_24DC': 'D',
            'CMD_REMOTE_220AC': 'R', 'CMD_REMOTE_24DC': 'RD',
            'CMD_LOCK_220AC': 'LK', 'CMD_LOCK_24DC': 'LD',
            'CMD_MANUAL_220AC': 'MK', 'CMD_MANUAL_24DC': 'MD',
            'CMD_ESD_OPEN_220AC': 'EO', 'CMD_ESD_OPEN_24DC': 'EB',
            'CMD_ESD_CLOSE_220AC': 'EC', 'CMD_ESD_CLOSE_24DC': 'EQ',
            'CMD_INTERLOCK_OPEN_220AC': 'IO', 'CMD_INTERLOCK_OPEN_24DC': 'ID',
            'CMD_INTERLOCK_CLOSE_220AC': 'IC', 'CMD_INTERLOCK_CLOSE_24DC': 'IK',
            'CMD_DRIVE_ENABLE_220AC': 'DV', 'CMD_DRIVE_ENABLE_24DC': 'DW',
            'CMD_MODE_220AC': 'MO', 'CMD_MODE_24DC': 'MW'},
    'SETPOINT': {'NONE': 'N0', 'CMD_POS_4_20MA_ACTIVE': 'A',
                 'CMD_POS_4_20MA_PASSIVE': 'P',
                 'CMD_POS_0_10V_ACTIVE': 'A0',
                 'CMD_POS_0_10V_PASSIVE': 'P0'},
    'POSITION_FEEDBACK': {'NONE': 'N0'},
    'PROTOCOL': {'NONE': 'N0'},
    'THERMAL_SENSOR': {'NO_SENSOR': 'T0', 'THERMAL_NO_OUTPUT': 'TX',
                       'FB_OVERHEAT_NC': 'T1', 'FB_OVERHEAT_SPDT': 'T2'},
}


def _cu_rules(line):
    """Позиция cu: коды — из AllowedControlUnitOption.ext_encoding серии
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
        for cu in ControlUnitInstalledOption.objects.all().order_by(
                'sorting_order', 'code'):
            code = CU_EXT.get(cu.code, '')
            if code in seen:
                continue
            seen.add(code)
            opts.append({'code': code, 'name': cu.name,
                         'is_default': cu.code == 'basic'})
    return opts


def _slot_rules(slot_code, position, line=None):
    """Позиции по каталогу опций слота (EaSlotOption)."""
    from params.models import IpOption
    opts = []
    seen = set()

    def add(code, name, is_default):
        if code is not None and code not in seen:
            seen.add(code)
            opts.append({'code': code, 'name': name,
                         'is_default': is_default})

    if position == 'ip':
        add('IP00', str(_('Без защиты')), False)
        for ip in IpOption.objects.filter(is_active=True).order_by('code'):
            add(ip.code, ip.name, False)
        return opts
    if position == 'exd':
        from electric_actuators.models import ElectricExdOption
        add('EX0', str(_('Без взрывозащиты')), True)
        for e in ElectricExdOption.objects.filter(
                model_line=line, is_active=True).order_by('sorting_order'):
            if not e.exd_short and not e.encoding:
                continue
            add(e.exd_short or e.encoding, e.name, False)
        return opts
    if position == 'bat':
        return opts
    if position == 'sp':
        from electric_actuators.models import ElectricSafetyPositionOption
        default_code = SP_DEFAULT
        seen_sp = {}
        for s in ElectricSafetyPositionOption.objects.filter(
                power_supply_option__model_line_item__model_line=line,
                is_active=True).select_related('safety_position'):
            seen_sp.setdefault(s.safety_position_id, s)
        for s in seen_sp.values():
            code = s.ext_encoding or SP_EXT.get(s.safety_position.code, '')
            if not code or code == SP_DEFAULT:
                continue
            add(code, s.safety_position.name, s.is_default)
            if s.is_default:
                default_code = code
        add(SP_DEFAULT, str(_('Оставаться в текущем положении')),
            default_code == SP_DEFAULT)
        return opts
    if position == 'ad':
        from electric_actuators.models import EaAccessDeviceOption
        add(AD_DEFAULT, str(_('Без устройства')), True)
        for a in EaAccessDeviceOption.objects.filter(is_active=True):
            add(AD_EXT.get(a.code), a.name, False)
        return opts
    if position == 'hart':
        add(HART_DEFAULT, str(_('Без HART')), True)
        add('H', 'HART', False)
        return opts
    default_code = None
    if position in ('end', 'way', 'torq'):
        default_code = PAIR_DEFAULT
    elif position == 'proto':
        default_code = PROTO_DEFAULT
    elif position == 'pos':
        default_code = POS_DEFAULT
    elif slot_code == 'THERMAL_SENSOR':
        default_code = NONE_SLOT_EXT[slot_code].get('NO_SENSOR')
    elif slot_code == 'HEATER_CONTROL_UNIT':
        default_code = HEATER_CU_EXT.get('NO_HEATER')
    elif slot_code == 'CMD':
        default_code = 'C0'  # уникальный дефолт multi-позиции (нет команд)
    elif slot_code in NONE_SLOT_EXT:
        default_code = NONE_SLOT_EXT[slot_code].get('NONE', 'N0')
    if default_code:
        add(default_code, str(_('Нет')), True)
    if position == 'proto':
        for p in EaCommProtocol.objects.filter(is_active=True).order_by('code'):
            add(PROTO_EXT.get(p.code), p.name, False)
        return opts
    for opt in EaSlotOption.objects.filter(
            is_active=True, slot__code=slot_code,
            slot__is_active=True).select_related('slot'):
        if position == 'hart':
            continue
        suffix = opt.code.split(':', 1)[1] if ':' in opt.code else opt.code
        if position in ('end', 'way', 'torq') and opt.kind == 'pair':
            code = (PAIR_PREFIX.get(slot_code, '') +
                    PAIR_CONTACT.get(suffix.rsplit('_', 1)[-1], ''))
            add(code, opt.name or opt.code, False)
        elif position == 'pos' and opt.kind == 'signal' and \
                opt.feedback_signal_id:
            add(POS_EXT.get(opt.feedback_signal.code), opt.feedback_signal.name,
                False)
        elif position == 'h_cu' and opt.kind == 'heater' and \
                opt.heater_supply_id:
            add(HEATER_CU_EXT.get(opt.heater_supply.code),
                opt.heater_supply.name,
                opt.heater_supply.code == 'NO_HEATER')
        elif opt.kind in ('none', 'signal', 'control') and \
                slot_code in NONE_SLOT_EXT:
            ext = NONE_SLOT_EXT[slot_code].get(suffix)
            if ext is None and opt.feedback_signal_id:
                ext = THERM_EXT.get(opt.feedback_signal.code)
            add(ext, opt.name or opt.code, suffix == 'NONE' or
                suffix == 'NO_SENSOR' or suffix == 'NO_HEATER')
        elif opt.kind == 'signal' and slot_code == 'POSITION_FEEDBACK':
            add(POS_EXT.get(opt.feedback_signal.code), opt.feedback_signal.name,
                False)
    return opts


def coding_rules(model_line, locale=None):
    """Правила кодирования серии: блоки → позиции → коды с именами.

    locale — зарезервирован для локализованных имён (фаза 6); сейчас имена
    берутся из справочников как есть.
    """
    line = model_line
    rules = []
    for block_key, block_title, positions in BLOCKS:
        block = {'key': block_key, 'title': block_title, 'positions': []}
        for pos in positions:
            if pos == 'cu':
                opts = _cu_rules(line)
            elif pos == 'cu_p':
                opts = [{'code': CU_P_DEFAULT,
                         'name': str(_('От питания привода')),
                         'is_default': True}]
                for ps in PowerSupplies.objects.all():
                    code = CU_P_EXT.get(ps.code, '')
                    if code:
                        opts.append({'code': code, 'name': ps.name,
                                     'is_default': False})
            elif pos == 'ps':
                opts = []
                for ps in PowerSupplies.objects.all().order_by(
                        'sorting_order', 'code'):
                    code = PS_EXT.get(ps.code, '')
                    if code and not any(o['code'] == code for o in opts):
                        opts.append({'code': code, 'name': ps.name,
                                     'is_default': ps.code == '220-AC'})
            elif pos == 'mode':
                opts = []
                for m, name in (('on_off', str(_('Двухпозиционный (on-off)'))),
                                ('modulating', str(_('Модулирующий')))):
                    opts.append({'code': MODE_EXT[m], 'name': name,
                                 'is_default': m == 'on_off'})
                opts.append({'code': 'B', 'name': str(_('Оба режима')),
                             'is_default': False})
            elif pos in ('ip', 'exd', 'hart'):
                opts = _slot_rules(None, pos) if pos == 'ip' else \
                    _slot_rules(None, pos, line)
            elif pos == 'sp':
                opts = _slot_rules(None, pos, line)
            elif pos == 'ad':
                opts = _slot_rules(None, pos, line)
            elif pos == 'proto':
                opts = _slot_rules('PROTOCOL', pos)
            elif pos in ('end', 'way', 'torq'):
                slot_code = {'end': 'LIMIT_SWITCHES',
                             'way': 'WAY_SWITCHES',
                             'torq': 'TORQUE_SWITCHES'}[pos]
                opts = _slot_rules(slot_code, pos)
            elif pos == 'pos':
                opts = _slot_rules('POSITION_FEEDBACK', pos)
            elif pos == 'temp':
                opts = []
                for t in ElectricTemperatureOption.objects.filter(
                        model_line=line, is_active=True).order_by(
                        'sorting_order', 'id'):
                    base = TEMP_BASE.get(t.code or '', '')
                    if not base and t.code not in ('', 'STD'):
                        continue
                    code = base
                    if base and t.heater_supply_id and \
                            t.heater_supply.code == 'MOTOR_CIRCUIT':
                        code = base + 'M'
                    if not code:
                        continue  # дефолтная запись без code (ensure_*)
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
    """Все правила серии в виде {позиция: {code: name}} + дефолтные коды."""
    rules = coding_rules(model_line)
    codes = {}
    for block in rules:
        for pos in block['positions']:
            codes[pos['key']] = {o['code']: o['name'] for o in pos['options']}
    return codes


def _default_codes(model_line):
    """Дефолтные коды позиций серии (первая is_default или первая опция)."""
    rules = coding_rules(model_line)
    defaults = {}
    for block in rules:
        for pos in block['positions']:
            dflt = None
            for o in pos['options']:
                if o['is_default']:
                    dflt = o['code']
                    break
            if dflt is None and pos['options']:
                dflt = pos['options'][0]['code']
            defaults[pos['key']] = dflt or ''
    return defaults


def build_ext_code(model_line, selection):
    """Сборка ext-кода из выбора {позиция: code}.

    Все позиции заполняются явно (хэш-аналог): пропущенная позиция берёт
    дефолтный код серии. Позиция cmd (multi-choice) может быть списком
    кодов — они конкатенируются. Неизвестный код позиции — ValueError.
    """
    codes = _codes_for(model_line)
    defaults = _default_codes(model_line)
    blocks = []
    for block_key, _title, positions in BLOCKS:
        parts = []
        for pos in positions:
            code = selection.get(pos) or defaults.get(pos, '')
            if isinstance(code, (list, tuple)):
                code = ''.join(code)
            if not code:
                raise ValueError(f'Позиция {pos} без кода (нет дефолта).')
            if pos == 'cu_p' and not selection.get('cu'):
                code = CU_P_DEFAULT
            if pos not in MULTI_POSITIONS and code not in codes.get(pos, {}):
                raise ValueError(f'Неизвестный код позиции {pos}: {code!r}')
            parts.append(code)
        blocks.append(''.join(parts))
    return '.'.join(blocks)


def decode_ext_code(model_line, ext_code):
    """Расшифровка ext-кода в {позиция: {code, name}} + warnings.

    Все позиции заполнены (явные коды) — расшифровка полная. Позиция cmd
    (multi-choice) собирает все коды команд подряд (список в 'codes').
    Неизвестный остаток блока — в warnings.
    """
    codes = _codes_for(model_line)
    defaults = _default_codes(model_line)
    result = {}
    warnings = []
    blocks = ext_code.split('.') if ext_code else []
    for (block_key, _title, positions), text in zip(BLOCKS, blocks):
        for pos in positions:
            pos_codes = [c for c in codes.get(pos, {}) if c]
            pos_codes.sort(key=len, reverse=True)
            if pos == 'cu_p' and not result.get('cu', {}).get('code'):
                result[pos] = {'code': defaults.get(pos, ''),
                               'name': codes[pos].get(
                                   defaults.get(pos, ''), '')}
                continue
            if pos in MULTI_POSITIONS:
                dflt = defaults.get(pos, '')
                pos_codes = [c for c in pos_codes if c != dflt]
                if dflt and text.startswith(dflt):
                    result[pos] = {'code': dflt,
                                   'name': codes[pos].get(dflt, '')}
                    text = text[len(dflt):]
                    continue
                matched_codes = []
                while text:
                    m = None
                    for code in pos_codes:
                        if text.startswith(code):
                            m = code
                            break
                    if m:
                        matched_codes.append(m)
                        text = text[len(m):]
                    else:
                        break
                if matched_codes:
                    result[pos] = {
                        'code': ''.join(matched_codes),
                        'codes': matched_codes,
                        'name': ', '.join(codes[pos].get(c, '')
                                          for c in matched_codes)}
                else:
                    result[pos] = {'code': defaults.get(pos, ''),
                                   'name': codes[pos].get(
                                       defaults.get(pos, ''), '')}
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
                result[pos] = {'code': defaults.get(pos, ''),
                               'name': codes[pos].get(defaults.get(pos, ''), '')}
        if text:
            warnings.append(f'Блок {block_key}: нераспознанный остаток {text!r}')
    for block_key, _title, positions in BLOCKS[len(blocks):]:
        for pos in positions:
            d = defaults.get(pos, '')
            result.setdefault(pos, {'code': d,
                                    'name': codes.get(pos, {}).get(d, '')})
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
    if slot == 'POSITION_FEEDBACK' and option.kind == 'none':
        return ('pos', POS_DEFAULT)
    if slot == 'PROTOCOL' and option.protocol_id:
        code = PROTO_EXT.get(option.protocol.code, '')
        return ('proto', code) if code else None
    if slot == 'PROTOCOL' and option.kind == 'none':
        return ('proto', PROTO_DEFAULT)
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
