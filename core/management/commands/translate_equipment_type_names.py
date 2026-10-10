"""Заполняет en/cn переводы названий и описаний типов оборудования.

Ключ — точная ru-строка (name/description). Плейсхолдеров в name/description нет —
это имена классификатора, которые подставляются в шаблоны карточек через
``{equipment_type}`` (глушители/заглушки и т.п.).

Идемпотентна: заполняет только отсутствующие локали.
"""

from django.core.management.base import BaseCommand

from core.models.equipment_type import EquipmentType


NAME_TRANSLATIONS = {
    'Электропривод': ('Electric actuator', '电动执行器'),
    'Позиционер для ЭП': ('Positioner for electric actuator', '电动执行器定位器'),
    'Пневмопривод': ('Pneumatic actuator', '气动执行器'),
    'Позиционер для ПП': ('Positioner for pneumatic actuator', '气动执行器定位器'),
    'INT Блок для ЭП': ('INT block for electric actuator', '电动执行器INT模块'),
    'Трансмиттер для ЭП': ('Transmitter for electric actuator', '电动执行器变送器'),
    'Соленоидный клапан': ('Solenoid valve', '电磁阀'),
    'Блок концевых выключателей': ('Limit switch box', '限位开关盒'),
    'Фитинги': ('Fittings', '管接头'),
    'Ручной дублер': ('Manual override', '手动超越'),
    'Фильтр-регулятор': ('Filter-regulator', '过滤调压阀'),
    'Кабельный ввод': ('Cable gland', '电缆接头'),
    'МК ISO 5211/5210/ГОСТ/JB2920': ('MK ISO 5211/5210/GOST/JB2920', 'MK ISO 5211/5210/GOST/JB2920'),
    'MK - ФР к приводу': ('MK - FR to actuator', 'MK - 过滤调压阀安装到执行器'),
    'MK - БКВ к приводу': ('MK - LSB to actuator', 'MK - 限位开关盒安装到执行器'),
    'MK - распределителя к приводу': ('MK - directional valve to actuator', 'MK - 换向阀安装到执行器'),
    'Фитинг резьба-трубка': ('Thread-to-tube fitting', '螺纹-管接头'),
    'MK - позиционер к приводу': ('MK - positioner to actuator', 'MK - 定位器安装到执行器'),
    'Кран шаровый': ('Ball valve', '球阀'),
    'Затвор дисковый': ('Butterfly valve', '蝶阀'),
    'Задвижка клиновая': ('Gate valve', '闸阀'),
    'Задвижка шиберная': ('Knife gate valve', '刀闸阀'),
    'Smoke ET': ('Smoke ET', 'Smoke ET'),
    'Глушитель пневматический': ('Pneumatic silencer', '气动消音器'),
    'Заглушка пневматическая': ('Pneumatic plug', '气动堵头'),
}

DESCRIPTION_TRANSLATIONS = {
    'Дублер': ('Override', '超越器'),
    'Монтажный комплект (скоба) для крепления фильтр-регулятора к пневмоприводу':
        ('Mounting kit (bracket) for mounting filter-regulator to pneumatic actuator',
         '用于将过滤调压阀安装到气动执行器的安装套件（支架）'),
    'Монтажный комплект для крепления БКВ к пневмоприводу':
        ('Mounting kit for mounting limit switch box to pneumatic actuator',
         '用于将限位开关盒安装到气动执行器的安装套件'),
    'Монтажный комплект для крепления клапана-распределителя к пневмоприводу':
        ('Mounting kit for mounting directional valve to pneumatic actuator',
         '用于将换向阀安装到气动执行器的安装套件'),
    'Монтажный комплект для крепления позиционера к пневмоприводу':
        ('Mounting kit for mounting positioner to pneumatic actuator',
         '用于将定位器安装到气动执行器的安装套件'),
}


class Command(BaseCommand):
    help = 'Заполняет en/cn переводы name/description типов оборудования (ключ — ru-строка).'

    def handle(self, *args, **options):
        updated = 0
        missing = set()
        for et in EquipmentType.objects.all():
            for field, i18n_field, translations in (
                ('name', 'name_i18n', NAME_TRANSLATIONS),
                ('description', 'description_i18n', DESCRIPTION_TRANSLATIONS),
            ):
                value = getattr(et, field) or ''
                if not value:
                    continue
                i18n = getattr(et, i18n_field) or {}
                if not isinstance(i18n, dict):
                    i18n = {}
                changed = False
                for locale in ('en', 'cn'):
                    if locale not in i18n:
                        translation = translations.get(value)
                        if translation is not None:
                            i18n[locale] = translation[0 if locale == 'en' else 1]
                            changed = True
                        else:
                            missing.add('%s: %s' % (field, value[:80]))
                if changed:
                    setattr(et, i18n_field, i18n)
                    et.save()
                    updated += 1
        self.stdout.write(self.style.SUCCESS('обновлено полей: %d' % updated))
        if missing:
            self.stdout.write(self.style.WARNING('без перевода (fallback ru):'))
            for item in sorted(missing):
                self.stdout.write('  ' + item)
