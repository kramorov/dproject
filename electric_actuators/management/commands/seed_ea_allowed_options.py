"""
Заливка данных ЭП (правила пользователя, 2026-10-18):

1. AllowedControlUnitOption для AR01E/AR11E (серийные пары БУ×напряжение +
   модельные перекрытия-запреты) и правило стартера: none×380 — нет нигде.
2. INDICATOR-правило на уровне бренда (Архимед):
   none → BLINKER (std, единственная);
   int-l/int-n/int-n-hr/int-n-mb/int-n-pb → LCD_POSITION (std) + LCD_BLINKER (opt);
   int-o → LED_SET (std) + LED_SET_BLINKER (opt).
3. capabilities БУ int-o/int-l/int-n (+hr/mb/pb) из сводной
   Управление_приводами_блоки_Сводная_АРХИМЕД_2025-06-24.xlsx.

Идемпотентна. Использование: python manage.py seed_ea_allowed_options
"""
from django.core.management.base import BaseCommand

from params.models import PowerSupplies, ControlUnitInstalledOption
from electric_actuators.models import (
    ElectricActuatorModelLine, ElectricActuatorModelLineItem,
    AllowedControlUnitOption, EaSignalSlot, EaSlotOption, EaSignalMatrixEntry,
)

# Серийные пары: (cu, ps) → активность. ps None = любое напряжение.
AR01_SERIES = {
    ('int-l', '24-DC'): True, ('int-l', '220-AC'): True,
    ('int-l', '380-AC'): True,
    ('basic', '24-DC'): True, ('basic', '220-AC'): True,
    ('basic', '380-AC'): False,
    ('posi-4-20', '24-DC'): True, ('posi-4-20', '220-AC'): True,
    ('posi-4-20', '380-AC'): True,
    ('posi10', '24-DC'): True, ('posi10', '220-AC'): True,
    ('posi10', '380-AC'): True,
    ('pote', '24-DC'): True, ('pote', '220-AC'): True,
    ('pote', '380-AC'): False,
    ('tr-4-20', '24-DC'): True, ('tr-4-20', '220-AC'): True,
    ('tr-4-20', '380-AC'): False,
    ('tr10', '24-DC'): True, ('tr10', '220-AC'): True,
    ('tr10', '380-AC'): False,
}
# Модельные перекрытия AR01E: (item_code, cu, ps) → active
AR01_ITEM = {
    ('003', 'posi-4-20', '380-AC'): False,
    ('003', 'posi10', '380-AC'): False,
    ('003', 'pote', '24-DC'): False, ('003', 'pote', '220-AC'): False,
    ('003', 'tr-4-20', '24-DC'): False, ('003', 'tr-4-20', '220-AC'): False,
    ('003', 'tr10', '24-DC'): False, ('003', 'tr10', '220-AC'): False,
    ('005', 'int-l', '24-DC'): False, ('005', 'int-l', '220-AC'): False,
    ('005', 'int-l', '380-AC'): False,
}

AR11_SERIES = {
    ('int-o', '24-DC'): True, ('int-o', '220-AC'): True,
    ('int-o', '380-AC'): True,
    ('int-l', '24-DC'): True, ('int-l', '220-AC'): True,
    ('int-l', '380-AC'): True,
    ('int-n', '24-DC'): True, ('int-n', '220-AC'): True,
    ('int-n', '380-AC'): True,
    ('int-n-hr', '24-DC'): True, ('int-n-hr', '220-AC'): True,
    ('int-n-hr', '380-AC'): True,
    ('int-n-mb', '24-DC'): True, ('int-n-mb', '220-AC'): True,
    ('int-n-mb', '380-AC'): True,
    ('int-n-pb', '24-DC'): True, ('int-n-pb', '220-AC'): True,
    ('int-n-pb', '380-AC'): True,
    ('basic', '24-DC'): True, ('basic', '220-AC'): True,
    ('basic', '380-AC'): False,
    ('posi-4-20', '24-DC'): True, ('posi-4-20', '220-AC'): True,
    ('posi-4-20', '380-AC'): True,
    ('posi10', '24-DC'): True, ('posi10', '220-AC'): True,
    ('posi10', '380-AC'): True,
    ('pote', '24-DC'): True, ('pote', '220-AC'): True,
    ('pote', '380-AC'): False,
    ('tr-4-20', '24-DC'): True, ('tr-4-20', '220-AC'): True,
    ('tr-4-20', '380-AC'): False,
    ('tr10', '24-DC'): True, ('tr10', '220-AC'): True,
}
AR11_ITEM = {
    ('005', 'posi-4-20', '380-AC'): False,
    ('005', 'posi10', '380-AC'): False,
}

# INDICATOR: cu → [(option_code, availability)]
INDICATOR_RULES = {
    'basic': [('INDICATOR:BLINKER', 'std')],
    'int-l': [('INDICATOR:LCD_POSITION', 'std'),
              ('INDICATOR:LCD_BLINKER', 'opt')],
    'int-n': [('INDICATOR:LCD_POSITION', 'std'),
              ('INDICATOR:LCD_BLINKER', 'opt')],
    'int-n-hr': [('INDICATOR:LCD_POSITION', 'std'),
                 ('INDICATOR:LCD_BLINKER', 'opt')],
    'int-n-mb': [('INDICATOR:LCD_POSITION', 'std'),
                 ('INDICATOR:LCD_BLINKER', 'opt')],
    'int-n-pb': [('INDICATOR:LCD_POSITION', 'std'),
                 ('INDICATOR:LCD_BLINKER', 'opt')],
    'int-o': [('INDICATOR:LED_SET', 'std'),
              ('INDICATOR:LED_SET_BLINKER', 'opt')],
}

# LOCAL_CONTROL (органы местного управления): cu → [(option_code, availability)]
# Правило пользователя 2026-10-18:
#   none/basic/позиционер/потенциометр/трансмиттер → NONE (std, единственная);
#   int-o → SELECTOR (std, единственная);
#   int-l/int-n (+hr/mb/pb) → SELECTOR (std) + BUTTONS (opt).
LOCAL_CONTROL_RULES = {
    'basic': [('LOCAL_CONTROL:NONE', 'std')],
    'pote': [('LOCAL_CONTROL:NONE', 'std')],
    'tr-4-20': [('LOCAL_CONTROL:NONE', 'std')],
    'tr10': [('LOCAL_CONTROL:NONE', 'std')],
    'posi-4-20': [('LOCAL_CONTROL:NONE', 'std')],
    'posi10': [('LOCAL_CONTROL:NONE', 'std')],
    'int-o': [('LOCAL_CONTROL:SELECTOR', 'std')],
    'int-l': [('LOCAL_CONTROL:SELECTOR', 'std'),
              ('LOCAL_CONTROL:BUTTONS', 'opt')],
    'int-n': [('LOCAL_CONTROL:SELECTOR', 'std'),
              ('LOCAL_CONTROL:BUTTONS', 'opt')],
    'int-n-hr': [('LOCAL_CONTROL:SELECTOR', 'std'),
                 ('LOCAL_CONTROL:BUTTONS', 'opt')],
    'int-n-mb': [('LOCAL_CONTROL:SELECTOR', 'std'),
                 ('LOCAL_CONTROL:BUTTONS', 'opt')],
    'int-n-pb': [('LOCAL_CONTROL:SELECTOR', 'std'),
                 ('LOCAL_CONTROL:BUTTONS', 'opt')],
}
# Напряжения, на которых заливаются INDICATOR-строки (none — без 380: стартера нет)
INDICATOR_PS = {'24-DC': '24-DC', '220-AC': '220-AC', '380-AC': '380-AC'}
INDICATOR_PS_BASIC = ['24-DC', '220-AC']

CAPABILITIES = {
    'int-o': {
        'power_supply_separate': True,
        'local_controls': {'buttons': True},
        'display': {'led_set': True, 'blinker': True},
        'inputs': ['open', 'close', 'stay'],
        'feedback': ['local_remote', 'end_open', 'end_close', 'stop',
                     'torque', 'alarm'],
    },
    'int-l': {
        'power_supply_separate': True,
        'local_controls': {'selector': True},
        'display': {'lcd': True, 'position': True, 'commands': True,
                    'status': True, 'error': True},
        'menu_languages': ['en'],
        'setup': {'non_intrusive': True, 'torque_setup': True},
        'inputs': ['open', 'close', 'stay', 'remote', 'setpoint_4_20'],
        'feedback': ['local_remote', 'end_open', 'end_close', 'stop',
                     'selector_position', 'torque', 'alarm', 'position_4_20'],
        'protocols': {'hart': True},
        'misc': ['parallel_interface', 'password_protection', 'wall_mount',
                 'fail_safe'],
        'menu_settings': ['end_switches', 'direction', 'setpoint_range',
                          'dead_zone', 'signal_loss_action', 'calib_4ma',
                          'calib_20ma', 'phase_loss'],
    },
    'int-n': {
        'power_supply_separate': True,
        'local_controls': {'selector': True},
        'display': {'lcd': True, 'position': True, 'commands': True,
                    'status': True, 'error': True, 'overload': True,
                    'torque': True},
        'menu_languages': ['en', 'ru'],
        'setup': {'non_intrusive': True, 'torque_setup': True, 'esd': True},
        'inputs': ['open', 'close', 'stay', 'remote', 'setpoint_4_20', 'esd'],
        'feedback': ['local_remote', 'end_open', 'end_close', 'stop',
                     'way_open', 'way_close', 'selector_position', 'torque',
                     'alarm', 'position_4_20', 'phase_loss'],
        'protocols': {'hart': True, 'modbus': True, 'profibus': True,
                      'foundation_fieldbus': True},
        'datalogger': ['events', 'starts', 'runtime'],
        'misc': ['parallel_interface', 'password_protection', 'wall_mount',
                 'fail_safe', 'torque_bypass', 'anti_water_hammer',
                 'motor_temp_control', 'phase_loss_control',
                 'phase_auto_correction'],
        'menu_settings': ['end_switches', 'direction', 'setpoint_range',
                          'dead_zone', 'signal_loss_action', 'calib_4ma',
                          'calib_20ma', 'phase_loss', 'rotation_error',
                          'limit_auto_detect', 'polarity',
                          'intermediate_position', 'two_speed'],
    },
}


class Command(BaseCommand):
    help = 'Заливка Allowed БУ×напряжение, INDICATOR-правила бренда и capabilities БУ'

    def handle(self, *args, **options):
        ps = {p.code: p for p in PowerSupplies.objects.all()}
        cu = {c.code: c for c in ControlUnitInstalledOption.objects.all()}
        lines = {l.code: l for l in ElectricActuatorModelLine.objects.all()}
        items = {i.code: i for i in ElectricActuatorModelLineItem.objects.all()}

        stats = {'allowed_created': 0, 'allowed_updated': 0,
                 'indicator_created': 0, 'local_control_created': 0,
                 'capabilities': 0}

        def set_pair(line_code, cu_code, ps_code, active, item_code=None):
            line = lines[line_code]
            item = None
            if item_code:
                item = ElectricActuatorModelLineItem.objects.get(
                    model_line=line, code=item_code)
            obj, created = AllowedControlUnitOption.objects.get_or_create(
                model_line=line, control_unit=cu[cu_code],
                power_supply=ps.get(ps_code) if ps_code else None,
                model_line_item=item,
                defaults={'is_active': active,
                          'encoding': obj_encoding(cu_code)})
            if not created and obj.is_active != active:
                obj.is_active = active
                obj.save(update_fields=['is_active'])
                stats['allowed_updated'] += 1
            elif created:
                stats['allowed_created'] += 1
            return obj

        def obj_encoding(cu_code):
            enc = {'int-l': 'INT/L', 'int-n': 'INT/N',
                   'int-n-hr': 'INT/N.HR', 'int-n-mb': 'INT/N.MB',
                   'int-n-pb': 'INT/N.PB', 'int-o': 'INT/O',
                   'basic': '', 'posi-4-20': 'POSI', 'posi10': 'POSI10',
                   'pote': 'POTE', 'tr-4-20': 'TR', 'tr10': 'TR10'}
            return enc.get(cu_code, '')

        # 1. AR01E / AR11E
        for line_code, pairs in (('AR01E', AR01_SERIES), ('AR11E', AR11_SERIES)):
            for (cu_code, ps_code), active in pairs.items():
                set_pair(line_code, cu_code, ps_code, active)
        for line_code, overrides in (('AR01E', AR01_ITEM), ('AR11E', AR11_ITEM)):
            for (item_code, cu_code, ps_code), active in overrides.items():
                set_pair(line_code, cu_code, ps_code, active,
                         item_code=item_code)

        # Правило стартера: basic×380 — запрет во всех сериях
        for a in AllowedControlUnitOption.objects.filter(
                control_unit__code='basic', power_supply__code='380-AC',
                is_active=True):
            a.is_active = False
            a.save(update_fields=['is_active'])
            stats['allowed_updated'] += 1

        # 2. INDICATOR — уровень бренда Архимед
        from producers.models import Brands
        brand = Brands.objects.get(name='Архимед')
        slot = EaSignalSlot.objects.get(code='INDICATOR')
        options = {o.code: o for o in EaSlotOption.objects.filter(slot=slot)}
        for cu_code, rules in INDICATOR_RULES.items():
            ps_codes = (INDICATOR_PS_BASIC if cu_code == 'basic'
                        else list(INDICATOR_PS.values()))
            for ps_code in ps_codes:
                for opt_code, availability in rules:
                    obj, created = EaSignalMatrixEntry.objects.get_or_create(
                        brand=brand, control_unit=cu[cu_code],
                        power_supply=ps[ps_code], mode='both', slot=slot,
                        option=options[opt_code],
                        defaults={'availability': availability,
                                  'name': options[opt_code].name,
                                  'is_default': availability == 'std'})
                    if created:
                        stats['indicator_created'] += 1
                    else:
                        changed = []
                        if obj.availability != availability:
                            obj.availability = availability
                            changed.append('availability')
                        if obj.is_default != (availability == 'std'):
                            obj.is_default = (availability == 'std')
                            changed.append('is_default')
                        if changed:
                            obj.save(update_fields=changed)
                            stats['allowed_updated'] += 1

        # 2a. LOCAL_CONTROL — уровень бренда Архимед (кнопки/селектор/нет)
        lc_slot = EaSignalSlot.objects.get(code='LOCAL_CONTROL')
        lc_options = {o.code: o
                      for o in EaSlotOption.objects.filter(slot=lc_slot)}
        # БУ без интегрированного управления (и basic) — 24/220; int-* — все.
        lc_ps_basic = set(LOCAL_CONTROL_RULES) - {
            'int-o', 'int-l', 'int-n', 'int-n-hr', 'int-n-mb', 'int-n-pb'}
        for cu_code, rules in LOCAL_CONTROL_RULES.items():
            ps_codes = (INDICATOR_PS_BASIC if cu_code in lc_ps_basic
                        else list(INDICATOR_PS.values()))
            for ps_code in ps_codes:
                for opt_code, availability in rules:
                    obj, created = EaSignalMatrixEntry.objects.get_or_create(
                        brand=brand, control_unit=cu[cu_code],
                        power_supply=ps[ps_code], mode='both', slot=lc_slot,
                        option=lc_options[opt_code],
                        defaults={'availability': availability,
                                  'name': lc_options[opt_code].name,
                                  'is_default': availability == 'std'})
                    if created:
                        stats['local_control_created'] += 1
                    else:
                        changed = []
                        if obj.availability != availability:
                            obj.availability = availability
                            changed.append('availability')
                        if obj.is_default != (availability == 'std'):
                            obj.is_default = (availability == 'std')
                            changed.append('is_default')
                        if changed:
                            obj.save(update_fields=changed)
                            stats['allowed_updated'] += 1

        # 2b. Сигнальные наборы по корпусам AR21E/CLFZE (2026-10-18, правило
        # пользователя): варианты сигналов на 220В и 380В одинаковые для всех
        # корпусов серии; образец — корпус AR21E007 (220-AC). Для AR21E —
        # включая int-o; для CLFZE — int-o нет. int-n-hr/mb/pb — как int-n.
        from electric_actuators.models import ElectricActuatorBody
        stats['signal_created'] = 0
        SIGNAL_SERIES = {
            'AR21E': (['AR21E007', 'AR21E010', 'AR21E020', 'AR21E050',
                       'AR21E060'],
                      ['basic', 'int-l', 'int-n', 'int-n-hr', 'int-n-mb',
                       'int-n-pb', 'int-o']),
            'CLFZE': (['CLFZ10-15', 'CLFZ20-30', 'CLFZ45-60', 'CLFZ90-120',
                       'CLFZ180-250', 'CLFZ350'],
                      ['basic', 'int-l', 'int-n', 'int-n-hr', 'int-n-mb',
                       'int-n-pb']),
        }
        CU_TPL = {'int-n-hr': 'int-n', 'int-n-mb': 'int-n',
                  'int-n-pb': 'int-n'}
        src_body = ElectricActuatorBody.objects.get(code='AR21E007')
        for line_code, (body_codes, cu_codes) in SIGNAL_SERIES.items():
            for body_code in body_codes:
                body = ElectricActuatorBody.objects.get(code=body_code)
                for cu_code in cu_codes:
                    tpl_cu = cu[cu_code]
                    src_cu = cu[CU_TPL.get(cu_code, cu_code)]
                    ps_codes = ['220-AC'] if cu_code == 'basic' else \
                        ['220-AC', '380-AC']
                    for ps_code in ps_codes:
                        for src in EaSignalMatrixEntry.objects.filter(
                                body=src_body, control_unit=src_cu,
                                power_supply__code='220-AC'):
                            bundle = src.bundle
                            if bundle and 'AR21E007' in bundle:
                                bundle = bundle.replace('AR21E007', body_code)
                            obj, created = \
                                EaSignalMatrixEntry.objects.get_or_create(
                                    body=body, control_unit=tpl_cu,
                                    power_supply=ps[ps_code], mode=src.mode,
                                    slot=src.slot, option=src.option,
                                    feedback_signal=src.feedback_signal,
                                    control_signal=src.control_signal,
                                    protocol=src.protocol, device=src.device,
                                    heater_supply=src.heater_supply,
                                    defaults={
                                        'availability': src.availability,
                                        'is_default': src.is_default,
                                        'name': src.name, 'bundle': bundle,
                                        'encoding': src.encoding,
                                        'ext_encoding': src.ext_encoding,
                                        'description': src.description,
                                    })
                            if created:
                                stats['signal_created'] += 1

        # 2c. Сигналы AR01E/AR11E по таблице AOX available-options-ea-AOX.xlsx
        # (2026-10-18): наборы по профилям БУ (st — std, opt? — opt), заливка
        # на уровень модели (item) — пары проверяются resolve_cu_pair (серийные
        # + модельные запреты). Исключения корпусов: R — без моментных;
        # R 005-008 — без DPDT/Way; Q 005-010 — без моментных; basic×24-DC
        # теплозащита — только Q.
        from electric_actuators.models.ea_allowed_options import \
            resolve_cu_pair
        PROFILE_COMMON = {
            'basic': [
                ('LIMIT_SWITCHES', 'END_SPDT', 'std'),
                ('LIMIT_SWITCHES', 'END_DPDT', 'opt'),
                ('WAY_SWITCHES', 'WAY_SPDT', 'opt'),
                ('WAY_SWITCHES', 'WAY_DPDT', 'opt'),
                ('TORQUE_SWITCHES', 'TORQUE_SPDT', 'std'),
                ('TORQUE_SWITCHES', 'TORQUE_DPDT', 'opt'),
                ('THERMAL_SENSOR', 'FB_OVERHEAT_NC', 'opt'),
                ('THERMAL_SENSOR', 'FB_OVERHEAT_SPDT', 'opt'),
            ],
            'int': [
                ('SETPOINT', 'CMD_POS_4_20MA_PASSIVE', 'std'),
                ('SETPOINT', 'CMD_POS_4_20MA_ACTIVE', 'opt'),
                ('LIMIT_SWITCHES', 'END_SPDT', 'std'),
                ('LIMIT_SWITCHES', 'END_DPDT', 'opt'),
                ('WAY_SWITCHES', 'WAY_SPDT', 'opt'),
                ('WAY_SWITCHES', 'WAY_DPDT', 'opt'),
                ('TORQUE_SWITCHES', 'TORQUE_SPDT', 'std'),
                ('TORQUE_SWITCHES', 'TORQUE_DPDT', 'opt'),
                ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE', 'std'),
                ('POSITION_FEEDBACK', 'FB_POS_4_20MA_ACTIVE', 'opt'),
                ('THERMAL_SENSOR', 'FB_OVERHEAT_NC', 'opt'),
                ('THERMAL_SENSOR', 'FB_OVERHEAT_SPDT', 'opt'),
                ('TURN_COUNTER', 'MECH', 'opt'),
                ('HEATER_CONTROL_UNIT', 'SEPARATE_LINE', 'opt'),
                ('HEATER_CONTROL_UNIT', 'CU_CIRCUIT', 'opt'),
            ],
            'pote': [('POSITION_FEEDBACK', 'FB_POS_POT_1K', 'std')],
            'tr-4-20': [('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE', 'std')],
            'tr10': [('POSITION_FEEDBACK', 'FB_POS_0_10V', 'opt')],
            'posi': [
                ('SETPOINT', 'CMD_POS_4_20MA_ACTIVE', 'opt'),
                ('POSITION_FEEDBACK', 'FB_POS_4_20MA_ACTIVE', 'opt'),
                ('SETPOINT', 'CMD_POS_0_10V_ACTIVE', 'opt'),
                ('POSITION_FEEDBACK', 'FB_POS_0_10V', 'opt'),
            ],
        }
        AOX_PROFILES = {
            'basic': PROFILE_COMMON['basic'],
            'int-l': PROFILE_COMMON['int'],
            'int-n': PROFILE_COMMON['int'],
            'int-n-hr': PROFILE_COMMON['int'],
            'int-n-mb': PROFILE_COMMON['int'],
            'int-n-pb': PROFILE_COMMON['int'],
            'int-o': PROFILE_COMMON['int'],
            'pote': PROFILE_COMMON['pote'],
            'tr-4-20': PROFILE_COMMON['tr-4-20'],
            'tr10': PROFILE_COMMON['tr10'],
            'posi-4-20': PROFILE_COMMON['posi'],
            'posi10': PROFILE_COMMON['posi'],
        }
        SERIES_BODIES = {
            'AR01E': ['AR01E003', 'AR01E005-008', 'AR01E010-015', 'AR01E020',
                      'AR01E030', 'AR01E040', 'AR01E060', 'AR01E080',
                      'AR01E100', 'AR01E160-500'],
            'AR11E': ['AR11E005-010', 'AR11E015-020', 'AR11E030',
                      'AR11E050-060', 'AR11E080-120', 'AR11E150',
                      'AR11E200-600'],
        }
        NO_TORQUE_BODIES = {'AR01E003', 'AR01E005-008', 'AR01E010-015',
                            'AR01E020', 'AR01E030', 'AR01E040', 'AR01E060',
                            'AR01E080', 'AR01E100', 'AR01E160-500',  # R-серия
                            'AR11E005-010'}  # Q 005-008-010
        NO_DPDT_WAY_BODIES = {'AR01E005-008'}
        option_by_code = {o.code: o for o in EaSlotOption.objects.all()}
        pair_cache = {}
        for line_code, body_codes in SERIES_BODIES.items():
            line = ElectricActuatorModelLine.objects.get(code=line_code)
            items = list(ElectricActuatorModelLineItem.objects.filter(
                model_line=line).select_related('body'))
            # Старые body-строки (заливка AOX v2) заменяются item-строками:
            # удаляем, чтобы резолвер не выдавал дубли сигналов.
            EaSignalMatrixEntry.objects.filter(
                body__code__in=body_codes).delete()
            # Пакетная заливка: ключи существующих строк одним запросом
            existing = set(EaSignalMatrixEntry.objects.filter(
                model_line_item__model_line=line).values_list(
                'model_line_item_id', 'control_unit_id', 'power_supply_id',
                'slot_id', 'option_id'))
            to_create = []
            for item in items:
                body_code = item.body.code if item.body_id else ''
                for cu_code, profile in AOX_PROFILES.items():
                    if cu_code not in cu:
                        continue
                    tpl_cu = cu[cu_code]
                    for ps_code in ('24-DC', '220-AC', '380-AC'):
                        key = (line.pk, item.pk, tpl_cu.pk, ps[ps_code].pk)
                        if key not in pair_cache:
                            pair_cache[key] = resolve_cu_pair(
                                line, item, tpl_cu, ps[ps_code])
                        if pair_cache[key] is None:
                            continue
                        for slot_code, opt_suffix, availability in profile:
                            if slot_code == 'TORQUE_SWITCHES' and \
                                    body_code in NO_TORQUE_BODIES:
                                continue
                            if slot_code in ('WAY_SWITCHES',) and \
                                    opt_suffix.startswith('WAY') and \
                                    body_code in NO_DPDT_WAY_BODIES:
                                continue
                            if slot_code == 'LIMIT_SWITCHES' and \
                                    opt_suffix == 'END_DPDT' and \
                                    body_code in NO_DPDT_WAY_BODIES:
                                continue
                            if slot_code == 'THERMAL_SENSOR' and \
                                    ps_code == '24-DC' and \
                                    line_code == 'AR01E':
                                continue
                            opt = option_by_code.get(
                                '%s:%s' % (slot_code, opt_suffix))
                            if opt is None:
                                continue
                            if (item.pk, tpl_cu.pk, ps[ps_code].pk,
                                    opt.slot_id, opt.pk) in existing:
                                continue
                            to_create.append(EaSignalMatrixEntry(
                                model_line_item=item, control_unit=tpl_cu,
                                power_supply=ps[ps_code], mode='both',
                                slot=opt.slot, option=opt,
                                availability=availability,
                                is_default=(availability == 'std'),
                                name=opt.name))
            if to_create:
                EaSignalMatrixEntry.objects.bulk_create(
                    to_create, batch_size=500)
                stats['signal_created'] += len(to_create)

        # 3. capabilities
        for cu_code, caps in CAPABILITIES.items():
            for code in [cu_code] + (
                    ['int-n-hr', 'int-n-mb', 'int-n-pb']
                    if cu_code == 'int-n' else []):
                c = cu[code]
                if c.capabilities != caps:
                    c.capabilities = caps
                    c.save(update_fields=['capabilities'])
                    stats['capabilities'] += 1

        # 4. ext-кодировки (позиции расширенного кода заказа)
        ext_stats = {'slot': 0, 'temp': 0, 'cu': 0, 'tpl': 0}
        from electric_actuators.services.ea_ext_code import (
            option_position_code, CU_EXT, AD_EXT)
        from electric_actuators.models import ElectricTemperatureOption
        for opt in EaSlotOption.objects.filter(is_active=True):
            pos_code = option_position_code(opt)
            ext = pos_code[1] if pos_code else ''
            if opt.ext_encoding != ext:
                opt.ext_encoding = ext
                opt.save(update_fields=['ext_encoding'])
                ext_stats['slot'] += 1
        TEMP_EXT = {'STD': '', 'LT': 'L', 'VLT': 'V'}
        for t in ElectricTemperatureOption.objects.filter(is_active=True):
            base = TEMP_EXT.get(t.code or '', '')
            ext = base
            if base and t.heater_supply_id and \
                    t.heater_supply.code == 'MOTOR_CIRCUIT':
                ext = base + 'M'
            if t.ext_encoding != ext:
                t.ext_encoding = ext
                t.save(update_fields=['ext_encoding'])
                ext_stats['temp'] += 1
        for a in AllowedControlUnitOption.objects.filter(is_active=True):
            ext = CU_EXT.get(a.control_unit.code, '')
            if a.ext_encoding != ext:
                a.ext_encoding = ext
                a.save(update_fields=['ext_encoding'])
                ext_stats['cu'] += 1
        EXT_TPL = ('{cu}{cu_p}{ps}{mode}{proto}.{ip}{exd}.'
                   '{end}{way}{torq}.{pos}{hart}.{temp}{h_cu}{therm}.'
                   '{lc}{cmd}{setp}{cnt}{ind}.{ad}.{sp}')
        # Основной артикул: плейсхолдер БУ — {cu_name} (номенклатура cu_*).
        ITEM_TPL = '{model_code}.{temperature}.{ip}.{cu_name}.{voltage}.{exd}'
        for ml in ElectricActuatorModelLine.objects.filter(is_active=True):
            if ml.ext_encoding_template != EXT_TPL:
                ml.ext_encoding_template = EXT_TPL
                ml.save(update_fields=['ext_encoding_template'])
                ext_stats['tpl'] += 1
            if ml.model_item_code_template and \
                    '{control_unit}' in ml.model_item_code_template and \
                    ml.model_item_code_template != ITEM_TPL:
                ml.model_item_code_template = ITEM_TPL
                ml.save(update_fields=['model_item_code_template'])
                ext_stats['tpl'] += 1

        # 4a. Положение безопасности (BAT = encoding записи) + exd_short
        from electric_actuators.models import (ElectricExdOption,
                                               ElectricSafetyPositionOption)
        from params.models import SafetyPositionOption
        # Кодировки положений: fl — пусто (стандарт), nc-no-fl — 'BAT'
        adj_sp, _ = SafetyPositionOption.objects.get_or_create(
            code='nc-no-fl',
            defaults={'name': 'НЗ/НО/FL — выбирается настройкой',
                      'sorting_order': 40})
        SP_ENC = {'fl': ('', 'FL'), 'nc': ('', 'NC'), 'no': ('', 'NO'),
                  'nc-no-fl': ('BAT', 'BAT')}
        for s in ElectricSafetyPositionOption.objects.filter(
                is_active=True).select_related('safety_position'):
            enc, ext = SP_ENC.get(s.safety_position.code, ('', ''))
            if s.encoding != enc or s.ext_encoding != ext:
                s.encoding = enc
                s.ext_encoding = ext
                s.save(update_fields=['encoding', 'ext_encoding'])
        for e in ElectricExdOption.objects.filter(is_active=True):
            short = ''
            if e.encoding or e.ext_encoding:
                # краткое: из name «… Ex db IIC T5 Gb X» → «IIC T5 Gb X»
                import re
                m = re.search(r'Ex db (.+)$', (e.name or ''))
                if m:
                    short = m.group(1).strip()
                elif not e.exd_short:
                    short = e.encoding or ''
            if short and e.exd_short != short:
                e.exd_short = short
                e.save(update_fields=['exd_short'])

        # 4c. Устройство ограничения несанкционированного доступа
        from electric_actuators.models import (EaAccessDeviceOption,
                                               ControlUnitAccessDeviceOption)
        ad_no, _ = EaAccessDeviceOption.objects.get_or_create(
            code='NO_DEVICE',
            defaults={'name': 'Устройства нет', 'sorting_order': 10})
        ad_dev, _ = EaAccessDeviceOption.objects.get_or_create(
            code='DEVICE',
            defaults={'name': 'С устройством для ограничения '
                             'несанкционированного доступа',
                      'sorting_order': 20})
        for opt, i18n in ((ad_no, {
                'ru': 'Устройства нет',
                'en': 'No anti-tamper device',
                'cn': '无防拆装置'}),
                          (ad_dev, {
                'ru': 'С устройством для ограничения несанкционированного доступа',
                'en': 'With anti-tamper device',
                'cn': '带防拆装置'})):
            if opt.name_i18n != i18n:
                opt.name_i18n = i18n
                opt.save(update_fields=['name_i18n'])
        for c in ControlUnitInstalledOption.objects.filter(is_active=True):
            basic_like = c.code in ('basic', 'none')
            for opt, is_default in ((ad_no, True), (ad_dev, False)):
                if basic_like and opt.code == 'DEVICE':
                    continue  # для basic/нет управления — только «нет»
                row, created = ControlUnitAccessDeviceOption.objects.get_or_create(
                    control_unit=c, access_device=opt,
                    defaults={'encoding': '',
                              'ext_encoding': AD_EXT[opt.code],
                              'is_default': is_default})
                if not created and (row.ext_encoding != AD_EXT[opt.code]
                                    or row.is_default != is_default):
                    row.ext_encoding = AD_EXT[opt.code]
                    row.is_default = is_default
                    row.save(update_fields=['ext_encoding', 'is_default'])

        # 4b. Макс. обороты мехсчётчиков (корпуса AR21E) + дефолты AR11E
        from electric_actuators.models import ElectricActuatorBody
        TURN_LIMITS = {'AR21E007': 321, 'AR21E010': 228, 'AR21E020': 180,
                       'AR21E050': 180, 'AR21E060-100': 144}
        for code, turns in TURN_LIMITS.items():
            body = ElectricActuatorBody.objects.filter(code=code).first()
            if body is not None and body.turn_counter_max_turns != turns:
                body.turn_counter_max_turns = turns
                body.save(update_fields=['turn_counter_max_turns'])
        line_ar11 = lines.get('AR11E')
        if line_ar11 is not None:
            fl_sp = SafetyPositionOption.objects.filter(code='fl').first()
            for s in ElectricSafetyPositionOption.objects.filter(
                    power_supply_option__model_line_item__model_line=line_ar11,
                    is_active=True):
                if s.safety_position_id == (fl_sp.id if fl_sp else None) \
                        and s.is_default:
                    s.is_default = False
                    s.save(update_fields=['is_default'])
                row, created = ElectricSafetyPositionOption.objects.get_or_create(
                    power_supply_option=s.power_supply_option,
                    safety_position=adj_sp,
                    defaults={'is_default': True})
                if not created and not row.is_default:
                    row.is_default = True
                    row.save(update_fields=['is_default'])

        # 5. EquipmentType: шаблоны наименования и спецификации (+i18n)
        # 5a. Переводы названий БУ (локализация {cu_name} в шаблонах).
        CU_NAME_I18N = {
            'basic': ('Basic (no control unit, motor voltage switching)',
                      'Basic（无控制单元，电机供电控制）'),
            'pote': ('Potentiometer, 0-1 kOhm', '电位器，0-1kΩ'),
            'posi10': ('Positioner, 0-10V feedback', '定位器，0-10V反馈'),
            'posi-4-20': ('Positioner, 4-20mA feedback',
                          '定位器，4-20mA反馈'),
            'tr-4-20': ('Transmitter, 4-20mA feedback',
                        '变送器，4-20mA反馈'),
            'tr10': ('Transmitter, 0-10V', '变送器，0-10V'),
            'int-o': ('With INT/O control unit', '带INT/O控制单元'),
            'int-l': ('With INT/L control unit', '带INT/L控制单元'),
            'int-n': ('With INT/N control unit', '带INT/N控制单元'),
            'int-n-hr': ('With INT/N control unit, HART',
                         '带INT/N控制单元，支持HART'),
            'int-n-mb': ('With INT/N control unit, ModBus',
                         '带INT/N控制单元，支持ModBus'),
            'int-n-pb': ('With INT/N control unit, ProfiBus',
                         '带INT/N控制单元，支持ProfiBus'),
        }
        for cu in ControlUnitInstalledOption.objects.filter(is_active=True):
            pair = CU_NAME_I18N.get(cu.code)
            if not pair:
                continue
            en, cn = pair
            i18n = dict(cu.name_i18n or {})
            if i18n.get('en') != en or i18n.get('cn') != cn:
                i18n['en'] = en
                i18n['cn'] = cn
                cu.name_i18n = i18n
                cu.save(update_fields=['name_i18n'])
        from core.models.equipment_type import EquipmentType
        et = EquipmentType.objects.filter(code='electric-actuator').first()
        if et is not None:
            name_ru = ('Электропривод {series_code} {model_code} {torque} Нм '
                       '{power_supply} {cu_name} {ext_code}')
            name_en = ('Electric actuator {series_code} {model_code} '
                       '{torque} Nm {power_supply} {cu_name} {ext_code}')
            name_cn = ('电动执行器 {series_code} {model_code} {torque} N·m '
                       '{power_supply} {cu_name} {ext_code}')
            spec_ru = ('Серия: {series_code}\nМодель: {model_code} ({body_code})\n'
                       'Момент: {torque} Нм, время закрытия: {time_to_close} с\n'
                       'Напряжение питания: {power_supply}\n'
                       'Блок управления: {cu_name}\n'
                       'Питание БУ: {cu_power_supply}\n'
                       'Режим: {cu_mode}\n'
                       'Шина: {ctl_protocol}\n'
                       'Команды: {ctl_commands}\n'
                       'Уставка: {ctl_setpoint}\n'
                       'Органы местного управления: {ctl_local_controls}\n'
                       'Концевые выключатели: {fb_end_switches}\n'
                       'Промежуточные: {fb_way_switches}\n'
                       'Моментные: {fb_torque_switches}\n'
                       'Позиционная ОС: {fb_position_feedback}\n'
                       'HART: {fb_hart}\n'
                       'Температурное исполнение: {temperature}\n'
                       'Обогрев БУ: {cu_heater}\n'
                       'Теплозащита: {fb_thermal_sensor}\n'
                       'Индикация: {fb_indicator}\n'
                       'Счётчик: {fb_turn_counter}\n'
                       'IP: {ip}\n'
                       'Взрывозащита: {exd}\n'
                       'Покрытие: {coating}\n'
                       'Цвет: {color}\n'
                       'Ручной дублёр: {hand_wheel}\n'
                       'Угол поворота: {turn_angle}\n'
                       'Кабельные вводы: {cable_glands}\n'
                       'Ограничение доступа: {access_device}\n'
                       'Положение безопасности: {safety_position}\n'
                       'Артикул: {article}\n'
                       'Расширенный код: {ext_code}')
            spec_en = ('Series: {series_code}\nModel: {model_code} ({body_code})\n'
                       'Torque: {torque} Nm, closing time: {time_to_close} s\n'
                       'Power supply: {power_supply}\n'
                       'Control unit: {cu_name}\n'
                       'CU power supply: {cu_power_supply}\n'
                       'Mode: {cu_mode}\n'
                       'Protocol: {ctl_protocol}\n'
                       'Commands: {ctl_commands}\n'
                       'Setpoint: {ctl_setpoint}\n'
                       'Local controls: {ctl_local_controls}\n'
                       'Limit switches: {fb_end_switches}\n'
                       'Mid-position switches: {fb_way_switches}\n'
                       'Torque switches: {fb_torque_switches}\n'
                       'Position feedback: {fb_position_feedback}\n'
                       'HART: {fb_hart}\n'
                       'Temperature version: {temperature}\n'
                       'CU heater: {cu_heater}\n'
                       'Thermal protection: {fb_thermal_sensor}\n'
                       'Indicator: {fb_indicator}\n'
                       'Turn counter: {fb_turn_counter}\n'
                       'IP: {ip}\n'
                       'Explosion protection: {exd}\n'
                       'Coating: {coating}\n'
                       'Color: {color}\n'
                       'Handwheel: {hand_wheel}\n'
                       'Rotation angle: {turn_angle}\n'
                       'Cable glands: {cable_glands}\n'
                       'Anti-tamper device: {access_device}\n'
                       'Fail position: {safety_position}\n'
                       'Article: {article}\n'
                       'Extended code: {ext_code}')
            spec_cn = ('系列: {series_code}\n型号: {model_code} ({body_code})\n'
                       '力矩: {torque} N·m, 关闭时间: {time_to_close} s\n'
                       '电源: {power_supply}\n'
                       '控制单元: {cu_name}\n'
                       '控制单元电源: {cu_power_supply}\n'
                       '模式: {cu_mode}\n'
                       '总线: {ctl_protocol}\n'
                       '指令: {ctl_commands}\n'
                       '设定值: {ctl_setpoint}\n'
                       '就地控制: {ctl_local_controls}\n'
                       '限位开关: {fb_end_switches}\n'
                       '中间位置开关: {fb_way_switches}\n'
                       '力矩开关: {fb_torque_switches}\n'
                       '位置反馈: {fb_position_feedback}\n'
                       'HART: {fb_hart}\n'
                       '温度版本: {temperature}\n'
                       '控制单元加热: {cu_heater}\n'
                       '热保护: {fb_thermal_sensor}\n'
                       '指示: {fb_indicator}\n'
                       '计数器: {fb_turn_counter}\n'
                       '防护等级: {ip}\n'
                       '防爆: {exd}\n'
                       '涂层: {coating}\n'
                       '颜色: {color}\n'
                       '手轮: {hand_wheel}\n'
                       '旋转角度: {turn_angle}\n'
                       '电缆接头: {cable_glands}\n'
                       '防拆装置: {access_device}\n'
                       '安全位置: {safety_position}\n'
                       '物料号: {article}\n'
                       '扩展代码: {ext_code}')
            changed = []
            if et.name_template != name_ru:
                et.name_template = name_ru
                changed.append('name_template')
            if et.name_template_i18n.get('ru') != name_ru or \
                    et.name_template_i18n.get('en') != name_en or \
                    et.name_template_i18n.get('cn') != name_cn:
                et.name_template_i18n = {'ru': name_ru, 'en': name_en,
                                         'cn': name_cn}
                changed.append('name_template_i18n')
            if et.spec_template != spec_ru:
                et.spec_template = spec_ru
                changed.append('spec_template')
            if et.spec_template_i18n.get('ru') != spec_ru or \
                    et.spec_template_i18n.get('en') != spec_en or \
                    et.spec_template_i18n.get('cn') != spec_cn:
                et.spec_template_i18n = {'ru': spec_ru, 'en': spec_en,
                                         'cn': spec_cn}
                changed.append('spec_template_i18n')
            if changed:
                et.save(update_fields=changed)

        self.stdout.write(self.style.SUCCESS(
            'Готово: Allowed создано %d/обновлено %d, INDICATOR строк %d, '
            'LOCAL_CONTROL строк %d, сигналов по корпусам %d, capabilities %d; '
            'ext: опции слотов %d, temp %d, БУ %d, шаблоны серий %d' % (
                stats['allowed_created'], stats['allowed_updated'],
                stats['indicator_created'], stats['local_control_created'],
                stats['signal_created'], stats['capabilities'],
                ext_stats['slot'], ext_stats['temp'], ext_stats['cu'],
                ext_stats['tpl'])))
