"""
Наполнение справочников сигналов ЭП (финал фазы 3 плана переезда).

Идемпотентная seed-команда: get_or_create по уникальному `code`, повторный запуск
не создаёт дублей. Данные — по маппингу F6 (`export_ea_signal_data`) + таблице
AOX + сверенным фактам каталогов AUMA/Rotork (разд. 10–13 отчёта):

- формы (8): сухие контакты, петля 4–20 мА (акт/пас), дискретные цепи, потенциометр;
- командные сигналы: О/С/З 220AC и 24DC, дистанционное управление, ESD (НЗ),
  уставка 4–20 (акт/пас + HART-варианты), блокировка, ручное дублирование,
  MODE, interlocks, drive enable;
- сигналы ОС: концевые/путевые/моментные (SPDT/DPDT), позиция (4–20 акт/пас/HART,
  потенциометр 0–1 кОм), перегрев (НЗ и SPDT), авария (×2), готовность, счётчик,
  аналоговый момент;
- протоколы (8): Modbus RTU/TCP, Profibus DP, Profinet, FF, Pakscan, DeviceNet,
  EtherNet/IP;
- устройства ОС (6): свои POT_RAW/TRANSMITTER_4_20 + AUMA PRECISION_POT/RWG_4020/
  EWG_01_1/MWG, эквивалентности «свой ↔ AUMA»;
- слоты (7): POSITION_FEEDBACK, LIMIT/WAY/TORQUE_SWITCHES, HEATER_ACTUATOR,
  HEATER_CONTROL_UNIT, PROTOCOL.

Использование:
    python manage.py seed_ea_signal_catalog
"""
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from electric_actuators.models import (
    EaSignalForm, EaControlSignal, EaFeedbackSignal, EaCommProtocol,
    EaFeedbackDevice, EaSignalSlot, ElectricTemperatureOption,
    EaSlotOption,
)


class Command(BaseCommand):
    help = 'Наполнение справочников сигналов ЭП (фаза 3)'

    def handle(self, *args, **options):
        stats = {'form': 0, 'control': 0, 'feedback': 0, 'protocol': 0,
                 'device': 0, 'slot': 0}
        new = {'form': 0, 'control': 0, 'feedback': 0, 'protocol': 0,
               'device': 0, 'slot': 0}

        # --- Формы ---
        forms = [
            ('DRY_SPST', 'Сухой контакт SPST', 'contact'),
            ('DRY_SPDT', 'Сухой контакт SPDT', 'contact'),
            ('DRY_DPDT', 'Сухой контакт DPDT', 'contact'),
            ('AN_4_20_ACTIVE', '4-20 мА, активный', 'analog'),
            ('AN_4_20_PASSIVE', '4-20 мА, пассивный', 'analog'),
            ('AN_0_10V_ACTIVE', '0-10 В, активный', 'analog'),
            ('AN_0_10V_PASSIVE', '0-10 В, пассивный', 'analog'),
            ('DISC_AC', 'Дискретная цепь AC', 'discrete'),
            ('DISC_DC', 'Дискретная цепь DC', 'discrete'),
            ('RES_POTENTIOMETER', 'Потенциометр (сопротивление)', 'resistance'),
        ]
        for code, name, category in forms:
            _, created = EaSignalForm.objects.get_or_create(
                code=code, defaults={'name': name, 'category': category})
            stats['form'] += 1
            new['form'] += int(created)

        def f(code):
            return EaSignalForm.objects.get(code=code)

        # --- Командные сигналы ---
        control_signals = [
            ('CMD_OCS_220AC', 'CMD_OCS', 'discrete', f('DISC_AC'), 220, 15, 2,
             'Команда Открыть/Стоп/Закрыть 220 В AC'),
            ('CMD_OCS_24DC', 'CMD_OCS', 'discrete', f('DISC_DC'), 24, 10, 2,
             'Команда Открыть/Стоп/Закрыть 24 В DC'),
            ('CMD_REMOTE_220AC', 'CMD_REMOTE', 'discrete', f('DISC_AC'), 220, 15, 2,
             'Дистанционное управление 220 В AC'),
            ('CMD_REMOTE_24DC', 'CMD_REMOTE', 'discrete', f('DISC_DC'), 24, 10, 2,
             'Дистанционное управление 24 В DC'),
            ('CMD_ESD_OPEN_24DC', 'CMD_EMERGENCY_OPEN', 'discrete', f('DISC_DC'),
             24, 10, 2, 'Аварийная команда «Открыть» 24 В DC (НЗ, контроль обрыва)'),
            ('CMD_ESD_CLOSE_24DC', 'CMD_EMERGENCY_CLOSE', 'discrete', f('DISC_DC'),
             24, 10, 2, 'Аварийная команда «Закрыть» 24 В DC (НЗ, контроль обрыва)'),
            ('CMD_POS_4_20MA_PASSIVE', 'CMD_4_20MA', 'analog', f('AN_4_20_PASSIVE'),
             None, None, 2, 'Уставка положения 4-20 мА, пассивный'),
            ('CMD_POS_4_20MA_ACTIVE', 'CMD_4_20MA', 'analog', f('AN_4_20_ACTIVE'),
             None, None, 2, 'Уставка положения 4-20 мА, активный'),
            ('CMD_LOCK_24DC', 'CMD_LOCK', 'discrete', f('DISC_DC'), 24, 10, 2,
             'Блокировка 24 В DC'),
            ('CMD_MANUAL_24DC', 'CMD_MANUAL_OVERRIDE', 'discrete', f('DISC_DC'),
             24, 10, 2, 'Ручное дублирование 24 В DC'),
            ('CMD_MODE_24DC', 'MODE', 'discrete', f('DISC_DC'), 24, 10, 2,
             'Переключение режима open-close / modulating'),
            ('CMD_INTERLOCK_OPEN_24DC', 'INTERLOCK_OPEN', 'discrete', f('DISC_DC'),
             24, 10, 2, 'Блокировка «Открыть» (interlock) 24 В DC'),
            ('CMD_INTERLOCK_CLOSE_24DC', 'INTERLOCK_CLOSE', 'discrete', f('DISC_DC'),
             24, 10, 2, 'Блокировка «Закрыть» (interlock) 24 В DC'),
            ('CMD_DRIVE_ENABLE_24DC', 'DRIVE_ENABLE', 'discrete', f('DISC_DC'),
             24, 10, 1, 'Разрешение хода (drive enable) 24 В DC'),
            # 220VAC-варианты команд (стандарт); 24DC — опция (2026-10-18)
            ('CMD_LOCK_220AC', 'CMD_LOCK', 'discrete', f('DISC_AC'), 220, 15, 2,
             'Блокировка 220 В AC'),
            ('CMD_MANUAL_220AC', 'CMD_MANUAL_OVERRIDE', 'discrete', f('DISC_AC'),
             220, 15, 2, 'Ручное дублирование 220 В AC'),
            ('CMD_MODE_220AC', 'MODE', 'discrete', f('DISC_AC'), 220, 15, 2,
             'Переключение режима 220 В AC'),
            ('CMD_INTERLOCK_OPEN_220AC', 'INTERLOCK_OPEN', 'discrete', f('DISC_AC'),
             220, 15, 2, 'Блокировка «Открыть» (interlock) 220 В AC'),
            ('CMD_INTERLOCK_CLOSE_220AC', 'INTERLOCK_CLOSE', 'discrete', f('DISC_AC'),
             220, 15, 2, 'Блокировка «Закрыть» (interlock) 220 В AC'),
            ('CMD_DRIVE_ENABLE_220AC', 'DRIVE_ENABLE', 'discrete', f('DISC_AC'),
             220, 15, 1, 'Разрешение хода (drive enable) 220 В AC'),
            ('CMD_ESD_OPEN_220AC', 'CMD_EMERGENCY_OPEN', 'discrete', f('DISC_AC'),
             220, 15, 2, 'Аварийная команда «Открыть» 220 В AC'),
            ('CMD_ESD_CLOSE_220AC', 'CMD_EMERGENCY_CLOSE', 'discrete', f('DISC_AC'),
             220, 15, 2, 'Аварийная команда «Закрыть» 220 В AC'),
            # Уставка 0-10 В (для позиционера 0-10В)
            ('CMD_POS_0_10V_PASSIVE', 'CMD_0_10V', 'analog', f('AN_0_10V_PASSIVE'),
             None, None, 2, 'Уставка положения 0-10 В, пассивный'),
            ('CMD_POS_0_10V_ACTIVE', 'CMD_0_10V', 'analog', f('AN_0_10V_ACTIVE'),
             None, None, 2, 'Уставка положения 0-10 В, активный'),
        ]
        for code, role, category, form, voltage, current, wires, name in control_signals:
            _, created = EaControlSignal.objects.get_or_create(
                code=code, defaults={
                    'role': role, 'category': category, 'form': form,
                    'voltage': voltage, 'current': current, 'wires': wires,
                    'name': name,
                })
            stats['control'] += 1
            new['control'] += int(created)

        # --- Сигналы ОС ---
        feedback_signals = [
            # (code, role, category, form_code, contact_normal, max_v, max_a, r_kohm, power, turns, wires, hart, name)
            ('FB_END_OPEN_SPDT', 'END_OPEN', 'contact', 'DRY_SPDT', 'CHANGEOVER',
             250, 5, None, None, None, 3, False, 'Конечное «Открыто», SPDT'),
            ('FB_END_CLOSE_SPDT', 'END_CLOSE', 'contact', 'DRY_SPDT', 'CHANGEOVER',
             250, 5, None, None, None, 3, False, 'Конечное «Закрыто», SPDT'),
            ('FB_END_OPEN_DPDT', 'END_OPEN', 'contact', 'DRY_DPDT', 'CHANGEOVER',
             250, 5, None, None, None, 6, False, 'Конечное «Открыто», DPDT'),
            ('FB_END_CLOSE_DPDT', 'END_CLOSE', 'contact', 'DRY_DPDT', 'CHANGEOVER',
             250, 5, None, None, None, 6, False, 'Конечное «Закрыто», DPDT'),
            ('FB_WAY_OPEN_SPDT', 'WAY_OPEN', 'contact', 'DRY_SPDT', 'CHANGEOVER',
             250, 5, None, None, None, 3, False, 'Промежуточное (открытие), SPDT'),
            ('FB_WAY_CLOSE_SPDT', 'WAY_CLOSE', 'contact', 'DRY_SPDT', 'CHANGEOVER',
             250, 5, None, None, None, 3, False, 'Промежуточное (закрытие), SPDT'),
            ('FB_WAY_OPEN_DPDT', 'WAY_OPEN', 'contact', 'DRY_DPDT', 'CHANGEOVER',
             250, 5, None, None, None, 6, False, 'Промежуточное (открытие), DPDT'),
            ('FB_WAY_CLOSE_DPDT', 'WAY_CLOSE', 'contact', 'DRY_DPDT', 'CHANGEOVER',
             250, 5, None, None, None, 6, False, 'Промежуточное (закрытие), DPDT'),
            ('FB_TORQUE_OPEN_SPDT', 'TORQUE_OPEN', 'contact', 'DRY_SPDT', 'CHANGEOVER',
             250, 5, None, None, None, 3, False, 'Моментный «Открыто», SPDT'),
            ('FB_TORQUE_CLOSE_SPDT', 'TORQUE_CLOSE', 'contact', 'DRY_SPDT', 'CHANGEOVER',
             250, 5, None, None, None, 3, False, 'Моментный «Закрыто», SPDT'),
            ('FB_TORQUE_OPEN_DPDT', 'TORQUE_OPEN', 'contact', 'DRY_DPDT', 'CHANGEOVER',
             250, 5, None, None, None, 6, False, 'Моментный «Открыто», DPDT'),
            ('FB_TORQUE_CLOSE_DPDT', 'TORQUE_CLOSE', 'contact', 'DRY_DPDT', 'CHANGEOVER',
             250, 5, None, None, None, 6, False, 'Моментный «Закрыто», DPDT'),
            ('FB_POS_4_20MA_ACTIVE', 'POSITION', 'analog', 'AN_4_20_ACTIVE', None,
             None, None, None, None, None, 2, False, 'Позиция 4-20 мА, активный'),
            ('FB_POS_4_20MA_PASSIVE', 'POSITION', 'analog', 'AN_4_20_PASSIVE', None,
             None, None, None, None, None, 2, False, 'Позиция 4-20 мА, пассивный'),
            ('FB_POS_4_20MA_ACTIVE_HART', 'POSITION', 'analog', 'AN_4_20_ACTIVE', None,
             None, None, None, None, None, 2, True, 'Позиция 4-20 мА, активный, HART'),
            ('FB_POS_4_20MA_PASSIVE_HART', 'POSITION', 'analog', 'AN_4_20_PASSIVE', None,
             None, None, None, None, None, 2, True, 'Позиция 4-20 мА, пассивный, HART'),
            ('FB_POS_POT_1K', 'POSITION', 'analog', 'RES_POTENTIOMETER', None,
             None, None, 1.0, 0.5, None, 3, False, 'Позиция, потенциометр 0-1 кОм'),
            ('FB_POS_0_10V', 'POSITION', 'analog', 'AN_0_10V_PASSIVE', None,
             None, None, None, None, None, 2, False, 'Позиция 0-10 В (трансмиттер)'),
            ('FB_OVERHEAT_NC', 'OVERHEAT', 'contact', 'DRY_SPST', 'NC',
             250, 5, None, None, None, 2, False, 'Перегрев, НЗ контакт'),
            ('FB_OVERHEAT_SPDT', 'OVERHEAT', 'contact', 'DRY_SPDT', 'CHANGEOVER',
             250, 5, None, None, None, 3, False, 'Перегрев, SPDT'),
            ('FB_ALARM_SPDT', 'ALARM', 'contact', 'DRY_SPDT', 'CHANGEOVER',
             250, 5, None, None, None, 3, False, 'Авария (1-й контакт), SPDT'),
            ('FB_ALARM2_SPDT', 'ALARM', 'contact', 'DRY_SPDT', 'CHANGEOVER',
             250, 5, None, None, None, 3, False, 'Авария (2-й контакт), SPDT'),
            ('FB_READY_NO', 'READY', 'contact', 'DRY_SPST', 'NO',
             250, 5, None, None, None, 2, False, 'Готовность, НО контакт'),
            ('FB_TURN_COUNTER_NO', 'TURN_COUNTER', 'contact', 'DRY_SPST', 'NO',
             250, 0.5, None, None, None, 2, False, 'Счётчик оборотов, НО контакт'),
            ('FB_TORQUE_4_20MA', 'TORQUE_ANALOG', 'analog', 'AN_4_20_ACTIVE', None,
             None, None, None, None, None, 2, False, 'Аналоговый момент 4-20 мА'),
            ('FB_STOP', 'STOP', 'contact', 'DRY_SPST', 'NO',
             250, 5, None, None, None, 2, False, 'Останов, сухой контакт'),
            ('FB_LOCAL_REMOTE', 'LOCAL_REMOTE', 'contact', 'DRY_SPDT', 'CHANGEOVER',
             250, 5, None, None, None, 3, False, 'Удалённое/местное управление'),
            ('FB_SELECTOR_POSITION', 'SELECTOR_POSITION', 'contact', 'DRY_SPDT',
             'CHANGEOVER', 250, 5, None, None, None, 3, False,
             'Положение ключа-селектора'),
            ('FB_PHASE_LOSS', 'PHASE_LOSS', 'contact', 'DRY_SPST', 'NO',
             250, 5, None, None, None, 2, False, 'Авария: потеря фазы'),
        ]
        for (code, role, category, form_code, cnormal, max_v, max_a, r_kohm,
             power, turns, wires, hart, name) in feedback_signals:
            _, created = EaFeedbackSignal.objects.get_or_create(
                code=code, defaults={
                    'role': role, 'category': category, 'form': f(form_code),
                    'contact_normal': cnormal, 'max_voltage': max_v,
                    'max_current': max_a, 'resistance_kohm': r_kohm,
                    'max_power_w': power, 'turns': turns, 'wires': wires,
                    'hart': hart, 'name': name,
                })
            stats['feedback'] += 1
            new['feedback'] += int(created)

        # --- Протоколы ---
        protocols = [
            ('MODBUS_RTU', 'Modbus RTU', 'rs485'),
            ('MODBUS_TCP', 'Modbus TCP', 'ethernet'),
            ('PROFIBUS_DP', 'Profibus DP', 'rs485'),
            ('PROFINET', 'Profinet', 'ethernet'),
            ('FOUNDATION_FIELDBUS', 'Foundation Fieldbus', 'h1'),
            ('PAKSCAN', 'Pakscan', 'current_loop'),
            ('DEVICENET', 'DeviceNet', 'other'),
            ('ETHERNET_IP', 'EtherNet/IP', 'ethernet'),
        ]
        for code, name, transport in protocols:
            _, created = EaCommProtocol.objects.get_or_create(
                code=code, defaults={'name': name, 'transport': transport})
            stats['protocol'] += 1
            new['protocol'] += int(created)

        # --- Устройства ОС ---
        devices = [
            ('POT_RAW', 'Потенциометр (свой)', 'POTENTIOMETER', False,
             'POSITION_SENSOR'),
            ('PRECISION_POT', 'Прецизионный потенциометр (AUMA)', 'POTENTIOMETER',
             False, 'POSITION_SENSOR'),
            ('TRANSMITTER_4_20', 'Трансмиттер 4-20 мА (свой)', 'POT_CONVERTER',
             False, 'POSITION_SENSOR'),
            ('RWG_4020', 'RWG 4020 (AUMA)', 'POT_CONVERTER', False,
             'POSITION_SENSOR'),
            ('EWG_01_1', 'EWG 01.1 (AUMA)', 'HALL', True, 'POSITION_SENSOR'),
            ('MWG', 'MWG (AUMA)', 'MAGNETIC', True, 'POSITION_SENSOR'),
            ('THERMAL_RELAY', 'Термореле (биметаллическое)', 'BIMETAL', False,
             'THERMAL_SENSOR'),
            ('PTC_THERMISTOR', 'PTC-термистор с реле оценки', 'PTC', False,
             'THERMAL_SENSOR'),
        ]
        for code, name, technology, contactless, kind in devices:
            obj, created = EaFeedbackDevice.objects.get_or_create(
                code=code, defaults={'name': name, 'technology': technology,
                                     'contactless': contactless, 'kind': kind})
            if not created and obj.kind != kind:
                obj.kind = kind
                obj.save(update_fields=['kind'])
            stats['device'] += 1
            new['device'] += int(created)

        # emits + equivalents
        pos_active = EaFeedbackSignal.objects.get(code='FB_POS_4_20MA_ACTIVE')
        pos_passive = EaFeedbackSignal.objects.get(code='FB_POS_4_20MA_PASSIVE')
        pot_1k = EaFeedbackSignal.objects.get(code='FB_POS_POT_1K')
        loop_signals = [pos_active, pos_passive]

        pot_raw = EaFeedbackDevice.objects.get(code='POT_RAW')
        pot_raw.emits.set([pot_1k])
        precision_pot = EaFeedbackDevice.objects.get(code='PRECISION_POT')
        precision_pot.emits.set([pot_1k])
        for code in ('TRANSMITTER_4_20', 'RWG_4020', 'EWG_01_1', 'MWG'):
            EaFeedbackDevice.objects.get(code=code).emits.set(loop_signals)
        transmitter = EaFeedbackDevice.objects.get(code='TRANSMITTER_4_20')
        rwg = EaFeedbackDevice.objects.get(code='RWG_4020')
        transmitter.equivalents.set([rwg])
        pot_raw.equivalents.set([precision_pot])

        # --- Слоты ---
        slots = [
            ('LOCAL_CONTROL', 'Органы местного управления'),
            ('POSITION_FEEDBACK', 'Позиционная обратная связь'),
            ('CMD', 'Команды управления'),
            ('SETPOINT', 'Уставка положения'),
            ('LIMIT_SWITCHES', 'Концевые выключатели'),
            ('WAY_SWITCHES', 'Путевые выключатели'),
            ('TORQUE_SWITCHES', 'Моментные выключатели'),
            ('THERMAL_SENSOR', 'Датчик температуры (теплозащита)'),
            ('HEATER_CONTROL_UNIT', 'Обогрев блока управления'),
            ('INDICATOR', 'Индикация'),
            ('TURN_COUNTER', 'Счётчик оборотов'),
            ('PROTOCOL', 'Шина (протокол связи)'),
        ]
        for code, name in slots:
            obj, created = EaSignalSlot.objects.get_or_create(
                code=code, defaults={'name': name, 'is_active': True})
            if not created and not obj.is_active:
                obj.is_active = True
                obj.save(update_fields=['is_active'])
            stats['slot'] += 1
            new['slot'] += int(created)
        # Обогрев привода ушёл в температурную опцию (плоская шкала LT/VLT)
        for code in ('HEATER_ACTUATOR',):
            EaSignalSlot.objects.filter(code=code).update(is_active=False)

        # --- Опции слотов (каталог для каркаса выгрузки и конфигуратора) ---
        from electric_actuators.models import EaSlotOption
        slot_opts = {
            'LOCAL_CONTROL': [
                ('BUTTONS', 'none', None, 'Кнопки Открыто/Закрыто/Стоп'),
                ('SELECTOR', 'none', None, 'Селекторы Местное/Удалённое + Открыто/Закрыто/Стоп'),
                ('NONE', 'none', None, 'Без органов управления (без БУ)'),
            ],
            'CMD': [
                ('CMD_OCS_220AC', 'control', None, None),
                ('CMD_OCS_24DC', 'control', None, None),
                ('CMD_REMOTE_220AC', 'control', None, None),
                ('CMD_REMOTE_24DC', 'control', None, None),
                ('CMD_ESD_OPEN_24DC', 'control', None, None),
                ('CMD_ESD_CLOSE_24DC', 'control', None, None),
                ('CMD_MODE_24DC', 'control', None, None),
                ('CMD_LOCK_24DC', 'control', None, None),
                ('CMD_MANUAL_24DC', 'control', None, None),
                ('CMD_INTERLOCK_OPEN_24DC', 'control', None, None),
                ('CMD_INTERLOCK_CLOSE_24DC', 'control', None, None),
                ('CMD_DRIVE_ENABLE_24DC', 'control', None, None),
                ('CMD_LOCK_220AC', 'control', None, None),
                ('CMD_MANUAL_220AC', 'control', None, None),
                ('CMD_MODE_220AC', 'control', None, None),
                ('CMD_INTERLOCK_OPEN_220AC', 'control', None, None),
                ('CMD_INTERLOCK_CLOSE_220AC', 'control', None, None),
                ('CMD_DRIVE_ENABLE_220AC', 'control', None, None),
                ('CMD_ESD_OPEN_220AC', 'control', None, None),
                ('CMD_ESD_CLOSE_220AC', 'control', None, None),
            ],
            'SETPOINT': [
                ('CMD_POS_4_20MA_ACTIVE', 'control', None, None),
                ('CMD_POS_4_20MA_PASSIVE', 'control', None, None),
                ('CMD_POS_0_10V_ACTIVE', 'control', None, None),
                ('CMD_POS_0_10V_PASSIVE', 'control', None, None),
            ],
            'LIMIT_SWITCHES': [
                ('END_SPDT', 'pair', None, 'Концевые SPDT (Откр/Закр)'),
                ('END_DPDT', 'pair', None, 'Концевые DPDT (Откр/Закр)'),
            ],
            'WAY_SWITCHES': [
                ('WAY_SPDT', 'pair', None, 'Промежуточные SPDT (Откр/Закр)'),
                ('WAY_DPDT', 'pair', None, 'Промежуточные DPDT (Откр/Закр)'),
            ],
            'TORQUE_SWITCHES': [
                ('TORQUE_SPDT', 'pair', None, 'Моментные SPDT (Откр/Закр)'),
                ('TORQUE_DPDT', 'pair', None, 'Моментные DPDT (Откр/Закр)'),
            ],
            'POSITION_FEEDBACK': [
                ('FB_POS_4_20MA_ACTIVE', 'signal', None, None),
                ('FB_POS_4_20MA_ACTIVE_HART', 'signal', None, None),
                ('FB_POS_4_20MA_PASSIVE', 'signal', None, None),
                ('FB_POS_4_20MA_PASSIVE_HART', 'signal', None, None),
                ('FB_POS_POT_1K', 'signal', None, None),
                ('FB_POS_0_10V', 'signal', None, None),
            ],
            'PROTOCOL': [
                ('MODBUS_RTU', 'protocol', None, None),
                ('MODBUS_TCP', 'protocol', None, None),
                ('PROFIBUS_DP', 'protocol', None, None),
                ('PROFINET', 'protocol', None, None),
                ('FOUNDATION_FIELDBUS', 'protocol', None, None),
                ('PAKSCAN', 'protocol', None, None),
                ('DEVICENET', 'protocol', None, None),
                ('ETHERNET_IP', 'protocol', None, None),
            ],
            'THERMAL_SENSOR': [
                ('NO_SENSOR', 'none', None, 'Нет датчика температуры'),
                ('THERMAL_NO_OUTPUT', 'none', 'THERMAL_RELAY',
                 'Датчик температуры без выхода ОС'),
                ('FB_OVERHEAT_NC', 'signal', 'THERMAL_RELAY', None),
                ('FB_OVERHEAT_SPDT', 'signal', 'THERMAL_RELAY', None),
            ],
            'HEATER_CONTROL_UNIT': [
                ('NO_HEATER', 'heater', None, 'Нет обогрева БУ'),
                ('CU_CIRCUIT', 'heater', None, 'От цепей питания БУ'),
                ('SEPARATE_LINE', 'heater', None, 'Отдельная линия'),
            ],
            'INDICATOR': [
                ('LED_SET', 'none', None,
                 'Светодиоды ОТКРЫТО/ЗАКРЫТО/ХОД/АВАРИЯ/СТОП'),
                ('BLINKER', 'none', None, 'Блинкер (мигающий светодиод)'),
                ('LED_SET_BLINKER', 'none', None, 'Светодиоды + блинкер'),
                ('LCD_POSITION', 'none', None, 'LCD-индикация позиции'),
                ('LCD_BLINKER', 'none', None, 'LCD + блинкер'),
            ],
            'TURN_COUNTER': [
                ('NONE', 'none', None, 'Без счётчика оборотов'),
                ('MECH', 'none', None, 'Механический счётчик'),
                ('ELECTRONIC', 'none', None, 'Электронный счётчик (в БУ)'),
                ('MECH_ELEC', 'none', None, 'Механический + электронный'),
                ('MECH_FB', 'none', None, 'Механический с ОС от него'),
                ('MECH_ELEC_FB', 'none', None,
                 'Механический + электронный, ОС от механического'),
            ],
        }
        slot_opt_stats = {'total': 0, 'new': 0}
        for slot_code, opts in slot_opts.items():
            slot = EaSignalSlot.objects.get(code=slot_code)
            for code, kind, device_code, name in opts:
                defaults = {'slot': slot, 'kind': kind}
                if kind == 'control':
                    defaults['control_signal'] = EaControlSignal.objects.get(
                        code=code)
                elif kind == 'protocol':
                    defaults['protocol'] = EaCommProtocol.objects.get(code=code)
                elif kind == 'signal':
                    defaults['feedback_signal'] = EaFeedbackSignal.objects.get(
                        code=code)
                elif kind == 'heater':
                    from params.models import ActuatorHeaterSupply
                    defaults['heater_supply'] = (
                        ActuatorHeaterSupply.objects.get(code=code))
                if device_code:
                    defaults['device'] = EaFeedbackDevice.objects.get(
                        code=device_code)
                if name:
                    defaults['name'] = name
                _, created = EaSlotOption.objects.get_or_create(
                    code=f'{slot_code}:{code}', defaults=defaults)
                slot_opt_stats['total'] += 1
                slot_opt_stats['new'] += int(created)
        self.stdout.write(
            f'Опции слотов: {slot_opt_stats["total"]} '
            f'({slot_opt_stats["new"]} новых)')

        self.stdout.write(self.style.SUCCESS(
            'Seed завершён. Всего (создано новых):'))
        for key, label in (('form', 'форм'), ('control', 'команд'), ('feedback', 'сигналов ОС'),
                           ('protocol', 'протоколов'), ('device', 'устройств'), ('slot', 'слотов')):
            self.stdout.write(f'  {label}: {stats[key]} ({new[key]} новых)')

        # --- Питание обогрева БУ (новое значение) ---
        from params.models import ActuatorHeaterSupply
        hs, created = ActuatorHeaterSupply.objects.get_or_create(
            code='CU_CIRCUIT',
            defaults={'name': 'От цепей питания блока управления'})
        self.stdout.write(f'ActuatorHeaterSupply CU_CIRCUIT: '
                          f'{"создано" if created else "уже есть"}')

        # --- Температурные опции: code + heater_supply + MOTOR_CIRCUIT-варианты ---
        temp_backfilled = 0
        temp_created = 0
        for temp in ElectricTemperatureOption.objects.all().select_related(
                'model_line'):
            name = temp.name or ''
            if not temp.code:
                temp.code = ('STD' if 'Стандарт' in name or 'стандарт' in name
                             else 'VLT' if 'VLT' in name
                             else 'LT' if 'LT' in name else '')
            if 'LT' in name and 'VLT' not in name:
                temp.code = 'LT'
            elif 'VLT' in name:
                temp.code = 'VLT'
            if not temp.heater_supply_id:
                temp.heater_supply = (
                    ActuatorHeaterSupply.objects.get(code='NO_HEATER')
                    if temp.code == 'STD'
                    else ActuatorHeaterSupply.objects.get(code='SEPARATE_LINE'))
            temp.save()
            temp_backfilled += 1
            # LT/VLT: добавить вариант «от мотора» (opt), если нет
            if temp.code in ('LT', 'VLT') and temp.heater_supply_id:
                motor = ActuatorHeaterSupply.objects.get(code='MOTOR_CIRCUIT')
                if not ElectricTemperatureOption.objects.filter(
                        model_line=temp.model_line, code=temp.code,
                        heater_supply=motor).exists():
                    ElectricTemperatureOption.objects.create(
                        model_line=temp.model_line,
                        work_temp_min=temp.work_temp_min,
                        work_temp_max=temp.work_temp_max,
                        code=temp.code, heater_supply=motor,
                        is_default=False, is_active=temp.is_active)
                    temp_created += 1
        self.stdout.write(
            f'Температурные опции: бэкфилл {temp_backfilled}, '
            f'MOTOR_CIRCUIT-вариантов создано {temp_created}')
