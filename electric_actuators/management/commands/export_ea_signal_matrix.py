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
        import openpyxl
        d_fields, d_rows = ea_matrix_io.export_device_rows(options['series'])
        extra = ea_matrix_io.export_extra_sheets(options['series'])
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'ea_signal_matrix'
        ws.append(d_fields or [])
        for row in d_rows:
            ws.append([row.get(f, '') for f in (d_fields or [])])
        for sheet_name, fields, sheet_rows in extra:
            ws2 = wb.create_sheet(sheet_name)
            ws2.append(fields)
            for row in sheet_rows:
                ws2.append([row.get(f, '') for f in fields])
        path = options['output'] or f'ea_matrix_{options["series"]}.xlsx'
        wb.save(path)
        self.stdout.write(self.style.SUCCESS(
            f'{path}: device {len(d_rows)} строк + листы '
            f'{[s[0] for s in extra]}'))
