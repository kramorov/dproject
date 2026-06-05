# pneumatic_fittings/management/commands/sync_pf_sku.py
"""
Консольная команда: перезаписать все PneumaticFitting для создания SKU.

Использование:
    python manage.py sync_pf_sku

Что делает:
    - Проходит по всем PneumaticFitting (is_active=True)
    - Вызывает save(), который дёргает sync_sku()
    - Выводит статистику: создано / обновлено / пропущено / ошибки
"""
from django.core.management.base import BaseCommand

from pneumatic_fittings.models import PneumaticFitting


class Command(BaseCommand):
    help = 'Перезаписать все PneumaticFitting для синхронизации с SKU'

    def handle(self, *args, **options):
        qs = PneumaticFitting.objects.filter(is_active=True).select_related('sku')
        total = qs.count()
        self.stdout.write(f'Найдено {total} объектов PneumaticFitting (is_active=True)')

        created = 0
        updated = 0
        errors = 0

        for pf in qs.iterator():
            had_sku = bool(pf.sku_id)
            try:
                pf.save()
                if had_sku:
                    updated += 1
                    self.stdout.write(f'  ↻ {pf.code or pf.id}: SKU обновлён')
                else:
                    created += 1
                    self.stdout.write(f'  + {pf.code or pf.id}: SKU создан')
            except Exception as e:
                errors += 1
                self.stderr.write(f'  ✕ {pf.code or pf.id}: {e}')

        self.stdout.write(self.style.SUCCESS(
            f'\nГотово. Всего: {total} | Создано: {created} | Обновлено: {updated} | Ошибок: {errors}'
        ))
