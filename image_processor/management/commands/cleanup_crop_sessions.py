"""
python manage.py cleanup_crop_sessions — удаление старых ImageCropSession.

Удаляет временные сессии обрезки изображений и их файлы из Cloud.ru.
По умолчанию: старше 1 часа.

Использование:
    python manage.py cleanup_crop_sessions                    # удалить сессии старше 1 часа
    python manage.py cleanup_crop_sessions --hours 24          # старше 24 часов
    python manage.py cleanup_crop_sessions --all               # удалить ВСЕ сессии
    python manage.py cleanup_crop_sessions --dry-run           # только посчитать
"""
import logging
from datetime import datetime, timedelta, timezone

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Удалить старые временные сессии ImageCropSession'

    def add_arguments(self, parser):
        parser.add_argument('--hours', type=int, default=1,
                            help='Удалить сессии старше N часов (по умолчанию 1)')
        parser.add_argument('--all', action='store_true',
                            help='Удалить ВСЕ сессии (игнорирует --hours)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Только посчитать, без удаления')

    def handle(self, **options):
        from image_processor.models import ImageCropSession

        hours = options['hours']
        delete_all = options['all']
        dry_run = options['dry_run']

        if delete_all:
            qs = ImageCropSession.objects.all()
            self.stdout.write('Удаление ВСЕХ сессий...')
        else:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            qs = ImageCropSession.objects.filter(created_at__lt=cutoff)
            self.stdout.write(f'Удаление сессий старше {hours} ч. (до {cutoff.strftime("%Y-%m-%d %H:%M")})...')

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('Нет сессий для удаления.'))
            return

        # Подсчёт суммарного размера файлов
        total_size = 0
        for s in qs:
            for field_name in ['original_file', 'result_sm', 'result_md', 'result_lg']:
                f = getattr(s, field_name)
                if f and f.name:
                    try:
                        total_size += f.size
                    except Exception:
                        pass

        self.stdout.write(f'Найдено сессий: {total} ({self._fmt_size(total_size)})')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — удаление не выполняется.'))
            return

        deleted = 0
        failed = 0
        freed = 0

        for s in qs:
            # Собираем размеры до удаления
            s_size = 0
            for field_name in ['original_file', 'result_sm', 'result_md', 'result_lg']:
                f = getattr(s, field_name)
                if f and f.name:
                    try:
                        s_size += f.size
                    except Exception:
                        pass
            try:
                s.delete()  # удаляет файлы из Cloud.ru + запись БД
                deleted += 1
                freed += s_size
            except Exception as e:
                failed += 1
                logger.warning(f'Ошибка удаления сессии #{s.id}: {e}')

            if (deleted + failed) % 50 == 0:
                self.stdout.write(f'  ... удалено {deleted}, ошибок {failed}')

        self.stdout.write(self.style.SUCCESS(
            f'Удалено: {deleted}, ошибок: {failed}. Освобождено: {self._fmt_size(freed)}'
        ))

    @staticmethod
    def _fmt_size(size_bytes: int) -> str:
        for unit in ('Б', 'КБ', 'МБ', 'ГБ', 'ТБ'):
            if size_bytes < 1024:
                return f'{size_bytes:.1f} {unit}'
            size_bytes /= 1024
        return f'{size_bytes:.1f} ПБ'
