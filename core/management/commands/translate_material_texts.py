"""Исправляет опечатку «AISl»→«AISI» и заполняет en/cn свободных текстов материалов.

Поля: GearBox.body_material_text, FilterRegulatorModelLine.body_material_text /
bowl_material_text / protection_material (свободные тексты «для описания»).

Перевод хранится в соседних ``<field>_i18n`` JSONField (канон lang.md §1):
``{"ru": ..., "en": ..., "cn": ...}``. Ключ словаря — точная RU-строка после
исправления опечатки. Коды/бренды не трогаются.

Идемпотентна: исправление опечатки применяется всегда; переводы en/cn — только
отсутствующие (ручные правки не перезаписываются). ``--force`` — перезаписать en/cn.
"""
from django.core.management.base import BaseCommand

from gearbox.models import GearBox
from filter_regulator.models import FilterRegulatorModelLine

# Опечатка в данных → корректное значение.
DATA_FIXES = {
    'Нержавеющая сталь AISl 316': 'Нержавеющая сталь AISI 316',
}

# Точная RU-строка → (en, cn).
TRANSLATIONS = {
    'Алюминий': ('Aluminium', '铝'),
    'Поликарбонат': ('Polycarbonate', '聚碳酸酯'),
    'Алюминиевый сплав / Углеродистая сталь': ('Aluminium alloy / Carbon steel', '铝合金 / 碳钢'),
    'Нержавеющая сталь AISI 316': ('Stainless steel AISI 316', '不锈钢 AISI 316'),
    'кожуха защиты нет': ('no guard', '无防护罩'),
}


def _localize(value):
    """Вернуть {ru, en, cn} для RU-значения или None, если перевода нет."""
    if not value:
        return None
    fixed = DATA_FIXES.get(value, value)
    en_cn = TRANSLATIONS.get(fixed)
    if not en_cn:
        return None
    return {'ru': fixed, 'en': en_cn[0], 'cn': en_cn[1]}


def _merge_i18n(current, localized, force):
    """Слить текущее значение с переведённым: ru — из словаря (канон после
    data-fix), en/cn — только отсутствующие, если не ``force``."""
    out = dict(current) if isinstance(current, dict) else {}
    out['ru'] = localized['ru']
    for locale in ('en', 'cn'):
        if force or locale not in out:
            out[locale] = localized[locale]
    return out


def _apply(field, obj, force):
    """Применить data-fix + переводы к полю ``field``; вернуть список update_fields."""
    i18n_field = f'{field}_i18n'
    raw = getattr(obj, field) or ''
    fixed = DATA_FIXES.get(raw, raw)
    update_fields = []
    if fixed != raw:
        setattr(obj, field, fixed)
        update_fields.append(field)
    localized = _localize(fixed)
    if localized is not None:
        merged = _merge_i18n(getattr(obj, i18n_field), localized, force)
        if merged != (getattr(obj, i18n_field) or {}):
            setattr(obj, i18n_field, merged)
            update_fields.append(i18n_field)
    return update_fields


class Command(BaseCommand):
    help = 'Fix AISl→AISI and backfill en/cn for free-text material fields.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перезаписать существующие переводы из словаря (затирает ручные правки).')

    def handle(self, *args, **options):
        force = options['force']
        updated = 0

        # GearBox: body_material_text на самом айтеме.
        for item in GearBox.objects.all():
            update_fields = _apply('body_material_text', item, force)
            if update_fields:
                item.save(update_fields=update_fields)
                updated += 1

        # FilterRegulatorModelLine: три свободных текста.
        fields = ('body_material_text', 'bowl_material_text', 'protection_material')
        for ml in FilterRegulatorModelLine.objects.all():
            update_fields = []
            for field in fields:
                update_fields.extend(_apply(field, ml, force))
            if update_fields:
                ml.save(update_fields=update_fields)
                updated += 1

        self.stdout.write(self.style.SUCCESS(f'Done. Updated rows: {updated}'))
