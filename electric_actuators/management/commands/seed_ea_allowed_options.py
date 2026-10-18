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
    ('none', '24-DC'): True, ('none', '220-AC'): True,
    ('none', '380-AC'): False,
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
    ('none', '24-DC'): True, ('none', '220-AC'): True,
    ('none', '380-AC'): False,
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
    'none': [('INDICATOR:BLINKER', 'std')],
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
# Напряжения, на которых заливаются INDICATOR-строки (none — без 380: стартера нет)
INDICATOR_PS = {'24-DC': '24-DC', '220-AC': '220-AC', '380-AC': '380-AC'}
INDICATOR_PS_NONE = ['24-DC', '220-AC']

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
                 'indicator_created': 0, 'capabilities': 0}

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
                   'none': '', 'posi-4-20': 'POSI', 'posi10': 'POSI10',
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

        # Правило стартера: none×380 — запрет во всех сериях
        for a in AllowedControlUnitOption.objects.filter(
                control_unit__code='none', power_supply__code='380-AC',
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
            ps_codes = (INDICATOR_PS_NONE if cu_code == 'none'
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

        self.stdout.write(self.style.SUCCESS(
            'Готово: Allowed создано %d/обновлено %d, INDICATOR строк %d, '
            'capabilities %d' % (stats['allowed_created'],
                                 stats['allowed_updated'],
                                 stats['indicator_created'],
                                 stats['capabilities'])))
