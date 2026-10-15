# pa_controls/management/commands/generate_posi_cards.py
"""
Материализация карточек позиционеров (PosiModelLineItem) для всех валидных
комбинаций опций серий (аналог generate_pa_cards для пневмоприводов).

Walk: серии (PosiModelLine, опционально по бренду) × доступные опции
(через through-модели, как в PositionerConstructor.get_available_options):
body_connections × levers × temperatures × signal_profiles × alarms × exd_rows.

Материализация — через pa_controls.services.posi_sku_service.materialize():
  - валидация комбинаций (рычаг/тип, доступность по взрывозащите) — невалидные
    комбинации пропускаются;
  - дедупликация по артикулу (code однозначно определяет SKU);
  - SKU синхронизируется в item.save() (SKUMixin.sync_sku);
  - exd M2M и галерея опции «Профиль сигналов» проставляются сервисом.

Примеры:
    python manage.py generate_posi_cards --brand Tissin
    python manage.py generate_posi_cards --model-line 4
    python manage.py generate_posi_cards --brand Tissin --dry-run
"""
import itertools
import logging
import time

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError

from pa_controls.models import PosiModelLine, PosiModelLineItem
from pa_controls.models.posi_model_line import (
    PosiAlarmOption,
    PosiBodyConnectionOption,
    PosiExdOption,
    PosiLeverOption,
    PosiSignalProfileOption,
    PosiTemperatureOption,
)
from pa_controls.services.posi_sku_service import materialize

logger = logging.getLogger(__name__)


class _ComboAdapter:
    """Лёгкий адаптер опций одной комбинации под контракт materialize(constructor)."""

    def __init__(self, model_line, body_connection, lever, temp_row,
                 signal_row, alarm, exd_row):
        self.selected_model_line = model_line
        self.selected_model_line_id = model_line.id
        self.selected_body_connection = body_connection
        self.selected_lever = lever
        if temp_row is not None:
            self.work_temp_min = temp_row.work_temp_min
            self.work_temp_max = temp_row.work_temp_max
        else:
            self.work_temp_min = None
            self.work_temp_max = None
        self.selected_signal_profile = signal_row.signal_profile if signal_row else None
        self.selected_smart_capability_set = (
            signal_row.smart_capability_set if signal_row else None)
        self.selected_alarm = alarm
        self.selected_exd_row = exd_row
        self._signal_row = signal_row

    def get_image_gallery(self):
        """Галерея опции «Профиль сигналов» (если задана), иначе None (фолбэк на серию)."""
        row = self._signal_row
        if row is not None and row.image_gallery_id:
            return row.image_gallery
        return None


class Command(BaseCommand):
    help = 'Материализовать карточки PosiModelLineItem для всех комбинаций опций серий.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--brand', type=str, default='Tissin',
            help='Бренд серий позиционеров (поиск по имени, регистронезависимый).',
        )
        parser.add_argument(
            '--model-line', type=int, default=None,
            help='Ограничиться одной серией (ID PosiModelLine) — приоритетнее --brand.',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Только посчитать комбинации, не писать в БД.',
        )

    PROGRESS_EVERY = 100

    def handle(self, *args, **options):
        ml_id = options['model_line']
        brand = options['brand']
        dry_run = options['dry_run']

        mls = PosiModelLine.objects.filter(is_active=True).select_related(
            'brand', 'acting_type', 'equipment_type',
        )
        if ml_id:
            mls = mls.filter(id=ml_id)
        elif brand:
            mls = mls.filter(brand__name__icontains=brand)
        mls = list(mls)
        if not mls:
            raise CommandError('Нет серий позиционеров для генерации.')

        total_combos = 0
        created_total = skipped_total = errors_total = 0
        for ml in mls:
            before_count = PosiModelLineItem.objects.filter(model_line=ml).count()
            combos = self._iter_combos(ml)
            if dry_run:
                n = 0
                for _ in combos:
                    n += 1
                total_combos += n
                self.stdout.write(
                    f'[dry-run] {ml.code}: комбинаций={n}, карточек сейчас={before_count}'
                )
                continue

            skipped = errors = processed = 0
            for adapter in combos:
                processed += 1
                if processed % self.PROGRESS_EVERY == 0:
                    self.stdout.write(
                        f'{ml.code}: обработано {processed}, пропущено {skipped}, ошибок {errors}'
                    )
                try:
                    self._materialize_with_retry(adapter)
                except ValidationError:
                    skipped += 1
                except Exception:
                    errors += 1
                    logger.exception('Ошибка материализации карточки %s', ml.code)

            after_count = PosiModelLineItem.objects.filter(model_line=ml).count()
            total_combos += processed
            created_total += max(after_count - before_count, 0)
            skipped_total += skipped
            errors_total += errors
            self.stdout.write(self.style.SUCCESS(
                f'{ml.code}: обработано={processed}, карточек={after_count} '
                f'(новых={after_count - before_count}), пропущено (невалидных)={skipped}, '
                f'ошибок={errors}'
            ))

        suffix = ' (dry-run)' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'Готово: комбинаций={total_combos}, создано={created_total}, '
            f'пропущено={skipped_total}, ошибок={errors_total}{suffix}'
        ))

    MAX_RETRIES = 3
    RETRY_DELAY_SEC = 1.0

    @classmethod
    def _materialize_with_retry(cls, adapter):
        """materialize с повтором при transient-блокировке SQLite (database is locked).

        Dev-сервер/другие процессы могут держать короткую блокировку БД —
        повтор через паузу обычно проходит (операция идемпотентна: дедуп по коду).
        """
        for attempt in range(1, cls.MAX_RETRIES + 1):
            try:
                return materialize(adapter)
            except OperationalError:
                if attempt == cls.MAX_RETRIES:
                    raise
                time.sleep(cls.RETRY_DELAY_SEC * attempt)

    @staticmethod
    def _iter_combos(ml):
        """Все комбинации опций серии (декартово произведение).

        Рычаги фильтруются типом действия серии (как в конструкторе).
        Отсутствующая группа опций → единственный вариант «не задано» (None).
        """
        body_connections = PosiBodyConnectionOption.objects.filter(
            model_line=ml, is_active=True,
        ).select_related('body_connection')
        levers = PosiLeverOption.objects.filter(
            model_line=ml, is_active=True,
        ).select_related('lever', 'lever__acting_type')
        if ml.acting_type_id:
            levers = levers.filter(lever__acting_type_id=ml.acting_type_id)
        temperatures = PosiTemperatureOption.objects.filter(
            model_line=ml, is_active=True,
        )
        signal_profiles = PosiSignalProfileOption.objects.filter(
            model_line=ml, is_active=True,
        ).select_related('signal_profile', 'smart_capability_set', 'image_gallery')
        alarms = PosiAlarmOption.objects.filter(
            model_line=ml, is_active=True,
        ).select_related('alarm')
        exd_rows = PosiExdOption.objects.filter(
            model_line=ml, is_active=True,
        ).prefetch_related('exd_options')

        bc_choices = [r.body_connection for r in body_connections] or [None]
        lever_choices = [r.lever for r in levers] or [None]
        temp_choices = list(temperatures) or [None]
        sig_choices = list(signal_profiles) or [None]
        alarm_choices = [r.alarm for r in alarms] or [None]
        exd_choices = list(exd_rows) or [None]

        for bc, lever, temp_row, sig_row, alarm, exd_row in itertools.product(
            bc_choices, lever_choices, temp_choices,
            sig_choices, alarm_choices, exd_choices,
        ):
            yield _ComboAdapter(ml, bc, lever, temp_row, sig_row, alarm, exd_row)
