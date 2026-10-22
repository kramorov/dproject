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
from django.core.management.base import BaseCommand

from ea_control.models import (CuCapability, CuCommProtocol, CuControlLogic,
                               CuControlSignal, CuFeedbackDevice,
                               CuFeedbackSignal, CuHeaterSupply, CuLocationOption,
                               CuMatrixEntry, CuSignalForm, CuSignalPower,
                               CuSignalPowerSource, CuSignalType, CuSlot,
                               CuSlotOption, CuSlotRule, ControlUnit,
                               CuSectionNode)
from ea_control.models.control_unit import ControlUnitKind


def _cu(model, code, **defaults):
    obj, _ = model.objects.get_or_create(code=code, defaults=defaults)
    return obj


def _opt(code, slot, kind, **fields):
    obj, _ = CuSlotOption.objects.get_or_create(
        code=code, defaults={'slot': slot, 'kind': kind, **fields})
    return obj


def _row(slot, option, cu, model_line=None, power_supply=None, **fields):
    obj, _ = CuMatrixEntry.objects.get_or_create(
        slot=slot, option=option, control_unit=cu,
        model_line=model_line, power_supply=power_supply,
        defaults=fields)
    return obj


class Command(BaseCommand):
    help = 'Демо-данные ea_control: справочники, БУ, слоты, матрица, правила.'

    def handle(self, *args, **options):
        forms, ctl, fb, proto, devices, heater, caps = self._seed_dictionaries()
        locations, sources, powers, logics, stypes = self._seed_cu_power()
        sections, slots, opts = self._seed_structure(forms, ctl, fb, proto,
                                                     devices, heater, sources,
                                                     powers, logics, stypes)
        cus = self._seed_units(caps, locations, ctl, fb, proto, powers, sources)
        self._seed_matrix(slots, opts, cus)
        self._seed_rules(slots, opts)
        self.stdout.write(self.style.SUCCESS('Демо-данные ea_control готовы.'))

    # ── Справочники-копии ──────────────────────────────────────────────────

    def _seed_dictionaries(self):
        forms = {
            'DRY_SPDT': _cu(CuSignalForm, 'DRY_SPDT', name='Сухой контакт SPDT',
                            category='contact'),
            'DRY_DPDT': _cu(CuSignalForm, 'DRY_DPDT', name='Сухой контакт DPDT',
                            category='contact'),
            'AN_4_20_ACTIVE': _cu(CuSignalForm, 'AN_4_20_ACTIVE',
                                  name='Петля 4-20 мА, активная', category='analog'),
            'AN_4_20_PASSIVE': _cu(CuSignalForm, 'AN_4_20_PASSIVE',
                                   name='Петля 4-20 мА, пассивная', category='analog'),
            'DISC_AC': _cu(CuSignalForm, 'DISC_AC', name='Дискретная команда AC',
                           category='discrete'),
            'DISC_DC': _cu(CuSignalForm, 'DISC_DC', name='Дискретная команда DC',
                           category='discrete'),
            'RES_POTENTIOMETER': _cu(CuSignalForm, 'RES_POTENTIOMETER',
                                     name='Потенциометр', category='resistance'),
        }
        ctl = {
            'CMD_OCS_220AC': _cu(CuControlSignal, 'CMD_OCS_220AC',
                                 name='Команда О/С/З 220 В AC', role='CMD_OCS',
                                 category='discrete', form=forms['DISC_AC'],
                                 voltage=220, wires=3),
            'CMD_OCS_24DC': _cu(CuControlSignal, 'CMD_OCS_24DC',
                                name='Команда О/С/З 24 В DC', role='CMD_OCS',
                                category='discrete', form=forms['DISC_DC'],
                                voltage=24, wires=3),
            'CMD_REMOTE_24DC': _cu(CuControlSignal, 'CMD_REMOTE_24DC',
                                   name='Дистанционное управление 24 В DC',
                                   role='CMD_REMOTE', category='discrete',
                                   form=forms['DISC_DC'], voltage=24, wires=2),
            'CMD_LOCK_24DC': _cu(CuControlSignal, 'CMD_LOCK_24DC',
                                 name='Блокировка 24 В DC', role='CMD_LOCK',
                                 category='discrete', form=forms['DISC_DC'],
                                 voltage=24, wires=2),
            'CMD_EMERGENCY_220AC': _cu(CuControlSignal, 'CMD_EMERGENCY_220AC',
                                       name='Аварийная команда 220 В AC',
                                       role='CMD_EMERGENCY_CLOSE',
                                       category='discrete', form=forms['DISC_AC'],
                                       voltage=220, wires=2),
            'CMD_4_20MA': _cu(CuControlSignal, 'CMD_4_20MA',
                              name='Уставка положения 4-20 мА', role='CMD_4_20MA',
                              category='analog', form=forms['AN_4_20_PASSIVE'],
                              wires=2),
            'CMD_4_20MA_HART': _cu(CuControlSignal, 'CMD_4_20MA_HART',
                                   name='Уставка 4-20 мА + HART', role='CMD_4_20MA',
                                   category='analog', form=forms['AN_4_20_PASSIVE'],
                                   hart=True, wires=2),
        }
        fb = {
            'FB_END_OPEN': _cu(CuFeedbackSignal, 'FB_END_OPEN',
                               name='Конечное «Открыто»', role='END_OPEN',
                               category='contact', form=forms['DRY_SPDT'],
                               max_voltage=250, max_current=5),
            'FB_END_CLOSE': _cu(CuFeedbackSignal, 'FB_END_CLOSE',
                                name='Конечное «Закрыто»', role='END_CLOSE',
                                category='contact', form=forms['DRY_SPDT'],
                                max_voltage=250, max_current=5),
            'FB_WAY_OPEN': _cu(CuFeedbackSignal, 'FB_WAY_OPEN',
                               name='Промежуточное «Открытие»', role='WAY_OPEN',
                               category='contact', form=forms['DRY_SPDT'],
                               max_voltage=250, max_current=5),
            'FB_TORQUE_OPEN': _cu(CuFeedbackSignal, 'FB_TORQUE_OPEN',
                                  name='Моментный «Открыто»', role='TORQUE_OPEN',
                                  category='contact', form=forms['DRY_SPDT'],
                                  max_voltage=250, max_current=5),
            'FB_POS_POT': _cu(CuFeedbackSignal, 'FB_POS_POT',
                              name='Позиция, потенциометр', role='POSITION',
                              category='analog', form=forms['RES_POTENTIOMETER'],
                              resistance_kohm=1),
            'FB_POS_4_20MA_ACTIVE': _cu(CuFeedbackSignal, 'FB_POS_4_20MA_ACTIVE',
                                        name='Позиция 4-20 мА, активный',
                                        role='POSITION', category='analog',
                                        form=forms['AN_4_20_ACTIVE'], wires=2),
            'FB_POS_4_20MA_PASSIVE': _cu(CuFeedbackSignal, 'FB_POS_4_20MA_PASSIVE',
                                         name='Позиция 4-20 мА, пассивный',
                                         role='POSITION', category='analog',
                                         form=forms['AN_4_20_PASSIVE'], wires=2),
            'FB_POS_4_20MA_HART': _cu(CuFeedbackSignal, 'FB_POS_4_20MA_HART',
                                      name='Позиция 4-20 мА + HART',
                                      role='POSITION', category='analog',
                                      form=forms['AN_4_20_PASSIVE'], hart=True,
                                      wires=2),
            'FB_OVERHEAT_NC': _cu(CuFeedbackSignal, 'FB_OVERHEAT_NC',
                                  name='Перегрев (NC)', role='OVERHEAT',
                                  category='contact', form=forms['DRY_SPDT'],
                                  contact_normal='NC'),
            'FB_ALARM': _cu(CuFeedbackSignal, 'FB_ALARM',
                            name='Авария', role='ALARM', category='contact',
                            form=forms['DRY_SPDT']),
            'FB_READY_NO': _cu(CuFeedbackSignal, 'FB_READY_NO',
                               name='Готовность (NO)', role='READY',
                               category='contact', form=forms['DRY_SPDT'],
                               contact_normal='NO'),
        }
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
        }
        devices['POT_1K'].emits.add(fb['FB_POS_POT'])
        devices['MWG'].emits.add(fb['FB_POS_4_20MA_ACTIVE'])
        devices['THERMO'].emits.add(fb['FB_OVERHEAT_NC'])
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
        return forms, ctl, fb, proto, devices, heater, caps

    def _seed_cu_power(self):
        locations = {
            'INTEGRATED': _cu(CuLocationOption, 'INTEGRATED', name='Встроенный'),
            'SEPARATE': _cu(CuLocationOption, 'SEPARATE', name='Навесной'),
        }
        sources = {
            'INTERNAL': _cu(CuSignalPowerSource, 'INTERNAL',
                            name='Встроенный (выдаётся приводом)',
                            description='БУ содержит собственный источник; на '
                                        'внешнюю клемму общего провода выдаётся '
                                        '+24 В.'),
            'EXTERNAL': _cu(CuSignalPowerSource, 'EXTERNAL',
                            name='Внешний (от сторонней системы)',
                            description='Цепи управления изолированы от '
                                        'внутренней логики; напряжение подаётся '
                                        'от стороннего источника.'),
        }
        from params.models import PowerSupplies
        ps24 = PowerSupplies.objects.filter(code='24-DC').first() or PowerSupplies.objects.first()
        ps220 = PowerSupplies.objects.filter(code='220-AC').first() or PowerSupplies.objects.first()
        powers = {
            'INT_24': CuSignalPower.objects.get_or_create(
                source=sources['INTERNAL'], power_supply=ps24,
                defaults=dict(name='Встроенный 24 В DC'))[0],
            'EXT_220': CuSignalPower.objects.get_or_create(
                source=sources['EXTERNAL'], power_supply=ps220,
                defaults=dict(name='Внешний 220 В AC'))[0],
        }
        logics = {
            'IMPULSE': _cu(CuControlLogic, 'IMPULSE', name='Импульсная',
                           has_self_holding=True),
            'CONTINUOUS': _cu(CuControlLogic, 'CONTINUOUS', name='Потенциальная'),
            'CONFIGURABLE': _cu(CuControlLogic, 'CONFIGURABLE',
                                name='Настраиваемая', has_self_holding=True),
        }
        stypes = {
            'DRY': _cu(CuSignalType, 'DRY', name='Сухой контакт',
                       logic_type='active_high', voltage='24V'),
            'POT220': _cu(CuSignalType, 'POT220', name='Потенциал 220 В AC',
                          logic_type='active_high', voltage='220V'),
        }
        return locations, sources, powers, logics, stypes

    # ── Узлы / слоты / опции ───────────────────────────────────────────────

    def _seed_structure(self, forms, ctl, fb, proto, devices, heater, sources,
                        powers, logics, stypes):
        sections = {
            'CONTROL_SIGNALS': CuSectionNode.objects.get_or_create(
                code='CONTROL_SIGNALS', defaults=dict(name='Сигналы управления'))[0],
            'FEEDBACK': CuSectionNode.objects.get_or_create(
                code='FEEDBACK', defaults=dict(name='Обратная связь'))[0],
            'COMM': CuSectionNode.objects.get_or_create(
                code='COMM', defaults=dict(name='Связь'))[0],
            'POWER': CuSectionNode.objects.get_or_create(
                code='POWER', defaults=dict(name='Обогрев / питание'))[0],
        }

        def _slot(code, **defaults):
            return CuSlot.objects.get_or_create(code=code, defaults=defaults)[0]

        slots = {
            'control_unit': _slot('control_unit', name='Тип БУ', slot_kind='object',
                                  selection_mode='single'),
            'LOCAL_CONTROL': _slot('LOCAL_CONTROL', name='Местное управление',
                                   section=sections['CONTROL_SIGNALS']),
            'CMD': _slot('CMD', name='Команды', selection_mode='multi',
                         section=sections['CONTROL_SIGNALS']),
            'SETPOINT': _slot('SETPOINT', name='Уставка 4-20',
                              section=sections['CONTROL_SIGNALS']),
            'SIGNAL_POWER_SOURCE': _slot('SIGNAL_POWER_SOURCE',
                                         name='Питание цепей управления',
                                         section=sections['POWER']),
            'CONTROL_LOGIC': _slot('CONTROL_LOGIC', name='Логика работы',
                                   section=sections['CONTROL_SIGNALS']),
            'SIGNAL_TYPE': _slot('SIGNAL_TYPE', name='Тип управляющего сигнала',
                                 section=sections['CONTROL_SIGNALS']),
            'LIMIT_SWITCHES': _slot('LIMIT_SWITCHES', name='Концевые выключатели',
                                    section=sections['FEEDBACK']),
            'WAY_SWITCHES': _slot('WAY_SWITCHES', name='Путевые выключатели',
                                  section=sections['FEEDBACK']),
            'TORQUE_SWITCHES': _slot('TORQUE_SWITCHES', name='Моментные выключатели',
                                     section=sections['FEEDBACK']),
            'POSITION_FEEDBACK': _slot('POSITION_FEEDBACK', name='Позиционная ОС',
                                       section=sections['FEEDBACK']),
            'THERMAL_SENSOR': _slot('THERMAL_SENSOR', name='Теплозащита',
                                    section=sections['FEEDBACK']),
            'INDICATOR': _slot('INDICATOR', name='Индикация',
                               section=sections['FEEDBACK']),
            'TURN_COUNTER': _slot('TURN_COUNTER', name='Счётчик оборотов',
                                  section=sections['FEEDBACK']),
            'PROTOCOL': _slot('PROTOCOL', name='Шина', section=sections['COMM']),
            'HEATER_CONTROL_UNIT': _slot('HEATER_CONTROL_UNIT', name='Обогрев БУ',
                                         section=sections['POWER']),
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
        # управление
        opts['BUTTONS'] = _none('BUTTONS', slots['LOCAL_CONTROL'], 'Кнопки')
        opts['SELECTOR'] = _none('SELECTOR', slots['LOCAL_CONTROL'], 'Селектор')
        opts['LOCAL_NONE'] = _none('LOCAL_NONE', slots['LOCAL_CONTROL'], 'Нет')
        opts['CMD_OCS'] = _opt('CMD_OCS', slots['CMD'], 'signal',
                               control_signal=ctl['CMD_OCS_220AC'])
        opts['CMD_REMOTE'] = _opt('CMD_REMOTE', slots['CMD'], 'signal',
                                  control_signal=ctl['CMD_REMOTE_24DC'])
        opts['CMD_LOCK'] = _opt('CMD_LOCK', slots['CMD'], 'signal',
                                control_signal=ctl['CMD_LOCK_24DC'])
        opts['CMD_EMERGENCY'] = _opt('CMD_EMERGENCY', slots['CMD'], 'signal',
                                     control_signal=ctl['CMD_EMERGENCY_220AC'])
        opts['SETPOINT_4_20'] = _opt('SETPOINT_4_20', slots['SETPOINT'], 'signal',
                                     control_signal=ctl['CMD_4_20MA'])
        opts['SETPOINT_HART'] = _opt('SETPOINT_HART', slots['SETPOINT'], 'signal',
                                     control_signal=ctl['CMD_4_20MA_HART'])
        opts['SP_EXT_220'] = _opt('SP_EXT_220', slots['SIGNAL_POWER_SOURCE'],
                                  'power', signal_power=powers['EXT_220'])
        opts['SP_INT_24'] = _opt('SP_INT_24', slots['SIGNAL_POWER_SOURCE'],
                                 'power', signal_power=powers['INT_24'])
        opts['LOG_IMPULSE'] = _opt('LOG_IMPULSE', slots['CONTROL_LOGIC'], 'logic',
                                   control_logic=logics['IMPULSE'])
        opts['LOG_CONTINUOUS'] = _opt('LOG_CONTINUOUS', slots['CONTROL_LOGIC'],
                                      'logic', control_logic=logics['CONTINUOUS'])
        opts['LOG_CONFIGURABLE'] = _opt('LOG_CONFIGURABLE', slots['CONTROL_LOGIC'],
                                        'logic', control_logic=logics['CONFIGURABLE'])
        opts['ST_DRY'] = _opt('ST_DRY', slots['SIGNAL_TYPE'], 'signal_type',
                              signal_type=stypes['DRY'])
        opts['ST_POT220'] = _opt('ST_POT220', slots['SIGNAL_TYPE'], 'signal_type',
                                 signal_type=stypes['POT220'])
        # обратная связь
        opts['END_SPDT'] = _opt('END_SPDT', slots['LIMIT_SWITCHES'], 'pair',
                                name='Концевые SPDT', ext_encoding='E1')
        opts['END_DPDT'] = _opt('END_DPDT', slots['LIMIT_SWITCHES'], 'pair',
                                name='Концевые DPDT', ext_encoding='E2')
        opts['LIMIT_NONE'] = _none('LIMIT_NONE', slots['LIMIT_SWITCHES'],
                                   'Без концевых')
        opts['WAY_SPDT'] = _opt('WAY_SPDT', slots['WAY_SWITCHES'], 'pair',
                                name='Путевые SPDT', ext_encoding='W1')
        opts['TORQUE_SPDT'] = _opt('TORQUE_SPDT', slots['TORQUE_SWITCHES'], 'pair',
                                   name='Моментные SPDT', ext_encoding='T1')
        opts['TORQUE_DPDT'] = _opt('TORQUE_DPDT', slots['TORQUE_SWITCHES'], 'pair',
                                   name='Моментные DPDT', ext_encoding='T2')
        opts['TORQUE_NONE'] = _none('TORQUE_NONE', slots['TORQUE_SWITCHES'],
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
                                   feedback_signal=fb['FB_OVERHEAT_NC'],
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
        return sections, slots, opts

    # ── Типы БУ ────────────────────────────────────────────────────────────

    def _seed_units(self, caps, locations, ctl, fb, proto, powers, sources):
        from producers.models import Brands
        from params.models import ControlUnitInstalledOption, PowerSupplies

        brand = Brands.objects.filter(code='arhimed').first() or Brands.objects.first()
        ps380 = PowerSupplies.objects.filter(code='380-AC').first() or PowerSupplies.objects.first()
        ps24 = PowerSupplies.objects.filter(code='24-DC').first() or PowerSupplies.objects.first()

        def _legacy(code):
            return ControlUnitInstalledOption.objects.filter(code=code).first()

        def _unit(code, name, kind, **defaults):
            unit, _ = ControlUnit.objects.get_or_create(
                brand=brand, code=code,
                defaults=dict(name=name, kind=kind, **defaults))
            return unit

        basic = _unit(
            'basic', 'БУ базовый', ControlUnitKind.BASIC,
            location=locations['INTEGRATED'], control_voltage=ps380,
            signal_power=powers['EXT_220'], legacy_cu=_legacy('basic'),
            name_template='БУ базовый {code}',
            description_template='Базовый блок управления {brand}: команды '
                                 'О/С/З, концевые и моментные выключатели.',
            spec_template={'Основные': {'Класс БУ': '_res_kind',
                                        'Питание цепей': '_res_signal_power'},
                           'Возможности': {'Функции': '_res_capabilities'}},
        )
        basic.accepts.set([ctl['CMD_OCS_220AC'], ctl['CMD_EMERGENCY_220AC']])
        basic.emits.set([fb['FB_END_OPEN'], fb['FB_END_CLOSE'],
                         fb['FB_TORQUE_OPEN']])
        basic.capabilities.set([caps['LOCAL_CONTROL']])

        int_unit = _unit(
            'int-n', 'БУ INT', ControlUnitKind.INTEGRATED,
            location=locations['INTEGRATED'], control_voltage=ps380,
            signal_power=powers['INT_24'], legacy_cu=_legacy('int-n'),
            name_template='БУ INT {code}',
            description_template='Интеллектуальный блок управления {brand}: '
                                 'дисплей, настройка логики, позиционная ОС '
                                 '4-20 мА. Функции: {capabilities}.',
            spec_template={'Основные': {'Класс БУ': '_res_kind',
                                        'Питание цепей': '_res_signal_power'},
                           'Связь': {'Протоколы': '_res_protocols'},
                           'Возможности': {'Функции': '_res_capabilities'}},
        )
        int_unit.accepts.set([ctl['CMD_OCS_220AC'], ctl['CMD_REMOTE_24DC'],
                              ctl['CMD_LOCK_24DC'], ctl['CMD_4_20MA']])
        int_unit.emits.set([fb['FB_END_OPEN'], fb['FB_END_CLOSE'],
                            fb['FB_WAY_OPEN'], fb['FB_TORQUE_OPEN'],
                            fb['FB_POS_4_20MA_ACTIVE'], fb['FB_ALARM'],
                            fb['FB_READY_NO'], fb['FB_OVERHEAT_NC']])
        int_unit.capabilities.set([caps['LOCAL_CONTROL'], caps['DISPLAY'],
                                   caps['DATALOGGER'], caps['PST'],
                                   caps['BLUETOOTH'], caps['ESD']])

        int_mb = _unit(
            'int-n-mb', 'БУ INT Modbus', ControlUnitKind.INTEGRATED,
            location=locations['INTEGRATED'], control_voltage=ps380,
            signal_power=powers['INT_24'], legacy_cu=_legacy('int-n-mb'),
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
            location=locations['INTEGRATED'], control_voltage=ps24,
            signal_power=powers['INT_24'], legacy_cu=_legacy('posi-4-20'),
            name_template='БУ позиционер {code}',
            description_template='Позиционер {brand}: уставка и обратная связь '
                                 'по петле 4-20 мА (HART).',
            spec_template={'Основные': {'Класс БУ': '_res_kind',
                                        'Питание цепей': '_res_signal_power'},
                           'Возможности': {'Функции': '_res_capabilities'}},
        )
        posi.accepts.set([ctl['CMD_4_20MA_HART']])
        posi.emits.set([fb['FB_POS_4_20MA_HART']])
        posi.capabilities.set([caps['DISPLAY'], caps['PID']])

        # опции слота control_unit ссылаются на типы БУ
        CuSlotOption.objects.filter(code='CU_BASIC').update(control_unit=basic)
        CuSlotOption.objects.filter(code='CU_INT').update(control_unit=int_unit)
        CuSlotOption.objects.filter(code='CU_INT_MB').update(control_unit=int_mb)
        CuSlotOption.objects.filter(code='CU_POSI').update(control_unit=posi)
        return {'basic': basic, 'int': int_unit, 'int_mb': int_mb, 'posi': posi}

    # ── Матрица ────────────────────────────────────────────────────────────

    def _seed_matrix(self, slots, opts, cus):
        from params.models import PowerSupplies
        from electric_actuators.models import ElectricActuatorModelLine

        ps380 = PowerSupplies.objects.filter(code='380-AC').first()
        ps24 = PowerSupplies.objects.filter(code='24-DC').first()
        ar01e = ElectricActuatorModelLine.objects.filter(code='AR01E').first()
        ar11e = ElectricActuatorModelLine.objects.filter(code='AR11E').first()

        std, opt, na = 'std', 'opt', 'na'
        # профиль БУ базовый
        p = [
            (slots['LOCAL_CONTROL'], opts['BUTTONS'], std),
            (slots['CMD'], opts['CMD_OCS'], std),
            (slots['CMD'], opts['CMD_EMERGENCY'], opt),
            (slots['LIMIT_SWITCHES'], opts['END_SPDT'], std),
            (slots['TORQUE_SWITCHES'], opts['TORQUE_SPDT'], std),
            (slots['POSITION_FEEDBACK'], opts['POS_NONE'], std),
            (slots['THERMAL_SENSOR'], opts['NO_SENSOR'], std),
            (slots['INDICATOR'], opts['LED_SET'], std),
            (slots['TURN_COUNTER'], opts['TC_NONE'], std),
            (slots['HEATER_CONTROL_UNIT'], opts['H_NO'], std),
            (slots['SIGNAL_POWER_SOURCE'], opts['SP_EXT_220'], std),
            (slots['CONTROL_LOGIC'], opts['LOG_IMPULSE'], std),
            (slots['SIGNAL_TYPE'], opts['ST_POT220'], std),
        ]
        for slot, option, avail in p:
            _row(slot, option, cus['basic'], availability=avail)

        # профиль БУ INT
        p = [
            (slots['LOCAL_CONTROL'], opts['SELECTOR'], std),
            (slots['CMD'], opts['CMD_OCS'], std),
            (slots['CMD'], opts['CMD_REMOTE'], opt),
            (slots['CMD'], opts['CMD_LOCK'], opt),
            (slots['SETPOINT'], opts['SETPOINT_4_20'], opt),
            (slots['LIMIT_SWITCHES'], opts['END_SPDT'], std),
            (slots['WAY_SWITCHES'], opts['WAY_SPDT'], opt),
            (slots['TORQUE_SWITCHES'], opts['TORQUE_SPDT'], std),
            (slots['POSITION_FEEDBACK'], opts['POS_4_20_ACTIVE'], std),
            (slots['THERMAL_SENSOR'], opts['NO_SENSOR'], std),
            (slots['THERMAL_SENSOR'], opts['OVERHEAT_NC'], opt),
            (slots['INDICATOR'], opts['LCD'], std),
            (slots['TURN_COUNTER'], opts['TC_EL'], opt),
            (slots['HEATER_CONTROL_UNIT'], opts['H_NO'], std),
            (slots['SIGNAL_POWER_SOURCE'], opts['SP_INT_24'], std),
            (slots['CONTROL_LOGIC'], opts['LOG_CONFIGURABLE'], std),
            (slots['SIGNAL_TYPE'], opts['ST_DRY'], std),
        ]
        rows = {}
        for slot, option, avail in p:
            rows[(slot.code, option.code)] = _row(
                slot, option, cus['int'], availability=avail)

        # пакет MWG (три слота, общий bundle; нет концевых/моментных)
        mwg_rows = [
            _row(slots['POSITION_FEEDBACK'], opts['POS_MWG'], cus['int'],
                 availability=opt, bundle='MWG'),
            _row(slots['LIMIT_SWITCHES'], opts['LIMIT_NONE'], cus['int'],
                 availability=opt, bundle='MWG'),
            _row(slots['TORQUE_SWITCHES'], opts['TORQUE_NONE'], cus['int'],
                 availability=opt, bundle='MWG'),
        ]
        # конфликт: MWG несовместим с моментными SPDT
        torque_row = rows[('TORQUE_SWITCHES', 'TORQUE_SPDT')]
        torque_row.conflicts.add(mwg_rows[0])

        # профиль БУ INT Modbus: как INT + шина
        for slot, option, avail in p:
            _row(slot, option, cus['int_mb'], availability=avail)
        _row(slots['PROTOCOL'], opts['MB_RTU'], cus['int_mb'], availability=std)
        _row(slots['PROTOCOL'], opts['PB_DP'], cus['int_mb'], availability=opt)

        # профиль БУ позиционер
        p = [
            (slots['LOCAL_CONTROL'], opts['SELECTOR'], std),
            (slots['SETPOINT'], opts['SETPOINT_HART'], std),
            (slots['LIMIT_SWITCHES'], opts['END_SPDT'], std),
            (slots['TORQUE_SWITCHES'], opts['TORQUE_SPDT'], std),
            (slots['POSITION_FEEDBACK'], opts['POS_HART'], std),
            (slots['THERMAL_SENSOR'], opts['NO_SENSOR'], std),
            (slots['INDICATOR'], opts['LCD'], std),
            (slots['HEATER_CONTROL_UNIT'], opts['H_NO'], std),
            (slots['SIGNAL_POWER_SOURCE'], opts['SP_INT_24'], std),
            (slots['CONTROL_LOGIC'], opts['LOG_CONTINUOUS'], std),
            (slots['SIGNAL_TYPE'], opts['ST_DRY'], std),
        ]
        for slot, option, avail in p:
            _row(slot, option, cus['posi'], availability=avail)

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
        _rule(slots['control_unit'], slots['CMD'], 'hide',
              when_value='CU_POSI',
              description='Позиционеру дискретные команды не показываем')
        _rule(slots['control_unit'], slots['SIGNAL_TYPE'], 'hide',
              when_value='CU_POSI',
              description='Позиционеру тип управляющего сигнала не показываем')
        _rule(slots['control_unit'], slots['PROTOCOL'], 'show',
              when_value='CU_INT_MB',
              description='БУ INT Modbus — показываем шину')
        # HART: уставка HART тянет позиционную ОС HART
        _rule(slots['SETPOINT'], slots['POSITION_FEEDBACK'], 'set_default',
              when_value='SETPOINT_HART', action_value='POS_HART',
              priority=10,
              description='Уставка HART → позиционная ОС HART по умолчанию')
