# ea_control/management/commands/reconcile_cu_structure.py
"""
Идемпотентная сверка структуры конфигуратора БУ с канонической схемой.

Убирает дрейф между seed_cu_demo и живой БД:

- переименовывает слот CMD_SIGNAL_SOURCE → CMD_WIRING (один канонический код
  «Схема цепей управления»);
- удаляет дрейфовые слоты CMD_SIGNAL_SOURCE_ESD и SETPOINT_Copy (и их опции);
- удаляет мусорные опции-копии (ALARM_NONE_Copy и прочие *_Copy);
- удаляет устаревшие bare-строки матрицы «нет сигнала» (option=None) —
  их заменили явные опции *_NONE в новой структуре сигналов (во всех
  слотах: такие строки игнорируются редактором и резолверами, но могли
  ломать валидацию «одна std» у single-слотов);
- перепривязывает опцию слота STOP_SIGNAL (STOP_SPDT) к сигналу FB_STOP
  (была ошибочно привязана к сигналу аварии FB_ALARM*).

Запуск: python manage.py reconcile_cu_structure
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from ea_control.models import (
    CuFeedbackSignal, CuMatrixEntry, CuSlot, CuSlotOption,
)


class Command(BaseCommand):
    help = ('Сверяет структуру БУ с канонической схемой: переименование '
            'CMD_WIRING, удаление дрейфовых слотов/опций и bare-строк, '
            'перепривязка STOP_SPDT к FB_STOP.')

    def handle(self, *args, **options):
        with transaction.atomic():
            renamed = self._rename_cmd_wiring()
            removed_slots = self._remove_drift_slots()
            removed_opts = self._remove_copy_options()
            removed_rows = self._remove_bare_rows()
            repointed = self._repoint_stop_signal()

        self.stdout.write(self.style.SUCCESS(
            'Сверка завершена: переименовано %d, удалено слотов %d, '
            'опций %d, bare-строк %d, перепривязано %d.' % (
                len(renamed), len(removed_slots), len(removed_opts),
                len(removed_rows), len(repointed),
            )))

    def _rename_cmd_wiring(self):
        slot = CuSlot.objects.filter(code='CMD_SIGNAL_SOURCE').first()
        if not slot:
            return []
        if not CuSlot.objects.filter(code='CMD_WIRING').exists():
            slot.code = 'CMD_WIRING'
            slot.name = 'Схема цепей управления'
            slot.save(update_fields=['code', 'name'])
        else:
            # канонический слот уже есть — убираем дрейфовый дубль
            CuMatrixEntry.objects.filter(slot=slot).delete()
            slot.delete()
        return ['CMD_SIGNAL_SOURCE']

    def _remove_drift_slots(self):
        removed = []
        for code in ('CMD_SIGNAL_SOURCE_ESD', 'SETPOINT_Copy'):
            slot = CuSlot.objects.filter(code=code).first()
            if not slot:
                continue
            CuMatrixEntry.objects.filter(slot=slot).delete()
            slot.delete()  # опции удаляются каскадом (CuSlotOption.slot CASCADE)
            removed.append(code)
        return removed

    def _remove_copy_options(self):
        # мусорные копии опций, не привязанные к удаляемым выше слотам
        # (например ALARM_NONE_Copy у слота STOP_SIGNAL)
        qs = CuSlotOption.objects.filter(code__endswith='_Copy')
        codes = list(qs.values_list('code', flat=True))
        qs.delete()
        return codes

    def _remove_bare_rows(self):
        # устаревшие bare-строки «нет сигнала» (option=None) — заменены
        # явными опциями *_NONE в новой структуре сигналов. Редактор
        # матрицы и резолверы такие строки игнорируют; удаляем во всех
        # слотах, а не только CMD_* (напр. TORQUE_SWITCHES_OPEN/WAY_* —
        # остаток старой структуры пар контактов).
        qs = CuMatrixEntry.objects.filter(option__isnull=True)
        ids = list(qs.values_list('id', flat=True))
        qs.delete()
        return ids

    def _repoint_stop_signal(self):
        fb_stop = CuFeedbackSignal.objects.filter(code='FB_STOP').first()
        if not fb_stop:
            return []
        updated = CuSlotOption.objects.filter(code='STOP_SPDT').update(
            feedback_signal=fb_stop)
        return ['STOP_SPDT'] if updated else []
