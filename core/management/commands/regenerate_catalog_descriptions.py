# core/management/commands/regenerate_catalog_descriptions.py
"""
Общая команда перегенерации названий/описаний каталога из шаблонов.

Использование:
    python manage.py regenerate_catalog_descriptions                     # все каталоги
    python manage.py regenerate_catalog_descriptions --model gearbox.GearBox
    python manage.py regenerate_catalog_descriptions --model pneumatic_actuators.PneumaticActuatorItem --inactive

Что делает:
    - проходит по записям каталога (is_active=True по умолчанию);
    - вызывает obj.save() → TemplateMixin.save() → генерация name/description
      из шаблонов model_line (или дефолтных) + sync_sku() при наличии SKUMixin;
    - выводит статистику: обновлено / пропущено / ошибки.

Реестр моделей-каталогов (единый контракт «шаблоны на model_line»):
    solenoid_valves.DirectionValve, pa_controls.LimitSwitchBox,
    pa_controls.PosiModelLineItem, filter_regulator.FilterRegulator,
    gearbox.GearBox, pneumatic_fittings.PneumaticFitting,
    pneumatic_actuators.PneumaticActuatorItem.
"""
from django.apps import apps
from django.core.management.base import BaseCommand, CommandError

CATALOG_MODELS = [
    'solenoid_valves.DirectionValve',
    'pa_controls.LimitSwitchBox',
    'pa_controls.PosiModelLineItem',
    'filter_regulator.FilterRegulator',
    'gearbox.GearBox',
    'pneumatic_fittings.PneumaticFitting',
    'pneumatic_actuators.PneumaticActuatorItem',
]


class Command(BaseCommand):
    help = 'Перегенерировать названия/описания каталога из шаблонов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model', dest='model',
            help='app_label.ModelName (например gearbox.GearBox); по умолчанию — все каталоги',
        )
        parser.add_argument(
            '--inactive', action='store_true', dest='inactive',
            help='Обрабатывать и неактивные записи',
        )

    def _get_models(self, model_name):
        if model_name:
            try:
                return [apps.get_model(*model_name.rsplit('.', 1))]
            except (LookupError, ValueError) as e:
                raise CommandError(f'Модель {model_name} не найдена: {e}')
        return [apps.get_model(*m.rsplit('.', 1)) for m in CATALOG_MODELS]

    def handle(self, *args, **options):
        models = self._get_models(options['model'])
        for model in models:
            qs = model.objects.all() if options['inactive'] else model.objects.filter(is_active=True)
            total = qs.count()
            self.stdout.write(f'{model._meta.label}: {total} записей')
            if not total:
                continue
            updated = skipped = errors = 0
            for obj in qs.iterator():
                old_name = obj.name or '(пусто)'
                old_desc = obj.description or '(пусто)'
                try:
                    obj.save()  # TemplateMixin.save → name/description; SKUMixin → sync_sku()
                    if obj.name != old_name or obj.description != old_desc:
                        updated += 1
                    else:
                        skipped += 1
                except Exception as e:
                    errors += 1
                    self.stderr.write(f'  ✗ {obj.pk}: {e}')
            self.stdout.write(
                self.style.SUCCESS(
                    f'  Готово: обновлено {updated} | без изменений {skipped} | ошибок {errors}'
                )
            )
