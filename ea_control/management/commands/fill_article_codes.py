# ea_control/management/commands/fill_article_codes.py
"""
Идемпотентная доводка артикульных кодировок опций БУ (вкладка «Кодировки»).

Для каждой строки базового профиля каждого типа БУ (scope пуст,
power_supply=None, mode=both, signal_power пуст, слот — не subtype):

- ``std`` → ``encoding=''``, ``ext_encoding=''`` (стандарт кодировку не даёт);
- ``opt`` → ``encoding=''``, ``ext_encoding`` = системная кодировка опции
  (``option.encoding``) — опция вносит свой код в ext-часть артикула;
- ``na`` → не трогаем (опция недоступна, вклада в артикул нет).

Строки других напряжений (power_supply != None) не меняются — они
переопределяют доступность, а не кодировку.

Запуск: python manage.py fill_article_codes
"""
from django.core.management.base import BaseCommand

from ea_control.models import ControlUnit, CuMatrixEntry


class Command(BaseCommand):
    help = ('Заполняет артикульные кодировки опций БУ: std → пусто, '
            'opt → ext = системная кодировка опции.')

    def handle(self, *args, **options):
        rows_qs = (CuMatrixEntry.objects
                   .filter(control_unit__isnull=False,
                           brand__isnull=True, model_line__isnull=True,
                           body__isnull=True, model_line_item__isnull=True,
                           power_supply__isnull=True, when_slot__isnull=True,
                           mode='both')
                   .exclude(slot__slot_kind='subtype')
                   .select_related('option'))

        updated = 0
        skipped = 0
        for row in rows_qs.iterator():
            if row.availability == 'std':
                encoding, ext_encoding = '', ''
            elif row.availability == 'opt':
                encoding, ext_encoding = '', (row.option.encoding
                                              if row.option_id else '')
            else:
                skipped += 1
                continue

            if (row.encoding or '') != encoding or (row.ext_encoding or '') != ext_encoding:
                row.encoding = encoding
                row.ext_encoding = ext_encoding
                row.save(update_fields=['encoding', 'ext_encoding'])
                updated += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            'Готово: обновлено %d строк, пропущено %d (na или без изменений).'
            % (updated, skipped)))
