"""
Импорт матрицы сигналов серии ЭП из Excel (формат экспорта).

    python manage.py import_ea_signal_matrix --file ea_matrix_AR01E.xlsx
"""
from django.core.management.base import BaseCommand

from electric_actuators.services import ea_matrix_io


class Command(BaseCommand):
    help = 'Импорт матрицы сигналов ЭП из xlsx (upsert)'

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True)

    def handle(self, *args, **options):
        rows = ea_matrix_io.read_xlsx(options['file'])
        stats = ea_matrix_io.apply_import(rows)
        self.stdout.write(self.style.SUCCESS(
            f'Импорт: создано {stats["created"]}, обновлено {stats["updated"]}, '
            f'ошибок {len(stats["errors"])}'))
        for err in stats['errors'][:20]:
            self.stdout.write(self.style.WARNING(f'  {err}'))
