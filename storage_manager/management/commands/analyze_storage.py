"""
python manage.py analyze_storage — сверка БД и бэкапа Cloud.ru.

Показывает по каждому MediaLibraryItem:
  - Сколько файлов должно быть (media_file + варианты по профилю)
  - Сколько файлов реально в облаке
  - Лишние preview_file (старое поле, дублирует MediaVariant)
  - Нехватку вариантов (есть PDF но нет превьюшек)

Использование:
    python manage.py analyze_storage
    python manage.py analyze_storage --manifest backups/cloudru/2026-06-01/manifest.json
"""
import json
import os
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Q

from media_library.models import MediaLibraryItem, MediaVariant, MediaCategory
from storage_manager.storage_backends.cloudru import CloudRuStorage


class Command(BaseCommand):
    help = 'Сверка БД и бэкапа: что сколько места занимает, где лишние preview'

    def add_arguments(self, parser):
        parser.add_argument('--manifest', help='Путь к manifest.json (если не указан — листинг Cloud.ru)')

    def handle(self, **options):
        manifest_path = options['manifest']
        if manifest_path:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            cloud_keys = {obj['key']: obj['size'] for obj in manifest['files']}
            cloud_total = sum(obj['size'] for obj in manifest['files'])
            source = f'манифест ({len(cloud_keys)} объектов, {self._fmt(cloud_total)})'
        else:
            storage = CloudRuStorage()
            s3 = storage.s3_admin
            bucket = storage.bucket_name
            cloud_keys = {}
            cloud_total = 0
            continuation_token = None
            while True:
                kw = {'Bucket': bucket, 'MaxKeys': 1000}
                if continuation_token:
                    kw['ContinuationToken'] = continuation_token
                resp = s3.list_objects_v2(**kw)
                for obj in resp.get('Contents', []):
                    cloud_keys[obj['Key']] = obj['Size']
                    cloud_total += obj['Size']
                if resp.get('IsTruncated'):
                    continuation_token = resp['NextContinuationToken']
                else:
                    break
            source = f'Cloud.ru live ({len(cloud_keys)} объектов, {self._fmt(cloud_total)})'

        self.stdout.write(f'Источник: {source}')
        self.stdout.write(f'MediaLibraryItem в БД: {MediaLibraryItem.objects.count()}')
        self.stdout.write(f'MediaVariant в БД: {MediaVariant.objects.count()}')
        self.stdout.write()

        # ── 1. По категориям: что должно быть vs что есть ──
        self.stdout.write('=== АНАЛИЗ ПО КАТЕГОРИЯМ ===')
        self.stdout.write(f'{"Категория":<25s} {"Элементов":>8s} {"Оригиналы":>12s} {"Варианты":>12s} {"Preview":>12s} {"Всего":>12s}')
        self.stdout.write('-' * 85)

        grand_total = 0
        grand_preview_size = 0
        grand_variant_size = 0
        grand_original_size = 0

        for cat in MediaCategory.objects.filter(is_active=True).order_by('sorting_order'):
            items = MediaLibraryItem.objects.filter(category=cat, is_active=True)
            item_count = items.count()
            if item_count == 0:
                continue

            original_size = 0
            preview_size = 0
            variant_size = 0

            for item in items:
                if item.media_file and item.media_file.name:
                    original_size += self._cloud_get(cloud_keys, item.media_file.name)
                if item.preview_file and item.preview_file.name:
                    preview_size += self._cloud_get(cloud_keys, item.preview_file.name)
                for v in item.variants.all():
                    if v.file_path:
                        variant_size += self._cloud_get(cloud_keys, v.file_path)

            total_real = original_size + preview_size + variant_size
            grand_total += total_real
            grand_preview_size += preview_size
            grand_variant_size += variant_size
            grand_original_size += original_size

            delta = ''
            if preview_size > 0:
                delta = f' ⚠ preview: {self._fmt(preview_size)}'

            self.stdout.write(
                f'{cat.code:<25s} {item_count:>8d} {self._fmt(original_size):>12s} '
                f'{self._fmt(variant_size):>12s} {self._fmt(preview_size):>12s} '
                f'{self._fmt(total_real):>12s}'
                f'{delta}'
            )

        self.stdout.write('-' * 85)
        self.stdout.write(
            f'{"ИТОГО":<25s} {"":>8s} {self._fmt(grand_original_size):>12s} '
            f'{self._fmt(grand_variant_size):>12s} {self._fmt(grand_preview_size):>12s} '
            f'{self._fmt(grand_total):>12s}'
        )
        self.stdout.write()
        if grand_preview_size > 0:
            self.stdout.write(self.style.WARNING(
                f'⚠ preview_file (старое поле): {self._fmt(grand_preview_size)} — кандидат на удаление'
            ))

        # ── 2. Детально: у каких элементов есть preview_file ──
        self.stdout.write('\n=== ЭЛЕМЕНТЫ С preview_file (старое поле) ===')
        with_preview = MediaLibraryItem.objects.exclude(
            Q(preview_file='') | Q(preview_file__isnull=True)
        ).select_related('category')
        self.stdout.write(f'Всего элементов с preview_file: {with_preview.count()}')
        for item in with_preview[:20]:
            variant_count = item.variants.count()
            key = self._norm(item.preview_file.name) if item.preview_file else ''
            in_cloud = '✅' if self._cloud_get(cloud_keys, key) > 0 else '❌'
            self.stdout.write(
                f'  #{item.id} [{item.category.code}] {item.name[:50]:<50s} '
                f'variants: {variant_count}  {in_cloud} {key}'
            )
        if with_preview.count() > 20:
            self.stdout.write(f'  ... и ещё {with_preview.count() - 20}')

        # ── 3. Элементы без вариантов ──
        self.stdout.write('\n=== PDF/Изображения БЕЗ MediaVariant (нет превьюшек) ===')
        no_variants = MediaLibraryItem.objects.filter(is_active=True).annotate(
            vc=Count('variants')
        ).filter(vc=0).select_related('category')

        missing_variants = []
        for item in no_variants:
            if not item.media_file:
                continue
            profile = item.category.profile
            if not profile or not profile.get('variants'):
                continue
            is_img = item.file_extension.lower() in ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg')
            is_pdf = item.file_extension.lower() == 'pdf'
            if is_img or is_pdf:
                missing_variants.append(item)

        self.stdout.write(f'Элементов без вариантов (должны быть): {len(missing_variants)}')
        for item in missing_variants[:30]:
            key = self._norm(item.media_file.name) if item.media_file else ''
            in_cloud = '✅' if self._cloud_get(cloud_keys, key) > 0 else '❌'
            expected = sum(len(vs.get('widths', [])) for vs in item.category.profile.get('variants', []))
            self.stdout.write(
                f'  #{item.id} [{item.category.code}] {item.name[:50]:<50s} '
                f'{item.file_extension} {in_cloud} | ожидалось вариантов: {expected}'
            )
        if len(missing_variants) > 30:
            self.stdout.write(f'  ... и ещё {len(missing_variants) - 30}')

        # ── 4. Топ элементов по размеру ──
        self.stdout.write('\n=== ТОП-15 ЭЛЕМЕНТОВ ПО РАЗМЕРУ ===')
        items_with_size = []
        for item in MediaLibraryItem.objects.filter(is_active=True).select_related('category'):
            total = 0
            if item.media_file and item.media_file.name:
                total += self._cloud_get(cloud_keys, item.media_file.name)
            for v in item.variants.all():
                if v.file_path:
                    total += self._cloud_get(cloud_keys, v.file_path)
            if item.preview_file and item.preview_file.name:
                total += self._cloud_get(cloud_keys, item.preview_file.name)
            if total > 0:
                items_with_size.append((item, total))

        items_with_size.sort(key=lambda x: -x[1])
        for item, size in items_with_size[:15]:
            vc = item.variants.count()
            pc = 1 if (item.preview_file and item.preview_file.name) else 0
            self.stdout.write(
                f'  {self._fmt(size):>10s}  #{item.id} [{item.category.code}] '
                f'{item.name[:50]:<50s}  файлов: 1+{vc}+{pc}'
            )

        # ── 5. БАЛАНС ──
        self.stdout.write('\n=== БАЛАНС: сверка облака и БД ===')
        all_db_keys = self._collect_all_db_keys()
        db_lookup_full = set()
        for k in all_db_keys:
            db_lookup_full.add(k)
            db_lookup_full.add(k.replace('/', '\\'))
            db_lookup_full.add(k.replace('\\', '/'))

        referenced_size = 0
        unmatched_size = 0
        for key, size in cloud_keys.items():
            if key in db_lookup_full:
                referenced_size += size
            else:
                unmatched_size += size

        # Пересчитываем учтённое с правильным lookup
        accounted_size = 0
        for cat in MediaCategory.objects.filter(is_active=True):
            for item in MediaLibraryItem.objects.filter(category=cat, is_active=True):
                if item.media_file and item.media_file.name:
                    accounted_size += self._cloud_get(cloud_keys, item.media_file.name)
                if item.preview_file and item.preview_file.name:
                    accounted_size += self._cloud_get(cloud_keys, item.preview_file.name)
                for v in item.variants.all():
                    if v.file_path:
                        accounted_size += self._cloud_get(cloud_keys, v.file_path)

        cloud_total = sum(cloud_keys.values())
        self.stdout.write(f'  Всего в облаке:           {self._fmt(cloud_total)}')
        self.stdout.write(f'  Привязано к БД:           {self._fmt(referenced_size)}')
        self.stdout.write(f'  Из них учтено в категориях: {self._fmt(accounted_size)}')
        self.stdout.write(f'  НЕ привязано к БД (орфаны):{self._fmt(unmatched_size)}')

        gap = referenced_size - accounted_size
        if gap > 0:
            self.stdout.write(self.style.WARNING(
                f'  Не учтено в разбивке:     {self._fmt(gap)}'
            ))
        if unmatched_size > 0:
            self.stdout.write(self.style.WARNING(
                f'  ⚠ Орфаны: {self._fmt(unmatched_size)} — запусти find_orphaned_files для деталей'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ Орфанов нет.'))

    def _cloud_get(self, cloud_keys: dict, path: str) -> int:
        """Размер файла в облаке с учётом обоих вариантов слешей."""
        k = self._norm(path)
        if k in cloud_keys:
            return cloud_keys[k]
        alt = k.replace('/', '\\')
        if alt != k and alt in cloud_keys:
            return cloud_keys[alt]
        return 0

    def _collect_all_db_keys(self):
        keys = set()
        for item in MediaLibraryItem.objects.all():
            for fld in ['media_file', 'preview_file']:
                val = getattr(item, fld)
                if val and val.name:
                    keys.add(self._norm(val.name))
        for v in MediaVariant.objects.all():
            if v.file_path:
                keys.add(self._norm(v.file_path))
        from image_processor.models import ImageCropSession
        for s in ImageCropSession.objects.all():
            for fld in ['original_file', 'result_sm', 'result_md', 'result_lg']:
                val = getattr(s, fld)
                if val and val.name:
                    keys.add(self._norm(val.name))
        return keys

    @staticmethod
    def _norm(path: str) -> str:
        return path.replace('\\', '/') if path else ''

    @staticmethod
    def _fmt(size_bytes: int) -> str:
        for unit in ('Б', 'КБ', 'МБ', 'ГБ', 'ТБ'):
            if size_bytes < 1024:
                return f'{size_bytes:.1f} {unit}'
            size_bytes /= 1024
        return f'{size_bytes:.1f} ПБ'
