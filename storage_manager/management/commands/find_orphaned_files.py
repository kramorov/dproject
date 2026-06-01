"""
python manage.py find_orphaned_files — поиск файлов в Cloud.ru, не привязанных к БД.

Сравнивает все объекты в бакете Cloud.ru с записями в БД:
  - MediaLibraryItem: media_file, preview_file
  - MediaVariant: file_path
  - ImageCropSession: original_file, result_sm, result_md, result_lg

Выводит список орфанов (файлы в облаке без ссылок в БД).

Использование:
    python manage.py find_orphaned_files                        # показать орфанов (листинг Cloud.ru)
    python manage.py find_orphaned_files --manifest manifest.json  # по манифесту (без запросов к облаку)
    python manage.py find_orphaned_files --delete               # удалить орфанов
    python manage.py find_orphaned_files --output orphans.json  # сохранить список в JSON
    python manage.py find_orphaned_files --save-manifest        # сохранить manifest для restore
    python manage.py find_orphaned_files --dry-run              # только посчитать, без удаления
"""
import json
import os
import sys
from datetime import datetime, timezone
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from storage_manager.storage_backends.cloudru import CloudRuStorage


class Command(BaseCommand):
    help = 'Найти файлы в Cloud.ru, отсутствующие в БД (орфаны)'

    def add_arguments(self, parser):
        parser.add_argument('--delete', action='store_true', help='Удалить орфанов из Cloud.ru')
        parser.add_argument('--dry-run', action='store_true', help='Только посчитать, без действий')
        parser.add_argument('--output', help='Сохранить список орфанов в JSON-файл')
        parser.add_argument('--manifest', help='Использовать manifest.json вместо листинга Cloud.ru')
        parser.add_argument('--save-manifest', action='store_true',
                            help='Сохранить орфанов как manifest.json для возможности restore')
        parser.add_argument('--page-size', type=int, default=1000, help='Размер страницы S3 list')

    def handle(self, **options):
        delete = options['delete']
        dry_run = options['dry_run']
        output_path = options['output']
        save_manifest = options['save_manifest']
        manifest_path = options['manifest']
        page_size = options['page_size']

        self.stdout.write('Сбор ссылок из БД...')

        # ─── 1. Сбор всех путей из БД ───
        db_keys = set()

        # MediaLibraryItem: media_file + preview_file
        from media_library.models import MediaLibraryItem
        for item in MediaLibraryItem.objects.exclude(
            Q(media_file='') | Q(media_file__isnull=True)
        ).values_list('media_file', flat=True):
            if item:
                db_keys.add(self._norm(item))
        for item in MediaLibraryItem.objects.exclude(
            Q(preview_file='') | Q(preview_file__isnull=True)
        ).values_list('preview_file', flat=True):
            if item:
                db_keys.add(self._norm(item))
        self.stdout.write(f'  MediaLibraryItem: media_file + preview_file — собрано')

        # MediaVariant: file_path
        from media_library.models import MediaVariant
        for path in MediaVariant.objects.exclude(
            Q(file_path='') | Q(file_path__isnull=True)
        ).values_list('file_path', flat=True):
            if path:
                db_keys.add(self._norm(path))
        self.stdout.write(f'  MediaVariant: file_path — собрано')

        # ImageCropSession: original_file + result_sm/md/lg
        from image_processor.models import ImageCropSession
        for session in ImageCropSession.objects.all().values_list(
            'original_file', 'result_sm', 'result_md', 'result_lg'
        ):
            for field in session:
                if field:
                    db_keys.add(self._norm(field))
        self.stdout.write(f'  ImageCropSession: original + results — собрано')

        self.stdout.write(self.style.SUCCESS(f'Уникальных путей из БД: {len(db_keys)}'))

        # Строим словарь для быстрого поиска (с учётом обоих вариантов слешей)
        # S3 ключ может быть с /, а в БД с \ или наоборот
        db_lookup = set()
        for k in db_keys:
            db_lookup.add(k)
            alt = k.replace('/', '\\')
            if alt != k:
                db_lookup.add(alt)
            alt2 = k.replace('\\', '/')
            if alt2 != k:
                db_lookup.add(alt2)

        # ─── 2. Получаем список объектов (Cloud.ru или manifest) ───
        storage = CloudRuStorage()
        s3 = storage.s3_admin
        bucket = storage.bucket_name

        cloud_files = []
        total_size = 0

        if manifest_path:
            self.stdout.write(f'Читаю manifest: {manifest_path}')
            if not os.path.exists(manifest_path):
                raise CommandError(f'Файл не найден: {manifest_path}')
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            cloud_files = manifest.get('files', [])
            self.stdout.write(f'  объектов в манифесте: {len(cloud_files)}')
        else:
            self.stdout.write('Получаю список объектов Cloud.ru...')
            continuation_token = None
            while True:
                list_kwargs = {'Bucket': bucket, 'MaxKeys': page_size}
                if continuation_token:
                    list_kwargs['ContinuationToken'] = continuation_token
                resp = s3.list_objects_v2(**list_kwargs)
                if 'Contents' in resp:
                    for obj in resp['Contents']:
                        cloud_files.append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'etag': obj.get('ETag', ''),
                            'last_modified': obj['LastModified'].isoformat(),
                        })
                if resp.get('IsTruncated'):
                    continuation_token = resp.get('NextContinuationToken')
                else:
                    break
                self.stdout.write(f'  ... проверено {len(cloud_files)} объектов')

        # ─── 3. Поиск орфанов ───
        orphans = []
        orphan_size = 0
        for obj in cloud_files:
            key = obj['key']
            size = obj['size']
            total_size += size
            if key not in db_lookup:
                orphans.append(obj)
                orphan_size += size

        total_objects = len(cloud_files)
        source_label = 'манифесте' if manifest_path else 'бакете'
        self.stdout.write(self.style.SUCCESS(
            f'Всего объектов в {source_label}: {total_objects} ({self._fmt_size(total_size)})'
        ))

        if not orphans:
            self.stdout.write(self.style.SUCCESS('Орфанов не найдено — все файлы привязаны к БД.'))
            return

        # ─── 4. Вывод результатов ───
        self.stdout.write(self.style.WARNING(
            f'\nНайдено орфанов: {len(orphans)} ({self._fmt_size(orphan_size)})'
        ))
        if total_size > 0:
            self.stdout.write(f'Это {orphan_size / total_size * 100:.1f}% от общего объёма\n')

        # Группируем по префиксу для наглядности
        by_prefix = defaultdict(lambda: {'count': 0, 'size': 0})
        for obj in orphans:
            parts = obj['key'].split('/')
            prefix = '/'.join(parts[:2]) if len(parts) >= 2 else parts[0]
            by_prefix[prefix]['count'] += 1
            by_prefix[prefix]['size'] += obj['size']

        self.stdout.write('По префиксам:')
        for prefix in sorted(by_prefix.keys()):
            info = by_prefix[prefix]
            self.stdout.write(f'  {prefix}/ — {info["count"]} файлов, {self._fmt_size(info["size"])}')

        # Показать первые 20 орфанов
        self.stdout.write('\nПримеры (первые 20):')
        for obj in orphans[:20]:
            self.stdout.write(f'  {obj["key"]} ({self._fmt_size(obj["size"])})')

        # ─── 5. Действия ───
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'scan_date': datetime.now(timezone.utc).isoformat(),
                    'bucket': bucket,
                    'total_objects': total_objects,
                    'total_size_bytes': total_size,
                    'orphan_count': len(orphans),
                    'orphan_size_bytes': orphan_size,
                    'orphans': orphans,
                }, f, ensure_ascii=False, indent=2)
            self.stdout.write(f'\nСписок орфанов сохранён: {output_path}')

        if save_manifest:
            manifest_out = f'orphans_manifest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(manifest_out, 'w', encoding='utf-8') as f:
                json.dump({
                    'backup_date': datetime.now(timezone.utc).isoformat(),
                    'bucket': bucket,
                    'endpoint': storage.endpoint_url,
                    'description': 'Орфаны — файлы без ссылок в БД. Можно восстановить через restore_cloudru.',
                    'total_objects': len(orphans),
                    'total_size_bytes': orphan_size,
                    'files': orphans,
                }, f, ensure_ascii=False, indent=2)
            self.stdout.write(f'Manifest орфанов сохранён: {manifest_out}')

        if delete:
            if dry_run:
                self.stdout.write(self.style.WARNING(
                    f'\nDRY RUN: было бы удалено {len(orphans)} орфанов ({self._fmt_size(orphan_size)})'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'\nУдаление {len(orphans)} орфанов...'
                ))
                deleted = 0
                failed = 0
                freed = 0
                for obj in orphans:
                    try:
                        s3.delete_object(Bucket=bucket, Key=obj['key'])
                        deleted += 1
                        freed += obj['size']
                    except Exception as e:
                        failed += 1
                        self.stdout.write(self.style.ERROR(f'  ✗ {obj["key"]}: {e}'))

                    if (deleted + failed) % 100 == 0:
                        self.stdout.write(f'  ... удалено {deleted}, ошибок {failed}')

                self.stdout.write(self.style.SUCCESS(
                    f'Удалено: {deleted}, ошибок: {failed}. '
                    f'Освобождено: {self._fmt_size(freed)}'
                ))
        elif not output_path and not save_manifest:
            self.stdout.write(
                '\nИспользуйте --delete для удаления орфанов, '
                '--output file.json для сохранения списка, '
                '--manifest manifest.json для проверки по бэкапу, '
                '--save-manifest для создания manifest-файла.'
            )

    @staticmethod
    def _norm(path: str) -> str:
        """Нормализация пути: обратные слеши → прямые."""
        return path.replace('\\', '/') if path else ''

    @staticmethod
    def _fmt_size(size_bytes: int) -> str:
        for unit in ('Б', 'КБ', 'МБ', 'ГБ', 'ТБ'):
            if size_bytes < 1024:
                return f'{size_bytes:.1f} {unit}'
            size_bytes /= 1024
        return f'{size_bytes:.1f} ПБ'
