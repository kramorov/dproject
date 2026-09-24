# Generated manually 2026-09-24
"""Переносит дефолтные name/description-шаблоны из хардкод-методов моделей
в EquipmentType (единая цепочка model_line → equipment_type → {model_code}).

Значения скопированы 1-в-1 из методов ``_get_default_name_template()`` /
``_get_default_description_template()`` соответствующих item-моделей перед
их удалением.
"""

from django.db import migrations


EQUIPMENT_TYPE_TEMPLATES = {
    'pneumatic-actuator': {
        'name_template': '{model_code} Пневмопривод {brand} {variety}; {safety_position}; {springs_qty}; Т.исп. {temperature}; {ip}; {exd}; Покрытие корпуса: {coating}; Ручной дублер: {hand_wheel}',
        'description_template': '{model_code} Пневмопривод {brand} {variety}; Положение безопасности: {safety_position}; Количество пружин: {springs_qty}; Т.исп. {temperature}; {ip}; {exd}; Покрытие корпуса: {coating}; Ручной дублер на корпусе: {hand_wheel}; Вес {weight} кг',
    },
    'directional-valve': {
        'name_template': '{model_code} Пневмораспределитель {brand} {function} {operation} {actuation}; {pneumatic_connection}; {pneumatic_connection_thread}; корпус: {body_material};  катушка: {solenoid_body_material}{solenoid_body_material_specified}; уплотнение {sealing_material_specified}; P {pressure_range} бар; T {temperature_range}°С;  {exd}; {ip}; {power_supply};',
        'description_template': '{model_code} Пневмораспределитель {brand} {operation} {construction} функция {function}; тип пневмоприсоединения - {pneumatic_connection}; присоединение {pneumatic_connection_thread}; Kv-{kv} м3/ч; корпус {body_material}({body_material_specified}); катушка {solenoid_body_material}{solenoid_body_material_specified}; уплотнение {sealing_material_specified}; Давление {pressure_range} бар; Темп.окр.среды {temperature_range}°С; отверстие под кабельный ввод {cable_glands_holes},  взрывозащита {exd}; {ip}; Dn {dn} мм; Питание {power_supply}; Мощность холодного/ном/удерж: {power_consumption_start} /  {power_consumption_hot} / {power_consumption_hold}, Вт; Ручной дублер: {manual_override}; макс. плотность рабочей среды {medium_density_max} сСт (мм2/с); Класс изоляции соленоида: {solenoid_insulation_class}; макс 5 циклов/сек; вес {weight}',
    },
    'lsb': {
        'name_template': '{model_code} Блок концевых выключателей {brand};  {points}, тип датчика: {sensor_variety}; {ip}, Взрывозащита: {exd}; Т.окр. {work_temp_min}..{work_temp_max} °С, Материал корпуса: {body_material_specified}, Отверстия под КВ:{cable_glands_holes}, вес {weight} кг.',
        'description_template': '{model_code} Блок концевых выключателей {brand}; {points}, тип датчика: {sensor_variety}, {ip}, Взрывозащита: {exd}; Т.окр. {work_temp_min}..{work_temp_max} °С, Материал корпуса: {body_material_specified}, Отверстия под КВ:{cable_glands_holes}, Монтаж:{mounting}, вес {weight}кг. Сигналы: {signal_profile_summary}',
    },
    'pa-posi': {
        'name_template': '{model_code} Позиционер {brand}, {acting_type}; {exd}; Т.окр. {work_temp_min}..{work_temp_max} °С; Присоединения: {body_connection}; Рычаг: {lever}; Материал корпуса: {body_material}',
        'description_template': '{model_code} Позиционер {brand}, {acting_type}; {exd}; {ip}; Т.окр. {work_temp_min}..{work_temp_max} °С; Присоединения корпуса: {body_connection}; Рычаг: {lever}; Материал корпуса: {body_material}, вес {weight} кг; Питание: {supply_pressure_range} бар; Пневмопривод: {actuator_action}; Сигнал тревоги: {alarm}. Сигналы: {signal_profile_summary}; Смарт-возможности: {smart_capabilities}',
    },
    'manual-override': {
        'name_template': '{model_code} {brand} {gearbox_variety}',
        'description_template': '{model_code} {brand} {gearbox_variety} {gearbox_output_variety}',
    },
    'fr': {
        'name_template': '{model_code} {filter_variety} {brand}; Расход {flow_rate} л/мин; {drain_variety}; Т.окр. {work_temp_min}..{work_temp_max} °С, Рег.давления {pressure_min}..{pressure_max} бар; Порты: {thread}; фильтрация {filtration_rating} мкм;',
        'description_template': '{model_code} {filter_variety} {brand}; Расход {flow_rate} л/мин; {drain_variety}; Т.окр. {work_temp_min}..{work_temp_max} °С, Материал корпуса: {body_material}, Материал стакана: {bowl_material}, Кожух: {protection_material} Порты: {thread}; слив: {drain_port_size}; {gauge_quantity}; фильтрация {filtration_rating} мкм; Диапазон регулировки давления {pressure_min}..{pressure_max} бар; Макс. входное давление {pressure_inlet_max} бар; вес {weight}кг. Настенное крепление: {wall_mounting_included}',
    },
    'fittings': {
        'name_template': '{model_code} {fitting_variety} {brand}',
        'description_template': '{model_code} {fitting_variety} {brand}, {thread_inner_outer} резьба {thread}, Т раб. {temperature_range} °С, Р раб. {pressure_range} бар',
    },
    'cable-gland': {
        'name_template': '{model_code} Кабельный ввод {brand}',
        'description_template': '{model_code} Кабельный ввод {brand}',
    },
}

# Виды оборудования, разделяющие одну модель PneumaticFitting.
FITTING_TYPE_CODES = ['fittings', 'fitting-thread-pipe', 'fitting-silencer', 'fitting-plug']


def populate_equipment_type_templates(apps, schema_editor):
    EquipmentType = apps.get_model('core', 'EquipmentType')

    for code, templates in EQUIPMENT_TYPE_TEMPLATES.items():
        codes = FITTING_TYPE_CODES if code == 'fittings' else [code]
        for c in codes:
            EquipmentType.objects.filter(code=c).update(
                name_template=templates['name_template'],
                description_template=templates['description_template'],
            )


def clear_equipment_type_templates(apps, schema_editor):
    EquipmentType = apps.get_model('core', 'EquipmentType')
    EquipmentType.objects.filter(
        code__in=list(EQUIPMENT_TYPE_TEMPLATES.keys()) + FITTING_TYPE_CODES
    ).update(name_template=None, description_template=None)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_equipmenttype_name_description_template'),
    ]

    operations = [
        migrations.RunPython(
            populate_equipment_type_templates,
            clear_equipment_type_templates,
        ),
    ]
