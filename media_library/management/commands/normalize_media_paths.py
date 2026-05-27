"""
Нормализует пути файлов в БД: заменяет \\ на / в media_file.name.
Физические файлы в S3 не трогает — CloudRuStorage._resolve_name найдёт оба варианта.
"""
from django.core.management.base import BaseCommand
from media_library.models import MediaLibraryItem


class Command(BaseCommand):
    help = 'Нормализует обратные слеши в путях media_file (Windows → S3)'

    def handle(self, *args, **options):
        updated = 0
        for item in MediaLibraryItem.objects.exclude(media_file='').exclude(media_file__isnull=True):
            old = item.media_file.name
            new = old.replace('\\', '/')
            if old != new:
                MediaLibraryItem.objects.filter(pk=item.pk).update(media_file=new)
                updated += 1
        self.stdout.write(f'Нормализовано: {updated} файлов')
