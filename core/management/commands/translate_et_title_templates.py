"""Заполняет en/cn переводы title_template / list_title_template типов оборудования.

Ключ — точная ru-строка шаблона (плейсхолдеры {field} сохраняются). Шаблоны без
перевода в словаре пропускаются (остаются ru) — команда сообщает о них.

Идемпотентна: заполняет только отсутствующие локали.
"""

from django.core.management.base import BaseCommand

from core.models.equipment_type import EquipmentType


TITLE_TRANSLATIONS = {
    # ── Пневмопривод ──
    '{model_code} Пневмопривод {brand} {variety} {construction_name}; {safety_position}; {springs_qty}; Темп. {temperature}; {ip}; {exd_short}; Покрытие корпуса: {coating}; Ручной дублер: {manual_override};  Монтаж: {mounting}, шток {stem_shape} {stem_size_dim}мм; Пневмо вх/вых: {thread_in}/{thread_out}, {pneumatic_conn}':
        ('{model_code} Pneumatic actuator {brand} {variety} {construction_name}; {safety_position}; {springs_qty}; Temp. {temperature}; {ip}; {exd_short}; Body coating: {coating}; Manual override: {manual_override}; Mounting: {mounting}, stem {stem_shape} {stem_size_dim}mm; Air in/out: {thread_in}/{thread_out}, {pneumatic_conn}',
         '{model_code} 气动执行器 {brand} {variety} {construction_name}; {safety_position}; {springs_qty}; 温度 {temperature}; {ip}; {exd_short}; 壳体涂层: {coating}; 手动超越: {manual_override}; 安装: {mounting}, 阀杆 {stem_shape} {stem_size_dim}mm; 进/出气口: {thread_in}/{thread_out}, {pneumatic_conn}'),
    '{model_code} Пневмопривод {brand} {variety} {construction_name}; {safety_position}; {springs_qty}; Темп. {temperature}; {ip}; {exd_short}; Покрытие корпуса: {coating}; Ручной дублер: {hand_wheel};  Монтаж: {mounting}, шток {stem_shape} {stem_size_dim}мм; Пневмо вх/вых: {thread_in}/{thread_out}, {pneumatic_conn}':
        ('{model_code} Pneumatic actuator {brand} {variety} {construction_name}; {safety_position}; {springs_qty}; Temp. {temperature}; {ip}; {exd_short}; Body coating: {coating}; Manual override: {hand_wheel}; Mounting: {mounting}, stem {stem_shape} {stem_size_dim}mm; Air in/out: {thread_in}/{thread_out}, {pneumatic_conn}',
         '{model_code} 气动执行器 {brand} {variety} {construction_name}; {safety_position}; {springs_qty}; 温度 {temperature}; {ip}; {exd_short}; 壳体涂层: {coating}; 手动超越: {hand_wheel}; 安装: {mounting}, 阀杆 {stem_shape} {stem_size_dim}mm; 进/出气口: {thread_in}/{thread_out}, {pneumatic_conn}'),
    # ── Ручной дублер ──
    '{model_code} {gearbox_variety} {is_declutchable} {gearbox_output_variety} Макс: {max_output_torque} Нм;   Темп. {work_temp_min}..{work_temp_max}°С;':
        ('{model_code} {gearbox_variety} {is_declutchable} {gearbox_output_variety} Max: {max_output_torque} Nm; Temp. {work_temp_min}..{work_temp_max}°C;',
         '{model_code} {gearbox_variety} {is_declutchable} {gearbox_output_variety} 最大: {max_output_torque} Nm; 温度 {work_temp_min}..{work_temp_max}°C;'),
    # ── Соленоидный клапан ──
    '{model_code} Пневмораспределитель {function}; {temperature_range}°С; {exd}; {ip}; {power_supply}; {operation}; {construction}':
        ('{model_code} Solenoid valve {function}; {temperature_range}°C; {exd}; {ip}; {power_supply}; {operation}; {construction}',
         '{model_code} 电磁阀 {function}; {temperature_range}°C; {exd}; {ip}; {power_supply}; {operation}; {construction}'),
    # ── Фильтр-регулятор ──
    '{model_code} {filter_variety} Т.окр. {work_temp_min}..{work_temp_max} °С, Рег.давления {pressure_min}..{pressure_max} бар':
        ('{model_code} {filter_variety} Ambient temp. {work_temp_min}..{work_temp_max} °C, Pressure regulation {pressure_min}..{pressure_max} bar',
         '{model_code} {filter_variety} 环境温度 {work_temp_min}..{work_temp_max} °C, 压力调节 {pressure_min}..{pressure_max} bar'),
    # ── Позиционер для ПП ──
    '{model_code} Позиционер {brand}, {acting_type}; {exd}; {ip}':
        ('{model_code} Positioner {brand}, {acting_type}; {exd}; {ip}',
         '{model_code} 定位器 {brand}, {acting_type}; {exd}; {ip}'),
    # ── Кабельный ввод ──
    'Кабельный ввод {brand} {cable_types}; {body_material};':
        ('Cable gland {brand} {cable_types}; {body_material};',
         '电缆接头 {brand} {cable_types}; {body_material};'),
}


class Command(BaseCommand):
    help = ('Заполняет en/cn переводы title_template_i18n / list_title_template_i18n '
            'типов оборудования (ключ — ru-шаблон).')

    def handle(self, *args, **options):
        updated = 0
        missing = set()
        for et in EquipmentType.objects.all():
            for field, i18n_field in (
                ('title_template', 'title_template_i18n'),
                ('list_title_template', 'list_title_template_i18n'),
            ):
                template = getattr(et, field) or ''
                if not template:
                    continue
                i18n = getattr(et, i18n_field) or {}
                if not isinstance(i18n, dict):
                    i18n = {}
                changed = False
                for locale in ('en', 'cn'):
                    if locale not in i18n:
                        translation = TITLE_TRANSLATIONS.get(template)
                        if translation is not None:
                            i18n[locale] = translation[0 if locale == 'en' else 1]
                            changed = True
                        else:
                            missing.add('%s: %s' % (field, template[:80]))
                if changed:
                    setattr(et, i18n_field, i18n)
                    et.save()
                    updated += 1
        self.stdout.write(self.style.SUCCESS('обновлено полей: %d' % updated))
        if missing:
            self.stdout.write(self.style.WARNING('без перевода (fallback ru):'))
            for item in sorted(missing):
                self.stdout.write('  ' + item)
