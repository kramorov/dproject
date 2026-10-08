"""Исправляет опечатку «AISl»→«AISI» и заполняет en/cn свободных текстов материалов.

Поля: GearBox.body_material_text, FilterRegulatorModelLine.body_material_text /
bowl_material_text / protection_material (свободные тексты «для описания»).

Перевод хранится в соседних ``<field>_i18n`` JSONField (канон lang.md §1):
``{"ru": ..., "en": ..., "cn": ...}``. Ключ словаря — точная RU-строка после
исправления опечатки. Коды/бренды не трогаются.

Идемпотентна: повторный запуск просто перезаписывает ru/en/cn и повторно
исправляет (уже исправленную) строку не меняет.
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


class Command(BaseCommand):
    help = 'Fix AISl→AISI and backfill en/cn for free-text material fields.'

    def handle(self, *args, **options):
        updated = 0

        # GearBox: body_material_text на самом айтеме.
        for item in GearBox.objects.all():
            raw = item.body_material_text or ''
            fixed = DATA_FIXES.get(raw, raw)
            changed = False
            update_fields = []
            if fixed != raw:
                item.body_material_text = fixed
                changed = True
                update_fields.append('body_material_text')
            i18n = _localize(fixed)
            if i18n is not None:
                item.body_material_text_i18n = i18n
                changed = True
                update_fields.append('body_material_text_i18n')
            if changed:
                item.save(update_fields=update_fields)
                updated += 1

        # FilterRegulatorModelLine: три свободных текста.
        fields = ('body_material_text', 'bowl_material_text', 'protection_material')
        for ml in FilterRegulatorModelLine.objects.all():
            changed = False
            update_fields = []
            for field in fields:
                i18n_field = f'{field}_i18n'
                raw = getattr(ml, field) or ''
                fixed = DATA_FIXES.get(raw, raw)
                if fixed != raw:
                    setattr(ml, field, fixed)
                    changed = True
                    update_fields.append(field)
                i18n = _localize(fixed)
                if i18n is not None:
                    setattr(ml, i18n_field, i18n)
                    changed = True
                    update_fields.append(i18n_field)
            if changed:
                ml.save(update_fields=update_fields)
                updated += 1

        self.stdout.write(self.style.SUCCESS(f'Done. Updated rows: {updated}'))
