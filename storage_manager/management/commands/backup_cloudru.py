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
import time

from django.core.management.base import BaseCommand

from storage_manager.backup_service import fmt_size, run_backup


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

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — файлы НЕ скачиваются'))
        if manifest_only:
            self.stdout.write(self.style.WARNING('MANIFEST ONLY — только индекс'))

        progress = _CliProgress(self.stdout)
        start = time.time()
        result = run_backup(
            prefix=prefix, output_dir=output_dir, dry_run=dry_run,
            manifest_only=manifest_only, page_size=page_size, progress=progress,
        )
        elapsed = time.time() - start

        if result['cancelled']:
            self.stdout.write(self.style.WARNING('Отменено.'))
            return
        if result['total_objects'] == 0:
            return  # сервис уже написал «Нет объектов для бэкапа»
        if manifest_only:
            self.stdout.write(self.style.SUCCESS('Готово (manifest-only).'))
            return
        self.stdout.write(self.style.SUCCESS(
            f'\nГотово за {elapsed:.1f}с. '
            f"Скачано: {result['downloaded']}, пропущено: {result['skipped']}, "
            f"ошибок: {result['failed']}. Всего: {fmt_size(result['bytes'])}"
        ))
