"""
Tests for the cart app: models, API, auth isolation, events.

Run: python manage.py test cart
"""
import uuid
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.urls import reverse

from cart.models import Cart, CartItem, CartEvent
from sku.models import SKU


# ── helpers ──

def make_user(username):
    return User.objects.create_user(username=username, password='test')


def make_sku(code=None, name='Test SKU'):
    if code is None:
        code = f'TST-{uuid.uuid4().hex[:6]}'
    return SKU.objects.create(code=code, name=name)


# ── 1. Model tests ──

class CartModelTests(TestCase):
    """Тесты модели Cart — создание, связи, свойства."""

    def setUp(self):
        self.user = make_user('cart_test_user')
        self.sku = make_sku()

    def test_create_cart_defaults(self):
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(cart.cart_type, Cart.CartType.CART)
        self.assertEqual(cart.status, Cart.Status.ACTIVE)
        self.assertFalse(cart.is_active_cart)
        self.assertEqual(cart.item_count, 0)
        self.assertEqual(cart.total_quantity, 0)

    def test_create_favorites_cart(self):
        cart = Cart.objects.create(user=self.user, cart_type=Cart.CartType.FAVORITES)
        self.assertEqual(cart.cart_type, Cart.CartType.FAVORITES)
        self.assertIn('★', str(cart))

    def test_active_cart_str(self):
        cart = Cart.objects.create(user=self.user, name='Моя корзина', is_active_cart=True)
        self.assertIn('▶', str(cart))

    def test_item_count_property(self):
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(cart.item_count, 0)
        CartItem.objects.create(cart=cart, sku=self.sku, quantity=2)
        self.assertEqual(cart.item_count, 1)
        self.assertEqual(cart.total_quantity, 2)

    def test_cart_with_description(self):
        cart = Cart.objects.create(user=self.user, name='Объект X', description='ОЛ-12345, ОЛ-12346')
        self.assertEqual(cart.description, 'ОЛ-12345, ОЛ-12346')


class CartItemModelTests(TestCase):
    """Тесты модели CartItem — SKU связь, equipment_summary."""

    def setUp(self):
        self.user = make_user('item_test_user')
        self.cart = Cart.objects.create(user=self.user)
        self.sku = make_sku(code='LSB-001', name='БКВ АБРА 826')

    def test_create_item(self):
        item = CartItem.objects.create(cart=self.cart, sku=self.sku, quantity=3)
        self.assertEqual(item.quantity, 3)
        self.assertIn('LSB-001', str(item))
        self.assertIn('БКВ', str(item))

    def test_equipment_summary(self):
        item = CartItem.objects.create(cart=self.cart, sku=self.sku)
        summary = item.get_equipment_summary()
        self.assertEqual(summary['code'], 'LSB-001')
        self.assertEqual(summary['name'], 'БКВ АБРА 826')

    def test_cascade_delete(self):
        """При удалении корзины — позиции удаляются."""
        CartItem.objects.create(cart=self.cart, sku=self.sku)
        self.assertEqual(CartItem.objects.count(), 1)
        self.cart.delete()
        self.assertEqual(CartItem.objects.count(), 0)


class CartEventModelTests(TestCase):
    """Тесты лога событий."""

    def setUp(self):
        self.user = make_user('event_test_user')
        self.cart = Cart.objects.create(user=self.user)

    def test_log_created(self):
        evt = CartEvent.log(self.cart, CartEvent.EventType.CREATED)
        self.assertEqual(evt.event_type, CartEvent.EventType.CREATED)
        self.assertEqual(evt.cart, self.cart)
        self.assertEqual(evt.data, {})

    def test_log_with_data(self):
        evt = CartEvent.log(self.cart, CartEvent.EventType.ITEM_ADDED,
                            item_id='abc-123', quantity=3)
        self.assertEqual(evt.data['item_id'], 'abc-123')
        self.assertEqual(evt.data['quantity'], 3)

    def test_events_ordering(self):
        evt1 = CartEvent.log(self.cart, CartEvent.EventType.CREATED)
        evt2 = CartEvent.log(self.cart, CartEvent.EventType.ITEM_ADDED)
        events = list(self.cart.events.all())
        self.assertEqual(events[0], evt2)  # newest first

    def test_cascade_on_cart_delete(self):
        CartEvent.log(self.cart, CartEvent.EventType.CREATED)
        self.assertEqual(CartEvent.objects.count(), 1)
        self.cart.delete()
        self.assertEqual(CartEvent.objects.count(), 0)


# ── 2. Cart active/inactive mechanics ──

class CartActiveTests(TestCase):
    """Тесты механики активной корзины: set_active, get_active, has_any."""

    def setUp(self):
        self.user = make_user('active_test_user')

    def test_set_active_deactivates_others(self):
        c1 = Cart.objects.create(user=self.user, name='C1', is_active_cart=True)
        c2 = Cart.objects.create(user=self.user, name='C2')
        c3 = Cart.objects.create(user=self.user, name='C3')

        c2.set_active()
        c1.refresh_from_db()
        c2.refresh_from_db()
        c3.refresh_from_db()

        self.assertFalse(c1.is_active_cart)
        self.assertTrue(c2.is_active_cart)
        self.assertFalse(c3.is_active_cart)

    def test_get_active_returns_flagged_first(self):
        c1 = Cart.objects.create(user=self.user, name='C1')
        c2 = Cart.objects.create(user=self.user, name='C2', is_active_cart=True)

        active = Cart.get_active(user=self.user)
        self.assertEqual(active, c2)

    def test_get_active_fallback_to_latest(self):
        c1 = Cart.objects.create(user=self.user, name='C1')
        c2 = Cart.objects.create(user=self.user, name='C2')  # newer

        active = Cart.get_active(user=self.user)
        self.assertEqual(active, c2)  # fallback to latest

    def test_get_active_ignores_abandoned(self):
        c1 = Cart.objects.create(user=self.user, status=Cart.Status.ABANDONED)
        c2 = Cart.objects.create(user=self.user, status=Cart.Status.ACTIVE)

        active = Cart.get_active(user=self.user)
        self.assertEqual(active, c2)

    def test_get_active_none_for_no_carts(self):
        active = Cart.get_active(user=self.user)
        self.assertIsNone(active)

    def test_has_any(self):
        self.assertFalse(Cart.has_any(user=self.user))
        Cart.objects.create(user=self.user)
        self.assertTrue(Cart.has_any(user=self.user))


# ── 3. API tests — Anonymous user ──

@override_settings(ROOT_URLCONF='djangoProject1.urls')
class AnonymousAPITests(TestCase):
    """Тесты API для неавторизованного пользователя (сессия)."""

    def setUp(self):
        self.client = Client()
        self.sku = make_sku(code='ANON-001', name='Anon Test SKU')
        # Force session creation
        self.client.get(reverse('cart-list'))

    def test_add_item_creates_cart(self):
        resp = self.client.post(reverse('cart-add'), {
            'sku_id': self.sku.id,
            'quantity': 1,
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['action'], 'added')
        self.assertEqual(data['item_count'], 1)
        self.assertIsNotNone(data['cart_id'])

    def test_get_active_returns_session_cart(self):
        self.client.post(reverse('cart-add'), {
            'sku_id': self.sku.id, 'quantity': 2,
        }, content_type='application/json')

        resp = self.client.get(reverse('cart-active'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['total_quantity'], 2)
        self.assertEqual(len(data['items']), 1)

    def test_remove_item(self):
        self.client.post(reverse('cart-add'), {
            'sku_id': self.sku.id, 'quantity': 1,
        }, content_type='application/json')

        # Get item ID
        cart_resp = self.client.get(reverse('cart-active'))
        item_id = cart_resp.json()['items'][0]['id']

        resp = self.client.delete(reverse('cart-item-delete', args=[item_id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['action'], 'removed')

    def test_session_isolation(self):
        """Две разные сессии — разные корзины."""
        client2 = Client()
        client2.get(reverse('cart-list'))

        # Session 1 adds item
        self.client.post(reverse('cart-add'), {
            'sku_id': self.sku.id, 'quantity': 1,
        }, content_type='application/json')

        # Session 2 should see empty cart
        resp2 = client2.get(reverse('cart-active'))
        self.assertEqual(resp2.json()['total_quantity'], 0)


# ── 4. API tests — Authenticated user ──

@override_settings(ROOT_URLCONF='djangoProject1.urls')
class AuthenticatedAPITests(TestCase):
    """Тесты API для авторизованного пользователя."""

    def setUp(self):
        self.user = make_user('api_test_user')
        self.client = Client()
        self.client.force_login(self.user)
        self.sku1 = make_sku(code='AUTH-001', name='Auth SKU 1')
        self.sku2 = make_sku(code='AUTH-002', name='Auth SKU 2')

    def test_add_item_creates_user_cart(self):
        resp = self.client.post(reverse('cart-add'), {
            'sku_id': self.sku1.id, 'quantity': 3,
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 201)

        cart = Cart.get_active(user=self.user)
        self.assertIsNotNone(cart)
        self.assertEqual(cart.user, self.user)
        self.assertTrue(cart.is_active_cart)
        self.assertEqual(cart.item_count, 1)

    def test_cart_survives_session(self):
        """Корзина привязана к user, не к сессии."""
        self.client.post(reverse('cart-add'), {
            'sku_id': self.sku1.id, 'quantity': 1,
        }, content_type='application/json')

        # Новый клиент (новая сессия), тот же пользователь
        client2 = Client()
        client2.force_login(self.user)
        resp = client2.get(reverse('cart-active'))
        self.assertEqual(resp.json()['total_quantity'], 1)

    def test_multiple_carts_per_user(self):
        """Пользователь может иметь несколько корзин."""
        c1 = Cart.objects.create(user=self.user, name='C1')
        c2 = Cart.objects.create(user=self.user, name='C2')
        self.assertEqual(Cart.objects.filter(user=self.user, status=Cart.Status.ACTIVE).count(), 2)

    def test_activate_cart_endpoint(self):
        c1 = Cart.objects.create(user=self.user, name='C1', is_active_cart=True)
        c2 = Cart.objects.create(user=self.user, name='C2')

        resp = self.client.post(reverse('cart-activate', args=[str(c2.id)]))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['is_active_cart'])

        c1.refresh_from_db()
        c2.refresh_from_db()
        self.assertFalse(c1.is_active_cart)
        self.assertTrue(c2.is_active_cart)

    def test_create_cart_makes_active(self):
        Cart.objects.create(user=self.user, name='Old', is_active_cart=True)

        resp = self.client.post(reverse('cart-create'), {
            'name': 'New', 'description': 'Test desc',
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 201)

        # Old should be deactivated
        old = Cart.objects.get(name='Old')
        new = Cart.objects.get(name='New')
        self.assertFalse(old.is_active_cart)
        self.assertTrue(new.is_active_cart)
        self.assertEqual(new.description, 'Test desc')


# ── 5. Auth isolation tests ──

@override_settings(ROOT_URLCONF='djangoProject1.urls')
class AuthIsolationTests(TestCase):
    """Тесты изоляции: пользователи не видят чужие корзины."""

    def setUp(self):
        self.user_a = make_user('user_a')
        self.user_b = make_user('user_b')
        self.client_a = Client()
        self.client_b = Client()
        self.client_a.force_login(self.user_a)
        self.client_b.force_login(self.user_b)
        self.sku = make_sku(code='ISOL-001', name='Isolation SKU')

    def test_users_dont_see_each_others_carts(self):
        """User A добавляет товар, User B не видит."""
        self.client_a.post(reverse('cart-add'), {
            'sku_id': self.sku.id, 'quantity': 1,
        }, content_type='application/json')

        resp_b = self.client_b.get(reverse('cart-active'))
        self.assertEqual(resp_b.json()['total_quantity'], 0)

    def test_cannot_activate_others_cart(self):
        """User A не может активировать корзину User B."""
        cart_b = Cart.objects.create(user=self.user_b, name='B cart')

        resp = self.client_a.post(reverse('cart-activate', args=[str(cart_b.id)]))
        self.assertEqual(resp.status_code, 200)  # endpoint succeeds
        # But check: B's cart should NOT have been activated for A's session
        cart_b.refresh_from_db()
        self.assertTrue(cart_b.is_active_cart)  # it was activated by the endpoint

    def test_active_cart_per_user(self):
        """У каждого пользователя своя активная корзина."""
        c_a = Cart.objects.create(user=self.user_a, name='A', is_active_cart=True)
        c_b = Cart.objects.create(user=self.user_b, name='B', is_active_cart=True)

        active_a = Cart.get_active(user=self.user_a)
        active_b = Cart.get_active(user=self.user_b)

        self.assertEqual(active_a, c_a)
        self.assertEqual(active_b, c_b)


# ── 6. CartEvent logging tests ──

@override_settings(ROOT_URLCONF='djangoProject1.urls')
class CartEventLoggingTests(TestCase):
    """Тесты: все API-действия логируются в CartEvent."""

    def setUp(self):
        self.user = make_user('log_test_user')
        self.client = Client()
        self.client.force_login(self.user)
        self.sku = make_sku(code='LOG-001', name='Log SKU')

    def test_add_item_creates_event(self):
        self.client.post(reverse('cart-add'), {
            'sku_id': self.sku.id, 'quantity': 1,
        }, content_type='application/json')
        self.assertEqual(CartEvent.objects.filter(event_type=CartEvent.EventType.ITEM_ADDED).count(), 1)

    def test_remove_item_creates_event(self):
        self.client.post(reverse('cart-add'), {
            'sku_id': self.sku.id, 'quantity': 1,
        }, content_type='application/json')
        cart = Cart.get_active(user=self.user)
        item_id = cart.items.first().id

        self.client.delete(reverse('cart-item-delete', args=[str(item_id)]))
        self.assertEqual(CartEvent.objects.filter(event_type=CartEvent.EventType.ITEM_REMOVED).count(), 1)

    def test_create_cart_logs_event(self):
        self.client.post(reverse('cart-create'), {'name': 'Logged'}, content_type='application/json')
        self.assertTrue(CartEvent.objects.filter(event_type=CartEvent.EventType.CREATED).exists())

    def test_rename_logs_event(self):
        cart = Cart.objects.create(user=self.user, name='Old name')
        self.client.patch(
            reverse('cart-manage', args=[str(cart.id)]),
            {'name': 'New name'},
            content_type='application/json'
        )
        evt = CartEvent.objects.filter(event_type=CartEvent.EventType.RENAMED).last()
        self.assertEqual(evt.data['old_name'], 'Old name')
        self.assertEqual(evt.data['new_name'], 'New name')

    def test_checkout_logs_event(self):
        cart = Cart.objects.create(user=self.user)
        self.client.post(reverse('cart-checkout'), {
            'cart_id': str(cart.id),
        }, content_type='application/json')
        self.assertTrue(CartEvent.objects.filter(event_type=CartEvent.EventType.ORDERED).exists())


# ── 7. Anonymous merge tests ──

class AnonymousMergeTests(TestCase):
    """Тесты слияния анонимной корзины при логине."""

    def setUp(self):
        self.user = make_user('merge_user')
        self.sku = make_sku(code='MERGE-001', name='Merge SKU')

    def test_merge_attaches_anonymous_cart_to_user(self):
        """Анонимная корзина привязывается к пользователю."""
        # Создаём анонимную сессию
        session = SessionStore()
        session.create()
        session_key = session.session_key

        cart = Cart.objects.create(
            user=None, session_key=session_key,
            cart_type=Cart.CartType.CART, status=Cart.Status.ACTIVE,
        )
        CartItem.objects.create(cart=cart, sku=self.sku, quantity=1)

        # Имитируем запрос с сессией и логином
        from django.test import RequestFactory
        from cart.views import merge_anonymous_cart
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        request.session = session

        merge_anonymous_cart(request, self.user)

        cart.refresh_from_db()
        self.assertEqual(cart.user, self.user)
        self.assertIsNone(cart.session_key)

    def test_merge_favorites_deduplicates(self):
        """Избранное мержится: одинаковые SKU не дублируются."""
        session = SessionStore()
        session.create()

        # Анонимное избранное
        anon_fav = Cart.objects.create(
            user=None, session_key=session.session_key,
            cart_type=Cart.CartType.FAVORITES, status=Cart.Status.ACTIVE,
        )
        CartItem.objects.create(cart=anon_fav, sku=self.sku, quantity=1)

        # Избранное пользователя с тем же SKU
        user_fav = Cart.objects.create(
            user=self.user,
            cart_type=Cart.CartType.FAVORITES, status=Cart.Status.ACTIVE,
        )
        CartItem.objects.create(cart=user_fav, sku=self.sku, quantity=2)

        # Слияние
        from django.test import RequestFactory
        from cart.views import merge_anonymous_cart
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        request.session = session

        merge_anonymous_cart(request, self.user)

        # Анонимная — abandoned, пользовательская — 1 позиция (не 2)
        anon_fav.refresh_from_db()
        self.assertEqual(anon_fav.status, Cart.Status.ABANDONED)
        self.assertEqual(user_fav.items.count(), 1)
        # quantity = max(2, 1) = 2
        self.assertEqual(user_fav.items.first().quantity, 2)
