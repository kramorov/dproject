# price/management/commands/import_prices.py
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now
from django.utils.dateparse import parse_date
from price.models import PriceHistory, Currency, PriceVariety
import os
import logging

logger = logging.getLogger(__name__)
"""
# Базовый импорт
python manage.py import_prices prices.xlsx --currency USD --price-type retail

# С указанием даты и колонок
python manage.py import_prices prices.xlsx \
    --currency RUB \
    --price-type wholesale \
    --date 2024-02-13 \
    --name-col "Наименование" \
    --price-col "Цена" \
    --code-col "Артикул"

# Тестовый запуск без сохранения
python manage.py import_prices prices.xlsx --currency EUR --price-type retail --dry-run

# Обновление существующих записей
python manage.py import_prices prices.xlsx --currency USD --price-type retail --update-existing
"""

class Command(BaseCommand):
    help = 'Импорт цен из Excel файла'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к Excel файлу')
        parser.add_argument('--sheet', type=str, default=0, help='Номер или название листа (по умолчанию 0)')
        parser.add_argument('--currency', type=str, required=True, help='Код валюты (RUB, USD, EUR, CNY)')
        parser.add_argument('--price-type', type=str, required=True, help='Код типа цены')
        parser.add_argument('--date', type=str, help='Дата цен (ГГГГ-ММ-ДД). Если не указана - сегодня')
        parser.add_argument('--name-col', type=str, default='name', help='Название колонки с наименованием')
        parser.add_argument('--price-col', type=str, default='price', help='Название колонки с ценой')
        parser.add_argument('--code-col', type=str, default='code', help='Название колонки с кодом')
        parser.add_argument('--desc-col', type=str, default='description', help='Название колонки с описанием')
        parser.add_argument('--skip-rows', type=int, default=0, help='Пропустить первые N строк')
        parser.add_argument('--dry-run', action='store_true', help='Тестовый запуск без сохранения')
        parser.add_argument('--update-existing', action='store_true',
                            help='Обновлять существующие записи по name+code+date')

    def handle(self, *args, **options):
        file_path = options['file_path']

        # Проверяем существование файла
        if not os.path.exists(file_path):
            raise CommandError(f'Файл не найден: {file_path}')

        self.stdout.write(f"📁 Файл: {file_path}")

        # Получаем валюту
        try:
            currency = Currency.objects.get(code=options['currency'])
            self.stdout.write(f"💰 Валюта: {currency.code} - {currency.name}")
        except Currency.DoesNotExist:
            raise CommandError(f'Валюта с кодом {options["currency"]} не найдена')

        # Получаем тип цены
        try:
            price_type = PriceVariety.objects.get(code=options['price_type'])
            self.stdout.write(f"🏷️ Тип цены: {price_type.name}")
        except PriceVariety.DoesNotExist:
            raise CommandError(f'Тип цены с кодом {options["price_type"]} не найден')

        # Определяем дату цен
        if options['date']:
            import_date = parse_date(options['date'])
            if not import_date:
                raise CommandError(f'Неверный формат даты: {options["date"]}. Используйте ГГГГ-ММ-ДД')
        else:
            import_date = now().date()

        self.stdout.write(f"📅 Дата цен: {import_date.strftime('%d.%m.%Y')}")

        # Читаем Excel
        self.stdout.write(f"📖 Чтение листа: {options['sheet']}")
        try:
            df = pd.read_excel(
                file_path,
                sheet_name=options['sheet'],
                skiprows=options['skip_rows'],
                dtype=str
            )
        except Exception as e:
            raise CommandError(f'Ошибка чтения Excel: {e}')

        self.stdout.write(f"📊 Найдено строк: {len(df)}")

        # Проверяем наличие колонок
        required_cols = [options['name_col'], options['price_col']]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            self.stdout.write(self.style.ERROR(f"❌ Доступные колонки: {list(df.columns)}"))
            raise CommandError(f'❌ Отсутствуют обязательные колонки: {", ".join(missing_cols)}')

        # Статистика
        stats = {
            'total': len(df),
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
        }

        error_rows = []

        # Обрабатываем строки
        for idx, row in df.iterrows():
            try:
                # Получаем данные
                name = str(row[options['name_col']]).strip()
                price_str = str(row[options['price_col']]).strip()

                # Пропускаем пустые строки
                if pd.isna(name) or not name or pd.isna(price_str) or not price_str:
                    stats['skipped'] += 1
                    continue

                # Очищаем цену от лишних символов
                price_str = (price_str.replace(' ', '')
                             .replace(',', '.')
                             .replace('₽', '')
                             .replace('$', '')
                             .replace('€', '')
                             .replace('¥', ''))

                try:
                    price = float(price_str)
                except ValueError:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️ Строка {idx + 2}: Неверный формат цены '{price_str}'"
                    ))
                    stats['skipped'] += 1
                    error_rows.append(idx + 2)
                    continue

                # Получаем код (если есть колонка)
                code = None
                if options['code_col'] in df.columns:
                    code_val = row[options['code_col']]
                    if not pd.isna(code_val):
                        code = str(code_val).strip()

                # Получаем описание (если есть колонка)
                description = ''
                if options['desc_col'] in df.columns:
                    desc_val = row[options['desc_col']]
                    if not pd.isna(desc_val):
                        description = str(desc_val).strip()

                # Проверяем существующую запись
                existing = None
                if options['update_existing']:
                    existing = PriceHistory.objects.filter(
                        name=name,
                        code=code,
                        price_date=import_date,
                        price_variety=price_type,
                        currency=currency
                    ).first()

                if existing and options['update_existing']:
                    # Обновляем существующую
                    if not options['dry_run']:
                        existing.price = price
                        existing.description = description
                        existing.save()
                    stats['updated'] += 1
                    action = "🔄 Обновлено"
                else:
                    # Создаем новую
                    if not options['dry_run']:
                        PriceHistory.objects.create(
                            name=name,
                            code=code if code else None,
                            price=price,
                            currency=currency,
                            price_variety=price_type,
                            price_date=import_date,
                            description=description,
                            is_active=True,
                        )
                    stats['created'] += 1
                    action = "✅ Создано"

                if options['dry_run']:
                    action = "📋 (dry-run) " + action

                self.stdout.write(f"{action}: {name} - {price} {currency.code}")

            except Exception as e:
                stats['errors'] += 1
                error_rows.append(idx + 2)
                self.stdout.write(self.style.ERROR(
                    f"❌ Ошибка в строке {idx + 2}: {e}"
                ))

        # Итог
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("📊 СТАТИСТИКА ИМПОРТА:"))
        self.stdout.write(f"📑 Всего строк: {stats['total']}")
        self.stdout.write(f"✅ Создано: {stats['created']}")
        self.stdout.write(f"🔄 Обновлено: {stats['updated']}")
        self.stdout.write(f"⏭️ Пропущено: {stats['skipped']}")
        self.stdout.write(f"❌ Ошибок: {stats['errors']}")

        if error_rows:
            self.stdout.write(self.style.WARNING(
                f"⚠️ Строки с ошибками: {', '.join(map(str, error_rows))}"
            ))

        if options['dry_run']:
            self.stdout.write(self.style.WARNING(
                "\n🔍 Это был тестовый запуск (dry-run). Данные не сохранены."
            ))

        self.stdout.write("=" * 50)