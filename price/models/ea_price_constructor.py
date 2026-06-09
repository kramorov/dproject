# price/models/ea_price_constructor.py
"""
EAPriceConstructor — конфигуратор цен на электроприводы.

Одна запись = одна строка конфигуратора:
  model_line_item + power_supply + option_field + option → surcharge

Базовая цена хранится с option_field='base', option_id=None.
Надбавки за опции — с option_field='selected_ip', option_id=...

Пример:
  AR01E005, 220/50, base,       None,  45000, RUB, retail
  AR01E005, 220/50, selected_ip, IP68,   2000, RUB, retail
  AR01E005, 220/50, selected_exd,POTE,   5000, RUB, retail

Расчёт: sum(surcharge) по всем записям для model_line_item + power_supply + price_type.

Валюта — одна на все записи конфигурации (берётся из первой не-null).
Конвертация через ExchangeRate при выдаче клиенту.
"""

from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class EAPriceConstructor(models.Model):
    """
    Конфигуратор цен на электроприводы.

    Связывает model_line_item, выбранное напряжение и конкретную опцию с ценой.
    """

    # --- Связи ---
    document = models.ForeignKey(
        'price.EAPriceDocument',
        on_delete=models.CASCADE,
        related_name='rows',
        null=True, blank=True,
        verbose_name=_('Документ'),
        help_text=_('Документ конфигуратора цен (если цена импортирована из документа)')
    )

    model_line_item = models.ForeignKey(
        'electric_actuators.ElectricActuatorModelLineItem',
        on_delete=models.CASCADE,
        related_name='price_rows',
        verbose_name=_('Модель'),
        help_text=_('Модель в серии электроприводов')
    )

    power_supply = models.ForeignKey(
        'electric_actuators.ElectricPowerSupplyOption',
        on_delete=models.CASCADE,
        related_name='price_rows',
        verbose_name=_('Напряжение питания'),
        help_text=_('Выбранное напряжение питания')
    )

    # --- Опция ---
    option_field = models.CharField(
        max_length=100,
        verbose_name=_('Поле опции'),
        help_text=_('Имя поля в ElectricActuatorConstructor (или "base" для базовой цены)')
    )

    # Храним ID опции напрямую — это может быть ID through-модели или реальной опции.
    # Для through_attr=None (temperature, power_supply, turn_angle): ID самой through-модели.
    # Для through_attr задан (ip, exd, ...): ID реальной опции (params.IpOption и т.д.).
    # Для option_field='base': option_id = None.
    option_id = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('ID опции'),
        help_text=_('ID выбранной опции (through-модели или реальной)')
    )

    # --- Цена ---
    surcharge = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name=_('Цена / надбавка'),
        help_text=_('Базовая цена (для base) или надбавка к базовой цене')
    )

    currency = models.ForeignKey(
        'price.Currency', on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name=_('Валюта'),
        help_text=_('Валюта цены')
    )

    price_variety = models.ForeignKey(
        'price.PriceVariety', on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name=_('Тип цены'),
        help_text=_('Вид цены')
    )

    # --- Служебное ---
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активно'),
        help_text=_('Учитывать при расчёте цены')
    )

    class Meta:
        verbose_name = _('Строка конфигуратора цен ЭП')
        verbose_name_plural = _('Конфигуратор цен ЭП')
        ordering = ['model_line_item', 'power_supply', 'option_field', 'option_id']
        indexes = [
            models.Index(fields=['model_line_item', 'power_supply', 'price_variety']),
            models.Index(fields=['model_line_item', 'power_supply', 'option_field', 'option_id']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['model_line_item', 'power_supply', 'option_field', 'option_id', 'price_variety'],
                name='uq_ea_price_row'
            )
        ]

    def __str__(self):
        curr = self.currency.code if self.currency else '?'
        if self.option_field == 'base':
            return f"{self.model_line_item} | {self.power_supply} | BASE: {self.surcharge} {curr}"
        return f"{self.model_line_item} | {self.power_supply} | {self.option_field}={self.option_id}: {self.surcharge} {curr}"

    def clean(self):
        if self.option_field != 'base' and self.option_id is None:
            raise ValidationError({'option_id': _('option_id обязателен для не-base опций')})
        if self.option_field == 'base' and self.option_id is not None:
            raise ValidationError({'option_id': _('option_id должен быть пустым для base')})

    @classmethod
    def calculate_price(cls, constructor, price_variety_id=None):
        """
        Рассчитать цену сконструированного электропривода.

        Args:
            constructor: ElectricActuatorConstructor
            price_variety_id: ID PriceVariety (если None — первая попавшаяся)

        Returns:
            dict: {total, currency_code, base, surcharges}
        """
        from django.db.models import Q

        if not constructor.selected_model_line_item or not constructor.selected_power_supply:
            return None

        # Собираем все выбранные опции для фильтрации
        # В БД option_field хранится без префикса 'selected_' (как приходит из фронта)
        option_conditions = Q()
        for field_name, config in constructor._OPTION_CONFIG.items():
            value = getattr(constructor, field_name)
            if value and field_name != 'selected_power_supply':
                # Убираем префикс 'selected_' для совпадения с БД
                db_field = field_name
                if db_field.startswith('selected_'):
                    db_field = db_field[9:]
                option_conditions |= Q(option_field=db_field, option_id=value.id)

        # Один запрос
        filter_kwargs = {
            'model_line_item': constructor.selected_model_line_item,
            'power_supply': constructor.selected_power_supply,
            'is_active': True,
        }
        if price_variety_id:
            filter_kwargs['price_variety_id'] = price_variety_id

        rows = cls.objects.filter(**filter_kwargs).filter(
            Q(option_field='base') | option_conditions
        ).select_related('currency')

        base = Decimal('0')
        surcharges = []
        currency_code = None

        for row in rows:
            if row.option_field == 'base':
                base = row.surcharge
            else:
                surcharges.append({
                    'option_field': row.option_field,
                    'surcharge': row.surcharge,
                })
            if not currency_code and row.currency:
                currency_code = row.currency.code

        total = base + sum(s['surcharge'] for s in surcharges)

        return {
            'total': total,
            'currency': currency_code or 'RUB',
            'base': base,
            'surcharges': surcharges,
        }
