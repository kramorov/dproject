"""
Экспорт матрицы сигналов серии ЭП в Excel.

    python manage.py export_ea_signal_matrix --series AR01E [--output путь]
"""
from django.core.management.base import BaseCommand

from electric_actuators.services import ea_matrix_io


class Command(BaseCommand):
    help = 'Экспорт матрицы сигналов серии ЭП в xlsx'

    def add_arguments(self, parser):
        parser.add_argument('--series', required=True)
        parser.add_argument('--output', default=None)

    def handle(self, *args, **options):
        headers, rows = ea_matrix_io.export_wide_rows(options['series'])
        d_fields, d_rows = ea_matrix_io.export_device_rows(options['series'])
        extra = ea_matrix_io.export_extra_sheets(options['series'])
        path = options['output'] or f'ea_matrix_{options["series"]}.xlsx'
        ea_matrix_io.write_wide_xlsx(path, headers, rows, d_fields, d_rows,
                                     extra_sheets=extra)
        self.stdout.write(self.style.SUCCESS(
            f'{path}: {len(rows)} строк x {len(headers)} колонок + листы '
            f'{[s[0] for s in extra]}'))
