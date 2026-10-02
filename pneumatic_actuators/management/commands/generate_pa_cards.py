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

    def handle(self, *args, **options):
        ml_id = options['model_line']
        dry_run = options['dry_run']
        archive = options['archive']

        mlis = PneumaticActuatorModelLineItem.objects.select_related(
            'model_line', 'body', 'pneumatic_actuator_variety',
        ).filter(model_line__isnull=False)
        if ml_id:
            mlis = mlis.filter(model_line_id=ml_id)
        mlis = list(mlis)
        if not mlis:
            raise CommandError('Нет типоразмеров (model_line_item) для генерации.')

        created = updated = reactivated = errors = 0
        seen_hashes = set()

        for mli in mlis:
            for kwargs in self._iter_combos(mli):
                probe = PneumaticActuatorCatalogItem(
                    source_model_line_item=mli,
                    exclude_from_catalog=True,
                    origin=PneumaticActuatorCatalogItem.Origin.GENERATED,
                    **kwargs,
                )
                config_hash = probe.compute_config_hash()
                code = probe.generated_model_item_code
                seen_hashes.add(config_hash)

                existing = PneumaticActuatorCatalogItem.objects.filter(
                    config_hash=config_hash,
                ).first()

                if existing is not None:
                    if existing.origin == PneumaticActuatorCatalogItem.Origin.MANUAL:
                        # Ручная карточка с этой конфигурацией — не трогаем.
                        continue
                    if not existing.is_active:
                        reactivated += 1
                        if not dry_run:
                            existing.is_active = True
                            existing.save()
                            if existing.sku_id:
                                SKU.objects.filter(pk=existing.sku_id).update(is_active=True)
                        continue
                    if existing.code != code:
                        updated += 1
                        if not dry_run:
                            existing.code = code
                            existing.save()  # пересчёт name/description + sync_sku
                    continue

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
                        code, config_hash,
                    )

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
        )
        coating = PneumaticBodyDesignOption.objects.filter(
            model_line=model_line, is_active=True,
        )
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
        hand_wheel_choices = [o.hand_wheel_option for o in hand_wheel] or [None]

        for sp, sq, temp, ip_opt, exd_opt, coat_opt, hw_opt in itertools.product(
            safety_choices, springs_choices, temperature_choices,
            ip_choices, exd_choices, coating_choices, hand_wheel_choices,
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
                'selected_manual_override': hw_opt,
            }
