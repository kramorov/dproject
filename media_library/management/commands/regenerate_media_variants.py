"""
Management command: регенерация MediaVariant для существующих MediaLibraryItem.

Использование:
    python manage.py regenerate_media_variants           # все
    python manage.py regenerate_media_variants --dry-run  # посмотреть что будет
    python manage.py regenerate_media_variants --category=CERTIFICATE  # только категория
    python manage.py regenerate_media_variants --id=42    # конкретный элемент
"""
from django.core.management.base import BaseCommand
from media_library.models import MediaLibraryItem
from media_library.services import delete_variants, generate_variants


class Command(BaseCommand):
    help = 'Регенерирует MediaVariant для изображений и PDF в медиабиблиотеке'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Только показать, без изменений')
        parser.add_argument('--category', type=str, help='Код категории (CERTIFICATE, PRODUCT_GALLERY...)')
        parser.add_argument('--id', type=int, help='ID конкретного элемента')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        qs = MediaLibraryItem.objects.filter(media_file__isnull=False, is_active=True)

        if options['id']:
            qs = qs.filter(pk=options['id'])
        if options['category']:
            qs = qs.filter(category__code=options['category'])

        total = qs.count()
        self.stdout.write(f'Найдено элементов: {total}')
        if dry_run:
            self.stdout.write('DRY RUN — изменения не применяются')

        processed = 0
        generated_total = 0
        skipped = 0
        errors = 0

        for item in qs.iterator():
            if not (item.is_image() or item._is_pdf()):
                skipped += 1
                continue

            profile = item.category.profile
            if not profile or not profile.get('variants'):
                self.stdout.write(f'  [{item.pk}] {item.name}: нет профиля для категории {item.category.code} — пропущен')
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(f'  [{item.pk}] {item.name} ({item.category.code}) — будет сгенерировано')
                processed += 1
                continue

            try:
                delete_variants(item)
                count = generate_variants(item)
                generated_total += count
                processed += 1
                self.stdout.write(f'  [{item.pk}] {item.name}: {count} вариантов')
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f'  [{item.pk}] {item.name}: ОШИБКА — {e}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nГотово: обработано {processed}, вариантов {generated_total}, '
            f'пропущено {skipped}, ошибок {errors}'
        ))
