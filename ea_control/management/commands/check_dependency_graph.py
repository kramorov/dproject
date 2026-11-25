"""Проверить зависимости условных строк матрицы на циклы (slots.md §6)."""
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand

from ea_control.models import ControlUnit, CuMatrixEntry
from ea_control.services.cu_matrix import _conditional_order


class Command(BaseCommand):
    help = 'Проверить условные строки матрицы на циклы (slots.md §6.3).'

    def handle(self, *args, **options):
        problems = []
        total = 0
        for unit in ControlUnit.objects.all().order_by('code'):
            rows = list(CuMatrixEntry.objects.filter(
                control_unit=unit, when_slot__isnull=False,
                option__isnull=False, is_active=True,
            ).select_related('when_slot', 'option__slot'))
            if not rows:
                continue
            total += len(rows)
            try:
                _conditional_order(rows)
            except ImproperlyConfigured as exc:
                problems.append((unit.code, str(exc)))

        if problems:
            self.stderr.write(self.style.ERROR('Обнаружены циклы зависимостей:'))
            for code, msg in problems:
                self.stderr.write(f'  {code}: {msg}')
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS(
            f'Циклов нет. Условных строк: {total}.'))
