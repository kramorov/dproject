"""Заполняет en/cn переводы шаблонов типов оборудования.

Поля: name_template / description_template / title_template / spec_title_template /
list_title_template (все 5 текстовых шаблонов EquipmentType). Шаблон спецификации
(spec_template) переводится командой ``translate_spec_templates``.

Ключ — точная ru-строка шаблона (плейсхолдеры {field} сохраняются). Шаблоны без
перевода в словаре пропускаются (остаются ru) — команда сообщает о них.

Идемпотентна: заполняет только отсутствующие локали.
"""

from django.core.management.base import BaseCommand

from core.models.equipment_type import EquipmentType


TEMPLATE_TRANSLATIONS = {
    # ── Пневмопривод ──
    '{model_code} Пневмопривод {brand} {variety} {construction_name}; {safety_position}; {springs_qty}; Темп. {temperature}; {ip}; {exd_short}; Покрытие корпуса: {coating}; Ручной дублер: {manual_override};  Монтаж: {mounting}, шток {stem_shape} {stem_size_dim}мм; Пневмо вх/вых: {thread_in}/{thread_out}, {pneumatic_conn}':
        ('{model_code} Pneumatic actuator {brand} {variety} {construction_name}; {safety_position}; {springs_qty}; Temp. {temperature}; {ip}; {exd_short}; Body coating: {coating}; Manual override: {manual_override}; Mounting: {mounting}, stem {stem_shape} {stem_size_dim}mm; Air in/out: {thread_in}/{thread_out}, {pneumatic_conn}',
         '{model_code} 气动执行器 {brand} {variety} {construction_name}; {safety_position}; {springs_qty}; 温度 {temperature}; {ip}; {exd_short}; 壳体涂层: {coating}; 手动超越: {manual_override}; 安装: {mounting}, 阀杆 {stem_shape} {stem_size_dim}mm; 进/出气口: {thread_in}/{thread_out}, {pneumatic_conn}'),
    '{model_code} Пневмопривод {brand} {variety} {construction_name}; {safety_position}; {springs_qty}; Темп. {temperature}; {ip}; {exd_short}; Покрытие корпуса: {coating}; Ручной дублер: {hand_wheel};  Монтаж: {mounting}, шток {stem_shape} {stem_size_dim}мм; Пневмо вх/вых: {thread_in}/{thread_out}, {pneumatic_conn}':
        ('{model_code} Pneumatic actuator {brand} {variety} {construction_name}; {safety_position}; {springs_qty}; Temp. {temperature}; {ip}; {exd_short}; Body coating: {coating}; Manual override: {hand_wheel}; Mounting: {mounting}, stem {stem_shape} {stem_size_dim}mm; Air in/out: {thread_in}/{thread_out}, {pneumatic_conn}',
         '{model_code} 气动执行器 {brand} {variety} {construction_name}; {safety_position}; {springs_qty}; 温度 {temperature}; {ip}; {exd_short}; 壳体涂层: {coating}; 手动超越: {hand_wheel}; 安装: {mounting}, 阀杆 {stem_shape} {stem_size_dim}mm; 进/出气口: {thread_in}/{thread_out}, {pneumatic_conn}'),
    # ── Пневмопривод: name_template (отличается от description/title) ──
    '{model_code} Пневмопривод {variety} {construction_name} {brand} {variety}; {safety_position}; {springs_qty}; {safety_position_text_value}  Темп. {temperature}; {ip}; {exd_short}; Покрытие корпуса: {coating}; Ручной дублер: {manual_override}; Пневмо вх/вых: {thread_in}/{thread_out}; Монтаж: {mounting}, шток {stem_shape} {stem_size_dim}мм {pneumatic_conn}':
        ('{model_code} Pneumatic actuator {variety} {construction_name} {brand} {variety}; {safety_position}; {springs_qty}; {safety_position_text_value}  Temp. {temperature}; {ip}; {exd_short}; Body coating: {coating}; Manual override: {manual_override}; Air in/out: {thread_in}/{thread_out}; Mounting: {mounting}, stem {stem_shape} {stem_size_dim}mm {pneumatic_conn}',
         '{model_code} 气动执行器 {variety} {construction_name} {brand} {variety}; {safety_position}; {springs_qty}; {safety_position_text_value} 温度 {temperature}; {ip}; {exd_short}; 壳体涂层: {coating}; 手动超越: {manual_override}; 进/出气口: {thread_in}/{thread_out}; 安装: {mounting}, 阀杆 {stem_shape} {stem_size_dim}mm {pneumatic_conn}'),
    # ── Ручной дублер ──
    '{model_code} {gearbox_variety} {is_declutchable} {gearbox_output_variety} Макс: {max_output_torque} Нм;   Темп. {work_temp_min}..{work_temp_max}°С;':
        ('{model_code} {gearbox_variety} {is_declutchable} {gearbox_output_variety} Max: {max_output_torque} Nm; Temp. {work_temp_min}..{work_temp_max}°C;',
         '{model_code} {gearbox_variety} {is_declutchable} {gearbox_output_variety} 最大: {max_output_torque} Nm; 温度 {work_temp_min}..{work_temp_max}°C;'),
    # ── Соленоидный клапан ──
    '{model_code} Пневмораспределитель {function}; {temperature_range}°С; {exd}; {ip}; {power_supply}; {operation}; {construction}':
        ('{model_code} Solenoid valve {function}; {temperature_range}°C; {exd}; {ip}; {power_supply}; {operation}; {construction}',
         '{model_code} 电磁阀 {function}; {temperature_range}°C; {exd}; {ip}; {power_supply}; {operation}; {construction}'),
    '{model_code} Пневмораспределитель {brand} {function} {operation} {actuation}; {pneumatic_connection}; {pneumatic_connection_thread}; корпус: {body_material};  катушка: {solenoid_body_material}{solenoid_body_material_specified}; уплотнение {sealing_material_specified}; P {pressure_range} бар; T {temperature_range}°С;  {exd_short}; {ip}; {power_supply};':
        ('{model_code} Solenoid valve {brand} {function} {operation} {actuation}; {pneumatic_connection}; {pneumatic_connection_thread}; body: {body_material}; coil: {solenoid_body_material}{solenoid_body_material_specified}; seal {sealing_material_specified}; P {pressure_range} bar; T {temperature_range}°C;  {exd_short}; {ip}; {power_supply};',
         '{model_code} 电磁阀 {brand} {function} {operation} {actuation}; {pneumatic_connection}; {pneumatic_connection_thread}; 阀体: {body_material}; 线圈: {solenoid_body_material}{solenoid_body_material_specified}; 密封 {sealing_material_specified}; P {pressure_range} bar; T {temperature_range}°C;  {exd_short}; {ip}; {power_supply};'),
    '{model_code} Пневмораспределитель {brand} {operation} {construction} функция {function}; тип пневмоприсоединения - {pneumatic_connection}; присоединение {pneumatic_connection_thread}; Kv-{kv} м3/ч; корпус {body_material}({body_material_specified}); катушка {solenoid_body_material}{solenoid_body_material_specified}; уплотнение {sealing_material_specified}; Давление {pressure_range} бар; Темп.окр.среды {temperature_range}°С; отверстие под кабельный ввод {cable_glands_holes},  взрывозащита {exd_short}; {ip}; Dn {dn} мм; Питание {power_supply}; Мощность холодного/ном/удерж: {power_consumption_start} /  {power_consumption_hot} / {power_consumption_hold}, Вт; Ручной дублер: {manual_override}; макс. плотность рабочей среды {medium_density_max} сСт (мм2/с); Класс изоляции соленоида: {solenoid_insulation_class}; макс 5 циклов/сек; вес {weight}':
        ('{model_code} Solenoid valve {brand} {operation} {construction} function {function}; pneumatic connection type - {pneumatic_connection}; connection {pneumatic_connection_thread}; Kv-{kv} m3/h; body {body_material}({body_material_specified}); coil {solenoid_body_material}{solenoid_body_material_specified}; seal {sealing_material_specified}; Pressure {pressure_range} bar; Ambient temp. {temperature_range}°C; cable gland hole {cable_glands_holes},  explosion protection {exd_short}; {ip}; Dn {dn} mm; Power supply {power_supply}; Power cold/hot/hold: {power_consumption_start} /  {power_consumption_hot} / {power_consumption_hold}, W; Manual override: {manual_override}; max. medium viscosity {medium_density_max} cSt (mm2/s); Solenoid insulation class: {solenoid_insulation_class}; max 5 cycles/sec; weight {weight}',
         '{model_code} 电磁阀 {brand} {operation} {construction} 功能 {function}; 气动连接类型 - {pneumatic_connection}; 连接 {pneumatic_connection_thread}; Kv-{kv} m3/h; 阀体 {body_material}({body_material_specified}); 线圈 {solenoid_body_material}{solenoid_body_material_specified}; 密封 {sealing_material_specified}; 压力 {pressure_range} bar; 环境温度 {temperature_range}°C; 电缆接头孔 {cable_glands_holes},  防爆 {exd_short}; {ip}; Dn {dn} mm; 电源 {power_supply}; 冷态/热态/保持功率: {power_consumption_start} /  {power_consumption_hot} / {power_consumption_hold}, W; 手动超越: {manual_override}; 最大介质粘度 {medium_density_max} cSt (mm2/s); 线圈绝缘等级: {solenoid_insulation_class}; 最大 5 次/秒; 重量 {weight}'),
    # ── Фильтр-регулятор ──
    '{model_code} {filter_variety} Т.окр. {work_temp_min}..{work_temp_max} °С, Рег.давления {pressure_min}..{pressure_max} бар':
        ('{model_code} {filter_variety} Ambient temp. {work_temp_min}..{work_temp_max} °C, Pressure regulation {pressure_min}..{pressure_max} bar',
         '{model_code} {filter_variety} 环境温度 {work_temp_min}..{work_temp_max} °C, 压力调节 {pressure_min}..{pressure_max} bar'),
    '{model_code} {filter_variety} {brand}; Расход {flow_rate} л/мин; {drain_variety}; Т.окр. {work_temp_min}..{work_temp_max} °С, Рег.давления {pressure_min}..{pressure_max} бар; Порты: {thread}; фильтрация {filtration_rating} мкм;':
        ('{model_code} {filter_variety} {brand}; Flow {flow_rate} l/min; {drain_variety}; Ambient temp. {work_temp_min}..{work_temp_max} °C, Pressure regulation {pressure_min}..{pressure_max} bar; Ports: {thread}; filtration {filtration_rating} µm;',
         '{model_code} {filter_variety} {brand}; 流量 {flow_rate} l/min; {drain_variety}; 环境温度 {work_temp_min}..{work_temp_max} °C, 压力调节 {pressure_min}..{pressure_max} bar; 接口: {thread}; 过滤精度 {filtration_rating} µm;'),
    '{model_code} {filter_variety} {brand}; Расход {flow_rate} л/мин; {drain_variety}; Т.окр. {work_temp_min}..{work_temp_max} °С, Материал корпуса: {body_material}, Материал стакана: {bowl_material}, Кожух: {protection_material} Порты: {thread}; слив: {drain_port_size}; {gauge_quantity}; фильтрация {filtration_rating} мкм; Диапазон регулировки давления {pressure_min}..{pressure_max} бар; Макс. входное давление {pressure_inlet_max} бар; вес {weight}кг. Настенное крепление: {wall_mounting_included}':
        ('{model_code} {filter_variety} {brand}; Flow {flow_rate} l/min; {drain_variety}; Ambient temp. {work_temp_min}..{work_temp_max} °C, Body material: {body_material}, Bowl material: {bowl_material}, Guard: {protection_material} Ports: {thread}; drain: {drain_port_size}; {gauge_quantity}; filtration {filtration_rating} µm; Pressure regulation range {pressure_min}..{pressure_max} bar; Max. inlet pressure {pressure_inlet_max} bar; weight {weight}kg. Wall mounting: {wall_mounting_included}',
         '{model_code} {filter_variety} {brand}; 流量 {flow_rate} l/min; {drain_variety}; 环境温度 {work_temp_min}..{work_temp_max} °C, 壳体材料: {body_material}, 杯体材料: {bowl_material}, 防护罩: {protection_material} 接口: {thread}; 排水: {drain_port_size}; {gauge_quantity}; 过滤精度 {filtration_rating} µm; 压力调节范围 {pressure_min}..{pressure_max} bar; 最大入口压力 {pressure_inlet_max} bar; 重量 {weight}kg. 壁式安装: {wall_mounting_included}'),
    # ── Позиционер для ПП ──
    '{model_code} Позиционер {brand}, {acting_type}; {exd}; {ip}':
        ('{model_code} Positioner {brand}, {acting_type}; {exd}; {ip}',
         '{model_code} 定位器 {brand}, {acting_type}; {exd}; {ip}'),
    '{model_code} Позиционер {brand}, {acting_type}; {exd_short}; Т.окр. {work_temp_min}..{work_temp_max} °С; Присоединения: {body_connection}; Рычаг: {lever}; Материал корпуса: {body_material}':
        ('{model_code} Positioner {brand}, {acting_type}; {exd_short}; Ambient temp. {work_temp_min}..{work_temp_max} °C; Connections: {body_connection}; Lever: {lever}; Body material: {body_material}',
         '{model_code} 定位器 {brand}, {acting_type}; {exd_short}; 环境温度 {work_temp_min}..{work_temp_max} °C; 连接: {body_connection}; 杠杆: {lever}; 壳体材料: {body_material}'),
    '{model_code} Позиционер {brand}, {acting_type}; {exd_short}; {ip}; Т.окр. {work_temp_min}..{work_temp_max} °С; Присоединения корпуса: {body_connection}; Рычаг: {lever}; Материал корпуса: {body_material}, вес {weight} кг; Питание: {supply_pressure_range} бар; Пневмопривод: {actuator_action}; Сигнал тревоги: {alarm}. Сигналы: {signal_profile_summary}; Смарт-возможности: {smart_capabilities}':
        ('{model_code} Positioner {brand}, {acting_type}; {exd_short}; {ip}; Ambient temp. {work_temp_min}..{work_temp_max} °C; Body connections: {body_connection}; Lever: {lever}; Body material: {body_material}, weight {weight} kg; Supply: {supply_pressure_range} bar; Pneumatic actuator: {actuator_action}; Alarm: {alarm}. Signals: {signal_profile_summary}; Smart features: {smart_capabilities}',
         '{model_code} 定位器 {brand}, {acting_type}; {exd_short}; {ip}; 环境温度 {work_temp_min}..{work_temp_max} °C; 壳体连接: {body_connection}; 杠杆: {lever}; 壳体材料: {body_material}, 重量 {weight} kg; 供气: {supply_pressure_range} bar; 气动执行器: {actuator_action}; 报警: {alarm}. 信号: {signal_profile_summary}; 智能功能: {smart_capabilities}'),
    # ── Кабельный ввод ──
    'Кабельный ввод {brand} {cable_types}; {body_material};':
        ('Cable gland {brand} {cable_types}; {body_material};',
         '电缆接头 {brand} {cable_types}; {body_material};'),
    '{model_code} Кабельный ввод {brand}':
        ('{model_code} Cable gland {brand}',
         '{model_code} 电缆接头 {brand}'),
    # ── Фитинги / фитинг резьба-трубка ──
    '{model_code} {fixation_method} {shape} {brand}':
        ('{model_code} {fixation_method} {shape} {brand}',
         '{model_code} {fixation_method} {shape} {brand}'),
    '{model_code} {fixation_method} {shape} {brand}, {thread_inner_outer} резьба {thread}, Т раб. {temperature_range} °С, Р раб. {pressure_range} бар':
        ('{model_code} {fixation_method} {shape} {brand}, {thread_inner_outer} thread {thread}, Working temp. {temperature_range} °C, Working pressure {pressure_range} bar',
         '{model_code} {fixation_method} {shape} {brand}, {thread_inner_outer} 螺纹 {thread}, 工作温度 {temperature_range} °C, 工作压力 {pressure_range} bar'),
    # ── Ручной дублер: name/description (только плейсхолдеры) ──
    '{model_code} {brand} {gearbox_variety}':
        ('{model_code} {brand} {gearbox_variety}',
         '{model_code} {brand} {gearbox_variety}'),
    '{model_code} {brand} {gearbox_variety} {gearbox_output_variety}':
        ('{model_code} {brand} {gearbox_variety} {gearbox_output_variety}',
         '{model_code} {brand} {gearbox_variety} {gearbox_output_variety}'),
    # ── Глушители ──
    '{model_code} {equipment_type} {brand} {thread} {thread_inner_outer} резьба, {body_material}, фильтрующий элемент {filter_element}, {shape}':
        ('{model_code} {equipment_type} {brand} {thread} {thread_inner_outer} thread, {body_material}, filter element {filter_element}, {shape}',
         '{model_code} {equipment_type} {brand} {thread} {thread_inner_outer} 螺纹, {body_material}, 过滤元件 {filter_element}, {shape}'),
    '{model_code} {equipment_type} {brand}, {thread_inner_outer} резьба {thread}, Т раб. {temperature_range} °С, Р раб. {pressure_range} бар':
        ('{model_code} {equipment_type} {brand}, {thread_inner_outer} thread {thread}, Working temp. {temperature_range} °C, Working pressure {pressure_range} bar',
         '{model_code} {equipment_type} {brand}, {thread_inner_outer} 螺纹 {thread}, 工作温度 {temperature_range} °C, 工作压力 {pressure_range} bar'),
    '{model_code} {equipment_type} {brand}':
        ('{model_code} {equipment_type} {brand}',
         '{model_code} {equipment_type} {brand}'),
    '{model_code} {equipment_type} {brand} {thread} {thread_inner_outer}':
        ('{model_code} {equipment_type} {brand} {thread} {thread_inner_outer}',
         '{model_code} {equipment_type} {brand} {thread} {thread_inner_outer}'),
    # ── Монтажные комплекты ──
    'Монтажный комплект (скоба) {model_code} для крепления фильтр-регулятора к пневмоприводу':
        ('Mounting kit (bracket) {model_code} for mounting filter-regulator to pneumatic actuator',
         '安装套件 (支架) {model_code} 用于将过滤调压阀安装到气动执行器'),
    'Монтажный комплект (скоба) {model_code} для крепленияБКВ к пневмоприводу':
        ('Mounting kit (bracket) {model_code} for mounting limit switch box to pneumatic actuator',
         '安装套件 (支架) {model_code} 用于将限位开关盒安装到气动执行器'),
    'Монтажный комплект (скоба) {model_code} для крепления клапана-распределителя к пневмоприводу':
        ('Mounting kit (bracket) {model_code} for mounting directional valve to pneumatic actuator',
         '安装套件 (支架) {model_code} 用于将换向阀安装到气动执行器'),
    'Монтажный комплект (скоба) {model_code} для крепления позиционера к пневмоприводу':
        ('Mounting kit (bracket) {model_code} for mounting positioner to pneumatic actuator',
         '安装套件 (支架) {model_code} 用于将定位器安装到气动执行器'),
}


TEMPLATE_FIELDS = (
    'name_template',
    'description_template',
    'title_template',
    'spec_title_template',
    'list_title_template',
)


class Command(BaseCommand):
    help = ('Заполняет en/cn переводы шаблонов типов оборудования '
            '(name/description/title/spec_title/list_title; ключ — ru-шаблон).')

    def handle(self, *args, **options):
        updated = 0
        missing = set()
        for et in EquipmentType.objects.all():
            for field in TEMPLATE_FIELDS:
                template = getattr(et, field) or ''
                if not template:
                    continue
                i18n_field = field + '_i18n'
                i18n = getattr(et, i18n_field) or {}
                if not isinstance(i18n, dict):
                    i18n = {}
                changed = False
                for locale in ('en', 'cn'):
                    if locale not in i18n:
                        translation = TEMPLATE_TRANSLATIONS.get(template)
                        if translation is not None:
                            i18n[locale] = translation[0 if locale == 'en' else 1]
                            changed = True
                        else:
                            missing.add('%s: %s' % (field, template[:90]))
                if changed:
                    setattr(et, i18n_field, i18n)
                    et.save()
                    updated += 1
        self.stdout.write(self.style.SUCCESS('обновлено полей: %d' % updated))
        if missing:
            self.stdout.write(self.style.WARNING('без перевода (fallback ru):'))
            for item in sorted(missing):
                self.stdout.write('  ' + item)
