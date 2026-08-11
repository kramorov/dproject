"""
configurator/tests/test_services.py

Тесты сервисов configurator на копии боевой базы.
БЕЗ Django TestCase — избегаем конфликтов с тестовой БД.

Запуск:
    python configurator/tests/runtests.py -v
"""
import os
import sys
import unittest

# ── Django setup (один раз, в runtests.py) ──
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, _PROJECT_ROOT)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
    import django
    django.setup()

from core.models import EquipmentType
from ai_assistant.models import CompositionGroup
from configurator.models import (
    AssemblyRequirements,
    ComponentRequirement,
    ParameterRule,
    DerivationRule,
)
from configurator.services.registry import (
    get_product_model_class,
    PRODUCT_MODEL_REGISTRY,
)
from configurator.services.expander import expand_composition_group
from configurator.services.resolver import (
    resolve_effective_requirements,
    resolve_all_components,
)
from configurator.services.filter_engine import (
    filter_by_requirements,
    select_product,
)
from configurator.services.cascade import cascade_after_select


# ═══════════════════════════════════════════════════════════════════
# 1. Registry
# ═══════════════════════════════════════════════════════════════════

class RegistryTest(unittest.TestCase):
    """Тесты реестра EquipmentType → Model."""

    def test_all_registered_types_resolve(self):
        for code in PRODUCT_MODEL_REGISTRY:
            model_class = get_product_model_class(code)
            self.assertIsNotNone(model_class, f"Model for '{code}' is None")

    def test_lsb_resolves_to_limitswitchbox(self):
        from pa_controls.models import LimitSwitchBox
        self.assertEqual(get_product_model_class('lsb'), LimitSwitchBox)

    def test_manual_override_resolves_to_gearbox(self):
        from gearbox.models.gearbox import GearBox
        self.assertEqual(get_product_model_class('manual-override'), GearBox)

    def test_unregistered_raises_keyerror(self):
        with self.assertRaises(KeyError):
            get_product_model_class('nonexistent-type')

    def test_equipment_type_instance_resolves(self):
        et = EquipmentType.objects.get(code='lsb')
        self.assertIsNotNone(get_product_model_class(et))

    def test_cache_returns_same_instance(self):
        m1 = get_product_model_class('lsb')
        m2 = get_product_model_class('lsb')
        self.assertIs(m1, m2)


# ═══════════════════════════════════════════════════════════════════
# 2. Expander
# ═══════════════════════════════════════════════════════════════════

class ExpanderTest(unittest.TestCase):
    """Тесты expand_composition_group()."""

    def setUp(self):
        self.cg_pa_kit = CompositionGroup.objects.get(code='pa-kit', is_active=True)
        self.assemblies = []  # для cleanup

    def tearDown(self):
        for a in self.assemblies:
            try:
                a.delete()
            except Exception:
                pass

    def _make_assembly(self):
        a = AssemblyRequirements.objects.create(
            composition_group=self.cg_pa_kit, status='draft',
        )
        self.assemblies.append(a)
        return a

    def test_expand_pa_kit_creates_components(self):
        assembly = self._make_assembly()
        created = expand_composition_group(assembly)
        self.assertGreater(len(created), 0)
        self.assertEqual(assembly.components.count(), len(created))

    def test_expand_sets_equipment_type(self):
        assembly = self._make_assembly()
        expand_composition_group(assembly)
        for cr in assembly.components.all():
            self.assertTrue(
                cr.equipment_type is not None or cr.composition_group_node is not None,
                f"CR #{cr.id} p={cr.path} has no ET and no CG node",
            )

    def test_expand_creates_tree_structure(self):
        assembly = self._make_assembly()
        expand_composition_group(assembly)
        roots = assembly.components.filter(parent__isnull=True)
        self.assertGreater(roots.count(), 0)
        children = assembly.components.filter(parent__isnull=False)
        if children.exists():
            sample = children.first()
            self.assertIsNotNone(sample.parent)
            self.assertGreater(sample.level, sample.parent.level)

    def test_expand_replaces_existing_components(self):
        assembly = self._make_assembly()
        first = expand_composition_group(assembly)
        first_ids = {cr.id for cr in first}
        second = expand_composition_group(assembly)
        second_ids = {cr.id for cr in second}
        self.assertFalse(first_ids & second_ids)

    def test_expand_virtual_nodes(self):
        assembly = self._make_assembly()
        expand_composition_group(assembly)
        virtual = assembly.components.filter(equipment_type__isnull=True)
        if virtual.exists():
            vn = virtual.first()
            self.assertIsNotNone(vn.composition_group_node)


# ═══════════════════════════════════════════════════════════════════
# 3. Resolver
# ═══════════════════════════════════════════════════════════════════

class ResolverTest(unittest.TestCase):
    """Тесты resolve_effective_requirements."""

    def setUp(self):
        self.cg = CompositionGroup.objects.get(code='pa-kit', is_active=True)
        self.assembly = AssemblyRequirements.objects.create(
            composition_group=self.cg,
            global_requirements={'temp_min': -40, 'temp_max': 60, 'exd': 'Exd'},
            status='draft',
        )
        expand_composition_group(self.assembly)

    def tearDown(self):
        try:
            self.assembly.delete()
        except Exception:
            pass

    def test_resolve_without_rules(self):
        cr = self.assembly.components.filter(equipment_type__isnull=False).first()
        if not cr:
            self.skipTest("No component with equipment_type")
        cr.own_requirements = {'ip_id': 5, 'work_temp_min': -20}
        cr.save()
        result = resolve_effective_requirements(cr)
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

    def test_key_translation(self):
        et = EquipmentType.objects.get(code='lsb')
        cr = ComponentRequirement.objects.create(
            assembly=self.assembly, equipment_type=et,
            path='999', level=1, order=999,
            own_requirements={'ip_id': 5, 'sensor_variety_id': 1},
        )
        try:
            result = resolve_effective_requirements(cr)
            self.assertIsInstance(result, dict)
            # field_path translation works: ip_id → ip
            self.assertIn('ip', result)
            self.assertEqual(result['ip'], 5)
        finally:
            cr.delete()

    def test_cascade_params_added(self):
        et = EquipmentType.objects.get(code='lsb')
        cr = ComponentRequirement.objects.create(
            assembly=self.assembly, equipment_type=et,
            path='998', level=1, order=998,
            cascade_params={'connection_size': 'G1/4'},
        )
        try:
            result = resolve_effective_requirements(cr)
            self.assertIn('connection_size', result)
            self.assertEqual(result['connection_size'], 'G1/4')
        finally:
            cr.delete()

    def test_skip_no_equipment_type(self):
        cr = ComponentRequirement.objects.create(
            assembly=self.assembly, equipment_type=None,
            path='997', level=1, order=997,
        )
        try:
            result = resolve_effective_requirements(cr)
            self.assertEqual(result, {})
        finally:
            cr.delete()

    def test_resolve_all(self):
        self.assembly.global_requirements = {'temp_min': -60, 'pressure': 10}
        self.assembly.save()
        resolve_all_components(self.assembly)
        for cr in self.assembly.components.filter(equipment_type__isnull=False):
            self.assertIsNotNone(cr.effective_requirements,
                                 f"CR #{cr.id} should have effective_requirements")


# ═══════════════════════════════════════════════════════════════════
# 4. FilterEngine
# ═══════════════════════════════════════════════════════════════════

class FilterEngineTest(unittest.TestCase):
    """Тесты filter_by_requirements и select_product."""

    def setUp(self):
        self.lsb_et = EquipmentType.objects.get(code='lsb')
        self.cg = CompositionGroup.objects.get(code='pa-kit', is_active=True)
        self.assembly = AssemblyRequirements.objects.create(
            composition_group=self.cg, status='draft',
        )
        self.cr = ComponentRequirement.objects.create(
            assembly=self.assembly, equipment_type=self.lsb_et,
            path='1', level=1, order=1,
            own_requirements={'ip_id': 5, 'work_temp_min': -20},
        )

    def tearDown(self):
        try:
            self.assembly.delete()
        except Exception:
            pass

    def test_filter_returns_candidates(self):
        resolve_effective_requirements(self.cr)
        result = filter_by_requirements(self.cr)
        self.assertIn('candidates', result)
        self.assertIsInstance(result['candidates'], list)
        self.assertGreater(result['total'], 0, "Should find at least some LSB models")

    def test_filter_empty_effective(self):
        self.cr.effective_requirements = {}
        self.cr.save()
        result = filter_by_requirements(self.cr)
        self.assertEqual(result['total'], 0)

    def test_filter_stores_results(self):
        resolve_effective_requirements(self.cr)
        filter_by_requirements(self.cr)
        self.cr.refresh_from_db()
        self.assertIsNotNone(self.cr.filter_results)
        self.assertEqual(self.cr.status, 'filtered')

    def test_select_product(self):
        resolve_effective_requirements(self.cr)
        fr = filter_by_requirements(self.cr)
        if not fr['candidates']:
            self.skipTest("No candidates to select")
        first_id = fr['candidates'][0]['id']
        specs = select_product(self.cr, first_id)
        self.assertIsNotNone(specs)
        self.cr.refresh_from_db()
        self.assertEqual(self.cr.status, 'selected')
        self.assertEqual(self.cr.selected_product_id, first_id)

    def test_select_nonexistent(self):
        self.assertEqual(select_product(self.cr, 99999999), {})

    def test_candidates_have_required_fields(self):
        resolve_effective_requirements(self.cr)
        fr = filter_by_requirements(self.cr)
        for c in fr['candidates']:
            self.assertIn('id', c)
            self.assertIn('name', c)

    def test_multiple_hard_params(self):
        self.cr.own_requirements = {'ip_id': 5, 'sensor_variety_id': 1}
        self.cr.save()
        resolve_effective_requirements(self.cr)
        result = filter_by_requirements(self.cr)
        self.assertGreaterEqual(result['total'], 0)

    def test_relaxation(self):
        self.cr.own_requirements = {'ip_id': 5, 'work_temp_min': -500}
        self.cr.save()
        resolve_effective_requirements(self.cr)
        result = filter_by_requirements(self.cr)
        if result['relaxed']:
            self.assertGreater(result['total'], 0)
            self.assertIn('relaxation_detail', result)


# ═══════════════════════════════════════════════════════════════════
# 5. Cascade
# ═══════════════════════════════════════════════════════════════════

class CascadeTest(unittest.TestCase):
    """Тесты cascade_after_select."""

    def setUp(self):
        self.lsb_et = EquipmentType.objects.get(code='lsb')
        self.cg_et = EquipmentType.objects.get(code='cable-gland')
        self.cg = CompositionGroup.objects.get(code='pa-kit', is_active=True)
        self.assembly = AssemblyRequirements.objects.create(
            composition_group=self.cg, status='draft',
        )
        self._cleanup_rules = []

    def tearDown(self):
        for rule in self._cleanup_rules:
            try:
                rule.delete()
            except Exception:
                pass
        try:
            self.assembly.delete()
        except Exception:
            pass

    def _make_rule(self, **kwargs):
        rule = DerivationRule.objects.create(is_active=True, **kwargs)
        self._cleanup_rules.append(rule)
        return rule

    def test_no_selection_returns_empty(self):
        cr = ComponentRequirement.objects.create(
            assembly=self.assembly, equipment_type=self.lsb_et,
            path='1', level=1, order=1,
        )
        result = cascade_after_select(cr)
        self.assertEqual(result, {'derived_params': {}, 'fittings_created': 0})

    def test_no_rules_returns_empty(self):
        cr = ComponentRequirement.objects.create(
            assembly=self.assembly, equipment_type=self.lsb_et,
            path='1', level=1, order=1,
            selected_product_id=1,
            selected_product_specs={'name': 'Test'},
            selected_product_type='pa_controls.LimitSwitchBox',
        )
        result = cascade_after_select(cr)
        self.assertEqual(result['derived_params'], {})

    def test_derivation_rule_cascade(self):
        rule = self._make_rule(
            code='test-cascade-1',
            source_type=self.lsb_et,
            source_product_field='name',
            target_type=self.cg_et,
            target_param='thread_size',
        )
        parent = ComponentRequirement.objects.create(
            assembly=self.assembly, equipment_type=self.lsb_et,
            path='1', level=1, order=1,
            selected_product_id=1,
            selected_product_specs={'name': 'LSB-Test'},
            selected_product_type='pa_controls.LimitSwitchBox',
        )
        child = ComponentRequirement.objects.create(
            assembly=self.assembly, equipment_type=self.cg_et,
            parent=parent, path='1/1', level=2, order=2, status='pending',
        )
        result = cascade_after_select(parent)
        self.assertIn(child.id, result['derived_params'])
        child.refresh_from_db()
        self.assertEqual(child.cascade_params.get('thread_size'), 'LSB-Test')

    def test_condition_respected(self):
        self._make_rule(
            code='test-cascade-2',
            source_type=self.lsb_et,
            source_product_field='name',
            target_type=self.cg_et,
            target_param='thread_size',
            condition={'field': 'name', 'value': 'SPECIAL'},
        )
        parent = ComponentRequirement.objects.create(
            assembly=self.assembly, equipment_type=self.lsb_et,
            path='1', level=1, order=1,
            selected_product_id=1,
            selected_product_specs={'name': 'ORDINARY'},
            selected_product_type='pa_controls.LimitSwitchBox',
        )
        ComponentRequirement.objects.create(
            assembly=self.assembly, equipment_type=self.cg_et,
            parent=parent, path='1/1', level=2, order=2, status='pending',
        )
        result = cascade_after_select(parent)
        self.assertEqual(result['derived_params'], {})

    def test_transform_applied(self):
        self._make_rule(
            code='test-cascade-3',
            source_type=self.lsb_et,
            source_product_field='name',
            target_type=self.cg_et,
            target_param='thread_size',
            transform={'map': {'G1/4': '1/4'}},
        )
        parent = ComponentRequirement.objects.create(
            assembly=self.assembly, equipment_type=self.lsb_et,
            path='1', level=1, order=1,
            selected_product_id=1,
            selected_product_specs={'name': 'G1/4'},
            selected_product_type='pa_controls.LimitSwitchBox',
        )
        child = ComponentRequirement.objects.create(
            assembly=self.assembly, equipment_type=self.cg_et,
            parent=parent, path='1/1', level=2, order=2, status='pending',
        )
        cascade_after_select(parent)
        child.refresh_from_db()
        self.assertEqual(child.cascade_params.get('thread_size'), '1/4')
