"""
Переносит файлы медиабиблиотеки из локального хранилища в Cloud.ru S3.

Использование:
    python manage.py migrate_media_to_cloudru [--dry-run]
"""
from django.core.management.base import BaseCommand
from media_library.models import MediaLibraryItem
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migrate media files from local storage to cloud.ru S3'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would be migrated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        items = MediaLibraryItem.objects.all().order_by('id')

        # Get cloud storage (uses admin credentials from settings)
        from storage_manager.storage_backends.cloudru import CloudRuStorage
        cloud = CloudRuStorage()

        migrated = skipped = errors = 0

        for item in items:
            for field_name in ('media_file', 'preview_file'):
                field = getattr(item, field_name)
                if not field or not field.name:
                    continue

                name = field.name
                if cloud.exists(name):
                    skipped += 1
                    continue

                self.stdout.write(f'  Uploading: {name}')
                if dry_run:
                    migrated += 1
                    continue

                try:
                    with field.storage.open(name, 'rb') as f:
                        cloud._save(name, f)
                    migrated += 1
                except Exception as e:
                    self.stderr.write(f'  ERROR: {name} — {e}')
                    errors += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. Migrated: {migrated}, Skipped: {skipped}, Errors: {errors}'
            )
        )
