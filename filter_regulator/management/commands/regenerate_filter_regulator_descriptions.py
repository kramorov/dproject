"""
Консольная команда: перегенерировать описания всех FilterRegulator из шаблонов.

Использование:
    python manage.py regenerate_filter_regulator_descriptions

Что делает:
    - Проходит по всем FilterRegulator (is_active=True)
    - Вызывает obj.save() → TemplateMixin.save() → update_description()
    - description генерируется из model_line.description_template
      или (если не задан) из _get_default_description_template()
    - Выводит статистику: обновлено / пропущено / ошибки
"""
from django.core.management.base import BaseCommand

from filter_regulator.models import FilterRegulator


class Command(BaseCommand):
    help = 'Перегенерировать описания всех FilterRegulator из шаблонов'

    def handle(self, *args, **options):
        qs = FilterRegulator.objects.filter(is_active=True)
        total = qs.count()
        self.stdout.write(f'Найдено {total} FilterRegulator (is_active=True)')

        updated = 0
        skipped = 0
        errors = 0

        for item in qs.iterator():
            old_desc = item.description or '(пусто)'
            try:
                item.save()  # TemplateMixin.save() → update_description()
                new_desc = item.description or '(пусто)'
                if old_desc != new_desc:
                    updated += 1
                    self.stdout.write(f'  ✓ {item.code or item.id}: "{old_desc[:60]}..." → "{new_desc[:60]}..."')
                else:
                    skipped += 1
            except Exception as e:
                errors += 1
                self.stderr.write(f'  ✕ {item.code or item.id}: {e}')

        self.stdout.write(self.style.SUCCESS(
            f'\nГотово. Всего: {total} | Обновлено: {updated} | Пропущено: {skipped} | Ошибок: {errors}'
        ))
