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
    EaFeedbackDevice, EaSignalSlot,
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
            ('POT_RAW', 'Потенциометр (свой)', 'POTENTIOMETER', False),
            ('PRECISION_POT', 'Прецизионный потенциометр (AUMA)', 'POTENTIOMETER', False),
            ('TRANSMITTER_4_20', 'Трансмиттер 4-20 мА (свой)', 'POT_CONVERTER', False),
            ('RWG_4020', 'RWG 4020 (AUMA)', 'POT_CONVERTER', False),
            ('EWG_01_1', 'EWG 01.1 (AUMA)', 'HALL', True),
            ('MWG', 'MWG (AUMA)', 'MAGNETIC', True),
        ]
        for code, name, technology, contactless in devices:
            _, created = EaFeedbackDevice.objects.get_or_create(
                code=code, defaults={'name': name, 'technology': technology,
                                     'contactless': contactless})
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
            ('POSITION_FEEDBACK', 'Позиционная обратная связь'),
            ('LIMIT_SWITCHES', 'Концевые выключатели'),
            ('WAY_SWITCHES', 'Путевые выключатели'),
            ('TORQUE_SWITCHES', 'Моментные выключатели'),
            ('HEATER_ACTUATOR', 'Обогрев привода'),
            ('HEATER_CONTROL_UNIT', 'Обогрев блока управления'),
            ('PROTOCOL', 'Шина (протокол связи)'),
        ]
        for code, name in slots:
            _, created = EaSignalSlot.objects.get_or_create(
                code=code, defaults={'name': name})
            stats['slot'] += 1
            new['slot'] += int(created)

        self.stdout.write(self.style.SUCCESS(
            'Seed завершён. Всего (создано новых):'))
        for key, label in (('form', 'форм'), ('control', 'команд'), ('feedback', 'сигналов ОС'),
                           ('protocol', 'протоколов'), ('device', 'устройств'), ('slot', 'слотов')):
            self.stdout.write(f'  {label}: {stats[key]} ({new[key]} новых)')
