# cable_glands/management/commands/generate_cable_gland_combinations.py
"""Генерация всех комбинаций CableGland для бренда БЛОК (BLOCK).

Сервисная команда: для каждой серии бренда перебирает опции
резьбы (CableGlandThreadOption, по корпусу «модели в серии»),
материала корпуса (CableGlandBodyMaterialOption) и взрывозащиты
(CableGlandExdOption — в данных одна строка на серию) и собирает
полный декартов набор артикулов.

Поведение (идемпотентно):
  * если артикул для комбинации уже существует — новая запись не создаётся,
    поля name/code/description перегенерируются из шаблонов серии, SKU
    синхронизируется;
  * если артикула нет — создаётся новый (+SKU).

Идентичность артикула определяется сочетанием
(model_line_item, thread_option, body_material_option, exd_option);
дополнительно делается fallback-поиск по code (уникальному), чтобы подхватить
устаревшие записи, созданные без опций (например, id=10 «20s16 КНК»).

Использование:
    python manage.py generate_cable_gland_combinations --dry-run
    python manage.py generate_cable_gland_combinations
    python manage.py generate_cable_gland_combinations --brand БЛОК BLOCK
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from cable_glands.models import (
    CableGland,
    CableGlandModelLine,
    CableGlandModelLineItem,
    CableGlandThreadOption,
    CableGlandBodyMaterialOption,
    CableGlandExdOption,
)
from sku.models import SKU

# Имена брендов, для которых генерируем комбинации. В данных это «BLOCK»,
# но пользователь оперирует также «БЛОК» — поддерживаем оба написания.
TARGET_BRANDS = ('БЛОК', 'BLOCK')


class Command(BaseCommand):
    help = 'Сгенерировать все комбинации CableGland (резьба × материал × взрывозащита) для бренда БЛОК'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только рассчитать комбинации и показать, что будет создано/обновлено, без записи в БД.',
        )
        parser.add_argument(
            '--brand',
            nargs='*',
            default=list(TARGET_BRANDS),
            help='Имена брендов для фильтра серий (по умолчанию: БЛОК BLOCK).',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        brands = options['brand'] or list(TARGET_BRANDS)

        model_lines = (
            CableGlandModelLine.objects
            .filter(brand__name__in=brands)
            .order_by('id')
        )
        ml_count = model_lines.count()
        if not ml_count:
            self.stdout.write(self.style.WARNING(
                f'Не найдено серий с брендами {brands}. Ничего не делаю.'
            ))
            return

        total_combos = 0
        created = 0
        updated = 0
        errors = 0
        skipped_no_options = 0

        for ml in model_lines:
            bm_options = list(
                CableGlandBodyMaterialOption.objects
                .filter(model_line=ml, is_active=True)
                .order_by('sorting_order', 'id')
            )
            exd_options = list(
                CableGlandExdOption.objects
                .filter(model_line=ml, is_active=True)
                .order_by('sorting_order', 'id')
            )
            items = list(
                CableGlandModelLineItem.objects
                .filter(model_line=ml, is_active=True)
                .select_related('body')
                .order_by('sorting_order', 'id')
            )

            if not bm_options or not exd_options:
                self.stdout.write(self.style.WARNING(
                    f'Серия {ml.code or ml.id}: нет опций материала/взрывозащиты — пропуск.'
                ))
                continue

            self.stdout.write(f'Серия {ml.code or ml.id}: '
                              f'{len(items)} моделей × {len(bm_options)} материалов '
                              f'× {len(exd_options)} Exd')

            for mli in items:
                body = mli.body
                if not body:
                    skipped_no_options += 1
                    continue

                thread_options = list(
                    CableGlandThreadOption.objects
                    .filter(cable_gland_body=body, is_active=True)
                    .order_by('sorting_order', 'id')
                )
                if not thread_options:
                    skipped_no_options += 1
                    self.stderr.write(
                        f'  ✕ {mli.code or mli.id}: нет активных опций резьбы для корпуса {body.code or body.id}'
                    )
                    continue

                for thread_opt in thread_options:
                    for bm_opt in bm_options:
                        for exd_opt in exd_options:
                            total_combos += 1
                            try:
                                status, item = self._process_combination(
                                    ml, mli, thread_opt, bm_opt, exd_opt, dry_run
                                )
                                if status == 'created':
                                    created += 1
                                else:
                                    updated += 1
                                if dry_run:
                                    self.stdout.write(
                                        f'  [dry-run] {"+" if status == "created" else "~"} '
                                        f'{item.code or item.name or "—"}'
                                    )
                            except Exception as e:
                                errors += 1
                                self.stderr.write(
                                    f'  ✕ {mli.code or mli.id} / {getattr(thread_opt, "encoding", "") or "default"} '
                                    f'/ {getattr(bm_opt, "encoding", "") or "default"} '
                                    f'/ {getattr(exd_opt, "encoding", "") or "default"}: {e}'
                                )

        summary = (
            f'\nГотово{" (dry-run)" if dry_run else ""}. '
            f'Комбинаций: {total_combos} | Создано: {created} | Обновлено: {updated} '
            f'| Ошибок: {errors} | Пропущено (нет опций): {skipped_no_options}'
        )
        if errors:
            self.stdout.write(self.style.WARNING(summary))
        else:
            self.stdout.write(self.style.SUCCESS(summary))

    # ──────────────────────────────────────────────────────────────────
    # Обработка одной комбинации
    # ──────────────────────────────────────────────────────────────────

    def _process_combination(self, ml, mli, thread_opt, bm_opt, exd_opt, dry_run):
        """Создать/обновить артикул для одной комбинации опций.

        Возвращает (status, item), где status ∈ {'created', 'updated'}.
        """
        # Артикул вычисляем заранее: он однозначно определяет и SKU, и запись.
        tmp = CableGland(
            model_line=ml,
            model_line_item=mli,
            thread_option=thread_opt,
            body_material_option=bm_opt,
            exd_option=exd_opt,
        )
        code = tmp.generated_model_item_code or None

        existing = self._find_existing(mli, thread_opt, bm_opt, exd_opt, code)
        if existing is not None:
            item = existing
            item.model_line = ml
            item.model_line_item = mli
            item.thread_option = thread_opt
            item.body_material_option = bm_opt
            item.exd_option = exd_opt
            status = 'updated'
        else:
            item = CableGland(
                model_line=ml,
                model_line_item=mli,
                thread_option=thread_opt,
                body_material_option=bm_opt,
                exd_option=exd_opt,
            )
            status = 'created'

        item.code = code

        if dry_run:
            return status, item

        with transaction.atomic():
            # save() перегенерирует name/description из шаблонов серии
            # (TemplateMixin.save) и синхронизирует SKU (sync_sku).
            item.save()
            self._sync_sku_code(item)

        return status, item

    def _find_existing(self, mli, thread_opt, bm_opt, exd_opt, code):
        """Найти существующий артикул по комбинации, с fallback по code."""
        item = CableGland.objects.filter(
            model_line_item_id=mli.id,
            thread_option_id=thread_opt.id if thread_opt else None,
            body_material_option_id=bm_opt.id if bm_opt else None,
            exd_option_id=exd_opt.id if exd_opt else None,
        ).first()
        if item is not None:
            return item
        if code:
            return CableGland.objects.filter(code=code).first()
        return None

    def _sync_sku_code(self, item):
        """Поддержать SKU.code в актуальном состоянии, если артикул перегенерировался.

        sync_sku() обновляет name/description/brand/equipment_type, но не трогает
        code; поэтому при изменении кода артикула подтягиваем код у привязанного SKU.
        """
        if not item.sku_id:
            return
        sku = item.sku
        if not sku or sku.code == item.code:
            return
        if SKU.objects.filter(code=item.code).exclude(pk=sku.pk).exists():
            raise CommandError(
                f'Конфликт кода SKU {item.code}: код уже занят другим SKU (артикул {item.pk}).'
            )
        sku.code = item.code
        sku.save(update_fields=['code'])
