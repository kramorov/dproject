"""
python manage.py restore_cloudru — восстановление из локального бэкапа в Cloud.ru.

Читает manifest.json, созданный backup_cloudru, и заливает файлы обратно в бакет.
По умолчанию пропускает существующие файлы того же размера.

Использование:
    python manage.py restore_cloudru backups/cloudru/2026-06-01/manifest.json
    python manage.py restore_cloudru --manifest backups/cloudru/2026-06-01/manifest.json
    python manage.py restore_cloudru --manifest ... --overwrite   # перезаписать существующие
    python manage.py restore_cloudru --manifest ... --dry-run     # только показать что будет залито
    python manage.py restore_cloudru --manifest ... --prefix media_library/  # только этот префикс
"""
import json
import os
import time
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from storage_manager.storage_backends.cloudru import CloudRuStorage


class Command(BaseCommand):
    help = 'Восстановить файлы из локального бэкапа в Cloud.ru бакет'

    def add_arguments(self, parser):
        parser.add_argument('manifest_path', nargs='?', help='Путь к manifest.json')
        parser.add_argument('--manifest', dest='manifest_arg', help='Путь к manifest.json (именованный)')
        parser.add_argument('--overwrite', action='store_true', help='Перезаписывать существующие файлы')
        parser.add_argument('--dry-run', action='store_true', help='Только показать что будет залито')
        parser.add_argument('--prefix', default='', help='Восстановить только файлы с этим S3-префиксом')

    def handle(self, **options):
        manifest_path = options['manifest_path'] or options['manifest_arg']
        if not manifest_path:
            raise CommandError('Укажите путь к manifest.json')

        if not os.path.exists(manifest_path):
            raise CommandError(f'Файл не найден: {manifest_path}')

        overwrite = options['overwrite']
        dry_run = options['dry_run']
        filter_prefix = options['prefix']

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        backup_dir = os.path.dirname(os.path.abspath(manifest_path))
        all_files = manifest.get('files', [])

        if filter_prefix:
            all_files = [obj for obj in all_files if obj['key'].startswith(filter_prefix)]

        total_size = sum(obj['size'] for obj in all_files)

        storage = CloudRuStorage()
        s3 = storage.s3_admin
        bucket = storage.bucket_name

        self.stdout.write(f'Manifest: {manifest_path}')
        self.stdout.write(f'Бакет: {bucket}')
        self.stdout.write(f'Дата бэкапа: {manifest.get("backup_date", "неизвестна")}')
        self.stdout.write(f'Папка бэкапа: {backup_dir}')
        self.stdout.write(f'Файлов к восстановлению: {len(all_files)} ({self._fmt_size(total_size)})')
        if filter_prefix:
            self.stdout.write(f'Фильтр по префиксу: {filter_prefix}')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — файлы НЕ заливаются'))

        if not all_files:
            self.stdout.write(self.style.WARNING('Нет файлов для восстановления.'))
            return

        uploaded = 0
        skipped = 0
        failed = 0
        uploaded_bytes = 0
        start_time = time.time()

        for i, obj in enumerate(all_files):
            key = obj['key']
            size = obj['size']
            local_path = os.path.join(backup_dir, key)

            if not os.path.exists(local_path):
                failed += 1
                self.stdout.write(self.style.ERROR(f'  ✗ Файл отсутствует локально: {key}'))
                continue

            local_size = os.path.getsize(local_path)

            # Проверяем существование в облаке
            if not overwrite and not dry_run:
                try:
                    resp = s3.head_object(Bucket=bucket, Key=key)
                    cloud_size = resp['ContentLength']
                    if cloud_size == local_size:
                        skipped += 1
                        if (i + 1) % 100 == 0:
                            self.stdout.write(f'  [{i+1}/{len(all_files)}] залито: {uploaded}, пропущено: {skipped}')
                        continue
                    else:
                        self.stdout.write(
                            f'  Размер отличается: {key} (локально {local_size}, облако {cloud_size}) — перезаливаю'
                        )
                except Exception:
                    pass  # файла нет в облаке — заливаем

            if dry_run:
                uploaded += 1
                uploaded_bytes += local_size
                continue

            try:
                s3.upload_file(local_path, bucket, key)
                uploaded += 1
                uploaded_bytes += local_size
            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f'  ✗ Ошибка заливки: {key} — {e}'))

            if (i + 1) % 50 == 0 or (i + 1) == len(all_files):
                elapsed = time.time() - start_time
                speed = uploaded_bytes / elapsed if elapsed > 0 else 0
                pct = (i + 1) / len(all_files) * 100
                self.stdout.write(
                    f'  [{i+1}/{len(all_files)}] {pct:.0f}% | '
                    f'залито: {uploaded}, пропущено: {skipped}, ошибок: {failed} | '
                    f'{self._fmt_size(uploaded_bytes)} @ {self._fmt_size(int(speed))}/c'
                )

        elapsed = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(
            f'\nГотово за {elapsed:.1f}с. '
            f'Залито: {uploaded}, пропущено: {skipped}, ошибок: {failed}. '
            f'Всего: {self._fmt_size(uploaded_bytes)}'
        ))

    @staticmethod
    def _fmt_size(size_bytes: int) -> str:
        for unit in ('Б', 'КБ', 'МБ', 'ГБ', 'ТБ'):
            if size_bytes < 1024:
                return f'{size_bytes:.1f} {unit}'
            size_bytes /= 1024
        return f'{size_bytes:.1f} ПБ'
