# price/management/commands/update_exchange_rates.py
"""
Команда для обновления курсов валют:
python manage.py update_exchange_rates
python manage.py update_exchange_rates --date 2024-01-15
python manage.py update_exchange_rates --period 7
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from datetime import date, datetime
from typing import Dict, Optional
from price.services.cbr_exchange import CBRExchangeService

class Command(BaseCommand):
    help = 'Обновление курсов валют от ЦБ РФ'

    def add_arguments(self, parser):
        parser.add_argument('--date', type=str, help='Дата курса (ГГГГ-ММ-ДД)')
        parser.add_argument('--period', type=int, help='Обновить за последние N дней')

    def handle(self, *args, **options):
        if options['date']:
            target_date = timezone.datetime.strptime(options['date'], '%Y-%m-%d').date()
            CBRExchangeService.fetch_and_save_rates(target_date)
            self.stdout.write(f"Курсы на {target_date} обновлены")

        elif options['period']:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=options['period'])
            CBRExchangeService.update_rates_for_period(start_date, end_date)
            self.stdout.write(f"Курсы за период {start_date} - {end_date} обновлены")

        else:
            CBRExchangeService.fetch_and_save_rates()
            self.stdout.write(f"Курсы на сегодня обновлены")