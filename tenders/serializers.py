# serializers.py
from rest_framework import serializers
from .models import Procurement, ImportLog
from django.utils.dateparse import parse_datetime
import csv
from io import TextIOWrapper, StringIO


class ProcurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Procurement
        fields = '__all__'


class CSVImportSerializer(serializers.Serializer):
    csv_file = serializers.FileField()

    def validate_csv_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Файл должен быть в формате CSV")
        return value

    def create(self, validated_data):
        csv_file = validated_data['csv_file']
        return self.import_csv(csv_file)

    def import_csv(self, csv_file):
        decoded_file = TextIOWrapper(csv_file.file, encoding='utf-8-sig')
        reader = csv.DictReader(decoded_file)

        import_log = {
            'filename': csv_file.name,
            'total_rows': 0,
            'imported_rows': 0,
            'skipped_rows': 0,
            'warnings': [],
            'errors': [],
            'status': 'success'
        }

        for row_num, row in enumerate(reader, 1):
            import_log['total_rows'] += 1

            try:
                # Очистка и валидация данных
                cleaned_data = self.clean_row_data(row)

                # Проверка уникальности
                subject = cleaned_data.get('subject', '')
                proc_number = cleaned_data.get('procurement_number', '')
                end_date = cleaned_data.get('end_date')

                if not all([subject, proc_number, end_date]):
                    import_log['skipped_rows'] += 1
                    import_log['warnings'].append(
                        f"Строка {row_num}: Пропущена - отсутствуют обязательные поля"
                    )
                    continue

                # Проверка существующих записей
                existing = Procurement.objects.filter(
                    subject=subject,
                    procurement_number=proc_number
                ).first()

                if existing:
                    if existing.end_date.date() == end_date.date():
                        import_log['skipped_rows'] += 1
                        import_log['warnings'].append(
                            f"Строка {row_num}: Пропущена - дубликат (все поля совпадают)"
                        )
                        continue
                    else:
                        import_log['warnings'].append(
                            f"Строка {row_num}: Внимание - изменена дата окончания "
                            f"для закупки {proc_number}. Было: {existing.end_date}, Стало: {end_date}"
                        )

                # Создание или обновление записи
                procurement, created = Procurement.objects.update_or_create(
                    subject=subject,
                    procurement_number=proc_number,
                    end_date=end_date,
                    defaults=cleaned_data
                )

                if created:
                    import_log['imported_rows'] += 1
                else:
                    import_log['warnings'].append(
                        f"Строка {row_num}: Обновлена существующая запись"
                    )

            except Exception as e:
                import_log['errors'].append(f"Строка {row_num}: Ошибка - {str(e)}")
                import_log['status'] = 'partial'

        # Сохранение лога импорта
        if import_log['errors']:
            import_log['status'] = 'failed'

        ImportLog.objects.create(**import_log)

        return import_log

    def clean_row_data(self, row):
        """Очистка и преобразование данных из CSV"""
        cleaned = {}

        # Маппинг полей CSV на поля модели
        field_mapping = {
            'Предмет закупки': 'subject',
            '№ Закупки': 'procurement_number',
            'Ссылка': 'link',
            'ТЗ (если недоступно по основной ссылке)': 'specification_link',
            'Статус': 'status',
            'Менеджер': 'manager',
            'Причина отсева': 'rejection_reason',
            'Дата окончания': 'end_date',
            'Закон или комм.площадка': 'platform',
            'Заказчик': 'customer',
            'Тип проведения': 'procurement_type',
            'НМЦ': 'nmc',
            'Обеспечение заявки': 'application_guarantee',
            'Обеспечение контракта': 'contract_guarantee',
            '': 'currency',  # Последняя колонка с валютой
        }

        status_mapping = {
            'отсев': 'rejected',
            'не актуально': 'not_actual',
            'активная': 'active',
            'завершена': 'completed',
        }

        type_mapping = {
            'Иной однолотовый способ': 'single_lot',
            'Запрос цен': 'price_request',
            'Запрос предложений': 'proposal_request',
            'Аукцион': 'auction',
            'Конкурс': 'competition',
        }

        for csv_field, model_field in field_mapping.items():
            value = row.get(csv_field, '').strip()

            if not value or value == '-':
                continue

            if model_field == 'end_date':
                # Преобразование даты
                try:
                    cleaned[model_field] = parse_datetime(value)
                    if not cleaned[model_field]:
                        # Попробуем другой формат
                        from datetime import datetime
                        cleaned[model_field] = datetime.strptime(value, '%d.%m.%Y %H:%M')
                except (ValueError, TypeError):
                    continue

            elif model_field == 'status' and value in status_mapping:
                cleaned[model_field] = status_mapping[value]

            elif model_field == 'procurement_type' and value in type_mapping:
                cleaned[model_field] = type_mapping[value]

            elif model_field in ['nmc', 'application_guarantee', 'contract_guarantee']:
                # Обработка числовых полей
                try:
                    cleaned[model_field] = float(value.replace(',', '.').replace(' ', ''))
                except (ValueError, TypeError):
                    continue

            else:
                cleaned[model_field] = value

        return cleaned