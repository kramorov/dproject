"""
python manage.py list_inactive_media — показать неактивные MediaLibraryItem и их размер.

Использование:
    python manage.py list_inactive_media
    python manage.py list_inactive_media --manifest backups/cloudru/2026-06-01/manifest.json
    python manage.py list_inactive_media --delete  # удалить неактивные (с файлами из облака)
"""
import json
from django.core.management.base import BaseCommand
from media_library.models import MediaLibraryItem


class Command(BaseCommand):
    help = 'Показать неактивные MediaLibraryItem'

    def add_arguments(self, parser):
        parser.add_argument('--manifest', help='manifest.json для получения размеров')
        parser.add_argument('--delete', action='store_true', help='Удалить неактивные элементы')

    def handle(self, **options):
        manifest_path = options['manifest']
        delete = options['delete']

        cloud_sizes = {}
        if manifest_path:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            cloud_sizes = {obj['key'].replace('\\', '/'): obj['size'] for obj in manifest['files']}

        qs = MediaLibraryItem.objects.filter(is_active=False).select_related('category')
        total_count = qs.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('Неактивных элементов нет.'))
            return

        total_size = 0
        total_files = 0
        self.stdout.write(f'Неактивных элементов: {total_count}\n')

        for item in qs:
            name = item.media_file.name if item.media_file else '-'
            key = name.replace('\\', '/') if name else ''
            size = cloud_sizes.get(key, 0)
            total_size += size
            if item.media_file:
                total_files += 1
            self.stdout.write(
                f'  #{item.id:<5d} [{item.category.code:<18s}] '
                f'{self._fmt(size):>10s}  '
                f'{item.name[:60]:<60s}  {key}'
            )

        self.stdout.write(f'\nФайлов: {total_files}, Суммарно: {self._fmt(total_size)}')

        if delete:
            self.stdout.write(self.style.WARNING(f'\nУдаление {total_count} неактивных элементов...'))
            deleted = 0
            for item in qs:
                try:
                    item.delete()  # удаляет файлы из Cloud.ru + запись БД
                    deleted += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ #{item.id}: {e}'))
            self.stdout.write(self.style.SUCCESS(f'Удалено: {deleted}'))

    @staticmethod
    def _fmt(s):
        for unit in ('Б', 'КБ', 'МБ', 'ГБ'):
            if s < 1024:
                return f'{s:.1f} {unit}'
            s /= 1024
        return f'{s:.1f} ГБ'
