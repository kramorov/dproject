"""Пересчёт display_i18n для всех БКВ (Фаза 4, Шаг 4).

Запуск: python manage.py rebuild_display_i18n [--limit N]
Обновляет только поле display_i18n (queryset.update — без save()/sync_sku).
"""
from django.core.management.base import BaseCommand

from pa_controls.models import LimitSwitchBox


class Command(BaseCommand):
    help = 'Пересчитать display_i18n для всех БКВ (Фаза 4, пилот).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit', type=int, default=None,
            help='Ограничить количество айтемов (для проверки).',
        )

    def handle(self, *args, **options):
        qs = LimitSwitchBox.objects.select_related('model_line').order_by('pk')
        if options['limit']:
            qs = qs[: options['limit']]
        total = qs.count()
        updated = 0
        for item in qs.iterator():
            item.display_i18n = item.build_display_i18n()
            LimitSwitchBox.objects.filter(pk=item.pk).update(display_i18n=item.display_i18n)
            updated += 1
        self.stdout.write(f'display_i18n пересчитан: {updated}/{total}')
