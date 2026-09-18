# Generated manually 2026-09-18

from django.db import migrations

PNEUMATIC_ACTUATOR_SPEC_TEMPLATE = {
    "Основные": {
        "Серия": "model_line_name",
        "Бренд": "brand_name",
        "Тип привода": "variety_name",
        "Тип работы": "construction",
        "Угол поворота": "turn_angle",
        "Корпус": "body_name",
        "Вес (кг)": "weight",
    },
    "Выбранные опции": {
        "Пружины": "springs_qty",
        "Температурный диапазон": "temperature",
        "Степень защиты IP": "ip",
        "Положение безопасности": "safety_position",
        "Взрывозащита": "exd",
        "Покрытие корпуса": "coating",
        "Ручной дублёр": "hand_wheel",
    },
    "Технические": {
        "Давление мин/макс": "pressure",
        "Расход воздуха": "air_usage",
    },
    "Присоединение к арматуре": {
        "Шток": "stem",
        "Монтажные площадки": "mounting",
    },
    "Подключения корпуса": {
        "Пневмовход": "thread_in",
        "Пневмовыход": "thread_out",
        "Типы пневмоподключений": "pneumatic_conn",
    },
    "Таблица моментов": {
        "torque_table": "torque_table",
    },
}


def set_pneumatic_actuator_spec_template(apps, schema_editor):
    EquipmentType = apps.get_model('core', 'EquipmentType')
    EquipmentType.objects.filter(code='pneumatic-actuator').update(
        spec_template=PNEUMATIC_ACTUATOR_SPEC_TEMPLATE,
    )


def unset_pneumatic_actuator_spec_template(apps, schema_editor):
    EquipmentType = apps.get_model('core', 'EquipmentType')
    EquipmentType.objects.filter(code='pneumatic-actuator').update(spec_template={})


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_alter_equipmenttype_spec_template'),
    ]

    operations = [
        migrations.RunPython(
            set_pneumatic_actuator_spec_template,
            unset_pneumatic_actuator_spec_template,
        ),
    ]
