# cart/views.py
"""REST API для корзины и избранного."""
import logging
from django.db import models as dj_models
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Cart, CartItem, CartEvent
from .serializers import (
    CartSerializer, CartBareSerializer, CartItemSerializer,
    AddToCartSerializer, CheckoutSerializer,
)

log = logging.getLogger(__name__)


# ── слияние анонимной корзины ──

def merge_anonymous_cart(request, user):
    """
    При логине: найти анонимную корзину по session_key, привязать к user.

    Вызывается из сигнала user_logged_in или из /auth/me/.
    """
    session_key = request.session.session_key
    if not session_key:
        return

    anon_carts = Cart.objects.filter(
        session_key=session_key,
        user__isnull=True,
        status=Cart.Status.ACTIVE,
    )

    for anon in anon_carts:
        if anon.cart_type == Cart.CartType.FAVORITES:
            # Избранное: перенести позиции в избранное пользователя
            user_fav = Cart.objects.filter(
                user=user,
                cart_type=Cart.CartType.FAVORITES,
                status=Cart.Status.ACTIVE,
            ).first()
            if not user_fav:
                anon.user = user
                anon.session_key = None
                anon.save()
                CartEvent.log(anon, CartEvent.EventType.RENAMED,
                              old_name='(anonymous)', new_name=anon.name or '')
                continue
            # Мержим позиции
            for item in anon.items.all():
                existing = user_fav.items.filter(sku=item.sku).first()
                if existing:
                    existing.quantity = max(existing.quantity, item.quantity)
                    existing.save()
                else:
                    item.cart = user_fav
                    item.save()
            anon.status = Cart.Status.ABANDONED
            anon.save()
            CartEvent.log(anon, CartEvent.EventType.ABANDONED,
                          data={'merged_into': str(user_fav.id)})
        else:
            # Обычная корзина: просто привязать к user
            anon.user = user
            anon.session_key = None
            anon.save()
            CartEvent.log(anon, CartEvent.EventType.RENAMED,
                          old_name='(anonymous)', new_name=anon.name or '')


# ── helpers ──

def _get_or_create_cart(request, cart_type=Cart.CartType.CART):
    """Получить активную корзину пользователя или создать новую."""
    user = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key or request.session.create()

    if cart_type == Cart.CartType.FAVORITES:
        # Избранное — ровно одна на пользователя/сессию
        if user:
            cart, __ = Cart.objects.get_or_create(
                user=user, cart_type=cart_type,
                defaults={'status': Cart.Status.ACTIVE},
            )
        else:
            cart, __ = Cart.objects.get_or_create(
                session_key=session_key, cart_type=cart_type,
                defaults={'status': Cart.Status.ACTIVE},
            )
        return cart

    # Обычная корзина — берём активную (is_active_cart) или последнюю
    cart = Cart.get_active(user=user, session_key=session_key, cart_type=cart_type)
    if not cart:
        from datetime import datetime
        default_name = f"Новая корзина {datetime.now():%y-%m-%d-%H-%M}"
        cart = Cart.objects.create(
            user=user,
            session_key=None if user else session_key,
            cart_type=cart_type,
            status=Cart.Status.ACTIVE,
            is_active_cart=True,
            name=default_name,
        )
        CartEvent.log(cart, CartEvent.EventType.CREATED)
    elif not cart.is_active_cart:
        # Если корзина есть, но не помечена активной — делаем активной
        cart.set_active()
    return cart


def _get_existing_cart_item(cart, sku_id):
    """Проверить, есть ли уже такой SKU в корзине."""
    return cart.items.filter(sku_id=sku_id).first()


# ── API endpoints ──

@api_view(['GET'])
@permission_classes([AllowAny])
def cart_list(request):
    """GET /api/cart/ — список корзин пользователя (без позиций)."""
    user = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key
    if not user and not session_key:
        return Response([], status=status.HTTP_200_OK)

    qs = Cart.objects.filter(status=Cart.Status.ACTIVE)
    if user:
        qs = qs.filter(user=user)
    else:
        qs = qs.filter(session_key=session_key)

    serializer = CartBareSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([AllowAny])
def cart_detail(request, cart_id=None):
    """
    GET    /api/cart/{id}/ — одна корзина с позициями.
    POST   /api/cart/{id}/items/ — добавить позицию.
    DELETE /api/cart/{id}/items/{item_id}/ — удалить позицию.
    """
    if request.method == 'GET':
        if not cart_id:
            # /api/cart/active/ — активная корзина
            cart = _get_or_create_cart(request)
            serializer = CartSerializer(cart)
            return Response(serializer.data)

        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@permission_classes([AllowAny])
def favorites(request):
    """GET /api/cart/favorites/ — избранное."""
    cart = _get_or_create_cart(request, cart_type=Cart.CartType.FAVORITES)
    serializer = CartSerializer(cart)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def add_item(request):
    """
    POST /api/cart/add/
    Body: { sku_id, quantity, cart_type? }
    """
    serializer = AddToCartSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    cart_type = data.get('cart_type', Cart.CartType.CART)

    cart = _get_or_create_cart(request, cart_type=cart_type)

    existing = _get_existing_cart_item(cart, data['sku_id'])
    if existing:
        existing.quantity += data['quantity']
        existing.save()
        CartEvent.log(cart, CartEvent.EventType.ITEM_QTY,
                       item_id=str(existing.id), quantity=existing.quantity)
        item_serializer = CartItemSerializer(existing)
        return Response({
            'cart_id': str(cart.id),
            'item': item_serializer.data,
            'item_count': cart.item_count,
            'action': 'updated',
        })

    item = CartItem.objects.create(
        cart=cart,
        sku_id=data['sku_id'],
        quantity=data['quantity'],
    )
    CartEvent.log(cart, CartEvent.EventType.ITEM_ADDED,
                   item_id=str(item.id), sku_id=data['sku_id'],
                   quantity=data['quantity'])
    item_serializer = CartItemSerializer(item)
    return Response({
        'cart_id': str(cart.id),
        'item': item_serializer.data,
        'item_count': cart.item_count,
        'action': 'added',
    }, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def remove_item(request, item_id):
    """
    DELETE /api/cart/items/{item_id}/
    """
    try:
        item = CartItem.objects.get(id=item_id)
    except CartItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    saved_cart_id = item.cart_id
    item_id_str = str(item_id)
    item.delete()

    cart = Cart.objects.get(id=saved_cart_id)
    CartEvent.log(cart, CartEvent.EventType.ITEM_REMOVED, item_id=item_id_str)
    return Response({
        'cart_id': str(saved_cart_id),
        'item_id': item_id_str,
        'item_count': cart.item_count,
        'action': 'removed',
    })


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_item(request, item_id):
    """
    PATCH /api/cart/items/{item_id}/ — изменить количество/заметки.
    Body: { quantity?: int, notes?: str }
    """
    try:
        item = CartItem.objects.get(id=item_id)
    except CartItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    if 'quantity' in request.data:
        try:
            qty = int(request.data['quantity'])
        except (TypeError, ValueError):
            return Response({'error': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)
        if qty <= 0:
            saved_cart_id = item.cart_id
            item_id_str = str(item_id)
            item.delete()
            cart = Cart.objects.get(id=saved_cart_id)
            CartEvent.log(cart, CartEvent.EventType.ITEM_REMOVED, item_id=item_id_str)
            return Response({
                'cart_id': str(saved_cart_id),
                'item_id': item_id_str,
                'item_count': cart.item_count,
                'action': 'removed',
            })
        item.quantity = qty
        CartEvent.log(Cart.objects.get(id=item.cart_id), CartEvent.EventType.ITEM_QTY,
                       item_id=str(item.id), quantity=qty)

    if 'notes' in request.data:
        item.notes = request.data['notes']

    item.save()
    serializer = CartItemSerializer(item)
    return Response({'item': serializer.data, 'action': 'updated'})


@api_view(['POST'])
@permission_classes([AllowAny])
def create_cart(request):
    """
    POST /api/cart/create/
    Явно создать новую пустую корзину и сделать её активной.
    Body: { name?: str, description?: str }
    """
    from .serializers import CreateCartSerializer
    serializer = CreateCartSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key or request.session.create()

    name = serializer.validated_data.get('name', '') or None
    if not name:
        from datetime import datetime
        name = f"Новая корзина {datetime.now():%y-%m-%d-%H-%M}"
    owner_q = dj_models.Q(user=user) if user else dj_models.Q(session_key=session_key)
    cart = Cart.objects.create(
        user=user,
        session_key=None if user else session_key,
        cart_type=Cart.CartType.CART,
        status=Cart.Status.ACTIVE,
        name=name,
        description=serializer.validated_data.get('description', ''),
        is_active_cart=True,
    )
    # Деактивировать остальные корзины
    Cart.objects.filter(owner_q, cart_type=Cart.CartType.CART).exclude(id=cart.id).update(is_active_cart=False)
    CartEvent.log(cart, CartEvent.EventType.CREATED)

    cart_serializer = CartSerializer(cart)
    return Response(cart_serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
@permission_classes([AllowAny])
def manage_cart(request, cart_id):
    """
    PATCH  /api/cart/{id}/manage/ — переименовать/сменить статус.
    DELETE /api/cart/{id}/manage/ — удалить корзину.
    """
    try:
        cart = Cart.objects.get(id=cart_id)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PATCH':
        from .serializers import UpdateCartSerializer
        serializer = UpdateCartSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        if 'name' in data:
            old_name = cart.name
            cart.name = data['name']
            CartEvent.log(cart, CartEvent.EventType.RENAMED,
                           old_name=old_name, new_name=data['name'])
        if 'description' in data:
            cart.description = data['description']
        if 'status' in data:
            cart.status = data['status']
        cart.save()
        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data)

    if request.method == 'DELETE':
        cart.status = Cart.Status.ABANDONED
        cart.save()
        CartEvent.log(cart, CartEvent.EventType.ABANDONED)
        return Response({
            'cart_id': str(cart.id),
            'status': cart.status,
            'action': 'abandoned',
        })

    return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
@permission_classes([AllowAny])
def activate_cart(request, cart_id):
    """
    POST /api/cart/{id}/activate/ — сделать корзину активной.
    """
    try:
        cart = Cart.objects.get(id=cart_id, status=Cart.Status.ACTIVE)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

    cart.set_active()
    CartEvent.log(cart, CartEvent.EventType.RENAMED,
                   data={'activated': True})
    return Response({'cart_id': str(cart.id), 'is_active_cart': True})


# Mapping app_label → catalog API prefix
_CATALOG_API_MAP = {
    'pa_controls': '/api/pa-controls/catalog/',
    'filter_regulator': '/api/filter-regulator/catalog/',
    'gearbox': '/api/gearbox/catalog/',
    'solenoid_valves': '/api/solenoid-valves/catalog/',
    'pneumatic_fittings': '/api/pneumatic-fittings/catalog/',
    'pneumatic_actuators': '/api/pneumatic_actuators/catalog/',
    'electric_actuators': '/api/electric_actuators/catalog/',
    'cable_glands': '/api/cable-glands/catalog/',
}


# Приоритетный маппинг: equipment_type.code → catalog API prefix.
# Для фитингов вид уточняет каталог (резьба-трубка / глушитель / заглушка).
_CATALOG_API_MAP_BY_EQUIPMENT_TYPE = {
    'fitting-thread-pipe': '/api/pneumatic-fittings/catalog/',
    'fitting-silencer': '/api/pneumatic-silencers/catalog/',
    'fitting-plug': '/api/pneumatic-plugs/catalog/',
}


@api_view(['GET'])
@permission_classes([AllowAny])
def item_detail(request, item_id):
    """
    GET /api/cart/items/{item_id}/detail/
    Возвращает полную карточку товара через каталоговый API.
    Резолвит SKU → source_object → catalog detail endpoint → возвращает как есть.
    """
    try:
        item = CartItem.objects.select_related('sku').get(id=item_id)
    except CartItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    sku = item.sku
    source = sku.source_object
    if not source:
        return Response({'error': 'No source equipment'}, status=status.HTTP_404_NOT_FOUND)

    # Определить catalog API URL по app_label модели-источника
    app_label = source._meta.app_label
    ml_eq = getattr(getattr(source, 'model_line', None), 'equipment_type', None)
    eq_code = getattr(ml_eq, 'code', None) or getattr(getattr(source, 'equipment_type', None), 'code', None)
    api_prefix = _CATALOG_API_MAP_BY_EQUIPMENT_TYPE.get(eq_code) or _CATALOG_API_MAP.get(app_label)
    if not api_prefix:
        return Response({'error': f'No catalog API for {app_label}'}, status=status.HTTP_404_NOT_FOUND)

    # Прокси к каталоговому API через реальный HTTP
    import requests as http_requests
    catalog_url = f'http://127.0.0.1:8000{api_prefix}{source.pk}/'
    try:
        # Передать сессию пользователя
        cookies = {}
        if hasattr(request, 'COOKIES'):
            cookies = request.COOKIES
        resp = http_requests.get(catalog_url, cookies=cookies, timeout=5)
        if resp.status_code == 200:
            return Response(resp.json())
        log.warning(f'item_detail catalog API returned {resp.status_code}: {catalog_url}')
    except Exception as e:
        log.warning(f'item_detail catalog API failed: {e}')

    # Fallback
    return Response({
        'id': source.pk,
        'code': getattr(source, 'code', sku.code),
        'name': getattr(source, 'name', sku.name),
        'title': getattr(source, 'name', sku.name),
        'sku': {'id': sku.id, 'code': sku.code},
        'sections': [],
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def checkout(request):
    """
    POST /api/cart/checkout/
    Заглушка — конвертация корзины в ClientRequest.

    Body: { cart_id, project_customer_id?, name? }
    """
    serializer = CheckoutSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    try:
        cart = Cart.objects.get(id=data['cart_id'])
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

    # TODO: реальная конвертация в ClientRequest
    cart.status = Cart.Status.ORDERED
    if data.get('name'):
        cart.name = data['name']
    cart.save()
    CartEvent.log(cart, CartEvent.EventType.ORDERED)

    return Response({
        'cart_id': str(cart.id),
        'status': cart.status,
        'message': 'Заказ оформлен (заглушка). Реальная конвертация — позже.',
    })
