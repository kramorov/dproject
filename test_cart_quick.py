"""Quick test runner — bypasses Django test runner to avoid migration overhead."""
import os, sys, django

os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoProject1.settings'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from cart.models import Cart, CartItem, CartEvent
from sku.models import SKU

passed = 0
failed = 0

def check(desc, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f'  ✅ {desc}')
    else:
        failed += 1
        print(f'  ❌ {desc}')

# ── Setup ──
u = User.objects.create_user(username='t', password='t')
sku = SKU.objects.create(code='T-001', name='Test')

# ── 1. Cart model ──
print('=== Cart model ===')
c = Cart.objects.create(user=u)
check('defaults', c.cart_type == 'cart' and c.status == 'active' and not c.is_active_cart)
check('item_count=0', c.item_count == 0 and c.total_quantity == 0)
CartItem.objects.create(cart=c, sku=sku, quantity=2)
check('item_count=1', c.item_count == 1)
check('total_quantity=2', c.total_quantity == 2)
check('description', Cart.objects.create(user=u, description='OL').description == 'OL')

# ── 2. CartItem model ──
print('=== CartItem model ===')
ci = c.items.first()
check('str', 'T-001' in str(ci))
s = ci.get_equipment_summary()
check('summary code', s['code'] == 'T-001')

# ── 3. CartEvent ──
print('=== CartEvent ===')
evt = CartEvent.log(c, CartEvent.EventType.CREATED)
check('event type', evt.event_type == 'created')
check('event cart', evt.cart == c)
evt2 = CartEvent.log(c, CartEvent.EventType.ITEM_ADDED, item_id='x', qty=3)
check('event data', evt2.data['qty'] == 3)
check('ordering newest first', list(c.events.all())[0] == evt2)

# ── 4. Active mechanics ──
print('=== Active cart ===')
c1 = Cart.objects.create(user=u, is_active_cart=True)
c2 = Cart.objects.create(user=u)
c2.set_active()
c1.refresh_from_db()
check('set_active deactivates', not c1.is_active_cart and c2.is_active_cart)

u2 = User.objects.create_user(username='t2', password='t')
c3 = Cart.objects.create(user=u2, is_active_cart=True)
check('get_active user1', Cart.get_active(user=u) == c2)
check('get_active user2', Cart.get_active(user=u2) == c3)
check('get_active none', Cart.get_active() is None)

u3 = User.objects.create_user(username='t3', password='t')
check('has_any false', not Cart.has_any(user=u3))
Cart.objects.create(user=u3)
check('has_any true', Cart.has_any(user=u3))

# ── 5. Cascade delete ──
print('=== Cascade delete ===')
cd = Cart.objects.create(user=u)
CartItem.objects.create(cart=cd, sku=sku)
item_count = CartItem.objects.count()
cd.delete()
check('cascade items', CartItem.objects.count() == item_count - 1)
event_count = CartEvent.objects.count()
CartEvent.log(Cart.objects.create(user=u), CartEvent.EventType.CREATED)
check('cascade events (different cart)', CartEvent.objects.count() == event_count + 1)

# ── Cleanup ──
Cart.objects.all().delete()
u.delete(); u2.delete(); u3.delete()
sku.delete()

print(f'\n{"="*30}')
print(f'Passed: {passed}, Failed: {failed}')
print('ALL PASSED' if not failed else 'SOME FAILED')
