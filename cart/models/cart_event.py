# cart/models/cart_event.py
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class CartEvent(models.Model):
    """
    Лог событий корзины — для аналитики и аудита.

    Каждое изменение корзины (создание, добавление/удаление позиций,
    переименование, оформление, удаление) пишет запись сюда.
    """
    class EventType(models.TextChoices):
        CREATED = 'created', _('Корзина создана')
        ITEM_ADDED = 'item_added', _('Позиция добавлена')
        ITEM_REMOVED = 'item_removed', _('Позиция удалена')
        ITEM_QTY = 'item_qty', _('Количество изменено')
        RENAMED = 'renamed', _('Переименована')
        ORDERED = 'ordered', _('Оформлена')
        ABANDONED = 'abandoned', _('Удалена')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    cart = models.ForeignKey(
        'cart.Cart',
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name=_('Корзина'),
    )

    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        verbose_name=_('Тип события'),
    )

    data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Данные'),
        help_text=_('item_id, old_name, new_name, quantity и т.д.'),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Время'),
    )

    class Meta:
        verbose_name = _('Событие корзины')
        verbose_name_plural = _('События корзин')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cart', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
        ]

    def __str__(self):
        return f'{self.cart.id.hex[:6]} {self.get_event_type_display()} @ {self.created_at:%Y-%m-%d %H:%M}'

    @classmethod
    def log(cls, cart, event_type, **data):
        """Утилита: быстро записать событие."""
        return cls.objects.create(cart=cart, event_type=event_type, data=data)
