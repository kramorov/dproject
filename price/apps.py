from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PriceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'price'
    verbose_name = _('Цены')

    def ready(self):
        # Defer exchange rate fetch to post-migrate signal
        # to avoid "Accessing the database during app initialization" warning
        from django.db.models.signals import post_migrate

        def fetch_rates_on_startup(sender, **kwargs):
            try:
                from price.services.cbr_exchange import CBRExchangeService
                from datetime import date
                CBRExchangeService.fetch_and_save_rates(date.today())
            except Exception:
                pass

        post_migrate.connect(fetch_rates_on_startup, sender=self)
