"""Backfill 'ru' in ``*_i18n`` JSONFields from the RU base fields.

После подключения локализующих миксинов новые JSONField у существующих
строк равны ``{}``. Эта команда заполняет ``_i18n['ru']`` из базового RU-поля
(``name``, ``description``, ``name_template``, ``description_template`` и т.п.),
не трогая переводы en/cn.

Запуск:
    python manage.py backfill_localized_ru [--dry-run]
"""
from django.core.management.base import BaseCommand
from django.apps import apps

from core.utils.localization import sync_ru


class Command(BaseCommand):
    help = 'Backfill "ru" in *_i18n JSONFields from the RU base fields.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Only report, do not write.')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        updated_models = 0
        updated_rows = 0

        for model in apps.get_models():
            meta = model._meta
            fields = {f.name for f in meta.fields}
            i18n_fields = [
                n for n in fields
                if n.endswith('_i18n') and n[:-5] in fields
            ]
            if not i18n_fields:
                continue

            rows = 0
            qs = meta.default_manager.all()
            for obj in qs.iterator():
                changed = False
                for i18n_field in i18n_fields:
                    base_field = i18n_field[:-5]  # 'name_i18n' -> 'name'
                    current = getattr(obj, i18n_field, None)
                    new = sync_ru(current, getattr(obj, base_field, '') or '')
                    if new != current:
                        setattr(obj, i18n_field, new)
                        changed = True
                if changed:
                    rows += 1
                    if not dry_run:
                        obj.save(update_fields=i18n_fields)

            if rows:
                updated_models += 1
                updated_rows += rows
                self.stdout.write(f'{meta.app_label}.{meta.object_name}: {rows} rows')

        self.stdout.write(self.style.SUCCESS(
            f'Done. Models: {updated_models}, rows: {updated_rows}' + (' (dry-run)' if dry_run else '')
        ))
