from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PriceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'price'
    verbose_name = _('Цены')

    def ready(self):
        """
        При старте сервера — обновить курсы ЦБ за сегодня.
        Если не получилось (нет сети, выходной у ЦБ) — используется
        последний сохранённый курс из БД.
        """
        try:
            from price.services.cbr_exchange import CBRExchangeService
            from datetime import date
            CBRExchangeService.fetch_and_save_rates(date.today())
        except Exception:
            pass
