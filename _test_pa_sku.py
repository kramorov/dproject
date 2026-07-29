"""Quick unit tests."""
import os, sys, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoProject1.settings'
sys.path.insert(0, '.')
django.setup()

from pneumatic_actuators.services.sku_service import _safe_code, build_pa_sku_code, build_pa_sku_name

errors = 0

# --- _safe_code ---
assert _safe_code(None) == '', f'None failed'
assert _safe_code(12) == '12'
assert _safe_code(0) == '0'
assert _safe_code(3.14) == '3.14'
assert _safe_code('hello') == 'hello'

class OptEnc: encoding = 'NC'; code = 'nc'
assert _safe_code(OptEnc()) == 'NC'

class OptCode: code = 'IP67'
assert _safe_code(OptCode()) == 'IP67'

class OptName: name = 'Std'
assert _safe_code(OptName()) == 'Std'

class OptEmptyEnc: encoding = ''; code = 'DA'
assert _safe_code(OptEmptyEnc()) == 'DA'

print('OK: _safe_code (8 tests)')

# --- build_pa_sku_code ---
class FakeItem: code = 'PA52'; name = 'PA52Name'
assert build_pa_sku_code(FakeItem(), {}) == 'PA52'
assert build_pa_sku_code(FakeItem(), {'springs_qty': 12, 'ip': 1}) == 'PA52-12-1'
assert build_pa_sku_code(FakeItem(), {'springs_qty': '12', 'ip': 'IP67'}) == 'PA52-12-IP67'
assert build_pa_sku_code(FakeItem(), {'springs_qty': 12, 'temperature': None, 'ip': 'IP67'}) == 'PA52-12-IP67'

class FakeItemNoCode: code = None; name = 'PA52Name'
assert build_pa_sku_code(FakeItemNoCode(), {'ip': 'IP67'}) == 'PA52Name-IP67'

print('OK: build_pa_sku_code (5 tests)')

# --- build_pa_sku_name ---
class FakeVar: name = 'SR'
class FakeBody: torque_at_6bar = 200
class FakeML: pass
class FakeItemFull: code='PA52'; name='PA52'; model_line=FakeML(); body=FakeBody(); pneumatic_actuator_variety=FakeVar()

name = build_pa_sku_name(FakeItemFull(), {'springs_qty': 12})
assert 'PA52' in name and 'SR' in name and '200' in name and '12' in name

class FakeMinimal: code='PA52'; name='PA52'; model_line=None; body=None; pneumatic_actuator_variety=None
assert build_pa_sku_name(FakeMinimal(), {}) == 'PA52'

print('OK: build_pa_sku_name (2 tests)')

print('\nAll pure-logic tests passed (15 total)')
