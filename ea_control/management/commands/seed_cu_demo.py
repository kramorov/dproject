# ea_control/management/commands/seed_cu_demo.py
"""
Демо-данные для отладки паттерна на БУ: справочники, узлы/слоты/опции,
несколько типов БУ (Архимед/AOX), профильные и серийные строки матрицы,
правила динамики.

Идемпотентная команда: повторный запуск не дублирует записи
(get_or_create по кодам/стабильным ключам). Запуск:

    python manage.py seed_cu_demo

Состав (по мотивам линейки AOX: AR01E/AR11E/AR21E/CLFZE):

- 4 типа БУ: базовый (basic), INT (int-n), INT Modbus (int-n-mb),
  позиционер 4-20 (posi-4-20) — с маппингом на legacy-справочник;
- узлы-секции: УПРАВЛЕНИЕ / ОБРАТНАЯ СВЯЗЬ / СВЯЗЬ / ПИТАНИЕ;
- слоты: control_unit + 13 сигнальных + 3 БУ-специфичных;
- профильные строки матрицы = дефолты каждого типа БУ (std/opt),
  пакет MWG (bundle), парный конфликт;
- серийные строки слота control_unit (AR01E/AR11E × БУ × напряжение)
  — «тип БУ характерен для серии», na-запрет;
- правила: профиль БУ → show/hide слотов, HART → set_default.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from ea_control.models import (CuCapability, CuCommProtocol, CuControlLogic,
                               CuControlSignal, CuControlSignalForm,
                               CuDisplayType, CuFeedbackDevice,
                               CuFeedbackSignal, CuFeedbackSignalForm,
                               CuHeaterSupply, CuLocalControlType,
                               CuLocationOption, CuMatrixEntry,
                               CuSignalPower, CuSignalPowerSource, CuSlot,
                               CuSlotOption, CuSlotRule, CuUnitPowerSource,
                               ControlUnit, CuSectionNode)
from ea_control.models.control_unit import ControlUnitKind


def _cu(model, code, **defaults):
    obj, _ = model.objects.get_or_create(code=code, defaults=defaults)
    return obj


def _opt(code, slot, kind, **fields):
    obj, _ = CuSlotOption.objects.update_or_create(
        code=code, defaults={'slot': slot, 'kind': kind, **fields})
    return obj


def _row(slot, option, cu, model_line=None, power_supply=None,
         signal_power=None, body=None, model_line_item=None, mode='both',
         **fields):
    # lookups — полная идентичность строки (скоуп + координаты): иначе
    # update_or_create мог бы перезатереть строку со специфичным скоупом
    obj, _ = CuMatrixEntry.objects.update_or_create(
        slot=slot, option=option, control_unit=cu,
        model_line=model_line, power_supply=power_supply,
        signal_power=signal_power, body=body,
        model_line_item=model_line_item, mode=mode,
        defaults=fields)
    return obj


class Command(BaseCommand):
    help = 'Демо-данные ea_control: справочники, БУ, слоты, матрица, правила.'

    def handle(self, *args, **options):
        forms, ctl, fb, proto, devices, heater, caps, local_ctrl, display, (
            unit_power) = self._seed_dictionaries()
        locations, sources, powers, logics = self._seed_cu_power(forms)
        sections, slots, opts = self._seed_structure(forms, ctl, fb, proto,
                                                     devices, heater, sources,
                                                     powers, logics,
                                                     local_ctrl, display,
                                                     unit_power, locations)
        cus = self._seed_units(caps, ctl, fb, proto)
        self._seed_matrix(slots, opts, cus, powers)
        self._seed_rules(slots, opts)
        self.stdout.write(self.style.SUCCESS('Демо-данные ea_control готовы.'))

    # ── Справочники-копии ──────────────────────────────────────────────────

    def _seed_dictionaries(self):
        ctl_forms = {
            'DRY_INPUT': _cu(CuControlSignalForm, 'DRY_INPUT',
                             name='Сухой контакт (внутренний опрос +24 В)',
                             category='dry_input'),
            'VOLTAGE_AC': _cu(CuControlSignalForm, 'VOLTAGE_AC',
                              name='Потенциал AC',
                              category='voltage_ac'),
            'VOLTAGE_DC': _cu(CuControlSignalForm, 'VOLTAGE_DC',
                              name='Потенциал DC',
                              category='voltage_dc'),
            'AN_4_20_ACTIVE': _cu(CuControlSignalForm, 'AN_4_20_ACTIVE',
                                  name='Петля 4-20 мА, активная',
                                  category='current_4_20'),
            'AN_4_20_PASSIVE': _cu(CuControlSignalForm, 'AN_4_20_PASSIVE',
                                   name='Петля 4-20 мА, пассивная',
                                   category='current_4_20'),
        }
        fb_forms = {
            'DRY_SPST': _cu(CuFeedbackSignalForm, 'DRY_SPST',
                            name='Сухой контакт SPST',
                            category='dry_output'),
            'DRY_SPDT': _cu(CuFeedbackSignalForm, 'DRY_SPDT',
                            name='Сухой контакт SPDT',
                            category='dry_output'),
            'DRY_DPDT': _cu(CuFeedbackSignalForm, 'DRY_DPDT',
                            name='Сухой контакт DPDT',
                            category='dry_output'),
            'AN_4_20_ACTIVE': _cu(CuFeedbackSignalForm, 'AN_4_20_ACTIVE',
                                  name='Петля 4-20 мА, активная',
                                  category='current_4_20'),
            'AN_4_20_PASSIVE': _cu(CuFeedbackSignalForm, 'AN_4_20_PASSIVE',
                                   name='Петля 4-20 мА, пассивная',
                                   category='current_4_20'),
            'RES_POTENTIOMETER': _cu(CuFeedbackSignalForm,
                                     'RES_POTENTIOMETER',
                                     name='Потенциометр',
                                     category='resistance'),
        }
        forms = {'ctl': ctl_forms, 'fb': fb_forms}
        ctl = {
            'CMD_4_20MA': _cu(CuControlSignal, 'CMD_4_20MA',
                              name='Уставка положения 4-20 мА',
                              role='CMD_4_20MA',
                              category='analog',
                              form=ctl_forms['AN_4_20_PASSIVE'],
                              wires=2),
            'CMD_4_20MA_HART': _cu(CuControlSignal, 'CMD_4_20MA_HART',
                                   name='Уставка 4-20 мА + HART',
                                   role='CMD_4_20MA',
                                   category='analog',
                                   form=ctl_forms['AN_4_20_PASSIVE'],
                                   hart=True, wires=2),
        }
        fb = {}
        for role, base in (
                ('END_OPEN', 'Конечное «Открыто»'),
                ('END_CLOSE', 'Конечное «Закрыто»'),
                ('WAY_OPEN', 'Промежуточное (открытие)'),
                ('WAY_CLOSE', 'Промежуточное (закрытие)'),
                ('TORQUE_OPEN', 'Моментный «Открыто»'),
                ('TORQUE_CLOSE', 'Моментный «Закрыто»'),
        ):
            fb[f'FB_{role}_SPDT'] = _cu(
                CuFeedbackSignal, f'FB_{role}_SPDT',
                name=f'{base}, SPDT', role=role, category='contact',
                form=fb_forms['DRY_SPDT'], contact_normal='CHANGEOVER',
                max_voltage=250, max_current=5)
            fb[f'FB_{role}_DPDT'] = _cu(
                CuFeedbackSignal, f'FB_{role}_DPDT',
                name=f'{base}, DPDT', role=role, category='contact',
                form=fb_forms['DRY_DPDT'], contact_normal='CHANGEOVER',
                max_voltage=250, max_current=5)
        fb.update({
            'FB_POS_POT': _cu(CuFeedbackSignal, 'FB_POS_POT',
                              name='Позиция, потенциометр', role='POSITION',
                              category='analog',
                              form=fb_forms['RES_POTENTIOMETER'],
                              resistance_kohm=1),
            'FB_POS_4_20MA_ACTIVE': _cu(CuFeedbackSignal, 'FB_POS_4_20MA_ACTIVE',
                                        name='Позиция 4-20 мА, активный',
                                        role='POSITION', category='analog',
                                        form=fb_forms['AN_4_20_ACTIVE'],
                                        wires=2),
            'FB_POS_4_20MA_PASSIVE': _cu(CuFeedbackSignal, 'FB_POS_4_20MA_PASSIVE',
                                         name='Позиция 4-20 мА, пассивный',
                                         role='POSITION', category='analog',
                                         form=fb_forms['AN_4_20_PASSIVE'],
                                         wires=2),
            'FB_POS_4_20MA_HART': _cu(CuFeedbackSignal, 'FB_POS_4_20MA_HART',
                                      name='Позиция 4-20 мА + HART',
                                      role='POSITION', category='analog',
                                      form=fb_forms['AN_4_20_PASSIVE'],
                                      hart=True, wires=2),
            'FB_TORQUE_4_20MA': _cu(CuFeedbackSignal, 'FB_TORQUE_4_20MA',
                                    name='Аналоговый момент 4-20 мА',
                                    role='TORQUE_ANALOG', category='analog',
                                    form=fb_forms['AN_4_20_ACTIVE'], wires=2),
            'FB_OVERHEAT': _cu(CuFeedbackSignal, 'FB_OVERHEAT',
                               name='Перегрев, SPST (НЗ)', role='OVERHEAT',
                               category='contact', form=fb_forms['DRY_SPST'],
                               contact_normal='NC', max_voltage=250,
                               max_current=5),
            'FB_ALARM': _cu(CuFeedbackSignal, 'FB_ALARM',
                            name='Авария (SPDT: НЗ + НО)', role='ALARM',
                            category='contact', form=fb_forms['DRY_SPDT'],
                            contact_normal='CHANGEOVER', max_voltage=250,
                            max_current=5),
            'FB_READY': _cu(CuFeedbackSignal, 'FB_READY',
                            name='Готовность (NO)', role='READY',
                            category='contact', form=fb_forms['DRY_SPST'],
                            contact_normal='NO', max_voltage=250,
                            max_current=5),
            'FB_LOCAL_REMOTE': _cu(CuFeedbackSignal, 'FB_LOCAL_REMOTE',
                                   name='Местное/удалённое (SPST НО)',
                                   role='LOCAL_REMOTE', category='contact',
                                   form=fb_forms['DRY_SPST'],
                                   contact_normal='NO', max_voltage=250,
                                   max_current=5),
            'FB_STOP': _cu(CuFeedbackSignal, 'FB_STOP',
                           name='Останов (NO)', role='STOP', category='contact',
                           form=fb_forms['DRY_SPST'], contact_normal='NO',
                           max_voltage=250, max_current=5),
            'FB_TURN_COUNTER': _cu(CuFeedbackSignal, 'FB_TURN_COUNTER',
                                   name='Счётчик оборотов (NO)',
                                   role='TURN_COUNTER', category='contact',
                                   form=fb_forms['DRY_SPST'],
                                   contact_normal='NO', max_voltage=250,
                                   max_current=Decimal('0.5')),
            'FB_SELECTOR_POSITION': _cu(
                CuFeedbackSignal, 'FB_SELECTOR_POSITION',
                name='Положение ключа-селектора', role='SELECTOR_POSITION',
                category='contact', form=fb_forms['DRY_SPDT'],
                contact_normal='CHANGEOVER', max_voltage=250, max_current=5),
            'FB_PHASE_LOSS': _cu(CuFeedbackSignal, 'FB_PHASE_LOSS',
                                 name='Авария: потеря фазы', role='PHASE_LOSS',
                                 category='contact', form=fb_forms['DRY_SPST'],
                                 contact_normal='NO', max_voltage=250,
                                 max_current=5),
        })
        proto = {
            'MODBUS_RTU': _cu(CuCommProtocol, 'MODBUS_RTU', name='Modbus RTU',
                              transport='RS485'),
            'PROFIBUS_DP': _cu(CuCommProtocol, 'PROFIBUS_DP', name='PROFIBUS DP',
                               transport='RS485'),
            'PROFINET': _cu(CuCommProtocol, 'PROFINET', name='PROFINET',
                            transport='ETHERNET'),
        }
        devices = {
            'POT_1K': CuFeedbackDevice.objects.get_or_create(
                code='POT_1K', defaults=dict(name='Потенциометр 1 кОм',
                                             kind='POSITION_SENSOR',
                                             technology='POTENTIOMETER'))[0],
            'MWG': CuFeedbackDevice.objects.get_or_create(
                code='MWG', defaults=dict(name='Датчик MWG',
                                          kind='POSITION_SENSOR',
                                          technology='MWG', contactless=True))[0],
            'THERMO': CuFeedbackDevice.objects.get_or_create(
                code='THERMO', defaults=dict(name='Термореле',
                                             kind='THERMAL_SENSOR',
                                             technology='ELECTRONIC'))[0],
            'LIMIT_MECH': CuFeedbackDevice.objects.get_or_create(
                code='LIMIT_MECH',
                defaults=dict(name='Концевые датчики, механические',
                              kind='POSITION_SENSOR',
                              technology='MECHANICAL'))[0],
        }
        devices['POT_1K'].emits.add(fb['FB_POS_POT'])
        devices['MWG'].emits.add(fb['FB_POS_4_20MA_ACTIVE'])
        devices['THERMO'].emits.add(fb['FB_OVERHEAT'])
        devices['LIMIT_MECH'].emits.add(fb['FB_END_OPEN_SPDT'])
        devices['LIMIT_MECH'].emits.add(fb['FB_END_OPEN_DPDT'])
        devices['LIMIT_MECH'].emits.add(fb['FB_END_CLOSE_SPDT'])
        devices['LIMIT_MECH'].emits.add(fb['FB_END_CLOSE_DPDT'])
        heater = {
            'NO_HEATER': _cu(CuHeaterSupply, 'NO_HEATER', name='Без обогрева'),
            'MOTOR_CIRCUIT': _cu(CuHeaterSupply, 'MOTOR_CIRCUIT',
                                 name='От цепей питания', electrical_specs='220В AC, 10 Вт'),
            'SEPARATE_LINE': _cu(CuHeaterSupply, 'SEPARATE_LINE',
                                 name='Отдельная линия', electrical_specs='24В DC, 5 Вт'),
        }
        caps = {
            'LOCAL_CONTROL': _cu(CuCapability, 'LOCAL_CONTROL',
                                 name='Местное управление'),
            'DISPLAY': _cu(CuCapability, 'DISPLAY', name='Дисплей/индикация'),
            'PST': _cu(CuCapability, 'PST', name='Частичный ход (PST)'),
            'DATALOGGER': _cu(CuCapability, 'DATALOGGER', name='Журнал данных'),
            'BLUETOOTH': _cu(CuCapability, 'BLUETOOTH', name='Bluetooth'),
            'ESD': _cu(CuCapability, 'ESD', name='Аварийный останов (ESD)'),
            'PID': _cu(CuCapability, 'PID', name='PID-регулятор'),
        }
        local_ctrl = {
            'BUTTONS': _cu(CuLocalControlType, 'BUTTONS', name='Кнопки'),
            'SELECTOR': _cu(CuLocalControlType, 'SELECTOR', name='Селекторы'),
        }
        display = {
            'LED': _cu(CuDisplayType, 'LED', name='Светодиод'),
            'LED_BLINK': _cu(CuDisplayType, 'LED_BLINK',
                             name='Мигающий светодиод'),
            'LCD': _cu(CuDisplayType, 'LCD', name='На LCD-экране'),
        }
        unit_power = {
            'SHARED_CABLE': _cu(CuUnitPowerSource, 'SHARED_CABLE',
                                name='От цепей питания привода (общий кабель)'),
            'SEPARATE_CABLE': _cu(CuUnitPowerSource, 'SEPARATE_CABLE',
                                  name='Отдельный кабель питания БУ'),
        }
        return (forms, ctl, fb, proto, devices, heater, caps, local_ctrl,
                display, unit_power)

    def _seed_cu_power(self, forms):
        locations = {
            'INTEGRATED': _cu(CuLocationOption, 'INTEGRATED', name='Встроенный'),
            'SEPARATE': _cu(CuLocationOption, 'SEPARATE', name='Навесной'),
        }
        sources = {
            'INTERNAL': _cu(CuSignalPowerSource, 'INTERNAL',
                            name='Встроенный (выдаётся приводом)',
                            internal=True,
                            description='БУ содержит собственный источник; на '
                                        'внешнюю клемму общего провода выдаётся '
                                        '+24 В.'),
            'EXTERNAL': _cu(CuSignalPowerSource, 'EXTERNAL',
                            name='Внешний (от сторонней системы)',
                            internal=False,
                            description='Цепи управления изолированы от '
                                        'внутренней логики; напряжение подаётся '
                                        'от стороннего источника.'),
        }
        # флаг internal у уже существующих записей (переход на семантику)
        for code, value in (('INTERNAL', True), ('EXTERNAL', False)):
            CuSignalPowerSource.objects.filter(code=code).update(
                internal=value)
        from params.models import PowerSupplies
        ps24 = PowerSupplies.objects.filter(code='24-DC').first() or PowerSupplies.objects.first()
        ps220 = PowerSupplies.objects.filter(code='220-AC').first() or PowerSupplies.objects.first()
        ctl_forms = forms['ctl']

        def _power(key, source, ps, name, input_form=None, polarity='NOT_APPLICABLE'):
            return CuSignalPower.objects.get_or_create(
                source=source, power_supply=ps, input_form=input_form,
                polarity=polarity,
                defaults=dict(name=name))[0]

        powers = {
            'INT_24': _power(
                'INT_24', sources['INTERNAL'], ps24,
                'Внутренний +24 В (сухой контакт)',
                input_form=ctl_forms['DRY_INPUT'],
                polarity='NOT_APPLICABLE'),
            'EXT_220': _power(
                'EXT_220', sources['EXTERNAL'], ps220,
                'Внешний 220 В AC (потенциал)',
                input_form=ctl_forms['VOLTAGE_AC'],
                polarity='NOT_APPLICABLE'),
            'EXT_24_PNP': _power(
                'EXT_24_PNP', sources['EXTERNAL'], ps24,
                'Внешний 24 В DC (PNP)',
                input_form=ctl_forms['VOLTAGE_DC'], polarity='PNP'),
            'EXT_24_NPN': _power(
                'EXT_24_NPN', sources['EXTERNAL'], ps24,
                'Внешний 24 В DC (NPN)',
                input_form=ctl_forms['VOLTAGE_DC'], polarity='NPN'),
        }
        logics = {
            'IMPULSE': _cu(CuControlLogic, 'IMPULSE', name='Импульсная',
                           has_self_holding=True),
            'CONTINUOUS': _cu(CuControlLogic, 'CONTINUOUS', name='Потенциальная'),
            'CONFIGURABLE': _cu(CuControlLogic, 'CONFIGURABLE',
                                name='Настраиваемая', has_self_holding=True),
        }
        return locations, sources, powers, logics

    # ── Узлы / слоты / опции ───────────────────────────────────────────────

    def _seed_structure(self, forms, ctl, fb, proto, devices, heater, sources,
                        powers, logics, local_ctrl, display, unit_power,
                        locations):
        # ── очистка устаревших слотов/опций/сигналов (переход на новую
        #    структуру «Дистанционное управление»; идемпотентно) ──
        obsolete_slots = ('CMD', 'SIGNAL_POWER_SOURCE', 'CONTROL_LOGIC',
                          'SIGNAL_TYPE', 'LIMIT_SWITCHES', 'WAY_SWITCHES',
                          'TORQUE_SWITCHES')
        CuMatrixEntry.objects.filter(
            slot__code__in=obsolete_slots).delete()
        CuSlot.objects.filter(code__in=obsolete_slots).delete()
        CuSlotOption.objects.filter(code__in=(
            'CMD_OCS', 'CMD_OCS_24', 'CMD_REMOTE', 'CMD_LOCK',
            'CMD_EMERGENCY', 'SP_EXT_220', 'SP_EXT_24', 'SP_INT_24',
            'LOG_IMPULSE', 'LOG_CONTINUOUS', 'LOG_CONFIGURABLE',
            'ST_DRY', 'ST_POT220', 'ST_POT24')).delete()
        # устаревшие пары контактов: слоты переименованы в понаправленные,
        # поэтому удаляем и строки матрицы, и сами опции (иначе строки
        # останутся с option=None)
        obsolete_pair_options = ('END_SPDT', 'END_DPDT', 'LIMIT_NONE',
                                 'WAY_SPDT', 'TORQUE_SPDT', 'TORQUE_DPDT',
                                 'TORQUE_NONE')
        CuMatrixEntry.objects.filter(
            option__code__in=obsolete_pair_options).delete()
        CuSlotOption.objects.filter(
            code__in=obsolete_pair_options).delete()
        # дискретные команды-справочники (напряжение ушло в схему цепей):
        # удаляем все, на которые больше не ссылаются ни опция, ни строка
        # матрицы (PROTECT не даст удалить используемые — напр. уставки)
        CuControlSignal.objects.filter(
            category='discrete', slot_options__isnull=True,
            matrix_rows__isnull=True).delete()
        # устаревшая пара «Внешний 24 В DC» без полярности (ссылки PROTECT
        # уже сняты удалением опций и строк выше)
        from params.models import PowerSupplies
        ps24 = PowerSupplies.objects.filter(code='24-DC').first()
        if ps24:
            CuSignalPower.objects.filter(
                source=sources['EXTERNAL'], power_supply=ps24,
                input_form__isnull=True).exclude(
                pk__in=[p.pk for p in powers.values()]).delete()

        sections = {
            'GENERAL': CuSectionNode.objects.get_or_create(
                code='GENERAL', defaults=dict(name='Общие параметры',
                                              sorting_order=0))[0],
            'CONTROL_SIGNALS': CuSectionNode.objects.get_or_create(
                code='CONTROL_SIGNALS', defaults=dict(name='Сигналы управления'))[0],
            'FEEDBACK': CuSectionNode.objects.get_or_create(
                code='FEEDBACK', defaults=dict(name='Обратная связь'))[0],
            'COMM': CuSectionNode.objects.get_or_create(
                code='COMM', defaults=dict(name='Связь'))[0],
            'POWER': CuSectionNode.objects.get_or_create(
                code='POWER', defaults=dict(name='Обогрев / питание'))[0],
        }
        # местная индикация: узел + вложенный узел сигналов
        ind_node = CuSectionNode.objects.get_or_create(
            code='LOCAL_INDICATION',
            defaults=dict(name='Местная индикация', sorting_order=40))[0]
        ind_signals = CuSectionNode.objects.get_or_create(
            code='IND_SIGNALS',
            defaults=dict(name='Отображаемые сигналы', parent=ind_node))[0]
        cabling = CuSectionNode.objects.get_or_create(
            code='CABLING',
            defaults=dict(name='Подключение кабелей', sorting_order=50))[0]
        # узел «Дистанционное управление»: схема цепей + состав сигналов
        cmd_inputs = CuSectionNode.objects.get_or_create(
            code='CMD_INPUTS',
            defaults=dict(name='Дистанционное управление',
                          parent=sections['CONTROL_SIGNALS'],
                          sorting_order=10))[0]

        def _slot(code, **defaults):
            return CuSlot.objects.get_or_create(code=code, defaults=defaults)[0]

        slots = {
            'control_unit': _slot('control_unit', name='Тип БУ', slot_kind='object',
                                  selection_mode='single'),
            'CU_LOCATION': _slot('CU_LOCATION', name='Размещение БУ',
                                 section=sections['GENERAL'],
                                 selection_mode='single', required=True),
            'LOCAL_CONTROL': _slot('LOCAL_CONTROL', name='Местное управление',
                                   section=sections['CONTROL_SIGNALS']),
            'CMD_WIRING': _slot('CMD_WIRING', name='Схема цепей управления',
                                section=cmd_inputs, selection_mode='single',
                                required=True),
            'CMD_OPEN': _slot('CMD_OPEN', name='Открыть', section=cmd_inputs,
                              selection_mode='single'),
            'CMD_CLOSE': _slot('CMD_CLOSE', name='Закрыть', section=cmd_inputs,
                               selection_mode='single'),
            'CMD_STOP': _slot('CMD_STOP', name='Стоп', section=cmd_inputs,
                              selection_mode='single'),
            'CMD_ESD': _slot('CMD_ESD', name='ESD (аварийная команда)',
                             section=cmd_inputs, selection_mode='single'),
            'SETPOINT': _slot('SETPOINT', name='Уставка 4-20',
                              section=sections['CONTROL_SIGNALS']),
            'LIMIT_SWITCHES_OPENED': _slot(
                'LIMIT_SWITCHES_OPENED', name='Концевые выключатели ОТКРЫТО',
                section=sections['FEEDBACK']),
            'LIMIT_SWITCHES_CLOSED': _slot(
                'LIMIT_SWITCHES_CLOSED', name='Концевые выключатели ЗАКРЫТО',
                section=sections['FEEDBACK']),
            'WAY_SWITCHES_OPEN': _slot(
                'WAY_SWITCHES_OPEN', name='Путевые выключатели ОТКРЫТО',
                section=sections['FEEDBACK']),
            'WAY_SWITCHES_CLOSED': _slot(
                'WAY_SWITCHES_CLOSED', name='Путевые выключатели ЗАКРЫТО',
                section=sections['FEEDBACK']),
            'TORQUE_SWITCHES_OPEN': _slot(
                'TORQUE_SWITCHES_OPEN', name='Моментные выключатели ОТКРЫТО',
                section=sections['FEEDBACK']),
            'TORQUE_SWITCHES_CLOSE': _slot(
                'TORQUE_SWITCHES_CLOSE', name='Моментные выключатели ЗАКРЫТО',
                section=sections['FEEDBACK']),
            'POSITION_FEEDBACK': _slot('POSITION_FEEDBACK', name='Позиционная ОС',
                                       section=sections['FEEDBACK']),
            'THERMAL_SENSOR': _slot('THERMAL_SENSOR', name='Теплозащита',
                                    section=sections['FEEDBACK']),
            'INDICATOR': _slot('INDICATOR', name='Индикация',
                               section=sections['FEEDBACK']),
            'TURN_COUNTER': _slot('TURN_COUNTER', name='Счётчик оборотов',
                                  section=sections['FEEDBACK']),
            'REMOTE_CONTROL': _slot('REMOTE_CONTROL', name='Удалённое управление',
                                    section=sections['FEEDBACK']),
            'ALARM_SIGNAL': _slot('ALARM_SIGNAL', name='Сигнал аварии',
                                  section=sections['FEEDBACK']),
            'PROTOCOL': _slot('PROTOCOL', name='Шина', section=sections['COMM']),
            'HEATER_CONTROL_UNIT': _slot('HEATER_CONTROL_UNIT', name='Обогрев БУ',
                                         section=sections['POWER']),
            'LOCAL_CONTROL_DESIGN': _slot('LOCAL_CONTROL_DESIGN',
                                          name='Дизайн органов управления',
                                          section=ind_node,
                                          selection_mode='single', required=True),
            'IND_OPEN': _slot('IND_OPEN', name='Открыто', section=ind_signals),
            'IND_CLOSED': _slot('IND_CLOSED', name='Закрыто', section=ind_signals),
            'IND_STOP': _slot('IND_STOP', name='Стоп', section=ind_signals),
            'IND_ALARM': _slot('IND_ALARM', name='Авария', section=ind_signals),
            'IND_LOCAL_REMOTE': _slot('IND_LOCAL_REMOTE',
                                      name='Местное или удалённое управление',
                                      section=ind_signals),
            'IND_RUN': _slot('IND_RUN', name='Ход', section=ind_signals),
            'IND_POSITION': _slot('IND_POSITION', name='Процент открытия',
                                  section=ind_signals),
            'CU_POWER_SUPPLY': _slot('CU_POWER_SUPPLY', name='Питание БУ',
                                     section=sections['POWER'],
                                     selection_mode='single', required=True),
            'CU_CABLE_GLANDS': _slot('CU_CABLE_GLANDS', name='Кабельные вводы БУ',
                                     section=cabling, selection_mode='single',
                                     required=True),
            'MOTOR_STARTER': _slot('MOTOR_STARTER', name='Стартер мотора',
                                   section=sections['POWER'],
                                   selection_mode='single', required=False),
        }

        def _none(code, slot, name, **kw):
            return _opt(code, slot, 'none', name=name, **kw)

        opts = {}
        # выбор БУ (опции-подтипы)
        opts['CU_BASIC'] = _opt('CU_BASIC', slots['control_unit'], 'unit',
                                encoding='N')
        opts['CU_INT'] = _opt('CU_INT', slots['control_unit'], 'unit', encoding='L')
        opts['CU_INT_MB'] = _opt('CU_INT_MB', slots['control_unit'], 'unit',
                                 encoding='M')
        opts['CU_POSI'] = _opt('CU_POSI', slots['control_unit'], 'unit',
                               encoding='P')
        opts['CU_INT_O'] = _opt('CU_INT_O', slots['control_unit'], 'unit',
                                encoding='O')
        # размещение БУ: опция = справочник CuLocationOption (kind=location)
        opts['CU_LOC_INTEGRATED'] = _opt(
            'CU_LOC_INTEGRATED', slots['CU_LOCATION'], 'location',
            location_option=locations['INTEGRATED'])
        opts['CU_LOC_SEPARATE'] = _opt(
            'CU_LOC_SEPARATE', slots['CU_LOCATION'], 'location',
            location_option=locations['SEPARATE'])
        # управление
        opts['BUTTONS'] = _none('BUTTONS', slots['LOCAL_CONTROL'], 'Кнопки')
        opts['SELECTOR'] = _none('SELECTOR', slots['LOCAL_CONTROL'], 'Селектор')
        opts['LOCAL_NONE'] = _none('LOCAL_NONE', slots['LOCAL_CONTROL'], 'Нет')
        # схема цепей управления: опция = пара источник × напряжение ×
        # форма × полярность (kind=power → CuSignalPower)
        opts['W_INT_24'] = _opt('W_INT_24', slots['CMD_WIRING'], 'power',
                                signal_power=powers['INT_24'])
        opts['W_EXT_220'] = _opt('W_EXT_220', slots['CMD_WIRING'], 'power',
                                 signal_power=powers['EXT_220'])
        opts['W_EXT_24_PNP'] = _opt('W_EXT_24_PNP', slots['CMD_WIRING'], 'power',
                                    signal_power=powers['EXT_24_PNP'])
        opts['W_EXT_24_NPN'] = _opt('W_EXT_24_NPN', slots['CMD_WIRING'], 'power',
                                    signal_power=powers['EXT_24_NPN'])
        # сигнальные слоты дистанционного управления: опция = логика работы
        # сигнала + явная опция «Отсутствие сигнала» (в основном для СТОП,
        # но доступна в каждом слоте — единообразно)
        for prefix, name in (('CMD_OPEN', 'Открыть'), ('CMD_CLOSE', 'Закрыть'),
                             ('CMD_STOP', 'Стоп'), ('CMD_ESD', 'ESD')):
            opts[f'{prefix}_IMP'] = _opt(f'{prefix}_IMP', slots[prefix], 'logic',
                                         control_logic=logics['IMPULSE'])
            opts[f'{prefix}_CONT'] = _opt(f'{prefix}_CONT', slots[prefix],
                                          'logic',
                                          control_logic=logics['CONTINUOUS'])
            opts[f'{prefix}_CONF'] = _opt(f'{prefix}_CONF', slots[prefix],
                                          'logic',
                                          control_logic=logics['CONFIGURABLE'])
            opts[f'{prefix}_NONE'] = _none(f'{prefix}_NONE', slots[prefix],
                                           'Отсутствие сигнала')
        opts['SETPOINT_4_20'] = _opt('SETPOINT_4_20', slots['SETPOINT'], 'signal',
                                     control_signal=ctl['CMD_4_20MA'])
        opts['SETPOINT_HART'] = _opt('SETPOINT_HART', slots['SETPOINT'], 'signal',
                                     control_signal=ctl['CMD_4_20MA_HART'])
        # обратная связь — понаправленные контакты, форма в коде сигнала
        opts['OPEN_SPDT'] = _opt('OPEN_SPDT', slots['LIMIT_SWITCHES_OPENED'],
                                 'signal',
                                 feedback_signal=fb['FB_END_OPEN_SPDT'],
                                 device=devices['LIMIT_MECH'],
                                 ext_encoding='E1')
        opts['OPEN_DPDT'] = _opt('OPEN_DPDT', slots['LIMIT_SWITCHES_OPENED'],
                                 'signal',
                                 feedback_signal=fb['FB_END_OPEN_DPDT'],
                                 device=devices['LIMIT_MECH'],
                                 ext_encoding='E2')
        opts['CLOSE_SPDT'] = _opt('CLOSE_SPDT', slots['LIMIT_SWITCHES_CLOSED'],
                                  'signal',
                                  feedback_signal=fb['FB_END_CLOSE_SPDT'],
                                  device=devices['LIMIT_MECH'])
        opts['CLOSE_DPDT'] = _opt('CLOSE_DPDT', slots['LIMIT_SWITCHES_CLOSED'],
                                  'signal',
                                  feedback_signal=fb['FB_END_CLOSE_DPDT'],
                                  device=devices['LIMIT_MECH'])
        opts['LIMIT_OPEN_NONE'] = _none('LIMIT_OPEN_NONE',
                                        slots['LIMIT_SWITCHES_OPENED'],
                                        'Без концевых')
        opts['LIMIT_CLOSE_NONE'] = _none('LIMIT_CLOSE_NONE',
                                         slots['LIMIT_SWITCHES_CLOSED'],
                                         'Без концевых')
        opts['WAY_OPEN_SPDT'] = _opt('WAY_OPEN_SPDT', slots['WAY_SWITCHES_OPEN'],
                                     'signal',
                                     feedback_signal=fb['FB_WAY_OPEN_SPDT'],
                                     ext_encoding='W1')
        opts['WAY_OPEN_DPDT'] = _opt('WAY_OPEN_DPDT', slots['WAY_SWITCHES_OPEN'],
                                     'signal',
                                     feedback_signal=fb['FB_WAY_OPEN_DPDT'])
        opts['WAY_CLOSE_SPDT'] = _opt('WAY_CLOSE_SPDT',
                                      slots['WAY_SWITCHES_CLOSED'], 'signal',
                                      feedback_signal=fb['FB_WAY_CLOSE_SPDT'])
        opts['WAY_CLOSE_DPDT'] = _opt('WAY_CLOSE_DPDT',
                                      slots['WAY_SWITCHES_CLOSED'], 'signal',
                                      feedback_signal=fb['FB_WAY_CLOSE_DPDT'])
        opts['WAY_OPEN_NONE'] = _none('WAY_OPEN_NONE', slots['WAY_SWITCHES_OPEN'],
                                      'Без путевых')
        opts['WAY_CLOSE_NONE'] = _none('WAY_CLOSE_NONE',
                                       slots['WAY_SWITCHES_CLOSED'],
                                       'Без путевых')
        opts['TORQUE_OPEN_SPDT'] = _opt('TORQUE_OPEN_SPDT',
                                        slots['TORQUE_SWITCHES_OPEN'],
                                        'signal',
                                        feedback_signal=fb['FB_TORQUE_OPEN_SPDT'],
                                        ext_encoding='T1')
        opts['TORQUE_OPEN_DPDT'] = _opt('TORQUE_OPEN_DPDT',
                                        slots['TORQUE_SWITCHES_OPEN'],
                                        'signal',
                                        feedback_signal=fb['FB_TORQUE_OPEN_DPDT'],
                                        ext_encoding='T2')
        opts['TORQUE_CLOSE_SPDT'] = _opt('TORQUE_CLOSE_SPDT',
                                         slots['TORQUE_SWITCHES_CLOSE'],
                                         'signal',
                                         feedback_signal=fb['FB_TORQUE_CLOSE_SPDT'])
        opts['TORQUE_CLOSE_DPDT'] = _opt('TORQUE_CLOSE_DPDT',
                                         slots['TORQUE_SWITCHES_CLOSE'],
                                         'signal',
                                         feedback_signal=fb['FB_TORQUE_CLOSE_DPDT'])
        opts['TORQUE_OPEN_NONE'] = _none('TORQUE_OPEN_NONE',
                                         slots['TORQUE_SWITCHES_OPEN'],
                                         'Без моментных')
        opts['TORQUE_CLOSE_NONE'] = _none('TORQUE_CLOSE_NONE',
                                          slots['TORQUE_SWITCHES_CLOSE'],
                                          'Без моментных')
        opts['POS_POT'] = _opt('POS_POT', slots['POSITION_FEEDBACK'], 'signal',
                               feedback_signal=fb['FB_POS_POT'],
                               device=devices['POT_1K'], ext_encoding='P')
        opts['POS_4_20_ACTIVE'] = _opt('POS_4_20_ACTIVE', slots['POSITION_FEEDBACK'],
                                       'signal', feedback_signal=fb['FB_POS_4_20MA_ACTIVE'],
                                       ext_encoding='TA')
        opts['POS_4_20_PASSIVE'] = _opt('POS_4_20_PASSIVE', slots['POSITION_FEEDBACK'],
                                        'signal', feedback_signal=fb['FB_POS_4_20MA_PASSIVE'],
                                        ext_encoding='T')
        opts['POS_HART'] = _opt('POS_HART', slots['POSITION_FEEDBACK'], 'signal',
                                feedback_signal=fb['FB_POS_4_20MA_HART'],
                                ext_encoding='TH')
        opts['POS_MWG'] = _opt('POS_MWG', slots['POSITION_FEEDBACK'], 'signal',
                               feedback_signal=fb['FB_POS_4_20MA_ACTIVE'],
                               device=devices['MWG'], ext_encoding='G')
        opts['POS_NONE'] = _none('POS_NONE', slots['POSITION_FEEDBACK'], 'Нет')
        opts['NO_SENSOR'] = _none('NO_SENSOR', slots['THERMAL_SENSOR'],
                                  'Без датчика')
        opts['OVERHEAT_NC'] = _opt('OVERHEAT_NC', slots['THERMAL_SENSOR'], 'signal',
                                   feedback_signal=fb['FB_OVERHEAT'],
                                   device=devices['THERMO'])
        opts['OVERHEAT_SPST_NC'] = _opt('OVERHEAT_SPST_NC', slots['THERMAL_SENSOR'],
                                        'signal',
                                        feedback_signal=fb['FB_OVERHEAT'],
                                        device=devices['THERMO'])
        opts['LED_SET'] = _none('LED_SET', slots['INDICATOR'], 'Светодиоды',
                                ext_encoding='D')
        opts['BLINKER'] = _none('BLINKER', slots['INDICATOR'], 'Блинкер',
                                ext_encoding='B')
        opts['LCD'] = _none('LCD', slots['INDICATOR'], 'Дисплей', ext_encoding='L')
        opts['TC_NONE'] = _none('TC_NONE', slots['TURN_COUNTER'], 'Нет')
        opts['TC_MECH'] = _none('TC_MECH', slots['TURN_COUNTER'], 'Механический',
                                ext_encoding='M')
        opts['TC_EL'] = _none('TC_EL', slots['TURN_COUNTER'], 'Электронный',
                              ext_encoding='E')
        # удалённое управление и сигнал аварии (ОС INT/O)
        opts['REMOTE_SPST_NO'] = _opt('REMOTE_SPST_NO', slots['REMOTE_CONTROL'],
                                      'signal',
                                      feedback_signal=fb['FB_LOCAL_REMOTE'])
        opts['REMOTE_NONE'] = _none('REMOTE_NONE', slots['REMOTE_CONTROL'],
                                    'Нет')
        opts['ALARM_SPDT'] = _opt('ALARM_SPDT', slots['ALARM_SIGNAL'], 'signal',
                                  feedback_signal=fb['FB_ALARM'])
        opts['ALARM_NONE'] = _none('ALARM_NONE', slots['ALARM_SIGNAL'], 'Нет')
        # связь / обогрев
        opts['MB_RTU'] = _opt('MB_RTU', slots['PROTOCOL'], 'signal',
                              protocol=proto['MODBUS_RTU'])
        opts['PB_DP'] = _opt('PB_DP', slots['PROTOCOL'], 'signal',
                             protocol=proto['PROFIBUS_DP'])
        opts['PN'] = _opt('PN', slots['PROTOCOL'], 'signal',
                          protocol=proto['PROFINET'])
        opts['H_NO'] = _opt('H_NO', slots['HEATER_CONTROL_UNIT'], 'heater',
                            heater_supply=heater['NO_HEATER'])
        opts['H_MOTOR'] = _opt('H_MOTOR', slots['HEATER_CONTROL_UNIT'], 'heater',
                               heater_supply=heater['MOTOR_CIRCUIT'],
                               ext_encoding='C')
        opts['H_SEP'] = _opt('H_SEP', slots['HEATER_CONTROL_UNIT'], 'heater',
                             heater_supply=heater['SEPARATE_LINE'],
                             ext_encoding='S')
        # местная индикация (справочники CuLocalControlType/CuDisplayType)
        opts['DESIGN_BTN'] = _opt('DESIGN_BTN', slots['LOCAL_CONTROL_DESIGN'],
                                  'local_control',
                                  local_control_type=local_ctrl['BUTTONS'])
        opts['DESIGN_SEL'] = _opt('DESIGN_SEL', slots['LOCAL_CONTROL_DESIGN'],
                                  'local_control',
                                  local_control_type=local_ctrl['SELECTOR'])
        opts['DESIGN_NONE'] = _none('DESIGN_NONE', slots['LOCAL_CONTROL_DESIGN'],
                                    'Нет')

        def _display_opt(code, slot, name, types):
            obj, _ = CuSlotOption.objects.get_or_create(
                code=code, defaults={'slot': slot, 'kind': 'display',
                                     'name': name})
            obj.display_types.set(types)
            return obj

        opts['IND_OPEN_LED'] = _display_opt('IND_OPEN_LED', slots['IND_OPEN'],
                                            'Светодиод', [display['LED']])
        opts['IND_OPEN_LCD'] = _display_opt('IND_OPEN_LCD', slots['IND_OPEN'],
                                            'На LCD-экране', [display['LCD']])
        opts['IND_CLOSED_LED'] = _display_opt('IND_CLOSED_LED', slots['IND_CLOSED'],
                                              'Светодиод', [display['LED']])
        opts['IND_CLOSED_LCD'] = _display_opt('IND_CLOSED_LCD', slots['IND_CLOSED'],
                                              'На LCD-экране', [display['LCD']])
        opts['IND_STOP_LED'] = _display_opt('IND_STOP_LED', slots['IND_STOP'],
                                            'Светодиод', [display['LED']])
        opts['IND_STOP_LCD'] = _display_opt('IND_STOP_LCD', slots['IND_STOP'],
                                            'На LCD-экране', [display['LCD']])
        opts['IND_ALARM_LED'] = _display_opt('IND_ALARM_LED', slots['IND_ALARM'],
                                             'Светодиод', [display['LED']])
        opts['IND_ALARM_LCD'] = _display_opt('IND_ALARM_LCD', slots['IND_ALARM'],
                                             'На LCD-экране', [display['LCD']])
        opts['IND_LR_LED'] = _display_opt('IND_LR_LED', slots['IND_LOCAL_REMOTE'],
                                          'Светодиод', [display['LED']])
        opts['IND_LR_LCD'] = _display_opt('IND_LR_LCD', slots['IND_LOCAL_REMOTE'],
                                          'На LCD-экране', [display['LCD']])
        opts['IND_RUN_BLINK'] = _display_opt('IND_RUN_BLINK', slots['IND_RUN'],
                                             'Только мигающий светодиод',
                                             [display['LED_BLINK']])
        opts['IND_RUN_LCD_BLINK'] = _display_opt(
            'IND_RUN_LCD_BLINK', slots['IND_RUN'],
            'На LCD + мигающий светодиод',
            [display['LCD'], display['LED_BLINK']])
        opts['IND_POS_LCD'] = _display_opt('IND_POS_LCD', slots['IND_POSITION'],
                                           'На LCD-экране', [display['LCD']])
        opts['IND_POS_NONE'] = _none('IND_POS_NONE', slots['IND_POSITION'], 'Нет')
        opts['IND_OPEN_NONE'] = _none('IND_OPEN_NONE', slots['IND_OPEN'], 'Нет')
        opts['IND_CLOSED_NONE'] = _none('IND_CLOSED_NONE', slots['IND_CLOSED'], 'Нет')
        opts['IND_STOP_NONE'] = _none('IND_STOP_NONE', slots['IND_STOP'], 'Нет')
        opts['IND_ALARM_NONE'] = _none('IND_ALARM_NONE', slots['IND_ALARM'], 'Нет')
        opts['IND_LR_NONE'] = _none('IND_LR_NONE', slots['IND_LOCAL_REMOTE'], 'Нет')
        opts['IND_RUN_NONE'] = _none('IND_RUN_NONE', slots['IND_RUN'], 'Нет')
        # питание БУ и кабельные вводы БУ
        opts['PU_SHARED'] = _opt('PU_SHARED', slots['CU_POWER_SUPPLY'],
                                 'unit_power',
                                 unit_power_source=unit_power['SHARED_CABLE'])
        opts['PU_SEPARATE'] = _opt('PU_SEPARATE', slots['CU_POWER_SUPPLY'],
                                   'unit_power',
                                   unit_power_source=unit_power['SEPARATE_CABLE'])
        # стартер мотора: физика — только 380 В; у базового БУ его нет
        opts['STARTER_BUILT_IN'] = _none('STARTER_BUILT_IN',
                                         slots['MOTOR_STARTER'],
                                         'Встроенный стартер мотора')
        opts['STARTER_NONE'] = _none('STARTER_NONE', slots['MOTOR_STARTER'],
                                     'Нет')

        def _thread(code, name, type_code, type_name, diameter=None):
            from params.models import ThreadSize, ThreadTypes
            tt, _ = ThreadTypes.objects.get_or_create(
                code=type_code, defaults=dict(name=type_name))
            ts, _ = ThreadSize.objects.get_or_create(
                code=code,
                defaults=dict(name=name, thread_type=tt,
                              thread_diameter=diameter))
            return ts

        def _gland_set_opt(opt_code, set_code, name, threads):
            """Опция вводов БУ: набор резьб (каждая резьба с количеством)."""
            from params.models import ThreadSizeSet, ThreadSizeSetItem
            tset, _ = ThreadSizeSet.objects.get_or_create(
                code=set_code, defaults=dict(name=name))
            if not tset.thread_items.exists():
                for pos, ts in enumerate(threads, start=1):
                    ThreadSizeSetItem.objects.get_or_create(
                        thread_set=tset, position=pos,
                        defaults=dict(thread_size=ts))
            opt = _opt(opt_code, slots['CU_CABLE_GLANDS'], 'cable_gland',
                       cable_gland_set=tset)
            opt.cable_gland_set = tset
            opt.save(update_fields=['cable_gland_set'])
            return opt

        opts['CG_M20'] = _gland_set_opt(
            'CG_M20', 'CU_M20', 'Одинаковая резьба M20×1,5',
            [_thread('M20', 'M20×1,5', 'METRIC', 'Метрическая', diameter=20)])
        opts['CG_M25'] = _gland_set_opt(
            'CG_M25', 'CU_M25', 'Одинаковая резьба M25×1,5',
            [_thread('M25', 'M25×1,5', 'METRIC', 'Метрическая', diameter=25)])
        opts['CG_PG16'] = _gland_set_opt(
            'CG_PG16', 'CU_PG16', 'Одинаковая резьба PG16',
            [_thread('PG16', 'PG16', 'PG', 'PG')])
        # набор вводов INT/O: 1×1½" NPT + 2×¾" NPT (из справочника резьб)
        opts['CG_NPT_112_34'] = _gland_set_opt(
            'CG_NPT_112_34', 'CU_NPT_112_34_34',
            '1×1½" NPT + 2×¾" NPT',
            [_thread('NPT_1_1_2', '1½" NPT', 'NPT', 'NPT', diameter=1.5),
             _thread('NPT_3_4', '¾" NPT', 'NPT', 'NPT', diameter=0.75),
             _thread('NPT_3_4', '¾" NPT', 'NPT', 'NPT', diameter=0.75)])
        return sections, slots, opts

    # ── Типы БУ ────────────────────────────────────────────────────────────

    def _seed_units(self, caps, ctl, fb, proto):
        from producers.models import Brands
        from params.models import ControlUnitInstalledOption

        brand = Brands.objects.filter(code='arhimed').first() or Brands.objects.first()

        def _legacy(code):
            return ControlUnitInstalledOption.objects.filter(code=code).first()

        def _unit(code, name, kind, **defaults):
            unit, _ = ControlUnit.objects.get_or_create(
                brand=brand, code=code,
                defaults=dict(name=name, kind=kind, **defaults))
            return unit

        basic = _unit(
            'basic', 'БУ базовый', ControlUnitKind.BASIC,
            legacy_cu=_legacy('basic'),
            name_template='БУ базовый {code}',
            description_template='Базовый блок управления {brand} (AOX-M): '
                                 'команды Открыть/Закрыть потенциальной '
                                 'логикой (Стоп — отсутствием сигнала), цепи '
                                 'управления от внешнего источника 220 В '
                                 '(опция: +24 В от внутреннего источника, '
                                 'сухой контакт), концевые и моментные '
                                 'выключатели, перегрев SPST (НЗ), обогрев '
                                 'отдельной линией.',
            spec_template={'Основные': {'Класс БУ': '_res_kind'},
                           'Возможности': {'Функции': '_res_capabilities'}},
        )
        basic.accepts.set([])
        basic.emits.set([fb['FB_END_OPEN_SPDT'], fb['FB_END_CLOSE_SPDT'],
                         fb['FB_TORQUE_OPEN_SPDT']])
        basic.capabilities.set([caps['LOCAL_CONTROL']])

        int_unit = _unit(
            'int-n', 'БУ INT', ControlUnitKind.INTEGRATED,
            legacy_cu=_legacy('int-n'),
            name_template='БУ INT {code}',
            description_template='Интеллектуальный блок управления {brand}: '
                                 'дисплей, настройка логики, позиционная ОС '
                                 '4-20 мА. Функции: {capabilities}.',
            spec_template={'Основные': {'Класс БУ': '_res_kind'},
                           'Связь': {'Протоколы': '_res_protocols'},
                           'Возможности': {'Функции': '_res_capabilities'}},
        )
        int_unit.accepts.set([ctl['CMD_4_20MA']])
        int_unit.emits.set([fb['FB_END_OPEN_SPDT'], fb['FB_END_CLOSE_SPDT'],
                            fb['FB_WAY_OPEN_SPDT'], fb['FB_TORQUE_OPEN_SPDT'],
                            fb['FB_POS_4_20MA_ACTIVE'], fb['FB_ALARM'],
                            fb['FB_READY'], fb['FB_OVERHEAT']])
        int_unit.capabilities.set([caps['LOCAL_CONTROL'], caps['DISPLAY'],
                                   caps['DATALOGGER'], caps['PST'],
                                   caps['BLUETOOTH'], caps['ESD']])

        int_mb = _unit(
            'int-n-mb', 'БУ INT Modbus', ControlUnitKind.INTEGRATED,
            legacy_cu=_legacy('int-n-mb'),
            name_template='БУ INT {code} (Modbus)',
            description_template='Интеллектуальный блок управления {brand} с '
                                 'шиной: {protocols}.',
            spec_template={'Основные': {'Класс БУ': '_res_kind'},
                           'Связь': {'Протоколы': '_res_protocols'},
                           'Возможности': {'Функции': '_res_capabilities'}},
        )
        int_mb.accepts.set(int_unit.accepts.all())
        int_mb.emits.set(int_unit.emits.all())
        int_mb.protocols.set([proto['MODBUS_RTU'], proto['PROFIBUS_DP']])
        int_mb.capabilities.set(int_unit.capabilities.all())

        posi = _unit(
            'posi-4-20', 'БУ позиционер 4-20', ControlUnitKind.POSITIONER,
            legacy_cu=_legacy('posi-4-20'),
            name_template='БУ позиционер {code}',
            description_template='Позиционер {brand}: уставка и обратная связь '
                                 'по петле 4-20 мА (HART).',
            spec_template={'Основные': {'Класс БУ': '_res_kind'},
                           'Возможности': {'Функции': '_res_capabilities'}},
        )
        posi.accepts.set([ctl['CMD_4_20MA_HART']])
        posi.emits.set([fb['FB_POS_4_20MA_HART']])
        posi.capabilities.set([caps['DISPLAY'], caps['PID']])

        int_o = _unit(
            'int-o', 'БУ INT/O', ControlUnitKind.INTEGRATED,
            legacy_cu=_legacy('int-o'),
            name_template='БУ INT/O {code}',
            description_template='БУ INT/O {brand}: навесной, команды '
                                 'Открыть/Закрыть (+24 В от внутреннего '
                                 'источника — сухой контакт; опция: внешние '
                                 '220 В AC), светодиодная индикация, стартер '
                                 '(380 В).',
            spec_template={'Основные': {'Класс БУ': '_res_kind'},
                           'Возможности': {'Функции': '_res_capabilities'}},
        )
        int_o.accepts.set([])
        int_o.emits.set([fb['FB_END_OPEN_SPDT'], fb['FB_END_CLOSE_SPDT'],
                         fb['FB_LOCAL_REMOTE'], fb['FB_ALARM']])
        int_o.capabilities.set([caps['LOCAL_CONTROL'], caps['DISPLAY']])

        # опции слота control_unit ссылаются на типы БУ
        CuSlotOption.objects.filter(code='CU_BASIC').update(control_unit=basic)
        CuSlotOption.objects.filter(code='CU_INT').update(control_unit=int_unit)
        CuSlotOption.objects.filter(code='CU_INT_MB').update(control_unit=int_mb)
        CuSlotOption.objects.filter(code='CU_POSI').update(control_unit=posi)
        CuSlotOption.objects.filter(code='CU_INT_O').update(control_unit=int_o)

        # устаревшие пары без формы входа (остались от прежней структуры
        # SIGNAL_POWER_SOURCE) — защищены от удаления, только пока на них
        # ссылаются опции CMD_WIRING; лишние чистим
        CuSignalPower.objects.filter(input_form__isnull=True).delete()

        # старые шаблоны спецификации ссылались на удалённый resolver
        # _res_signal_power (поле signal_power убрано из модели) — чистим,
        # иначе в спецификации остаётся пустая ячейка «Питание цепей»
        for unit in (basic, int_unit, int_mb, posi, int_o):
            spec = unit.spec_template or {}
            changed = False
            for section, fields in list(spec.items()):
                if not isinstance(fields, dict):
                    continue
                for label, path in list(fields.items()):
                    if path == '_res_signal_power':
                        del fields[label]
                        changed = True
            if changed:
                # .update() в обход TemplateMixin.save() — не перегенерируем
                # name/description при чистке шаблона
                ControlUnit.objects.filter(pk=unit.pk).update(
                    spec_template=spec)
        return {'basic': basic, 'int': int_unit, 'int_mb': int_mb, 'posi': posi,
                'int_o': int_o}

    # ── Матрица ────────────────────────────────────────────────────────────

    def _seed_matrix(self, slots, opts, cus, powers):
        from params.models import PowerSupplies
        from electric_actuators.models import ElectricActuatorModelLine

        ps380 = PowerSupplies.objects.filter(code='380-AC').first()
        ps24 = PowerSupplies.objects.filter(code='24-DC').first()
        ps220 = PowerSupplies.objects.filter(code='220-AC').first()
        ar01e = ElectricActuatorModelLine.objects.filter(code='AR01E').first()
        ar11e = ElectricActuatorModelLine.objects.filter(code='AR11E').first()
        ar21e = ElectricActuatorModelLine.objects.filter(code='AR21E').first()

        std, opt, na = 'std', 'opt', 'na'
        # профиль БУ базовый (AOX-M, AR21E): местного управления нет;
        # цепи управления — внешний источник 220 В (опция 24 В); логика
        # потенциальная (стоп — отсутствием сигнала); перегрев — SPST НЗ;
        # обогрев — отдельной линией (опция от питания привода)
        p = [
            (slots['LOCAL_CONTROL'], opts['LOCAL_NONE'], std),
            (slots['CMD_WIRING'], opts['W_EXT_220'], std),
            (slots['CMD_WIRING'], opts['W_INT_24'], opt),
            (slots['CMD_WIRING'], opts['W_EXT_24_PNP'], na),
            (slots['CMD_WIRING'], opts['W_EXT_24_NPN'], na),
            (slots['CMD_OPEN'], opts['CMD_OPEN_CONT'], std),
            (slots['CMD_OPEN'], opts['CMD_OPEN_IMP'], na),
            (slots['CMD_OPEN'], opts['CMD_OPEN_CONF'], na),
            (slots['CMD_OPEN'], opts['CMD_OPEN_NONE'], na),
            (slots['CMD_CLOSE'], opts['CMD_CLOSE_CONT'], std),
            (slots['CMD_CLOSE'], opts['CMD_CLOSE_IMP'], na),
            (slots['CMD_CLOSE'], opts['CMD_CLOSE_CONF'], na),
            (slots['CMD_CLOSE'], opts['CMD_CLOSE_NONE'], na),
            (slots['CMD_STOP'], opts['CMD_STOP_NONE'], std),
            (slots['CMD_STOP'], opts['CMD_STOP_CONT'], na),
            (slots['CMD_STOP'], opts['CMD_STOP_IMP'], na),
            (slots['CMD_STOP'], opts['CMD_STOP_CONF'], na),
            (slots['CMD_ESD'], opts['CMD_ESD_NONE'], std),
            (slots['CMD_ESD'], opts['CMD_ESD_CONT'], na),
            (slots['CMD_ESD'], opts['CMD_ESD_IMP'], na),
            (slots['CMD_ESD'], opts['CMD_ESD_CONF'], na),
            (slots['LIMIT_SWITCHES_OPENED'], opts['OPEN_SPDT'], std),
            (slots['LIMIT_SWITCHES_CLOSED'], opts['CLOSE_SPDT'], std),
            (slots['TORQUE_SWITCHES_OPEN'], opts['TORQUE_OPEN_SPDT'], std),
            (slots['TORQUE_SWITCHES_CLOSE'], opts['TORQUE_CLOSE_SPDT'], std),
            (slots['POSITION_FEEDBACK'], opts['POS_NONE'], std),
            (slots['THERMAL_SENSOR'], opts['OVERHEAT_SPST_NC'], std),
            (slots['INDICATOR'], opts['LED_SET'], std),
            (slots['TURN_COUNTER'], opts['TC_NONE'], std),
            (slots['HEATER_CONTROL_UNIT'], opts['H_SEP'], std),
            (slots['HEATER_CONTROL_UNIT'], opts['H_MOTOR'], opt),
        ]
        for slot, option, avail in p:
            _row(slot, option, cus['basic'], availability=avail)
        # явные na для базового (update_or_create обновит прежние std-строки)
        for slot_code, opt_codes in [
                ('THERMAL_SENSOR', ['NO_SENSOR', 'OVERHEAT_NC']),
                ('HEATER_CONTROL_UNIT', ['H_NO'])]:
            for oc in opt_codes:
                _row(slots[slot_code], opts[oc], cus['basic'], availability=na)
        _row(slots['LOCAL_CONTROL'], opts['BUTTONS'], cus['basic'],
             availability=na)
        _row(slots['LOCAL_CONTROL'], opts['SELECTOR'], cus['basic'],
             availability=na)

        # профиль БУ INT
        p = [
            (slots['LOCAL_CONTROL'], opts['SELECTOR'], std),
            (slots['CMD_WIRING'], opts['W_INT_24'], std),
            (slots['CMD_WIRING'], opts['W_EXT_220'], opt),
            (slots['CMD_WIRING'], opts['W_EXT_24_PNP'], na),
            (slots['CMD_WIRING'], opts['W_EXT_24_NPN'], na),
            (slots['CMD_OPEN'], opts['CMD_OPEN_CONF'], std),
            (slots['CMD_OPEN'], opts['CMD_OPEN_IMP'], opt),
            (slots['CMD_OPEN'], opts['CMD_OPEN_CONT'], opt),
            (slots['CMD_OPEN'], opts['CMD_OPEN_NONE'], na),
            (slots['CMD_CLOSE'], opts['CMD_CLOSE_CONF'], std),
            (slots['CMD_CLOSE'], opts['CMD_CLOSE_IMP'], opt),
            (slots['CMD_CLOSE'], opts['CMD_CLOSE_CONT'], opt),
            (slots['CMD_CLOSE'], opts['CMD_CLOSE_NONE'], na),
            (slots['CMD_STOP'], opts['CMD_STOP_CONF'], std),
            (slots['CMD_STOP'], opts['CMD_STOP_NONE'], opt),
            (slots['CMD_STOP'], opts['CMD_STOP_IMP'], opt),
            (slots['CMD_STOP'], opts['CMD_STOP_CONT'], opt),
            (slots['CMD_ESD'], opts['CMD_ESD_NONE'], std),
            (slots['CMD_ESD'], opts['CMD_ESD_CONF'], opt),
            (slots['CMD_ESD'], opts['CMD_ESD_CONT'], opt),
            (slots['CMD_ESD'], opts['CMD_ESD_IMP'], na),
            (slots['SETPOINT'], opts['SETPOINT_4_20'], opt),
            (slots['LIMIT_SWITCHES_OPENED'], opts['OPEN_SPDT'], std),
            (slots['LIMIT_SWITCHES_CLOSED'], opts['CLOSE_SPDT'], std),
            (slots['WAY_SWITCHES_OPEN'], opts['WAY_OPEN_SPDT'], opt),
            (slots['WAY_SWITCHES_CLOSED'], opts['WAY_CLOSE_SPDT'], opt),
            (slots['TORQUE_SWITCHES_OPEN'], opts['TORQUE_OPEN_SPDT'], std),
            (slots['TORQUE_SWITCHES_CLOSE'], opts['TORQUE_CLOSE_SPDT'], std),
            (slots['POSITION_FEEDBACK'], opts['POS_4_20_ACTIVE'], std),
            (slots['THERMAL_SENSOR'], opts['NO_SENSOR'], std),
            (slots['THERMAL_SENSOR'], opts['OVERHEAT_NC'], opt),
            (slots['INDICATOR'], opts['LCD'], std),
            (slots['TURN_COUNTER'], opts['TC_EL'], opt),
            (slots['HEATER_CONTROL_UNIT'], opts['H_NO'], std),
        ]
        rows = {}
        for slot, option, avail in p:
            rows[(slot.code, option.code)] = _row(
                slot, option, cus['int'], availability=avail)

        # пакет MWG (общий bundle; нет концевых/моментных в обе стороны)
        mwg_rows = [
            _row(slots['POSITION_FEEDBACK'], opts['POS_MWG'], cus['int'],
                 availability=opt, bundle='MWG'),
            _row(slots['LIMIT_SWITCHES_OPENED'], opts['LIMIT_OPEN_NONE'],
                 cus['int'], availability=opt, bundle='MWG'),
            _row(slots['LIMIT_SWITCHES_CLOSED'], opts['LIMIT_CLOSE_NONE'],
                 cus['int'], availability=opt, bundle='MWG'),
            _row(slots['TORQUE_SWITCHES_OPEN'], opts['TORQUE_OPEN_NONE'],
                 cus['int'], availability=opt, bundle='MWG'),
            _row(slots['TORQUE_SWITCHES_CLOSE'], opts['TORQUE_CLOSE_NONE'],
                 cus['int'], availability=opt, bundle='MWG'),
        ]
        # конфликт: MWG несовместим с моментными SPDT
        for key in (('TORQUE_SWITCHES_OPEN', 'TORQUE_OPEN_SPDT'),
                    ('TORQUE_SWITCHES_CLOSE', 'TORQUE_CLOSE_SPDT')):
            rows[key].conflicts.add(mwg_rows[0])

        # профиль БУ INT Modbus: как INT + шина
        for slot, option, avail in p:
            _row(slot, option, cus['int_mb'], availability=avail)
        _row(slots['PROTOCOL'], opts['MB_RTU'], cus['int_mb'], availability=std)
        _row(slots['PROTOCOL'], opts['PB_DP'], cus['int_mb'], availability=opt)

        # профиль БУ позиционер
        p = [
            (slots['LOCAL_CONTROL'], opts['SELECTOR'], std),
            (slots['CMD_WIRING'], opts['W_INT_24'], std),
            (slots['CMD_WIRING'], opts['W_EXT_24_PNP'], opt),
            (slots['CMD_WIRING'], opts['W_EXT_24_NPN'], na),
            (slots['CMD_WIRING'], opts['W_EXT_220'], na),
            # дискретного управления нет — управление уставкой по петле
            (slots['CMD_OPEN'], opts['CMD_OPEN_NONE'], std),
            (slots['CMD_CLOSE'], opts['CMD_CLOSE_NONE'], std),
            (slots['CMD_STOP'], opts['CMD_STOP_NONE'], std),
            (slots['CMD_ESD'], opts['CMD_ESD_NONE'], std),
            (slots['SETPOINT'], opts['SETPOINT_HART'], std),
            (slots['LIMIT_SWITCHES_OPENED'], opts['OPEN_SPDT'], std),
            (slots['LIMIT_SWITCHES_CLOSED'], opts['CLOSE_SPDT'], std),
            (slots['TORQUE_SWITCHES_OPEN'], opts['TORQUE_OPEN_SPDT'], std),
            (slots['TORQUE_SWITCHES_CLOSE'], opts['TORQUE_CLOSE_SPDT'], std),
            (slots['POSITION_FEEDBACK'], opts['POS_HART'], std),
            (slots['THERMAL_SENSOR'], opts['NO_SENSOR'], std),
            (slots['INDICATOR'], opts['LCD'], std),
            (slots['HEATER_CONTROL_UNIT'], opts['H_NO'], std),
        ]
        for slot, option, avail in p:
            _row(slot, option, cus['posi'], availability=avail)
        # «набор сигналов — опции схемы»: у позиционера дискретные команды
        # появляются только при внешней схеме 24 В DC (PNP) — строки с
        # координатой signal_power перекрывают профильные «нет сигнала»
        for slot_code, opt_code in (('CMD_OPEN', 'CMD_OPEN_CONT'),
                                    ('CMD_CLOSE', 'CMD_CLOSE_CONT')):
            _row(slots[slot_code], opts[opt_code], cus['posi'],
                 signal_power=powers['EXT_24_PNP'], availability=opt)

        # местная индикация — профили БУ
        led_lcd = {
            'IND_OPEN': ('IND_OPEN_LED', 'IND_OPEN_LCD', 'IND_OPEN_NONE'),
            'IND_CLOSED': ('IND_CLOSED_LED', 'IND_CLOSED_LCD', 'IND_CLOSED_NONE'),
            'IND_STOP': ('IND_STOP_LED', 'IND_STOP_LCD', 'IND_STOP_NONE'),
            'IND_ALARM': ('IND_ALARM_LED', 'IND_ALARM_LCD', 'IND_ALARM_NONE'),
            'IND_LOCAL_REMOTE': ('IND_LR_LED', 'IND_LR_LCD', 'IND_LR_NONE'),
        }
        # базовый БУ (AOX-M): индикация — светодиоды Открыто/Закрыто;
        # Ход — нет стандарт, блинкер опция; остальные сигналы скрыты правилами
        for slot_code, (led_opt, lcd_opt, none_opt) in led_lcd.items():
            if slot_code in ('IND_OPEN', 'IND_CLOSED'):
                _row(slots[slot_code], opts[led_opt], cus['basic'],
                     availability=std)
                _row(slots[slot_code], opts[lcd_opt], cus['basic'],
                     availability=na)
                _row(slots[slot_code], opts[none_opt], cus['basic'],
                     availability=na)
            else:  # IND_STOP/IND_ALARM/IND_LOCAL_REMOTE — скрыты
                _row(slots[slot_code], opts[none_opt], cus['basic'],
                     availability=std)
                _row(slots[slot_code], opts[led_opt], cus['basic'],
                     availability=na)
                _row(slots[slot_code], opts[lcd_opt], cus['basic'],
                     availability=na)
        _row(slots['IND_RUN'], opts['IND_RUN_NONE'], cus['basic'],
             availability=std)
        _row(slots['IND_RUN'], opts['IND_RUN_BLINK'], cus['basic'],
             availability=opt)
        _row(slots['IND_RUN'], opts['IND_RUN_LCD_BLINK'], cus['basic'],
             availability=na)
        _row(slots['IND_POSITION'], opts['IND_POS_NONE'], cus['basic'],
             availability=std)
        _row(slots['IND_POSITION'], opts['IND_POS_LCD'], cus['basic'],
             availability=na)
        _row(slots['LOCAL_CONTROL_DESIGN'], opts['DESIGN_NONE'], cus['basic'],
             availability=std)
        _row(slots['LOCAL_CONTROL_DESIGN'], opts['DESIGN_BTN'], cus['basic'],
             availability=na)
        _row(slots['LOCAL_CONTROL_DESIGN'], opts['DESIGN_SEL'], cus['basic'],
             availability=na)
        # INT / INT Modbus: оба органа управления; светодиоды стандарт,
        # LCD опция; ход — блинкер или LCD+блинкер; процент открытия — LCD
        for cu in (cus['int'], cus['int_mb']):
            for slot_code, (led_opt, lcd_opt, none_opt) in led_lcd.items():
                _row(slots[slot_code], opts[led_opt], cu, availability=std)
                _row(slots[slot_code], opts[lcd_opt], cu, availability=opt)
                _row(slots[slot_code], opts[none_opt], cu, availability=opt)
            _row(slots['LOCAL_CONTROL_DESIGN'], opts['DESIGN_SEL'], cu,
                 availability=std)
            _row(slots['LOCAL_CONTROL_DESIGN'], opts['DESIGN_BTN'], cu,
                 availability=opt)
            _row(slots['LOCAL_CONTROL_DESIGN'], opts['DESIGN_NONE'], cu,
                 availability=na)
            _row(slots['IND_RUN'], opts['IND_RUN_BLINK'], cu, availability=std)
            _row(slots['IND_RUN'], opts['IND_RUN_LCD_BLINK'], cu,
                 availability=opt)
            _row(slots['IND_RUN'], opts['IND_RUN_NONE'], cu, availability=opt)
            _row(slots['IND_POSITION'], opts['IND_POS_LCD'], cu,
                 availability=std)
            _row(slots['IND_POSITION'], opts['IND_POS_NONE'], cu,
                 availability=opt)
        # позиционер: LCD стандарт, светодиоды опция
        for slot_code, (led_opt, lcd_opt, none_opt) in led_lcd.items():
            _row(slots[slot_code], opts[lcd_opt], cus['posi'], availability=std)
            _row(slots[slot_code], opts[led_opt], cus['posi'], availability=opt)
            _row(slots[slot_code], opts[none_opt], cus['posi'], availability=opt)
        _row(slots['LOCAL_CONTROL_DESIGN'], opts['DESIGN_SEL'], cus['posi'],
             availability=std)
        _row(slots['LOCAL_CONTROL_DESIGN'], opts['DESIGN_BTN'], cus['posi'],
             availability=opt)
        _row(slots['LOCAL_CONTROL_DESIGN'], opts['DESIGN_NONE'], cus['posi'],
             availability=na)
        _row(slots['IND_RUN'], opts['IND_RUN_LCD_BLINK'], cus['posi'],
             availability=std)
        _row(slots['IND_RUN'], opts['IND_RUN_BLINK'], cus['posi'],
             availability=opt)
        _row(slots['IND_RUN'], opts['IND_RUN_NONE'], cus['posi'],
             availability=opt)
        _row(slots['IND_POSITION'], opts['IND_POS_LCD'], cus['posi'],
             availability=std)

        # профиль БУ INT/O (AOX-M, навесной): кнопки std/селектор opt;
        # команды О/С/З — активный +24 В std, внешние 220 В opt; цепи 24 В
        # встроенные; логика потенциальная; светодиоды; стартер на 380 В
        p = [
            (slots['CU_LOCATION'], opts['CU_LOC_SEPARATE'], std),
            (slots['CU_LOCATION'], opts['CU_LOC_INTEGRATED'], na),
            (slots['LOCAL_CONTROL'], opts['BUTTONS'], std),
            (slots['LOCAL_CONTROL'], opts['SELECTOR'], opt),
            (slots['LOCAL_CONTROL_DESIGN'], opts['DESIGN_BTN'], std),
            (slots['LOCAL_CONTROL_DESIGN'], opts['DESIGN_SEL'], opt),
            (slots['LIMIT_SWITCHES_OPENED'], opts['OPEN_SPDT'], std),
            (slots['LIMIT_SWITCHES_OPENED'], opts['OPEN_DPDT'], opt),
            (slots['LIMIT_SWITCHES_CLOSED'], opts['CLOSE_SPDT'], std),
            (slots['LIMIT_SWITCHES_CLOSED'], opts['CLOSE_DPDT'], opt),
            (slots['TORQUE_SWITCHES_OPEN'], opts['TORQUE_OPEN_NONE'], std),
            (slots['TORQUE_SWITCHES_CLOSE'], opts['TORQUE_CLOSE_NONE'], std),
            (slots['POSITION_FEEDBACK'], opts['POS_NONE'], std),
            (slots['THERMAL_SENSOR'], opts['NO_SENSOR'], std),
            (slots['REMOTE_CONTROL'], opts['REMOTE_SPST_NO'], std),
            (slots['REMOTE_CONTROL'], opts['REMOTE_NONE'], opt),
            (slots['ALARM_SIGNAL'], opts['ALARM_SPDT'], std),
            (slots['ALARM_SIGNAL'], opts['ALARM_NONE'], opt),
            (slots['INDICATOR'], opts['LED_SET'], std),
            (slots['TURN_COUNTER'], opts['TC_MECH'], std),
            (slots['HEATER_CONTROL_UNIT'], opts['H_NO'], std),
            (slots['HEATER_CONTROL_UNIT'], opts['H_MOTOR'], opt),
            (slots['HEATER_CONTROL_UNIT'], opts['H_SEP'], opt),
            (slots['CMD_WIRING'], opts['W_INT_24'], std),
            (slots['CMD_WIRING'], opts['W_EXT_220'], opt),
            (slots['CMD_WIRING'], opts['W_EXT_24_PNP'], na),
            (slots['CMD_WIRING'], opts['W_EXT_24_NPN'], na),
            (slots['CMD_OPEN'], opts['CMD_OPEN_CONT'], std),
            (slots['CMD_OPEN'], opts['CMD_OPEN_IMP'], na),
            (slots['CMD_OPEN'], opts['CMD_OPEN_CONF'], na),
            (slots['CMD_OPEN'], opts['CMD_OPEN_NONE'], na),
            (slots['CMD_CLOSE'], opts['CMD_CLOSE_CONT'], std),
            (slots['CMD_CLOSE'], opts['CMD_CLOSE_IMP'], na),
            (slots['CMD_CLOSE'], opts['CMD_CLOSE_CONF'], na),
            (slots['CMD_CLOSE'], opts['CMD_CLOSE_NONE'], na),
            (slots['CMD_STOP'], opts['CMD_STOP_NONE'], std),
            (slots['CMD_STOP'], opts['CMD_STOP_CONT'], opt),
            (slots['CMD_STOP'], opts['CMD_STOP_IMP'], na),
            (slots['CMD_STOP'], opts['CMD_STOP_CONF'], na),
            (slots['CMD_ESD'], opts['CMD_ESD_NONE'], std),
            (slots['CMD_ESD'], opts['CMD_ESD_CONT'], na),
            (slots['CMD_ESD'], opts['CMD_ESD_IMP'], na),
            (slots['CMD_ESD'], opts['CMD_ESD_CONF'], na),
            (slots['CU_POWER_SUPPLY'], opts['PU_SEPARATE'], std),
            (slots['CU_POWER_SUPPLY'], opts['PU_SHARED'], opt),
            (slots['CU_CABLE_GLANDS'], opts['CG_NPT_112_34'], std),
        ]
        for slot, option, avail in p:
            _row(slot, option, cus['int_o'], availability=avail)
        # индикация INT/O: светодиоды; ход — только мигающий; процент — нет
        for slot_code, (led_opt, lcd_opt, none_opt) in led_lcd.items():
            _row(slots[slot_code], opts[led_opt], cus['int_o'], availability=std)
        _row(slots['IND_RUN'], opts['IND_RUN_BLINK'], cus['int_o'],
             availability=std)
        _row(slots['IND_POSITION'], opts['IND_POS_NONE'], cus['int_o'],
             availability=std)
        # стартер INT/O — только 380 В
        if ps380:
            _row(slots['MOTOR_STARTER'], opts['STARTER_BUILT_IN'],
                 cus['int_o'], power_supply=ps380, availability=std)
            _row(slots['MOTOR_STARTER'], opts['STARTER_NONE'],
                 cus['int_o'], availability=opt)

        # питание БУ и кабельные вводы БУ: у встроенных БУ питание — от цепей
        # привода (общий кабель), отдельный кабель недоступен; резьба вводов
        # БУ — M20 стандарт (слоты у встроенных скрыты правилами)
        for cu in (cus['basic'], cus['int'], cus['int_mb'], cus['posi']):
            _row(slots['CU_LOCATION'], opts['CU_LOC_INTEGRATED'], cu,
                 availability=std)
            _row(slots['CU_LOCATION'], opts['CU_LOC_SEPARATE'], cu,
                 availability=na)
            _row(slots['CU_POWER_SUPPLY'], opts['PU_SHARED'], cu,
                 availability=std)
            _row(slots['CU_POWER_SUPPLY'], opts['PU_SEPARATE'], cu,
                 availability=na)
            _row(slots['CU_CABLE_GLANDS'], opts['CG_M20'], cu, availability=std)
            _row(slots['CU_CABLE_GLANDS'], opts['CG_M25'], cu, availability=opt)
            _row(slots['CU_CABLE_GLANDS'], opts['CG_PG16'], cu,
                 availability=opt)

        # стартер мотора: только 380 В; у базового БУ нет, у интеллектуальных
        # как правило есть (профильная строка с конкретным напряжением)
        _row(slots['MOTOR_STARTER'], opts['STARTER_NONE'], cus['basic'],
             availability=std)
        _row(slots['MOTOR_STARTER'], opts['STARTER_BUILT_IN'], cus['basic'],
             availability=na)
        if ps380:
            for cu in (cus['int'], cus['int_mb'], cus['posi']):
                _row(slots['MOTOR_STARTER'], opts['STARTER_BUILT_IN'], cu,
                     power_supply=ps380, availability=std)
                _row(slots['MOTOR_STARTER'], opts['STARTER_NONE'], cu,
                     availability=opt)

        # серийные строки слота control_unit: какой БУ доступен для серии
        if ar01e:
            _row(slots['control_unit'], opts['CU_BASIC'], None,
                 model_line=ar01e, power_supply=ps380,
                 availability=std, encoding='N')
            _row(slots['control_unit'], opts['CU_INT'], None,
                 model_line=ar01e, power_supply=ps380,
                 availability=opt, encoding='L')
            _row(slots['control_unit'], opts['CU_INT_MB'], None,
                 model_line=ar01e, power_supply=ps380,
                 availability=opt, encoding='M')
            _row(slots['control_unit'], opts['CU_POSI'], None,
                 model_line=ar01e, power_supply=ps24,
                 availability=opt, encoding='P')
            _row(slots['control_unit'], opts['CU_POSI'], None,
                 model_line=ar01e, power_supply=ps380,
                 availability=na, encoding='')
        if ar11e:
            _row(slots['control_unit'], opts['CU_INT'], None,
                 model_line=ar11e, power_supply=ps380,
                 availability=std, encoding='L')
        # AOX-M = AR21E: базовый БУ (380/220 В) и INT/O (380 В, опция)
        if ar21e:
            _row(slots['control_unit'], opts['CU_BASIC'], None,
                 model_line=ar21e, power_supply=ps380,
                 availability=std, encoding='N')
            _row(slots['control_unit'], opts['CU_INT_O'], None,
                 model_line=ar21e, power_supply=ps380,
                 availability=opt, encoding='O')
            if ps220:
                _row(slots['control_unit'], opts['CU_BASIC'], None,
                     model_line=ar21e, power_supply=ps220,
                     availability=std, encoding='N')

    # ── Правила ────────────────────────────────────────────────────────────

    def _seed_rules(self, slots, opts):
        def _rule(when_slot, target_slot, action, when_value=None,
                  action_value=None, description='', priority=0, operator='exact'):
            CuSlotRule.objects.get_or_create(
                when_slot=when_slot, target_slot=target_slot, action=action,
                description=description,
                defaults=dict(when_value=when_value, action_value=action_value,
                              priority=priority, when_operator=operator))

        # профиль БУ → доступность слотов
        _rule(slots['control_unit'], slots['PROTOCOL'], 'hide',
              when_value='CU_BASIC',
              description='Базовому БУ шину не показываем')
        _rule(slots['control_unit'], slots['SETPOINT'], 'hide',
              when_value='CU_BASIC',
              description='Базовому БУ уставку не показываем')
        for cmd_slot in ('CMD_OPEN', 'CMD_CLOSE', 'CMD_STOP', 'CMD_ESD'):
            _rule(slots['control_unit'], slots[cmd_slot], 'hide',
                  when_value='CU_POSI',
                  description='Позиционеру дискретные команды не показываем')
        _rule(slots['control_unit'], slots['PROTOCOL'], 'show',
              when_value='CU_INT_MB',
              description='БУ INT Modbus — показываем шину')
        # HART: уставка HART тянет позиционную ОС HART
        _rule(slots['SETPOINT'], slots['POSITION_FEEDBACK'], 'set_default',
              when_value='SETPOINT_HART', action_value='POS_HART',
              priority=10,
              description='Уставка HART → позиционная ОС HART по умолчанию')
        # базовому БУ (AOX-M) нет органов местного управления; из индикации —
        # светодиоды Открыто/Закрыто и блинкер-опция (Ход); стартера нет
        # (устаревшее правило удаляем — заменено циклом ниже; идемпотентность
        # при повторном сиде поверх прежних данных)
        CuSlotRule.objects.filter(
            when_slot=slots['control_unit'],
            target_slot=slots['IND_POSITION'], action='hide',
            description='Базовому БУ процент открытия не показываем',
        ).delete()
        for hidden in ('LOCAL_CONTROL', 'LOCAL_CONTROL_DESIGN', 'IND_STOP',
                       'IND_LOCAL_REMOTE', 'IND_POSITION', 'IND_ALARM',
                       'MOTOR_STARTER'):
            _rule(slots['control_unit'], slots[hidden], 'hide',
                  when_value='CU_BASIC',
                  description=f'Базовому БУ слот {hidden} не показываем')
        # встроенным БУ питание БУ и вводы БУ не показываем (вводы — у привода)
        for hidden in ('CU_POWER_SUPPLY', 'CU_CABLE_GLANDS'):
            _rule(slots['control_unit'], slots[hidden], 'hide',
                  when_value=['CU_BASIC', 'CU_INT', 'CU_INT_MB', 'CU_POSI'],
                  operator='in',
                  description=f'Встроенному БУ слот {hidden} не показываем')
