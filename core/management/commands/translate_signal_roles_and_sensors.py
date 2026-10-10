"""Заполняет en/cn переводы ролей сигналов и шаблонов описания датчиков (БКВ).

Роли сигналов (params.SignalRole) — ``name_i18n``; шаблоны датчиков
(pa_controls.LimitSwitchSensorVariety) — ``name_template_i18n`` /
``description_template_i18n``. Коды и служебные обозначения («SPDT», «NAMUR»,
«4-20мА», «Ui», «Ii») не переводятся — остаются как есть.

Идемпотентна: повторный запуск перезаписывает en/cn (ru синхронизируется
миксинами при save).
"""
from django.core.management.base import BaseCommand
from django.apps import apps

# Код роли сигнала → (en, cn)
SIGNAL_ROLES = {
    'OUTPUT_OPEN': ('Output open', '输出 打开'),
    'OUTPUT_CLOSE': ('Output closed', '输出 关闭'),
    'OUTPUT_WAY_SWITCH': ('Output intermediate position', '输出 中间位置'),
    'OUTPUT_TORQUE_OPEN': ('Output torque switch "Open"', '输出 力矩开关“打开”'),
    'OUTPUT_TORQUE_CLOSE': ('Output torque switch "Closed"', '输出 力矩开关“关闭”'),
    'OUTPUT_WAY_SWITCH_X2': ('Output 2 intermediate positions (2 sensors)', '输出 2个中间位置（2个传感器）'),
    'OUTPUT_CURRENT_POSITION': ('Output current position (analog signal)', '输出 当前位置（模拟信号）'),
    'OUTPUT_POTENTIOMETER': ('Output potentiometer', '输出 电位计'),
    'OUTPUT_ALARM': ('Output alarm', '输出 报警'),
    'OUTPUT_ALARM_2': ('Output alarm 2', '输出 报警2'),
    'OUTPUT_REMOTE_CONTROL': ('Output remote control', '输出 远程控制'),
    'OUTPUT_OVERHEAT': ('Output motor overheat', '输出 电机过热'),
    'INPUT_OPEN': ('Input signal "Open"', '输入 信号“打开”'),
    'INPUT_STOP': ('Input signal "Stop"', '输入 信号“停止”'),
    'INPUT_CLOSE': ('Input signal "Close"', '输入 信号“关闭”'),
    'INPUT_POSITION': ('Input position signal (analog)', '输入 位置信号（模拟）'),
    'INPUT_ESD': ('Input emergency shut down (ESD) signal', '输入 紧急停机 (ESD) 信号'),
    'HART_DIAG': ('HART diagnostics and configuration', 'HART 诊断与配置'),
    'MODBUS_CTRL': ('Modbus RTU/TCP control and diagnostics', 'Modbus RTU/TCP 控制与诊断'),
    'PROFINET_CTRL': ('Profinet control and diagnostics', 'Profinet 控制与诊断'),
    'PROFIBUS_DP_CTRL': ('Profibus DP cyclic exchange', 'Profibus DP 循环交换'),
    'FF_CTRL': ('Foundation Fieldbus control and diagnostics', 'Foundation Fieldbus 控制与诊断'),
    'HART_POS': ('Current position with HART', '带 HART 的当前位置'),
    'IN_OUT_DP_HART': ('In/Out 4-20+HART', '输入/输出 4-20+HART'),
}

# Общие шаблоны (перевод только описательных слов, плейсхолдеры и коды не трогаем).
_COMMON_NAME = (
    '{model_code} - {brand} {sensor_variety}, signal type: {signal_type}, contact form: {contact_form} ({contact_form_code}), contact state: {contact_state}, {electrical_specs}, {wires_count} wires per sensor.',
    '{model_code} - {brand} {sensor_variety}，信号类型：{signal_type}，触点形式：{contact_form} ({contact_form_code})，触点状态：{contact_state}，{electrical_specs}，每个传感器 {wires_count} 根线。',
)
_COMMON_DESC = (
    '{model_code} - {brand} {sensor_variety}, signal type: {signal_type}, contact form: {contact_form} ({contact_form_code}), contact state: {contact_state}, {electrical_specs}, {wires_count} wires per sensor, {extra_params}',
    '{model_code} - {brand} {sensor_variety}，信号类型：{signal_type}，触点形式：{contact_form} ({contact_form_code})，触点状态：{contact_state}，{electrical_specs}，每个传感器 {wires_count} 根线，{extra_params}',
)
_COMMON_DESC_NOEXTRA = (
    '{model_code} - {brand} {sensor_variety}, signal type: {signal_type}, contact form: {contact_form} ({contact_form_code}), contact state: {contact_state}, {electrical_specs}, {wires_count} wires per sensor.',
    '{model_code} - {brand} {sensor_variety}，信号类型：{signal_type}，触点形式：{contact_form} ({contact_form_code})，触点状态：{contact_state}，{electrical_specs}，每个传感器 {wires_count} 根线。',
)
_IND_DESC = (
    '{model_code} - {brand} {sensor_variety}, signal type: {signal_type}, contact form: {contact_form} ({contact_form_code}), contact state: {contact_state}, {wires_count} wires per sensor. Ui(V): {ui}, Ii(mA): {ii}, {electrical_specs}, {exi_params}, {extra_params}',
    '{model_code} - {brand} {sensor_variety}，信号类型：{signal_type}，触点形式：{contact_form} ({contact_form_code})，触点状态：{contact_state}，每个传感器 {wires_count} 根线。Ui(V)：{ui}，Ii(mA)：{ii}，{electrical_specs}，{exi_params}，{extra_params}',
)
_POTE_NAME = (
    '{model_code} - {brand} {sensor_variety}, signal type: {signal_type}, {electrical_specs}, {wires_count} wires per sensor.',
    '{model_code} - {brand} {sensor_variety}，信号类型：{signal_type}，{electrical_specs}，每个传感器 {wires_count} 根线。',
)
_POTE_DESC = (
    '{model_code} - {brand} {sensor_variety}, signal type: {signal_type}, {electrical_specs}, {wires_count} wires per sensor.',
    '{model_code} - {brand} {sensor_variety}，信号类型：{signal_type}，{electrical_specs}，每个传感器 {wires_count} 根线。',
)

# Код разновидности датчика → {name: (en, cn), description: (en, cn)}
SENSOR_VARIETY_TEMPLATES = {
    'MECH': {'name': _COMMON_NAME, 'description': _COMMON_DESC},
    'IND': {'name': _COMMON_NAME, 'description': _IND_DESC},
    'REED': {'name': _COMMON_NAME, 'description': _COMMON_DESC},
    'MAG': {'name': _COMMON_NAME, 'description': _COMMON_DESC_NOEXTRA},
    'PNEUM': {'name': _COMMON_NAME, 'description': _COMMON_DESC_NOEXTRA},
    'TRANS': {'name': _COMMON_NAME, 'description': _COMMON_DESC},
    'POTE': {'name': _POTE_NAME, 'description': _POTE_DESC},
}


class Command(BaseCommand):
    help = 'Backfill en/cn translations for signal roles and sensor description templates.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перезаписать существующие переводы (затирает ручные правки).')

    def handle(self, *args, **options):
        force = options['force']
        total = 0

        # 1. Роли сигналов → name_i18n
        Role = apps.get_model('params', 'SignalRole')
        updated = 0
        for obj in Role.objects.all():
            if obj.code not in SIGNAL_ROLES:
                continue
            en, cn = SIGNAL_ROLES[obj.code]
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
            total += updated
            self.stdout.write(f'params.SignalRole: {updated}')

        # 2. Шаблоны датчиков → name_template_i18n / description_template_i18n
        Variety = apps.get_model('pa_controls', 'LimitSwitchSensorVariety')
        updated = 0
        for obj in Variety.objects.all():
            spec = SENSOR_VARIETY_TEMPLATES.get(obj.code)
            if not spec:
                continue
            name_i18n = dict(obj.name_template_i18n or {})
            desc_i18n = dict(obj.description_template_i18n or {})
            changed = False
            for locale in ('en', 'cn'):
                if force or locale not in name_i18n:
                    name_i18n[locale] = spec['name'][0 if locale == 'en' else 1]
                    changed = True
                if force or locale not in desc_i18n:
                    desc_i18n[locale] = spec['description'][0 if locale == 'en' else 1]
                    changed = True
            if changed:
                obj.name_template_i18n = name_i18n
                obj.description_template_i18n = desc_i18n
                obj.save(update_fields=['name_template_i18n', 'description_template_i18n'])
                updated += 1
        if updated:
            total += updated
            self.stdout.write(f'pa_controls.LimitSwitchSensorVariety: {updated}')

        self.stdout.write(self.style.SUCCESS(f'Done. Translated rows: {total}'))
