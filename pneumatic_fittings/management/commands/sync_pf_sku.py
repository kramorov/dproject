# pneumatic_fittings/management/commands/sync_pf_sku.py
"""
Консольная команда: перезаписать все позиции фитингов/глушителей/заглушек
для создания/обновления SKU и пересчёта config_hash.

Использование:
    python manage.py sync_pf_sku
"""
from django.core.management.base import BaseCommand

from pneumatic_fittings.models import PneumaticFitting, PneumaticSilencer, PneumaticPlug


class Command(BaseCommand):
    help = 'Перезаписать все позиции фитингов/глушителей/заглушек для синхронизации с SKU'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        errors = 0
        total = 0

        for Model in (PneumaticFitting, PneumaticSilencer, PneumaticPlug):
            qs = Model.objects.filter(is_active=True).select_related('sku')
            total += qs.count()
            for pf in qs.iterator():
                had_sku = bool(pf.sku_id)
                try:
                    pf.save()
                    if had_sku:
                        updated += 1
                    else:
                        created += 1
                except Exception as e:
                    errors += 1
                    self.stderr.write(f'  ✕ {Model.__name__} {pf.code or pf.id}: {e}')

        self.stdout.write(self.style.SUCCESS(
            f'\nГотово. Всего: {total} | Создано: {created} | Обновлено: {updated} | Ошибок: {errors}'
        ))
