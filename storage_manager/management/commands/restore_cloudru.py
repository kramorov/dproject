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
import os
import time

from django.core.management.base import BaseCommand, CommandError

from storage_manager.backup_service import fmt_size, run_restore


class _CliProgress:
    """Адаптер прогресса сервиса → stdout."""

    def __init__(self, out):
        self.out = out

    def start(self, phase, total=0):
        pass

    def set(self, **kw):
        pass

    def log(self, text):
        self.out.write(text)

    def finish(self, phase):
        pass


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

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — файлы НЕ заливаются'))
        if filter_prefix:
            self.stdout.write(f'Фильтр по префиксу: {filter_prefix}')

        progress = _CliProgress(self.stdout)
        start = time.time()
        result = run_restore(
            manifest_path=manifest_path, overwrite=overwrite,
            dry_run=dry_run, prefix=filter_prefix, progress=progress,
        )
        elapsed = time.time() - start

        if result['cancelled']:
            self.stdout.write(self.style.WARNING('Отменено.'))
            return
        if result['total'] == 0:
            return  # сервис уже написал «Нет файлов для восстановления»
        self.stdout.write(self.style.SUCCESS(
            f'\nГотово за {elapsed:.1f}с. '
            f"Залито: {result['uploaded']}, пропущено: {result['skipped']}, "
            f"ошибок: {result['failed']}. Всего: {fmt_size(result['bytes'])}"
        ))
