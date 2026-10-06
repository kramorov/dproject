"""Backfill en/cn translations for descriptive reference names in `params`.

Только РУССКИЕ ОПИСАТЕЛЬНЫЕ названия справочников. Коды/стандартные обозначения
(Ex db..., IP54, NPT, G, M, У1/ХЛ1, T1..T6, A..VI, группы IIA..IIIC) намеренно
НЕ переводятся — для них локаль возвращает RU-значение (fallback в pick_i18n).
"""
from django.db import migrations

TRANSLATIONS = {
    'BodyCoatingOption': {
        'Нет покрытия, корпус - металл': ('No coating, metal body', '无涂层，金属壳体'),
        'Стандарт, аналог AUMA KN': ('Standard, AUMA KN equivalent', '标准，等效AUMA KN'),
        'Покрытие - аналог AUMA KS': ('Coating, AUMA KS equivalent', '涂层，等效AUMA KS'),
        'Покрытие, аналог AUMA KX': ('Coating, AUMA KX equivalent', '涂层，等效AUMA KX'),
        'Анодирование': ('Anodizing', '阳极氧化'),
        'Нерж. сталь AISI304': ('Stainless steel AISI304', '不锈钢AISI304'),
        'Эпоксидная смола': ('Epoxy resin', '环氧树脂'),
    },
    'CoatingVariety': {
        'Эпоксидное порошковое покрытие 250мкм': ('Epoxy powder coating 250µm', '环氧粉末涂层250微米'),
    },
    'BodyColor': {
        'Синий (Signal Blue) ABRA': ('Blue (Signal Blue) ABRA', '蓝色 (Signal Blue) ABRA'),
        'Синий (Sky Blue) Gala': ('Blue (Sky Blue) Gala', '蓝色 (Sky Blue) Gala'),
        'Генцианово-синий Архимед': ('Gentian blue Archimedes', '龙胆蓝'),
        'Зеленый мох Gala': ('Moss green Gala', '苔绿 Gala'),
        'Серый (Телегрей 1) ABRA': ('Grey (Telegrey 1) ABRA', '灰色 (Telegrey 1) ABRA'),
        'Серый (Кварцевый серый AR21)': ('Grey (Quartz grey AR21)', '灰色 (石英灰AR21)'),
        'Серый (Пыльно-серый) Chenglei': ('Grey (Dust grey) Chenglei', '灰色 (尘灰) Chenglei'),
        'Серый (Бело-алюминиевый)': ('Grey (White aluminium)', '灰色 (白铝色)'),
        'Красный (Огненно-красный) ABRA': ('Red (Fire red) ABRA', '红色 (火红) ABRA'),
        'Охра (Красная окись) ABRA': ('Ochre (Red oxide) ABRA', '赭色 (氧化红) ABRA'),
        'Черный (Глубокий черный AR21)': ('Black (Deep black AR21)', '黑色 (深黑AR21)'),
    },
    'ValveFunctionVariety': {
        'Запорная': ('Shut-off', '截止'),
        'Регулирующая': ('Regulating', '调节'),
        'Запорно-регулирующая': ('Shut-off and regulating', '截止调节'),
        'Комбинированная': ('Combined', '组合'),
        'Предохранительная': ('Safety', '安全'),
        'Обратная': ('Check (non-return)', '止回'),
    },
    'ValveActuationVariety': {
        'Голый шток (без механизма)': ('Bare stem (no actuator)', '裸阀杆（无执行机构）'),
        'Ручка': ('Handle', '手柄'),
        'Ручной редуктор': ('Manual gearbox', '手动减速器'),
        'Электропривод': ('Electric actuator', '电动执行器'),
        'Пневмопривод': ('Pneumatic actuator', '气动执行器'),
    },
    'ValveTypes': {
        'Кран шаровый': ('Ball valve', '球阀'),
        'Затвор дисковый': ('Butterfly valve', '蝶阀'),
        'Задвижка клиновая': ('Wedge gate valve', '楔式闸阀'),
        'Задвижка шиберная': ('Knife gate valve', '刀闸阀'),
        'Клапан': ('Valve', '阀门'),
        'Обратный клапан': ('Check valve', '止回阀'),
        'Клапан (вентиль)': ('Globe valve', '截止阀'),
    },
    'ThreadInnerOuter': {
        'Внутренняя': ('Internal', '内螺纹'),
        'Наружная': ('External', '外螺纹'),
    },
    'SafetyPositionOption': {
        'НЗ - Нормально - Закрытое': ('NC - Normally Closed', '常闭'),
        'НО - Нормально-Открытое': ('NO - Normally Open', '常开'),
        'Оставаться в текущем положении': ('Stay in current position', '保持当前位置'),
    },
    'ExplosionProtectionMethod': {
        'Ex d (Взрывонепроницаемая оболочка)': ('Ex d (Flameproof enclosure)', 'Ex d（隔爆外壳）'),
        'Ex i (Искробезопасная электрическая цепь)': ('Ex i (Intrinsic safety)', 'Ex i（本质安全电路）'),
        'Ex t (Защита оболочкой от пыли)': ('Ex t (Protection by enclosure — dust)', 'Ex t（粉尘外壳保护）'),
        'Ex e (Повышенная защита вида «е»)': ('Ex e (Increased safety)', 'Ex e（增安型）'),
        'Ex m (Герметизация компаундом)': ('Ex m (Encapsulation)', 'Ex m（浇封型）'),
    },
    'OperatingModeOption': {
        'S2 - 15мин': ('S2 - 15min', 'S2 - 15分钟'),
        'S4 - 25%': ('S4 - 25%', 'S4 - 25%'),
        'S2-15мин/S4-25%': ('S2-15min/S4-25%', 'S2-15分钟/S4-25%'),
    },
}


def apply_translations(apps, schema_editor):
    for model_name, trans in TRANSLATIONS.items():
        Model = apps.get_model('params', model_name)
        updated = 0
        for obj in Model.objects.all():
            if obj.name in trans:
                en, cn = trans[obj.name]
                i18n = dict(obj.name_i18n or {})
                i18n['en'] = en
                i18n['cn'] = cn
                obj.name_i18n = i18n
                obj.save(update_fields=['name_i18n'])
                updated += 1
        print(f'  {model_name}: {updated} translated')


def revert_translations(apps, schema_editor):
    for model_name in TRANSLATIONS:
        Model = apps.get_model('params', model_name)
        for obj in Model.objects.all():
            i18n = dict(obj.name_i18n or {})
            changed = i18n.pop('en', None) is not None or i18n.pop('cn', None) is not None
            if changed:
                obj.name_i18n = i18n
                obj.save(update_fields=['name_i18n'])


class Migration(migrations.Migration):
    dependencies = [
        ('params', '0070_actuatorgearboxcombinationtypes_description_i18n_and_more'),
    ]

    operations = [
        migrations.RunPython(apply_translations, revert_translations),
    ]
