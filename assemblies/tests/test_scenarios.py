"""Интеграционные сценарии (9 сюжетов из assy.md).

Покрывают полный жизненный цикл: draft → expand → fixate → fork → шаблон → MBOM.
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
    materialize_mbom,
    get_assembly_chain,
)
from configurator.services.expander import expand_composition_group


class ScenarioTest(unittest.TestCase):
    """End-to-end сценарии по assy.md."""

    def setUp(self):
        self.cg = CompositionGroup.objects.get(code="pa-kit", is_active=True)
        self.assemblies = []
        self.mboms = []

    def tearDown(self):
        for a in self.assemblies:
            try:
                a.delete()
            except Exception:
                pass
        for m in self.mboms:
            try:
                m.delete()
            except Exception:
                pass

    def _make(self):
        a = AssemblyRequirements.objects.create(composition_group=self.cg, status="draft")
        expand_composition_group(a)
        self.assemblies.append(a)
        return a

    # Сюжет 1: новый запрос → драфт-сборка с развёрнутым деревом
    def test_s1_create_draft(self):
        a = self._make()
        self.assertEqual(a.status, "draft")
        self.assertIsNone(a.revision)
        self.assertGreater(a.components.count(), 0)

    # Сюжет 6: закрепление (КП/счёт/в работу)
    def test_s6_fixate(self):
        a = self._make()
        a.components.update(status="selected")
        fixate(a)
        a.refresh_from_db()
        self.assertEqual(a.status, "fixed")
        self.assertEqual(a.revision, 1)
        self.assertIsNotNone(a.fixed_at)

    # Сюжет 7а: изменились требования → fork, parent_assembly=None
    def test_s7a_requirements_change(self):
        a = self._make()
        clone = fork_assembly(a, for_requirements_change=True)
        self.assemblies.append(clone)
        self.assertIsNone(clone.parent_assembly)
        self.assertEqual(clone.status, "draft")
        self.assertEqual(clone.components.count(), a.components.count())

    # Сюжет 7б: состав изменился, требования те же → fork, parent_assembly=source
    def test_s7b_composition_change(self):
        a = self._make()
        clone = fork_assembly(a, for_requirements_change=False)
        self.assemblies.append(clone)
        self.assertEqual(clone.parent_assembly_id, a.id)
        self.assertEqual(clone.requirement_version, a.requirement_version)

    # Сюжет 9: история состава (цепочка parent_assembly)
    def test_s9_history_chain(self):
        a1 = self._make()
        a2 = fork_assembly(a1, for_requirements_change=False)
        self.assemblies.append(a2)
        a3 = fork_assembly(a2, for_requirements_change=False)
        self.assemblies.append(a3)
        chain = get_assembly_chain(a3)
        ids = [x.id for x in chain]
        self.assertEqual(ids, [a3.id, a2.id, a1.id])

    # Сюжет 8: публикация типовой сборки + материализация MBOM
    def test_s8_template_and_mbom(self):
        a = self._make()
        a.components.update(status="selected")
        fixate(a)
        a.is_template = True
        a.save(update_fields=["is_template"])
        a.refresh_from_db()
        self.assertTrue(a.is_template)

        mbom = materialize_mbom(a)
        self.mboms.append(mbom)
        self.assertIsNotNone(mbom)
        self.assertGreater(mbom.items.count(), 0)

        # Идемпотентность: повторный вызов возвращает тот же MBOM
        mbom2 = materialize_mbom(a)
        self.assertEqual(mbom2.id, mbom.id)

    # Сюжет 4 (механизм): excluded-узел не попадает в MBOM
    def test_s4_excluded_component_skipped(self):
        a = self._make()
        first = a.components.order_by("order").first()
        first.included = False
        first.status = "skipped"
        first.save(update_fields=["included", "status"])

        a.components.filter(included=True).update(status="selected")
        fixate(a)
        mbom = materialize_mbom(a)
        self.mboms.append(mbom)

        included_count = a.components.filter(included=True).count()
        self.assertEqual(mbom.items.count(), included_count)
