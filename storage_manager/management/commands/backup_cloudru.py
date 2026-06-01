"""
python manage.py backup_cloudru — бэкап Cloud.ru на локальный диск.

Скачивает все объекты из бакета Cloud.ru в локальную папку,
сохраняя структуру ключей S3. Создаёт manifest.json с метаданными.

Использование:
    python manage.py backup_cloudru                          # полный бэкап
    python manage.py backup_cloudru --prefix media_library/   # только media_library
    python manage.py backup_cloudru --dry-run                 # только листинг, без скачивания
    python manage.py backup_cloudru --output-dir D:\backups   # кастомная папка
    python manage.py backup_cloudru --manifest-only           # только manifest.json, без файлов
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

from django.conf import settings
from django.core.management.base import BaseCommand

from storage_manager.storage_backends.cloudru import CloudRuStorage


class Command(BaseCommand):
    help = 'Скачать все объекты из Cloud.ru бакета на локальный диск'

    def add_arguments(self, parser):
        parser.add_argument('--prefix', default='', help='S3-префикс (папка) для фильтрации')
        parser.add_argument('--output-dir', help='Папка для бэкапа (по умолчанию backups/cloudru/YYYY-MM-DD/)')
        parser.add_argument('--dry-run', action='store_true', help='Только показать что будет скачано')
        parser.add_argument('--manifest-only', action='store_true', help='Создать только manifest.json без скачивания файлов')
        parser.add_argument('--page-size', type=int, default=1000, help='Размер страницы S3 list')

    def handle(self, **options):
        prefix = options['prefix']
        dry_run = options['dry_run']
        manifest_only = options['manifest_only']
        page_size = options['page_size']

        output_dir = options['output_dir']
        if not output_dir:
            date_str = datetime.now().strftime('%Y-%m-%d')
            output_dir = os.path.join('backups', 'cloudru', date_str)

        storage = CloudRuStorage()
        s3 = storage.s3_admin  # админский клиент для чтения объектов
        bucket = storage.bucket_name

        self.stdout.write(f'Бакет: {bucket}')
        self.stdout.write(f'Endpoint: {storage.endpoint_url}')
        self.stdout.write(f'Префикс: {prefix or "(все)"}')
        self.stdout.write(f'Папка бэкапа: {output_dir}')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — файлы НЕ скачиваются'))
        if manifest_only:
            self.stdout.write(self.style.WARNING('MANIFEST ONLY — только индекс'))

        # ── Листинг всех объектов ──
        self.stdout.write('Получаю список объектов...')
        all_objects = []
        total_size = 0
        continuation_token = None

        while True:
            list_kwargs = {
                'Bucket': bucket,
                'MaxKeys': page_size,
            }
            if prefix:
                list_kwargs['Prefix'] = prefix
            if continuation_token:
                list_kwargs['ContinuationToken'] = continuation_token

            resp = s3.list_objects_v2(**list_kwargs)

            if 'Contents' in resp:
                for obj in resp['Contents']:
                    all_objects.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'etag': obj.get('ETag', ''),
                        'last_modified': obj['LastModified'].isoformat(),
                    })
                    total_size += obj['Size']

            if resp.get('IsTruncated'):
                continuation_token = resp.get('NextContinuationToken')
            else:
                break

            self.stdout.write(f'  ... {len(all_objects)} объектов ({self._fmt_size(total_size)})')

        self.stdout.write(self.style.SUCCESS(
            f'Всего объектов: {len(all_objects)}, общий размер: {self._fmt_size(total_size)}'
        ))

        if not all_objects:
            self.stdout.write(self.style.WARNING('Нет объектов для бэкапа.'))
            return

        # ── Создаём папку ──
        if not dry_run:
            os.makedirs(output_dir, exist_ok=True)

        # ── Manifest ──
        manifest = {
            'backup_date': datetime.now(timezone.utc).isoformat(),
            'bucket': bucket,
            'endpoint': storage.endpoint_url,
            'prefix': prefix,
            'total_objects': len(all_objects),
            'total_size_bytes': total_size,
            'files': all_objects,
        }
        manifest_path = os.path.join(output_dir, 'manifest.json')

        if not dry_run:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            self.stdout.write(f'Manifest сохранён: {manifest_path}')

        if manifest_only:
            self.stdout.write(self.style.SUCCESS('Готово (manifest-only).'))
            return

        # ── Скачивание ──
        downloaded = 0
        skipped = 0
        failed = 0
        downloaded_bytes = 0
        start_time = time.time()

        for i, obj in enumerate(all_objects):
            key = obj['key']
            size = obj['size']
            local_path = os.path.join(output_dir, key)

            # Пропускаем если файл уже существует и размер совпадает
            if os.path.exists(local_path) and os.path.getsize(local_path) == size:
                skipped += 1
                if (i + 1) % 100 == 0:
                    self.stdout.write(f'  [{i+1}/{len(all_objects)}] проверено (скачано: {downloaded}, пропущено: {skipped})')
                continue

            if dry_run:
                downloaded += 1
                downloaded_bytes += size
                continue

            try:
                local_dir = os.path.dirname(local_path)
                os.makedirs(local_dir, exist_ok=True)

                s3.download_file(bucket, key, local_path)

                # Проверяем размер после скачивания
                actual_size = os.path.getsize(local_path)
                if actual_size != size:
                    self.stdout.write(self.style.WARNING(
                        f'  ⚠ Размер не совпадает: {key} (ожидалось {size}, получено {actual_size})'
                    ))

                downloaded += 1
                downloaded_bytes += size

            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f'  ✗ Ошибка: {key} — {e}'))

            if (i + 1) % 50 == 0 or (i + 1) == len(all_objects):
                elapsed = time.time() - start_time
                speed = downloaded_bytes / elapsed if elapsed > 0 else 0
                pct = (i + 1) / len(all_objects) * 100
                self.stdout.write(
                    f'  [{i+1}/{len(all_objects)}] {pct:.0f}% | '
                    f'скачано: {downloaded}, пропущено: {skipped}, ошибок: {failed} | '
                    f'{self._fmt_size(downloaded_bytes)} @ {self._fmt_size(int(speed))}/c'
                )

        elapsed = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(
            f'\nГотово за {elapsed:.1f}с. '
            f'Скачано: {downloaded}, пропущено: {skipped}, ошибок: {failed}. '
            f'Всего: {self._fmt_size(downloaded_bytes)}'
        ))

    @staticmethod
    def _fmt_size(size_bytes: int) -> str:
        for unit in ('Б', 'КБ', 'МБ', 'ГБ', 'ТБ'):
            if size_bytes < 1024:
                return f'{size_bytes:.1f} {unit}'
            size_bytes /= 1024
        return f'{size_bytes:.1f} ПБ'
