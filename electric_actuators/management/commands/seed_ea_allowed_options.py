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
            option_position_code, CU_EXT)
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
        EXT_TPL = ('{cu}{cu_p}{ps}{mode}{proto}.{end}{way}{torq}.'
                   '{pos}{hart}.{temp}{h_cu}{therm}.{lc}{cmd}{setp}{cnt}{ind}')
        for ml in ElectricActuatorModelLine.objects.filter(is_active=True):
            if ml.ext_encoding_template != EXT_TPL:
                ml.ext_encoding_template = EXT_TPL
                ml.save(update_fields=['ext_encoding_template'])
                ext_stats['tpl'] += 1

        # 5. EquipmentType: шаблоны наименования и спецификации (+i18n)
        from core.models.equipment_type import EquipmentType
        et = EquipmentType.objects.filter(code='electric-actuator').first()
        if et is not None:
            name_ru = ('Электропривод {series_code} {model_code} {torque} Нм '
                       '{power_supply} {control_unit} {ext_code}')
            name_en = ('Electric actuator {series_code} {model_code} '
                       '{torque} Nm {power_supply} {control_unit} {ext_code}')
            name_cn = ('电动执行器 {series_code} {model_code} {torque} N·m '
                       '{power_supply} {control_unit} {ext_code}')
            spec_ru = ('Серия: {series_code}\nМодель: {model_code} ({body_code})\n'
                       'Момент: {torque} Нм, время закрытия: {time_to_close} с\n'
                       'Напряжение питания: {power_supply}\n'
                       'Блок управления: {control_unit}\n'
                       'Питание БУ: {cu_power_supply}\n'
                       'Режим: {mode}\n'
                       'Шина: {protocol}\n'
                       'Команды: {commands}\n'
                       'Уставка: {setpoint}\n'
                       'Концевые выключатели: {end_switches}\n'
                       'Промежуточные: {way_switches}\n'
                       'Моментные: {torque_switches}\n'
                       'Позиционная ОС: {position_feedback}\n'
                       'HART: {hart}\n'
                       'Температурное исполнение: {temperature}\n'
                       'Обогрев БУ: {heater_cu}\n'
                       'Теплозащита: {thermal_sensor}\n'
                       'Органы местного управления: {local_control}\n'
                       'Индикация: {indicator}\n'
                       'Счётчик: {turn_counter}\n'
                       'IP: {ip}\n'
                       'Взрывозащита: {exd}\n'
                       'Покрытие: {coating}\n'
                       'Цвет: {color}\n'
                       'Ручной дублёр: {hand_wheel}\n'
                       'Угол поворота: {turn_angle}\n'
                       'Кабельные вводы: {cable_glands}\n'
                       'Артикул: {article}')
            spec_en = ('Series: {series_code}\nModel: {model_code} ({body_code})\n'
                       'Torque: {torque} Nm, closing time: {time_to_close} s\n'
                       'Power supply: {power_supply}\n'
                       'Control unit: {control_unit}\n'
                       'CU power supply: {cu_power_supply}\n'
                       'Mode: {mode}\n'
                       'Protocol: {protocol}\n'
                       'Commands: {commands}\n'
                       'Setpoint: {setpoint}\n'
                       'Limit switches: {end_switches}\n'
                       'Mid-position switches: {way_switches}\n'
                       'Torque switches: {torque_switches}\n'
                       'Position feedback: {position_feedback}\n'
                       'HART: {hart}\n'
                       'Temperature version: {temperature}\n'
                       'CU heater: {heater_cu}\n'
                       'Thermal protection: {thermal_sensor}\n'
                       'Local controls: {local_control}\n'
                       'Indicator: {indicator}\n'
                       'Turn counter: {turn_counter}\n'
                       'IP: {ip}\n'
                       'Explosion protection: {exd}\n'
                       'Coating: {coating}\n'
                       'Color: {color}\n'
                       'Handwheel: {hand_wheel}\n'
                       'Rotation angle: {turn_angle}\n'
                       'Cable glands: {cable_glands}\n'
                       'Article: {article}')
            spec_cn = ('系列: {series_code}\n型号: {model_code} ({body_code})\n'
                       '力矩: {torque} N·m, 关闭时间: {time_to_close} s\n'
                       '电源: {power_supply}\n'
                       '控制单元: {control_unit}\n'
                       '控制单元电源: {cu_power_supply}\n'
                       '模式: {mode}\n'
                       '总线: {protocol}\n'
                       '指令: {commands}\n'
                       '设定值: {setpoint}\n'
                       '限位开关: {end_switches}\n'
                       '中间位置开关: {way_switches}\n'
                       '力矩开关: {torque_switches}\n'
                       '位置反馈: {position_feedback}\n'
                       'HART: {hart}\n'
                       '温度版本: {temperature}\n'
                       '控制单元加热: {heater_cu}\n'
                       '热保护: {thermal_sensor}\n'
                       '就地控制: {local_control}\n'
                       '指示: {indicator}\n'
                       '计数器: {turn_counter}\n'
                       '防护等级: {ip}\n'
                       '防爆: {exd}\n'
                       '涂层: {coating}\n'
                       '颜色: {color}\n'
                       '手轮: {hand_wheel}\n'
                       '旋转角度: {turn_angle}\n'
                       '电缆接头: {cable_glands}\n'
                       '物料号: {article}')
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
            'capabilities %d; ext: опции слотов %d, temp %d, БУ %d, '
            'шаблоны серий %d' % (stats['allowed_created'],
                                  stats['allowed_updated'],
                                  stats['indicator_created'],
                                  stats['capabilities'],
                                  ext_stats['slot'], ext_stats['temp'],
                                  ext_stats['cu'], ext_stats['tpl'])))
