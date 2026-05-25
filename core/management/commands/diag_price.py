from django.core.management.base import BaseCommand
from price.models import ExchangeRate, PriceHistory, PriceVariety
from price.services.currency_converter import convert_price, get_bulk_prices
from project_customers.models import ProjectCustomer
from decimal import Decimal
from datetime import date

class Command(BaseCommand):
    def handle(self, *args, **options):
        # 1. Курсы
        self.stdout.write("=== ExchangeRate (last 5) ===")
        for r in ExchangeRate.objects.order_by('-date')[:5]:
            self.stdout.write(f"  {r.currency} -> RUB: {r.rate} on {r.date} (per one: {r.rate_per_one})")

        # 2. Цены
        self.stdout.write("\n=== PriceHistory (is_current, with SKU) ===")
        for p in PriceHistory.objects.filter(is_current=True, sku__isnull=False).select_related('sku','currency')[:3]:
            self.stdout.write(f"  SKU:{p.sku.code} price={p.price} {p.currency.code}")

        # 3. Конвертация
        self.stdout.write("\n=== Convert 100 USD -> RUB ===")
        r = convert_price(Decimal('100'), 'USD', 'RUB')
        self.stdout.write(f"  Result: {r} RUB")

        # 4. Bulk
        self.stdout.write("\n=== get_bulk_prices(['RD-1'], 'RUB') ===")
        self.stdout.write(str(get_bulk_prices(['RD-1'], 'RUB')))

        # 5. Customer
        self.stdout.write("\n=== Customer Архимед ===")
        a = ProjectCustomer.objects.filter(name__icontains='Архимед').first()
        if a:
            try:
                cs = a.settings
                self.stdout.write(f"  {a.name}: currency={cs.default_currency} (id={cs.default_currency_id})")
            except Exception as e:
                self.stdout.write(f"  {a.name}: no settings - {e}")
        else:
            self.stdout.write("  NOT FOUND")
