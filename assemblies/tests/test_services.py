"""Тесты сервисов assemblies (fork/fixate/validator/resolution).

Запуск: python assemblies/tests/runtests.py [-v]
"""
import os
import sys
import unittest

if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, _PROJECT_ROOT)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoProject1.settings")
    import django
    django.setup()

from ai_assistant.models import CompositionGroup
from assemblies.models import AssemblyRequirements
from assemblies.services import (
    fork_assembly,
    fixate,
    validate_requirements,
    get_current_assembly,
    get_assembly_chain,
)
from configurator.services.expander import expand_composition_group


class ForkTest(unittest.TestCase):
    def setUp(self):
        self.cg = CompositionGroup.objects.get(code="pa-kit", is_active=True)
        self.assemblies = []

    def tearDown(self):
        for a in self.assemblies:
            try:
                a.delete()
            except Exception:
                pass

    def _make(self):
        a = AssemblyRequirements.objects.create(composition_group=self.cg, status="draft")
        expand_composition_group(a)
        self.assemblies.append(a)
        return a

    def test_fork_requirements_change(self):
        src = self._make()
        clone = fork_assembly(src, for_requirements_change=True, new_requirement_version=None)
        self.assemblies.append(clone)
        self.assertIsNone(clone.parent_assembly)
        self.assertIsNone(clone.requirement_version)
        self.assertEqual(clone.status, "draft")
        self.assertEqual(clone.components.count(), src.components.count())

    def test_fork_composition_change(self):
        src = self._make()
        clone = fork_assembly(src, for_requirements_change=False)
        self.assemblies.append(clone)
        self.assertEqual(clone.parent_assembly_id, src.id)
        self.assertEqual(clone.requirement_version, src.requirement_version)

    def test_fork_is_deep_copy(self):
        src = self._make()
        clone = fork_assembly(src, for_requirements_change=False)
        self.assemblies.append(clone)
        # Мутируем копию — оригинал не меняется
        clone.global_requirements = {"temperature_min": -100}
        clone.save(update_fields=["global_requirements"])
        first = clone.components.first()
        first.own_requirements = {"ip_id": 999}
        first.save(update_fields=["own_requirements"])

        src.refresh_from_db()
        self.assertEqual(src.global_requirements, {})
        src_first = src.components.order_by("order").first()
        self.assertEqual(src_first.own_requirements, {})

    def test_fork_repaires_parent_links(self):
        src = self._make()
        clone = fork_assembly(src, for_requirements_change=False)
        self.assemblies.append(clone)
        # Родительские ссылки должны указывать на клоны, а не на исходные компоненты
        for cr in clone.components.filter(parent__isnull=False):
            self.assertEqual(cr.parent.assembly_id, clone.id)


class FixateTest(unittest.TestCase):
    def setUp(self):
        self.cg = CompositionGroup.objects.get(code="pa-kit", is_active=True)
        self.assemblies = []

    def tearDown(self):
        for a in self.assemblies:
            try:
                a.delete()
            except Exception:
                pass

    def _make(self):
        a = AssemblyRequirements.objects.create(composition_group=self.cg, status="draft")
        expand_composition_group(a)
        self.assemblies.append(a)
        return a

    def test_fixate_ok(self):
        a = self._make()
        a.components.update(status="selected")
        fixate(a)
        a.refresh_from_db()
        self.assertEqual(a.status, "fixed")
        self.assertEqual(a.revision, 1)
        self.assertIsNotNone(a.fixed_at)

    def test_fixate_blocked_by_unresolved(self):
        a = self._make()  # компоненты pending
        with self.assertRaises(ValueError):
            fixate(a)

    def test_fixate_skipped_allowed(self):
        a = self._make()
        a.components.update(status="skipped")
        fixate(a)
        a.refresh_from_db()
        self.assertEqual(a.status, "fixed")

    def test_fixate_idempotent(self):
        a = self._make()
        a.components.update(status="selected")
        fixate(a)
        fixate(a)  # повторный вызов — no-op
        a.refresh_from_db()
        self.assertEqual(a.revision, 1)


class ValidatorTest(unittest.TestCase):
    def test_unknown_key(self):
        from core.models import EquipmentType
        et = EquipmentType.objects.get(code="lsb")
        result = validate_requirements(et, {"totally_unknown_param": 1})
        self.assertFalse(result["is_valid"])
        self.assertTrue(result["errors"])

    def test_empty_for_none_type(self):
        result = validate_requirements(None, {})
        self.assertFalse(result["is_valid"])


class ResolutionTest(unittest.TestCase):
    def test_get_assembly_chain_no_cycle(self):
        self.cg = CompositionGroup.objects.get(code="pa-kit", is_active=True)
        a1 = AssemblyRequirements.objects.create(composition_group=self.cg, status="draft")
        a2 = AssemblyRequirements.objects.create(
            composition_group=self.cg, status="draft", parent_assembly=a1,
        )
        chain = get_assembly_chain(a2)
        ids = [x.id for x in chain]
        self.assertEqual(ids[0], a2.id)
        self.assertEqual(ids[1], a1.id)
        a1.delete()
        a2.delete()
