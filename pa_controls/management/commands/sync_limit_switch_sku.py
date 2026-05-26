# pa_controls/management/commands/sync_limit_switch_sku.py
"""
Консольная команда: перезаписать все LimitSwitchBox для создания SKU.

Использование:
    python manage.py sync_gearbox_sku

Что делает:
    - Проходит по всем LimitSwitchBox (is_active=True)
    - Вызывает save(), который дёргает sync_sku()
    - Выводит статистику: создано / обновлено / пропущено / ошибки
"""
from django.core.management.base import BaseCommand

from pa_controls.models.limit_switch import LimitSwitchBox


class Command(BaseCommand):
    help = 'Перезаписать все GearBox для синхронизации с SKU'

    def handle(self, *args, **options):
        qs = LimitSwitchBox.objects.filter(is_active=True).select_related('sku')
        total = qs.count()
        self.stdout.write(f'Найдено {total} объектов LimitSwitchBox (is_active=True)')

        created = 0
        updated = 0
        skipped = 0
        errors = 0

        for gb in qs.iterator():
            had_sku = bool(gb.sku_id)
            try:
                gb.save()
                if had_sku:
                    updated += 1
                    self.stdout.write(f'  ↻ {gb.code or gb.id}: SKU обновлён')
                else:
                    created += 1
                    self.stdout.write(f'  + {gb.code or gb.id}: SKU создан')
            except Exception as e:
                errors += 1
                self.stderr.write(f'  ✕ {gb.code or gb.id}: {e}')

        self.stdout.write(self.style.SUCCESS(
            f'\nГотово. Всего: {total} | Создано: {created} | Обновлено: {updated} | Ошибок: {errors}'
        ))
