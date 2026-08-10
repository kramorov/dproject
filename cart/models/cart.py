# cart/models/cart.py
import uuid
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from djangoProject1.common_models.abstract_models import CreatedAtMixin, UpdatedAtMixin


class Cart(CreatedAtMixin, UpdatedAtMixin):
    """
    Корзина / Избранное.

    Может быть привязана к:
    - авторизованному пользователю (user)
    - анонимной сессии (session_key)
    - ProjectCustomer + сотруднику

    cart_type='favorites' — ровно одна корзина на пользователя/сессию.
    cart_type='cart' — может быть несколько.

    is_active_cart — указатель на активную корзину.
    Только одна корзина на пользователя/сессию может быть активной.
    """
    class CartType(models.TextChoices):
        CART = 'cart', _('Корзина')
        FAVORITES = 'favorites', _('Избранное')

    class Status(models.TextChoices):
        ACTIVE = 'active', _('Активна')
        ORDERED = 'ordered', _('Оформлена')
        ABANDONED = 'abandoned', _('Брошена')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    cart_type = models.CharField(
        max_length=20,
        choices=CartType.choices,
        default=CartType.CART,
        verbose_name=_('Тип'),
    )

    name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Название'),
        help_text=_('Краткое название для идентификации среди других корзин'),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Описание'),
        help_text=_('Подробное описание/назначение корзины (например, ОЛ, объект)'),
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name=_('Статус'),
    )

    is_active_cart = models.BooleanField(
        default=False,
        verbose_name=_('Активная корзина'),
        help_text=_('Указатель — в какую корзину добавлять товары. Только одна на пользователя.'),
    )

    # ── Владелец ──
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='carts',
        verbose_name=_('Пользователь'),
    )

    session_key = models.CharField(
        max_length=40,
        blank=True, null=True,
        db_index=True,
        verbose_name=_('Ключ сессии'),
        help_text=_('Для неавторизованных пользователей'),
    )

    project_customer = models.ForeignKey(
        'project_customers.ProjectCustomer',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='carts',
        verbose_name=_('Клиент (компания)'),
    )

    employee = models.ForeignKey(
        'project_customers.ProjectCustomerUser',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='carts',
        verbose_name=_('Сотрудник'),
    )

    # ── Для конвертации в заказ ──
    client_request = models.ForeignKey(
        'client_requests.ClientRequest',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='source_carts',
        verbose_name=_('Созданная заявка'),
        help_text=_('Заявка, созданная из этой корзины при оформлении'),
    )

    class Meta:
        verbose_name = _('Корзина')
        verbose_name_plural = _('Корзины')
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'cart_type', 'status']),
            models.Index(fields=['session_key', 'cart_type']),
            models.Index(fields=['project_customer', 'status']),
            models.Index(fields=['user', 'is_active_cart']),
        ]

    def __str__(self):
        type_label = '★' if self.cart_type == self.CartType.FAVORITES else '🛒'
        name = self.name or f'Корзина {self.id.hex[:6]}'
        active = ' ▶' if self.is_active_cart else ''
        return f'{type_label} {name}{active}'

    @property
    def item_count(self):
        return self.items.count()

    @property
    def total_quantity(self):
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0

    def set_active(self):
        """Сделать эту корзину активной, деактивировать остальные."""
        owner_filter = (
            models.Q(user=self.user) if self.user else
            models.Q(session_key=self.session_key)
        )
        Cart.objects.filter(owner_filter, cart_type=self.cart_type).update(is_active_cart=False)
        self.is_active_cart = True
        self.save(update_fields=['is_active_cart'])

    @classmethod
    def get_active(cls, user=None, session_key=None, cart_type='cart'):
        """Получить активную корзину пользователя."""
        qs = cls.objects.filter(cart_type=cart_type, status=cls.Status.ACTIVE)
        if user:
            qs = qs.filter(user=user)
        elif session_key:
            qs = qs.filter(session_key=session_key)
        else:
            return None

        # Сначала — явно отмеченная активной
        active = qs.filter(is_active_cart=True).first()
        if active:
            return active
        # Иначе — последняя активная
        return qs.order_by('-updated_at').first()

    @classmethod
    def has_any(cls, user=None, session_key=None, cart_type='cart'):
        """Есть ли хоть одна активная корзина (любая, не обязательно с флагом)."""
        qs = cls.objects.filter(cart_type=cart_type, status=cls.Status.ACTIVE)
        if user:
            qs = qs.filter(user=user)
        elif session_key:
            qs = qs.filter(session_key=session_key)
        else:
            return False
        return qs.exists()
