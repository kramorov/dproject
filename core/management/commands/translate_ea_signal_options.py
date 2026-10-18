"""Заполняет en/cn переводы сигнальных справочников ЭП (конструктор, фаза 9).

Паттерн БКВ (translate_signal_roles_and_sensors): идемпотентная команда,
словари keyed by code / точная ru-строка; пишет только en/cn в ``name_i18n``
(ru синхронизируется миксинами при save). Коды и служебные обозначения
(«SPDT», «DPDT», «LCD», «HART», «4-20 мА») не переводятся.

Модели:
    electric_actuators.EaSignalSlot         — слоты матрицы (12)
    electric_actuators.EaSlotOption         — варианты опций слотов (с ru-именами)
    electric_actuators.EaSignalMatrixEntry  — строки матрицы (keyed by ru-имя)
    electric_actuators.EaFeedbackSignal     — сигналы ОС (30)
    electric_actuators.EaControlSignal      — команды управления (24)
    params.ActuatorHeaterSupply             — питание обогрева (4)
    params.ControlUnitInstalledOption       — варианты БУ -q/-nq (8)
    params.SafetyPositionOption             — nc-no-fl (1)

Идемпотентна; ``--force`` — перезаписать существующие en/cn.
"""
from django.core.management.base import BaseCommand
from django.apps import apps

# Код слота → (en, cn)
SLOTS = {
    'CMD': ('Control commands', '控制命令'),
    'HEATER_CONTROL_UNIT': ('Control unit heater', '控制单元加热'),
    'INDICATOR': ('Indication', '指示'),
    'LIMIT_SWITCHES': ('Limit switches', '限位开关'),
    'LOCAL_CONTROL': ('Local controls', '本地控制'),
    'POSITION_FEEDBACK': ('Position feedback', '位置反馈'),
    'PROTOCOL': ('Bus (communication protocol)', '总线（通信协议）'),
    'SETPOINT': ('Position setpoint', '位置设定'),
    'THERMAL_SENSOR': ('Temperature sensor (thermal protection)', '温度传感器（热保护）'),
    'TORQUE_SWITCHES': ('Torque switches', '力矩开关'),
    'TURN_COUNTER': ('Turn counter', '圈数计数器'),
    'WAY_SWITCHES': ('Intermediate position switches', '中间位置开关'),
}

# Код варианта опции слота → (en, cn) — только для вариантов с собственным ru-именем
SLOT_OPTIONS = {
    'CMD:NONE': ('No control commands', '无控制命令'),
    'HEATER_CONTROL_UNIT:NO_HEATER': ('No CU heater', '无控制单元加热'),
    'HEATER_CONTROL_UNIT:CU_CIRCUIT': ('From CU power circuits', '来自控制单元电源回路'),
    'HEATER_CONTROL_UNIT:SEPARATE_LINE': ('Separate line', '独立线路'),
    'INDICATOR:LED_SET': ('LEDs OPEN/CLOSED/RUN/ALARM/STOP', 'LED 打开/关闭/运行/报警/停止'),
    'INDICATOR:BLINKER': ('Blinker (flashing LED)', '闪烁指示灯'),
    'INDICATOR:LED_SET_BLINKER': ('LEDs + blinker', 'LED + 闪烁指示灯'),
    'INDICATOR:LCD_POSITION': ('LCD position indication', 'LCD 位置指示'),
    'INDICATOR:LCD_BLINKER': ('LCD + blinker', 'LCD + 闪烁指示灯'),
    'INDICATOR:NONE': ('No indicator', '无指示器'),
    'LIMIT_SWITCHES:END_SPDT': ('Limit SPDT (Open/Close)', '限位 SPDT（开/关）'),
    'LIMIT_SWITCHES:END_DPDT': ('Limit DPDT (Open/Close)', '限位 DPDT（开/关）'),
    'LOCAL_CONTROL:BUTTONS': ('Pushbuttons Open/Close/Stop', '按钮 开/关/停'),
    'LOCAL_CONTROL:SELECTOR': ('Selectors Local/Remote + Open/Close/Stop',
                               '选择开关 本地/远程 + 开/关/停'),
    'LOCAL_CONTROL:NONE': ('No local controls (no CU)', '无本地控制（无控制单元）'),
    'POSITION_FEEDBACK:NONE': ('No position feedback', '无位置反馈'),
    'PROTOCOL:NONE': ('No bus', '无总线'),
    'SETPOINT:NONE': ('No setpoint', '无设定值'),
    'THERMAL_SENSOR:NO_SENSOR': ('No temperature sensor', '无温度传感器'),
    'THERMAL_SENSOR:THERMAL_NO_OUTPUT': ('Temperature sensor without feedback output',
                                         '温度传感器，无反馈输出'),
    'THERMAL_SENSOR:FB_OVERHEAT_NC': ('Thermal protection, NC contact', '热保护，常闭触点'),
    'THERMAL_SENSOR:FB_OVERHEAT_SPDT': ('Thermal protection, changeover contact (SPDT)',
                                        '热保护，转换触点（SPDT）'),
    'TORQUE_SWITCHES:TORQUE_SPDT': ('Torque SPDT (Open/Close)', '力矩 SPDT（开/关）'),
    'TORQUE_SWITCHES:TORQUE_DPDT': ('Torque DPDT (Open/Close)', '力矩 DPDT（开/关）'),
    'TORQUE_SWITCHES:FB_TORQUE_4_20MA': ('Torque signal 4-20 mA', '力矩信号 4-20 mA'),
    'TURN_COUNTER:NONE': ('No turn counter', '无圈数计数器'),
    'TURN_COUNTER:MECH': ('Mechanical counter', '机械计数器'),
    'TURN_COUNTER:ELECTRONIC': ('Electronic counter (in CU)', '电子计数器（控制单元内）'),
    'TURN_COUNTER:MECH_ELEC': ('Mechanical + electronic', '机械 + 电子'),
    'TURN_COUNTER:MECH_FB': ('Mechanical with feedback', '机械，带反馈'),
    'TURN_COUNTER:MECH_ELEC_FB': ('Mechanical + electronic, feedback from mechanical',
                                  '机械 + 电子，机械反馈'),
    'WAY_SWITCHES:WAY_SPDT': ('Intermediate SPDT (Open/Close)', '中间 SPDT（开/关）'),
    'WAY_SWITCHES:WAY_DPDT': ('Intermediate DPDT (Open/Close)', '中间 DPDT（开/关）'),
}

# Точное ru-имя строки матрицы → (en, cn)
MATRIX_NAMES = {
    'LCD + блинкер': ('LCD + blinker', 'LCD + 闪烁指示灯'),
    'LCD-индикация позиции': ('LCD position indication', 'LCD 位置指示'),
    'Без органов управления (без БУ)': ('No local controls (no CU)', '无本地控制（无控制单元）'),
    'Блинкер (мигающий светодиод)': ('Blinker (flashing LED)', '闪烁指示灯'),
    'Кнопки Открыто/Закрыто/Стоп': ('Pushbuttons Open/Close/Stop', '按钮 开/关/停'),
    'Концевые DPDT (Откр/Закр)': ('Limit DPDT (Open/Close)', '限位 DPDT（开/关）'),
    'Концевые SPDT (Откр/Закр)': ('Limit SPDT (Open/Close)', '限位 SPDT（开/关）'),
    'Механический счётчик': ('Mechanical counter', '机械计数器'),
    'Моментные DPDT (Откр/Закр)': ('Torque DPDT (Open/Close)', '力矩 DPDT（开/关）'),
    'Моментные SPDT (Откр/Закр)': ('Torque SPDT (Open/Close)', '力矩 SPDT（开/关）'),
    'Моментный сигнал 4-20 мА': ('Torque signal 4-20 mA', '力矩信号 4-20 mA'),
    'От цепей питания БУ': ('From CU power circuits', '来自控制单元电源回路'),
    'Отдельная линия': ('Separate line', '独立线路'),
    'Промежуточные DPDT (Откр/Закр)': ('Intermediate DPDT (Open/Close)', '中间 DPDT（开/关）'),
    'Промежуточные SPDT (Откр/Закр)': ('Intermediate SPDT (Open/Close)', '中间 SPDT（开/关）'),
    'Светодиоды + блинкер': ('LEDs + blinker', 'LED + 闪烁指示灯'),
    'Светодиоды ОТКРЫТО/ЗАКРЫТО/ХОД/АВАРИЯ/СТОП': ('LEDs OPEN/CLOSED/RUN/ALARM/STOP',
                                               'LED 打开/关闭/运行/报警/停止'),
    'Селекторы Местное/Удалённое + Открыто/Закрыто/Стоп': (
        'Selectors Local/Remote + Open/Close/Stop', '选择开关 本地/远程 + 开/关/停'),
    'Теплозащита, НЗ контакт': ('Thermal protection, NC contact', '热保护，常闭触点'),
    'Теплозащита, перекидной контакт (SPDT)': (
        'Thermal protection, changeover contact (SPDT)', '热保护，转换触点（SPDT）'),
}

# Код сигнала ОС → (en, cn)
FEEDBACK_SIGNALS = {
    'FB_ALARM2_SPDT': ('Alarm (2nd contact), SPDT', '报警（第2触点），SPDT'),
    'FB_ALARM_SPDT': ('Alarm (1st contact), SPDT', '报警（第1触点），SPDT'),
    'FB_END_CLOSE_DPDT': ('Limit "Closed", DPDT', '限位“关闭”，DPDT'),
    'FB_END_CLOSE_SPDT': ('Limit "Closed", SPDT', '限位“关闭”，SPDT'),
    'FB_END_OPEN_DPDT': ('Limit "Open", DPDT', '限位“打开”，DPDT'),
    'FB_END_OPEN_SPDT': ('Limit "Open", SPDT', '限位“打开”，SPDT'),
    'FB_END_SPDT': ('Limit position, SPDT', '限位位置，SPDT'),
    'FB_LOCAL_REMOTE': ('Remote/local control', '远程/本地控制'),
    'FB_OVERHEAT_NC': ('Overheat, NC contact', '过热，常闭触点'),
    'FB_OVERHEAT_SPDT': ('Overheat, SPDT', '过热，SPDT'),
    'FB_PHASE_LOSS': ('Alarm: phase loss', '报警：缺相'),
    'FB_POS_0_10V': ('Position 0-10 V (transmitter)', '位置 0-10 V（变送器）'),
    'FB_POS_4_20MA_ACTIVE': ('Position 4-20 mA, active', '位置 4-20 mA，有源'),
    'FB_POS_4_20MA_ACTIVE_HART': ('Position 4-20 mA, active, HART', '位置 4-20 mA，有源，HART'),
    'FB_POS_4_20MA_PASSIVE': ('Position 4-20 mA, passive', '位置 4-20 mA，无源'),
    'FB_POS_4_20MA_PASSIVE_HART': ('Position 4-20 mA, passive, HART', '位置 4-20 mA，无源，HART'),
    'FB_POS_POT_1K': ('Position, potentiometer 0-1 kOhm', '位置，电位计 0-1 kΩ'),
    'FB_READY_NO': ('Ready, NO contact', '就绪，常开触点'),
    'FB_SELECTOR_POSITION': ('Selector switch position', '选择开关位置'),
    'FB_STOP': ('Stop, dry contact', '停止，干接点'),
    'FB_TORQUE_4_20MA': ('Analog torque 4-20 mA', '模拟力矩 4-20 mA'),
    'FB_TORQUE_CLOSE_DPDT': ('Torque "Closed", DPDT', '力矩“关闭”，DPDT'),
    'FB_TORQUE_CLOSE_SPDT': ('Torque "Closed", SPDT', '力矩“关闭”，SPDT'),
    'FB_TORQUE_OPEN_DPDT': ('Torque "Open", DPDT', '力矩“打开”，DPDT'),
    'FB_TORQUE_OPEN_SPDT': ('Torque "Open", SPDT', '力矩“打开”，SPDT'),
    'FB_TURN_COUNTER_NO': ('Turn counter, NO contact', '圈数计数器，常开触点'),
    'FB_WAY_CLOSE_DPDT': ('Intermediate (closing), DPDT', '中间（关闭），DPDT'),
    'FB_WAY_CLOSE_SPDT': ('Intermediate (closing), SPDT', '中间（关闭），SPDT'),
    'FB_WAY_OPEN_DPDT': ('Intermediate (opening), DPDT', '中间（打开），DPDT'),
    'FB_WAY_OPEN_SPDT': ('Intermediate (opening), SPDT', '中间（打开），SPDT'),
}

# Код команды управления → (en, cn)
CONTROL_SIGNALS = {
    'CMD_DRIVE_ENABLE_220AC': ('Drive enable 220 V AC', '驱动使能 220 V AC'),
    'CMD_DRIVE_ENABLE_24DC': ('Drive enable 24 V DC', '驱动使能 24 V DC'),
    'CMD_ESD_CLOSE_220AC': ('Emergency command "Close" 220 V AC', '紧急指令“关闭” 220 V AC'),
    'CMD_ESD_CLOSE_24DC': ('Emergency command "Close" 24 V DC (NC, wire-break monitoring)',
                           '紧急指令“关闭” 24 V DC（常闭，断线监测）'),
    'CMD_ESD_OPEN_220AC': ('Emergency command "Open" 220 V AC', '紧急指令“打开” 220 V AC'),
    'CMD_ESD_OPEN_24DC': ('Emergency command "Open" 24 V DC (NC, wire-break monitoring)',
                          '紧急指令“打开” 24 V DC（常闭，断线监测）'),
    'CMD_INTERLOCK_CLOSE_220AC': ('Interlock "Close" 220 V AC', '联锁“关闭” 220 V AC'),
    'CMD_INTERLOCK_CLOSE_24DC': ('Interlock "Close" 24 V DC', '联锁“关闭” 24 V DC'),
    'CMD_INTERLOCK_OPEN_220AC': ('Interlock "Open" 220 V AC', '联锁“打开” 220 V AC'),
    'CMD_INTERLOCK_OPEN_24DC': ('Interlock "Open" 24 V DC', '联锁“打开” 24 V DC'),
    'CMD_LOCK_220AC': ('Lock 220 V AC', '锁定 220 V AC'),
    'CMD_LOCK_24DC': ('Lock 24 V DC', '锁定 24 V DC'),
    'CMD_MANUAL_220AC': ('Manual override 220 V AC', '手动操作 220 V AC'),
    'CMD_MANUAL_24DC': ('Manual override 24 V DC', '手动操作 24 V DC'),
    'CMD_MODE_220AC': ('Mode switch 220 V AC', '模式切换 220 V AC'),
    'CMD_MODE_24DC': ('Mode switch open-close / modulating', '模式切换 开关型/调节型'),
    'CMD_OCS_220AC': ('Command O/S/C 220 V AC', '指令 开/停/关 220 V AC'),
    'CMD_OCS_24DC': ('Command Open/Stop/Close 24 V DC', '指令 开/停/关 24 V DC'),
    'CMD_POS_0_10V_ACTIVE': ('Position setpoint 0-10 V, active', '位置设定 0-10 V，有源'),
    'CMD_POS_0_10V_PASSIVE': ('Position setpoint 0-10 V, passive', '位置设定 0-10 V，无源'),
    'CMD_POS_4_20MA_ACTIVE': ('Position setpoint 4-20 mA, active', '位置设定 4-20 mA，有源'),
    'CMD_POS_4_20MA_PASSIVE': ('Position setpoint 4-20 mA, passive', '位置设定 4-20 mA，无源'),
    'CMD_REMOTE_220AC': ('Remote control 220 V AC', '远程控制 220 V AC'),
    'CMD_REMOTE_24DC': ('Remote control 24 V DC', '远程控制 24 V DC'),
}

# Код питания обогрева → (en, cn)
HEATER_SUPPLIES = {
    'CU_CIRCUIT': ('From control unit power circuits', '来自控制单元电源回路'),
    'NO_HEATER': ('No heater', '无加热'),
    'MOTOR_CIRCUIT': ('From device power circuits', '来自设备电源回路'),
    'SEPARATE_LINE': ('From separate line', '来自独立线路'),
}

# Код БУ (варианты -q/-nq) → (en, cn)
CU_VARIANTS = {
    'basic-nq': ('Basic (no CU), R series', 'Basic（无控制单元），R 系列'),
    'int-l-nq': ('With INT/L control unit, R series', '带 INT/L 控制单元，R 系列'),
    'int-l-q': ('With INT/L control unit, Q 005-010', '带 INT/L 控制单元，Q 005-010'),
    'int-n-q': ('With INT/N control unit, Q 005-010', '带 INT/N 控制单元，Q 005-010'),
    'int-n-hr-q': ('With INT/N control unit with HART, Q 005-010', '带 INT/N 控制单元，支持 HART，Q 005-010'),
    'int-n-mb-q': ('With INT/N control unit with ModBus, Q 005-010', '带 INT/N 控制单元，支持 ModBus，Q 005-010'),
    'int-n-pb-q': ('With INT/N control unit with ProfiBus, Q 005-010', '带 INT/N 控制单元，支持 ProfiBus，Q 005-010'),
    'int-o-q': ('With INT/O control unit, Q 005-010', '带 INT/O 控制单元，Q 005-010'),
}

# Код положения безопасности → (en, cn)
SAFETY_POSITIONS = {
    'nc-no-fl': ('NC/NO/FL — selectable by setting', 'NC/NO/FL — 可通过设置选择'),
}


class Command(BaseCommand):
    help = 'Backfill en/cn translations for EA signal reference dicts (constructor).'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перезаписать существующие переводы (затирает ручные правки).')

    def _fill_by_code(self, model_label, table, force):
        model = apps.get_model(*model_label.split('.'))
        updated = 0
        for obj in model.objects.all():
            if obj.code not in table:
                continue
            en, cn = table[obj.code]
            i18n = dict(obj.name_i18n or {})
            changed = False
            for locale, value in (('en', en), ('cn', cn)):
                if force or locale not in i18n:
                    i18n[locale] = value
                    changed = True
            if changed:
                obj.name_i18n = i18n
                obj.save(update_fields=['name_i18n'])
                updated += 1
        if updated:
            self.stdout.write(f'{model_label}: {updated}')

    def _fill_by_name(self, model_label, table, force):
        model = apps.get_model(*model_label.split('.'))
        updated = 0
        for obj in model.objects.exclude(name=''):
            if obj.name not in table:
                continue
            en, cn = table[obj.name]
            i18n = dict(obj.name_i18n or {})
            changed = False
            for locale, value in (('en', en), ('cn', cn)):
                if force or locale not in i18n:
                    i18n[locale] = value
                    changed = True
            if changed:
                obj.name_i18n = i18n
                obj.save(update_fields=['name_i18n'])
                updated += 1
        if updated:
            self.stdout.write(f'{model_label}: {updated}')

    def handle(self, *args, **options):
        force = options['force']

        self._fill_by_code('electric_actuators.EaSignalSlot', SLOTS, force)
        self._fill_by_code('electric_actuators.EaSlotOption', SLOT_OPTIONS, force)
        self._fill_by_name('electric_actuators.EaSignalMatrixEntry', MATRIX_NAMES, force)
        self._fill_by_code('electric_actuators.EaFeedbackSignal', FEEDBACK_SIGNALS, force)
        self._fill_by_code('electric_actuators.EaControlSignal', CONTROL_SIGNALS, force)
        self._fill_by_code('params.ActuatorHeaterSupply', HEATER_SUPPLIES, force)
        self._fill_by_code('params.ControlUnitInstalledOption', CU_VARIANTS, force)
        self._fill_by_code('params.SafetyPositionOption', SAFETY_POSITIONS, force)

        self.stdout.write(self.style.SUCCESS('Done.'))
