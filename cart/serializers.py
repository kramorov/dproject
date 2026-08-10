# cart/serializers.py
from rest_framework import serializers

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    """Позиция корзины с информацией из SKU и ценой."""
    equipment_summary = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    images = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'sku_id', 'quantity', 'added_at', 'notes',
            'equipment_summary', 'price', 'total', 'images',
        ]
        read_only_fields = ['id', 'added_at', 'equipment_summary', 'price', 'total', 'images']

    def get_images(self, obj: CartItem) -> list:
        """Вернуть массив изображений в формате [{preview_url, url}] (как в каталоге)."""
        img = obj.get_equipment_summary().get('image')
        if img:
            return [{'preview_url': img, 'url': img}]
        return []

    def get_equipment_summary(self, obj: CartItem) -> dict:
        """Вернуть краткую информацию о товаре: код, название, бренд, фото, характеристики."""
        return obj.get_equipment_summary()

    def get_price(self, obj: CartItem) -> float | None:
        """Вернуть цену за единицу в RUB (с конвертацией из USD через курс ЦБ)."""
        info = self._get_price_info(obj)
        return info['price']

    def get_total(self, obj: CartItem) -> float | None:
        """Вернуть сумму = цена × количество."""
        info = self._get_price_info(obj)
        price = info['price']
        return round(price * obj.quantity, 2) if price is not None else None

    def _get_price_info(self, obj: CartItem) -> dict:
        """
        Разрешить цену SKU с кешированием на уровне запроса.

        Двухуровневый кеш:
        1. CartItem.price_date >= сегодня → цена из price_snapshot (0 запросов к БД)
        2. Иначе → PriceHistory.get_current_price_by_sku() → конвертация → запись в БД
        """
        if not hasattr(self, '_price_cache'):
            self._price_cache = {}
        key = obj.sku_id
        if key not in self._price_cache:
            self._price_cache[key] = _resolve_sku_price(obj.sku_id, existing_item=obj)
        return self._price_cache[key]


def _resolve_sku_price(sku_id, existing_item=None):
    """
    Получить цену SKU. Кешируется в CartItem.price_snapshot на один день.

    Логика:
    1. Если price_snapshot есть и price_date >= сегодня → вернуть кеш
    2. Иначе → запросить PriceHistory, сохранить в CartItem, вернуть
    """
    from datetime import date
    today = date.today()

    # 1. Кеш ещё актуален?
    if existing_item and existing_item.price_snapshot is not None:
        if existing_item.price_date and existing_item.price_date >= today:
            return {
                'price': float(existing_item.price_snapshot),
                'currency_symbol': '₽',
                'currency_code': 'RUB',
            }

    # 2. Запросить реальную цену
    try:
        from price.models import PriceHistory, PriceVariety, Currency
        from price.models.exchange_rate import ExchangeRate
        pv = PriceVariety.objects.filter(is_active=True).order_by('sorting_order').first()
        if not pv:
            return {'price': None, 'currency_symbol': '', 'currency_code': ''}
        ph = PriceHistory.get_current_price_by_sku(sku_id, pv)
        if ph and ph.price is not None:
            price_val = float(ph.price)
            ph_currency = ph.currency
            # Конвертация в RUB через курс ЦБ
            if ph_currency and ph_currency.code != 'RUB':
                rate_obj = ExchangeRate.objects.filter(
                    currency=ph_currency.code
                ).order_by('-date').first()
                if rate_obj and rate_obj.rate:
                    price_val = round(price_val * float(rate_obj.rate) / float(rate_obj.nominal or 1), 2)
            # Сохранить кеш в CartItem (всегда в RUB)
            if existing_item:
                existing_item.price_snapshot = price_val
                existing_item.price_date = today
                existing_item.price_currency = 'RUB'
                existing_item.save(update_fields=['price_snapshot', 'price_date', 'price_currency'])
            return {
                'price': price_val,
                'currency_symbol': '₽',
                'currency_code': 'RUB',
            }
        # fallback
        cur = Currency.objects.filter(is_active=True).order_by('sorting_order').first()
        return {
            'price': None,
            'currency_symbol': cur.symbol if cur else '₽',
            'currency_code': cur.code if cur else 'RUB',
        }
    except Exception:
        return {'price': None, 'currency_symbol': '₽', 'currency_code': 'RUB'}


class CartSerializer(serializers.ModelSerializer):
    """Корзина со списком позиций."""
    items = CartItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = [
            'id', 'cart_type', 'name', 'status',
            'user', 'session_key', 'project_customer', 'employee',
            'client_request',
            'items', 'item_count', 'total_quantity',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CartBareSerializer(serializers.ModelSerializer):
    """Список корзин без позиций (для навигации)."""
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = [
            'id', 'cart_type', 'name', 'status',
            'is_active_cart', 'item_count', 'updated_at',
        ]
        read_only_fields = ['id', 'is_active_cart', 'updated_at']


class AddToCartSerializer(serializers.Serializer):
    """Добавление позиции в корзину по SKU."""
    sku_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1, min_value=1)
    cart_type = serializers.ChoiceField(choices=Cart.CartType.choices, default=Cart.CartType.CART)


class CartItemBulkUpdateSerializer(serializers.Serializer):
    """Массовое обновление количества позиций."""
    items = serializers.ListField(
        child=serializers.DictField(child=serializers.IntegerField()),
        help_text="[{'item_id': str, 'quantity': int}, ...]"
    )


class CreateCartSerializer(serializers.Serializer):
    """Явное создание новой корзины."""
    name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)


class UpdateCartSerializer(serializers.Serializer):
    """Обновление корзины — название, описание, статус."""
    name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=Cart.Status.choices, required=False)


class CheckoutSerializer(serializers.Serializer):
    """Оформление заказа — конвертация в ClientRequest."""
    cart_id = serializers.UUIDField()
    project_customer_id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)
