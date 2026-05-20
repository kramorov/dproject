# price/models/pricing_rule.py
"""
PricingRule — правила скидок/наценок для партнёров и категорий клиентов.

Применяются при расчёте цены для отображения:
    base_price = PriceHistory.get_current_price(product, РРЦ)
    display_price = apply_rules(partner_or_company, base_price)

Правила имеют приоритет: при конфликте нескольких правил
выбирается правило с наибольшим priority (или наиболее специфичное).
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import StructuredDataMixin


class PricingRule(StructuredDataMixin, models.Model):
    """
    Правило скидки или наценки.

    Связывает:
        target (КОМУ) — партнёр или категория клиентов
        scope (НА ЧТО) — бренд / тип оборудования / серия / конкретный товар
        action (ЧТО) — скидка или наценка, в процентах

    Поля:
        target_type — partner / company
        partner — FK → ProjectCustomer (если target_type=partner)
        company — FK → Company (если target_type=company)
        scope_type — brand / equipment_type / model_line / product
        brand — FK → Brands (если scope_type=brand)
        equipment_type — FK → EquipmentType (если scope_type=equipment_type)
        rule_type — discount / markup
        value — проценты (положительное число)
        priority — при конфликте правил (больше = приоритетнее)
    """
    class TargetType(models.TextChoices):
        PARTNER = 'partner', 'Партнёр'
        COMPANY = 'company', 'Клиент'

    class ScopeType(models.TextChoices):
        BRAND = 'brand', 'Бренд'
        EQUIPMENT_TYPE = 'equipment_type', 'Тип оборудования'
        MODEL_LINE = 'model_line', 'Серия'
        PRODUCT = 'product', 'Конкретный товар'

    class RuleType(models.TextChoices):
        DISCOUNT = 'discount', 'Скидка'
        MARKUP = 'markup', 'Наценка'

    # КОМУ применяется
    target_type = models.CharField(
        max_length=10, choices=TargetType.choices,
        verbose_name=_("Тип цели")
    )
    partner = models.ForeignKey(
        'project_customers.ProjectCustomer', on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='pricing_rules',
        verbose_name=_("Партнёр")
    )
    company = models.ForeignKey(
        'clients.Company', on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='pricing_rules',
        verbose_name=_("Клиент")
    )

    # НА ЧТО применяется
    scope_type = models.CharField(
        max_length=20, choices=ScopeType.choices,
        verbose_name=_("Область действия")
    )
    brand = models.ForeignKey(
        'producers.Brands', on_delete=models.CASCADE,
        blank=True, null=True,
        verbose_name=_("Бренд")
    )
    equipment_type = models.ForeignKey(
        'core.EquipmentType', on_delete=models.CASCADE,
        blank=True, null=True,
        verbose_name=_("Тип оборудования")
    )

    # ЧТО делаем
    rule_type = models.CharField(
        max_length=10, choices=RuleType.choices,
        verbose_name=_("Тип правила")
    )
    value = models.DecimalField(
        max_digits=5, decimal_places=2,
        verbose_name=_("Значение, %"),
        help_text=_("Положительное число: 10 = 10% скидки/наценки")
    )

    priority = models.IntegerField(
        default=0,
        verbose_name=_("Приоритет"),
        help_text=_("Больше = приоритетнее при конфликте")
    )

    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        ordering = ['-priority']
        verbose_name = _('Правило ценообразования')
        verbose_name_plural = _('Правила ценообразования')

    def __str__(self):
        target = self.partner or self.company or '?'
        action = f"{'+' if self.rule_type == 'markup' else '-'}{self.value}%"
        scope = self.brand or self.equipment_type or 'всё'
        return f"{target}: {action} на {scope}"

    def apply(self, base_price):
        """
        Применить правило к базовой цене.

        Returns:
            float — цена после применения правила
        """
        factor = 1 + (self.value / 100) if self.rule_type == 'markup' else 1 - (self.value / 100)
        return round(float(base_price) * factor, 2)
