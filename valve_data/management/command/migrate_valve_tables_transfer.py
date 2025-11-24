
# management/commands/migrate_valve_tables_transfer.py
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from valve_data.models import ValveLine, ValveModelDataTable, ValveLineModelData


class Command(BaseCommand):
    help = _('Миграция данных в новую структуру с шаблонами')

    def handle(self, *args, **options):
        processed_count = 0
        skipped_count = 0

        for valve_line in ValveLine.objects.all():
            # Проверяем, есть ли связанные ValveLineModelData
            has_model_data = ValveLineModelData.objects.filter(valve_model_line=valve_line).exists()

            if not has_model_data:
                self.stdout.write(
                    self.style.WARNING(
                        f'Пропущена серия {valve_line.name}: нет данных моделей арматуры'
                    )
                )
                skipped_count += 1
                continue

            # Создаем шаблон на основе серии
            template, created = ValveModelDataTable.objects.get_or_create(
                code=f"TEMPLATE_{valve_line.code}",
                defaults={
                    'name': f"Шаблон для {valve_line.name}",
                    'description': f"Автоматически созданный шаблон для серии {valve_line.name}"
                }
            )

            # Обновляем связь в серии
            valve_line.valve_model_template = template
            valve_line.save()

            # Обновляем модели данных
            updated_count = ValveLineModelData.objects.filter(valve_model_line=valve_line).update(
                valve_model_template=template
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Обработана серия {valve_line.name}: создан шаблон {template.name}, перенесено {updated_count} моделей'
                )
            )
            processed_count += 1

        # Итоговая статистика
        self.stdout.write(
            self.style.SUCCESS(
                f'Миграция завершена. Обработано: {processed_count}, пропущено: {skipped_count}'
            )
        )