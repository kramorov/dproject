"""Заливка профилей сигналов БУ (фаза 9): строки EaSignalMatrixEntry БЕЗ
скоупов (только control_unit × напряжение × режим) = «варианты опций типа
БУ производителя». Серийные особенности — отдельные типы БУ (-nq).

Правила: таблица AOX available-options-ea-AOX.xlsx + правила 2026-10-18.
Идемпотентна: удаляет ВСЕ старые строки матрицы (скоупы brand/line/body/
item) и заливает профили; Allowed пересвязываются на вариантные типы БУ.
"""
from django.core.management.base import BaseCommand

from params.models import ControlUnitInstalledOption, PowerSupplies
from electric_actuators.models import (
    EaSignalMatrixEntry, EaSignalSlot, EaSlotOption,
    AllowedControlUnitOption,
)

# Профили: cu_code -> {ps_code или '*': [(slot, opt_suffix, availability)]}
# '*' — оба напряжения 24/220; '+380' — добавляет 380 к 24/220.
PROFILES = {
    'basic': {'*': [
        ('LIMIT_SWITCHES', 'END_SPDT', 'std'),
        ('LIMIT_SWITCHES', 'END_DPDT', 'opt'),
        ('WAY_SWITCHES', 'WAY_SPDT', 'opt'),
        ('WAY_SWITCHES', 'WAY_DPDT', 'opt'),
        ('TORQUE_SWITCHES', 'TORQUE_SPDT', 'std'),
        ('TORQUE_SWITCHES', 'TORQUE_DPDT', 'opt'),
        ('THERMAL_SENSOR', 'FB_OVERHEAT_NC', 'opt'),
        ('THERMAL_SENSOR', 'FB_OVERHEAT_SPDT', 'opt'),
    ]},
    # R-серия: без моментных/DPDT/Way; теплозащита только 220 (DC24V — нет)
    'basic-nq': {'220-AC': [
        ('LIMIT_SWITCHES', 'END_SPDT', 'std'),
        ('THERMAL_SENSOR', 'FB_OVERHEAT_NC', 'opt'),
        ('THERMAL_SENSOR', 'FB_OVERHEAT_SPDT', 'opt'),
    ], '24-DC': [
        ('LIMIT_SWITCHES', 'END_SPDT', 'std'),
    ]},
    'int': {'*': [
        ('SETPOINT', 'CMD_POS_4_20MA_PASSIVE', 'std'),
        ('SETPOINT', 'CMD_POS_4_20MA_ACTIVE', 'opt'),
        ('LIMIT_SWITCHES', 'END_SPDT', 'std'),
        ('LIMIT_SWITCHES', 'END_DPDT', 'opt'),
        ('WAY_SWITCHES', 'WAY_SPDT', 'opt'),
        ('WAY_SWITCHES', 'WAY_DPDT', 'opt'),
        ('TORQUE_SWITCHES', 'TORQUE_SPDT', 'std'),
        ('TORQUE_SWITCHES', 'TORQUE_DPDT', 'opt'),
        ('TORQUE_SWITCHES', 'FB_TORQUE_4_20MA', 'opt'),
        ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE', 'std'),
        ('POSITION_FEEDBACK', 'FB_POS_4_20MA_ACTIVE', 'opt'),
        ('THERMAL_SENSOR', 'FB_OVERHEAT_NC', 'opt'),
        ('THERMAL_SENSOR', 'FB_OVERHEAT_SPDT', 'opt'),
        ('TURN_COUNTER', 'MECH', 'opt'),
        ('HEATER_CONTROL_UNIT', 'SEPARATE_LINE', 'opt'),
        ('HEATER_CONTROL_UNIT', 'CU_CIRCUIT', 'opt'),
    ]},
    # R-серия: без моментных/DPDT/Way; теплозащита только 220
    'int-nq': {'*': [
        ('SETPOINT', 'CMD_POS_4_20MA_PASSIVE', 'std'),
        ('SETPOINT', 'CMD_POS_4_20MA_ACTIVE', 'opt'),
        ('LIMIT_SWITCHES', 'END_SPDT', 'std'),
        ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE', 'std'),
        ('POSITION_FEEDBACK', 'FB_POS_4_20MA_ACTIVE', 'opt'),
        ('TURN_COUNTER', 'MECH', 'opt'),
        ('HEATER_CONTROL_UNIT', 'SEPARATE_LINE', 'opt'),
        ('HEATER_CONTROL_UNIT', 'CU_CIRCUIT', 'opt'),
    ], '220-AC': [
        ('THERMAL_SENSOR', 'FB_OVERHEAT_NC', 'opt'),
        ('THERMAL_SENSOR', 'FB_OVERHEAT_SPDT', 'opt'),
    ]},
    # Q005-010: без моментных
    'int-nq-q': {'*': [
        ('SETPOINT', 'CMD_POS_4_20MA_PASSIVE', 'std'),
        ('SETPOINT', 'CMD_POS_4_20MA_ACTIVE', 'opt'),
        ('LIMIT_SWITCHES', 'END_SPDT', 'std'),
        ('LIMIT_SWITCHES', 'END_DPDT', 'opt'),
        ('WAY_SWITCHES', 'WAY_SPDT', 'opt'),
        ('WAY_SWITCHES', 'WAY_DPDT', 'opt'),
        ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE', 'std'),
        ('POSITION_FEEDBACK', 'FB_POS_4_20MA_ACTIVE', 'opt'),
        ('THERMAL_SENSOR', 'FB_OVERHEAT_NC', 'opt'),
        ('THERMAL_SENSOR', 'FB_OVERHEAT_SPDT', 'opt'),
        ('TURN_COUNTER', 'MECH', 'opt'),
        ('HEATER_CONTROL_UNIT', 'SEPARATE_LINE', 'opt'),
        ('HEATER_CONTROL_UNIT', 'CU_CIRCUIT', 'opt'),
    ]},
    'pote': {'*': [('POSITION_FEEDBACK', 'FB_POS_POT_1K', 'std')]},
    'tr-4-20': {'*': [('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE', 'std')]},
    'tr10': {'*': [('POSITION_FEEDBACK', 'FB_POS_0_10V', 'opt')]},
    'posi-4-20': {'*': [
        ('SETPOINT', 'CMD_POS_4_20MA_ACTIVE', 'opt'),
        ('POSITION_FEEDBACK', 'FB_POS_4_20MA_ACTIVE', 'opt'),
    ]},
    'posi10': {'*': [
        ('SETPOINT', 'CMD_POS_0_10V_ACTIVE', 'opt'),
        ('POSITION_FEEDBACK', 'FB_POS_0_10V', 'opt'),
    ]},
    # HART — только int-n-hr (доп. опции ОС с HART)
    'int-n-hr': {'*': [
        ('POSITION_FEEDBACK', 'FB_POS_4_20MA_ACTIVE_HART', 'opt'),
        ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE_HART', 'opt'),
    ]},
}

# Отображение кодов БУ → профили
CU_PROFILES = {
    'basic': 'basic', 'basic-nq': 'basic-nq',
    'int-l': 'int', 'int-n': 'int', 'int-o': 'int',
    'int-n-hr': 'int', 'int-n-mb': 'int', 'int-n-pb': 'int',
    'int-l-nq': 'int-nq',  # R: без DPDT/Way/TORQUE, thermal 220
    'int-l-q': 'int-nq-q', 'int-n-q': 'int-nq-q', 'int-o-q': 'int-nq-q',
    'int-n-hr-q': 'int-nq-q', 'int-n-mb-q': 'int-nq-q',
    'int-n-pb-q': 'int-nq-q',  # Q005-010: без моментных
    'pote': 'pote', 'tr-4-20': 'tr-4-20', 'tr10': 'tr10',
    'posi-4-20': 'posi-4-20', 'posi10': 'posi10',
}

# INDICATOR / LOCAL_CONTROL — правила бренда (профиль БУ)
INDICATOR_RULES = {
    'basic': [('INDICATOR:BLINKER', 'std')],
    'basic-nq': [('INDICATOR:BLINKER', 'std')],
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
    'int-l-nq': [('INDICATOR:LCD_POSITION', 'std'),
                 ('INDICATOR:LCD_BLINKER', 'opt')],
    'int-l-q': [('INDICATOR:LCD_POSITION', 'std'),
                ('INDICATOR:LCD_BLINKER', 'opt')],
    'int-n-q': [('INDICATOR:LCD_POSITION', 'std'),
                ('INDICATOR:LCD_BLINKER', 'opt')],
    'int-o-q': [('INDICATOR:LED_SET', 'std'),
                ('INDICATOR:LED_SET_BLINKER', 'opt')],
    'int-n-hr-q': [('INDICATOR:LCD_POSITION', 'std'),
                   ('INDICATOR:LCD_BLINKER', 'opt')],
    'int-n-mb-q': [('INDICATOR:LCD_POSITION', 'std'),
                   ('INDICATOR:LCD_BLINKER', 'opt')],
    'int-n-pb-q': [('INDICATOR:LCD_POSITION', 'std'),
                   ('INDICATOR:LCD_BLINKER', 'opt')],
}
LOCAL_CONTROL_RULES = {
    'basic': [('LOCAL_CONTROL:NONE', 'std')],
    'basic-nq': [('LOCAL_CONTROL:NONE', 'std')],
    'pote': [('LOCAL_CONTROL:NONE', 'std')],
    'tr-4-20': [('LOCAL_CONTROL:NONE', 'std')],
    'tr10': [('LOCAL_CONTROL:NONE', 'std')],
    'posi-4-20': [('LOCAL_CONTROL:NONE', 'std')],
    'posi10': [('LOCAL_CONTROL:NONE', 'std')],
    'int-o': [('LOCAL_CONTROL:SELECTOR', 'std')],
    'int-o-nq': [('LOCAL_CONTROL:SELECTOR', 'std')],
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
    'int-l-nq': [('LOCAL_CONTROL:SELECTOR', 'std'),
                 ('LOCAL_CONTROL:BUTTONS', 'opt')],
    'int-l-q': [('LOCAL_CONTROL:SELECTOR', 'std'),
                ('LOCAL_CONTROL:BUTTONS', 'opt')],
    'int-n-q': [('LOCAL_CONTROL:SELECTOR', 'std'),
                ('LOCAL_CONTROL:BUTTONS', 'opt')],
    'int-o-q': [('LOCAL_CONTROL:SELECTOR', 'std')],
    'int-n-hr-q': [('LOCAL_CONTROL:SELECTOR', 'std'),
                   ('LOCAL_CONTROL:BUTTONS', 'opt')],
    'int-n-mb-q': [('LOCAL_CONTROL:SELECTOR', 'std'),
                   ('LOCAL_CONTROL:BUTTONS', 'opt')],
    'int-n-pb-q': [('LOCAL_CONTROL:SELECTOR', 'std'),
                   ('LOCAL_CONTROL:BUTTONS', 'opt')],
}


class Command(BaseCommand):
    help = 'Заливка профилей сигналов БУ (фаза 9): строки без скоупов'

    def handle(self, *args, **options):
        cu = {c.code: c for c in ControlUnitInstalledOption.objects.all()}
        ps = {p.code: p for p in PowerSupplies.objects.all()}
        options = {o.code: o for o in EaSlotOption.objects.all()}
        stats = {'deleted': 0, 'created': 0}

        # 1. Удалить все старые строки матрицы (скоупы + бренд-правила)
        stats['deleted'] = EaSignalMatrixEntry.objects.all().delete()[0]

        # 2. Вариантные типы БУ (-nq и т.п.)
        VARIANT_CUS = {
            'basic-nq': ('Basic (без БУ), серия R', 'BASIC'),
            'int-l-nq': ('С блоком управления типа INT/L, серия R',
                         'INTEGRATED'),
            'int-l-q': ('С блоком управления типа INT/L, Q 005-010',
                        'INTEGRATED'),
            'int-n-q': ('С блоком управления типа INT/N, Q 005-010',
                        'INTEGRATED'),
            'int-n-hr-q': ('С блоком управления типа INT/N с HART, Q 005-010',
                           'INTEGRATED'),
            'int-n-mb-q': ('С блоком управления типа INT/N с ModBus, Q 005-010',
                           'INTEGRATED'),
            'int-n-pb-q': ('С блоком управления типа INT/N с ProfiBus, Q 005-010',
                           'INTEGRATED'),
            'int-o-q': ('С блоком управления типа INT/O, Q 005-010',
                        'INTEGRATED'),
        }
        for code, (name, kind) in VARIANT_CUS.items():
            cu[code], _ = ControlUnitInstalledOption.objects.get_or_create(
                code=code, defaults={'name': name, 'kind': kind})

        # 3. Профили сигналов (строки без скоупов)
        to_create = []
        for cu_code, profile_name in CU_PROFILES.items():
            if cu_code not in cu:
                continue
            profile = PROFILES[profile_name]
            # список ps: '*' → 24/220; '+380' → +380; явные ключи
            for ps_key, rules in profile.items():
                ps_codes = (['24-DC', '220-AC'] if ps_key == '*'
                            else [ps_key])
                if ps_key == '+380':
                    continue  # не используется — резерв
                for ps_code in ps_codes:
                    if ps_code not in ps:
                        continue
                    for slot_code, opt_suffix, availability in rules:
                        opt = options.get('%s:%s' % (slot_code, opt_suffix))
                        if opt is None:
                            continue
                        to_create.append(EaSignalMatrixEntry(
                            control_unit=cu[cu_code],
                            power_supply=ps[ps_code], mode='both',
                            slot=opt.slot, option=opt,
                            feedback_signal=opt.feedback_signal,
                            control_signal=opt.control_signal,
                            protocol=opt.protocol,
                            heater_supply=opt.heater_supply,
                            device=opt.device,
                            availability=availability,
                            is_default=(availability == 'std'),
                            name=opt.name))
        # INDICATOR / LOCAL_CONTROL (профильные строки бренда)
        for cu_code, rules in INDICATOR_RULES.items():
            if cu_code not in cu:
                continue
            for opt_code, availability in rules:
                opt = options.get(opt_code)
                if opt is None:
                    continue
                for ps_code in ('24-DC', '220-AC', '380-AC'):
                    if cu_code in ('basic', 'basic-nq') and ps_code == '380-AC':
                        continue
                    to_create.append(EaSignalMatrixEntry(
                        control_unit=cu[cu_code], power_supply=ps[ps_code],
                        mode='both', slot=opt.slot, option=opt,
                        availability=availability,
                        is_default=(availability == 'std'), name=opt.name))
        for cu_code, rules in LOCAL_CONTROL_RULES.items():
            if cu_code not in cu:
                continue
            for opt_code, availability in rules:
                opt = options.get(opt_code)
                if opt is None:
                    continue
                for ps_code in ('24-DC', '220-AC', '380-AC'):
                    if cu_code in ('basic', 'basic-nq', 'pote', 'tr-4-20',
                                   'tr10', 'posi-4-20', 'posi10') and \
                            ps_code == '380-AC':
                        continue
                    to_create.append(EaSignalMatrixEntry(
                        control_unit=cu[cu_code], power_supply=ps[ps_code],
                        mode='both', slot=opt.slot, option=opt,
                        availability=availability,
                        is_default=(availability == 'std'), name=opt.name))
        EaSignalMatrixEntry.objects.bulk_create(to_create, batch_size=500)
        stats['created'] = len(to_create)

        # 3a. Перепривязка схем EaWiringDiagramBinding к профильным строкам
        # (M2M signals очищается при перезаливке — восстанавливаем по
        # (БУ, напряжение) каждой схемы).
        from electric_actuators.models import EaWiringDiagramBinding
        stats['bindings'] = 0
        for b in EaWiringDiagramBinding.objects.filter(is_active=True):
            rows = EaSignalMatrixEntry.objects.filter(
                control_unit=b.control_unit, power_supply=b.power_supply,
                brand__isnull=True, model_line__isnull=True,
                body__isnull=True, model_line_item__isnull=True)
            b.signals.set(rows)
            stats['bindings'] += 1

        # 4. Allowed: R-серия → -nq; Q005-010 → -q
        for a in AllowedControlUnitOption.objects.filter(
                model_line__code='AR01E'):
            swap = {'basic': 'basic-nq', 'int-l': 'int-l-nq'}.get(
                a.control_unit.code)
            if swap and swap in cu:
                a.control_unit = cu[swap]
                a.save(update_fields=['control_unit'])
        for a in AllowedControlUnitOption.objects.filter(
                model_line__code='AR11E',
                model_line_item__code__in=['005', '008', '010']):
            swap = {'int-l': 'int-l-q', 'int-n': 'int-n-q',
                    'int-n-hr': 'int-n-hr-q', 'int-n-mb': 'int-n-mb-q',
                    'int-n-pb': 'int-n-pb-q', 'int-o': 'int-o-q'}.get(
                a.control_unit.code)
            if swap and swap in cu:
                a.control_unit = cu[swap]
                a.save(update_fields=['control_unit'])

        self.stdout.write(self.style.SUCCESS(
            'Профили БУ: удалено %d старых строк, создано %d профильных '
            'строк; вариантные БУ созданы; схем перепривязано %d' % (
                stats['deleted'], stats['created'], stats['bindings'])))
