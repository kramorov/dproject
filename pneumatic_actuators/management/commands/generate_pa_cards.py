# pneumatic_actuators/management/commands/generate_pa_cards.py
"""
Материализация карточек пневмоприводов (PneumaticActuatorCatalogItem) для всех валидных
комбинаций опций.

Walk: типоразмеры (PneumaticActuatorModelLineItem) × доступные опции (через
through-модели, как в get_available_options). Дифф по config_hash:

  - новый хэш → создать карточку + SKU;
  - хэш исчез из набора → is_active=False (карточка + SKU) при --archive;
  - encoding изменился → та же карточка, пересчитанный code.

Карточки создаются с exclude_from_catalog=True (не в листингах каталога,
но в глобальном поиске и деталке).
"""
import itertools
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from pneumatic_actuators.models.pa_item import PneumaticActuatorCatalogItem
from pneumatic_actuators.models.pa_model_line import PneumaticActuatorModelLineItem
from pneumatic_actuators.models.pa_options import (
    PneumaticSafetyPositionOption,
    PneumaticSpringsQtyOption,
    PneumaticTemperatureOption,
    PneumaticIpOption,
    PneumaticExdOption,
    PneumaticBodyDesignOption,
    PneumaticBodyColorOption,
    PneumaticManualOverrideOption,
)
from sku.models import SKU

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Материализовать карточки PneumaticActuatorCatalogItem для всех комбинаций опций.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model-line', type=int, default=None,
            help='Ограничиться одной серией (ID PneumaticActuatorModelLine)',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Только посчитать создаваемые/обновляемые, не писать в БД',
        )
        parser.add_argument(
            '--archive', action='store_true',
            help='Архивировать (is_active=False) комбинации, исчезнувшие из набора',
        )

    PROGRESS_EVERY = 100
    SAVE_BATCH_SIZE = 100

    def handle(self, *args, **options):
        ml_id = options['model_line']
        dry_run = options['dry_run']
        archive = options['archive']

        mlis = PneumaticActuatorModelLineItem.objects.select_related(
            'model_line', 'model_line__equipment_type', 'model_line__brand',
            'model_line__pneumatic_actuator_construction_variety',
            'body', 'pneumatic_actuator_variety',
        ).prefetch_related('body__pneumatic_connection').filter(
            model_line__isnull=False,
        )
        if ml_id:
            mlis = mlis.filter(model_line_id=ml_id)
        mlis = list(mlis)
        if not mlis:
            raise CommandError('Нет типоразмеров (model_line_item) для генерации.')

        # Существующие карточки — одним запросом со всеми связями: сравнение и
        # обновление идут на existing, чтобы генерация не делала ленивых запросов.
        existing_map_qs = PneumaticActuatorCatalogItem.objects.all()
        if ml_id:
            existing_map_qs = existing_map_qs.filter(model_line_id=ml_id)
        existing_map = {
            item.config_hash: item
            for item in existing_map_qs.select_related(
                'model_line', 'model_line__equipment_type', 'model_line__brand',
                'body', 'pneumatic_actuator_variety',
                'selected_safety_position', 'selected_springs_qty', 'selected_temperature',
                'selected_ip', 'selected_exd', 'selected_body_coating', 'selected_body_color',
                'selected_manual_override', 'manual_override_option',
                'manual_override_option__hand_wheel_option', 'sku',
            ).prefetch_related(
                'selected_exd__exd_options', 'body__pneumatic_connection',
            )
        }

        created = updated = reactivated = processed = errors = 0
        seen_hashes = set()
        pending_saves = []  # [(existing, update_fields)] — флаш батчем по SAVE_BATCH_SIZE

        for mli in mlis:
            for kwargs in self._iter_combos(mli):
                processed += 1
                self._log_progress(processed, updated)

                probe = PneumaticActuatorCatalogItem(
                    source_model_line_item=mli,
                    exclude_from_catalog=True,
                    origin=PneumaticActuatorCatalogItem.Origin.GENERATED,
                    **kwargs,
                )
                probe.weight = probe.compute_weight()
                config_hash = probe.compute_config_hash()
                seen_hashes.add(config_hash)

                existing = existing_map.get(config_hash)
                if existing is None:
                    created += 1
                    if dry_run:
                        continue
                    try:
                        with transaction.atomic():
                            probe.save()
                    except Exception:
                        errors += 1
                        logger.exception(
                            'Не удалось создать карточку: code=%s config_hash=%s',
                            probe.generated_model_item_code, config_hash,
                        )
                    continue

                if existing.origin == PneumaticActuatorCatalogItem.Origin.MANUAL:
                    # Ручная карточка с этой конфигурацией — не трогаем.
                    continue
                if not existing.is_active:
                    reactivated += 1
                    if not dry_run:
                        existing.is_active = True
                        existing.weight = probe.weight
                        existing.save()
                        if existing.sku_id:
                            SKU.objects.filter(pk=existing.sku_id).update(is_active=True)
                    continue

                # Сравнение на самом existing (конфигурация та же — карточка найдена
                # по config_hash): правки шаблонов/справочников меняют name/description
                # без изменения code. Свежий вес — до генерации: {weight} в шаблоне
                # должен видеть актуальное значение.
                old_weight = existing.weight
                existing.weight = probe.weight
                fresh_code = existing.generated_model_item_code
                fresh_name = existing.generate_name()
                fresh_description = existing.generate_description()
                name_stale = bool(fresh_name) and (existing.name or '') != fresh_name
                desc_stale = bool(fresh_description) and (
                    existing.description or '') != fresh_description

                if existing.code != fresh_code or name_stale or desc_stale:
                    updated += 1
                    if not dry_run:
                        # Пишем только реально изменившиеся поля (update_fields),
                        # а сами UPDATE — батчем в одной SQLite-транзакции
                        # (иначе 2–3 fsync на карточку: item + SKU).
                        update_fields = set()
                        if existing.code != fresh_code:
                            existing.code = fresh_code
                            update_fields.add('code')
                        if name_stale and fresh_name:
                            existing.name = fresh_name
                            update_fields.add('name')
                        if desc_stale and fresh_description:
                            existing.description = fresh_description
                            update_fields.add('description')
                        if old_weight != probe.weight:
                            update_fields.add('weight')
                        # config_hash пересчитывается в save() — включаем в UPDATE.
                        update_fields.add('config_hash')
                        pending_saves.append((existing, update_fields))
                        if len(pending_saves) >= self.SAVE_BATCH_SIZE:
                            self._flush_pending(pending_saves)

        self._flush_pending(pending_saves)

        archived = 0
        if archive and not dry_run:
            qs = PneumaticActuatorCatalogItem.objects.filter(
                is_active=True,
                origin=PneumaticActuatorCatalogItem.Origin.GENERATED,
            )
            if ml_id:
                qs = qs.filter(model_line_id=ml_id)
            for item in qs.iterator(chunk_size=500):
                if item.config_hash and item.config_hash not in seen_hashes:
                    item.is_active = False
                    item.save()
                    if item.sku_id:
                        SKU.objects.filter(pk=item.sku_id).update(is_active=False)
                    archived += 1

        suffix = ' (dry-run)' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'Готово: создано={created}, обновлено={updated}, '
            f'реактивировано={reactivated}, архивировано={archived}, '
            f'ошибок={errors}{suffix}'
        ))

    @staticmethod
    def _flush_pending(pending_saves):
        """Сохранение пачки обновлений в одной транзакции (быстрый commit)."""
        if not pending_saves:
            return
        with transaction.atomic():
            for item, update_fields in pending_saves:
                item.save(update_fields=update_fields, skip_auto_generate=True)
        pending_saves.clear()

    def _log_progress(self, processed, updated):
        """Промежуточный лог хода работы (каждые PROGRESS_EVERY записей)."""
        if processed % self.PROGRESS_EVERY == 0:
            self.stdout.write(f'Обработано - {processed}, изменено - {updated}')

    def _iter_combos(self, mli):
        """Все комбинации опций типоразмера (декартово произведение)."""
        model_line = mli.model_line

        safety = PneumaticSafetyPositionOption.objects.filter(
            model_line_item=mli, is_active=True,
        ).select_related('safety_position')
        springs = PneumaticSpringsQtyOption.objects.filter(
            model_line_item=mli, is_active=True,
        ).select_related('springs_qty')
        temperature = PneumaticTemperatureOption.objects.filter(
            model_line=model_line, is_active=True,
        )
        ip = PneumaticIpOption.objects.filter(
            model_line=model_line, is_active=True,
        ).select_related('ip_option')
        exd = PneumaticExdOption.objects.filter(
            model_line=model_line, is_active=True,
        ).prefetch_related('exd_options')
        coating = PneumaticBodyDesignOption.objects.filter(
            model_line=model_line, is_active=True,
        ).select_related('body_material')
        color = PneumaticBodyColorOption.objects.filter(
            model_line=model_line, is_active=True,
        ).select_related('color_option')
        hand_wheel = PneumaticManualOverrideOption.objects.filter(
            model_line_item=mli, is_active=True,
        ).select_related('hand_wheel_option')

        # Отсутствующая категория → единственный вариант «не задано» (None).
        safety_choices = [o.safety_position for o in safety] or [None]
        springs_choices = [o.springs_qty for o in springs] or [None]
        temperature_choices = list(temperature) or [None]
        ip_choices = [o.ip_option for o in ip] or [None]
        exd_choices = list(exd) or [None]
        coating_choices = list(coating) or [None]
        color_choices = list(color) or [None]
        hand_wheel_choices = list(hand_wheel) or [None]  # через-опции с mo_weight

        for sp, sq, temp, ip_opt, exd_opt, coat_opt, color_opt, hw_opt in itertools.product(
            safety_choices, springs_choices, temperature_choices,
            ip_choices, exd_choices, coating_choices, color_choices, hand_wheel_choices,
        ):
            yield {
                'model_line': model_line,
                'body': mli.body,
                'pneumatic_actuator_variety': mli.pneumatic_actuator_variety,
                'selected_safety_position': sp,
                'selected_springs_qty': sq,
                'selected_temperature': temp,
                'selected_ip': ip_opt,
                'selected_exd': exd_opt,
                'selected_body_coating': coat_opt,
                'selected_body_color': color_opt,
                'selected_manual_override': hw_opt.hand_wheel_option if hw_opt else None,
                'manual_override_option': hw_opt,
            }
