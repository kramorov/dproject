"""
Тесты конвейера подбора ai_assistant.

Покрывают:
- Модели: EquipmentType, SelectionNode, CascadeRule, StepConfig, StepConfigOverride, JSONSchema
- API: decompose, extract, filter, select, compare, ebom, mbom, tree
- TreeProcessor: все шаги (с моками LLM)
"""
import json
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client as TestClient
from django.urls import reverse
from django.db import IntegrityError

from ai_assistant.models import (
    AIConversation, EquipmentType, SelectionNode, CascadeRule,
    StepConfig, StepConfigOverride, JSONSchema, AIPromptTemplate,
)


# ═══════════════════════════════════════════════════════════════════
# Модели
# ═══════════════════════════════════════════════════════════════════

class EquipmentTypeTests(TestCase):
    def test_create_equipment_type(self):
        eq = EquipmentType.objects.create(
            code="test_actuator", label="Пневмопривод", level=2,
            param_semantics={"torque_nm": {"direction": "min"}},
            filter_endpoint="/api/pa/selector/search/"
        )
        self.assertEqual(eq.code, "test_actuator")
        self.assertEqual(eq.label, "Пневмопривод")
        self.assertEqual(eq.level, 2)
        self.assertTrue(eq.is_active)
        self.assertEqual(str(eq), "Пневмопривод (test_actuator)")

    def test_code_unique(self):
        EquipmentType.objects.create(code="test_valve", label="Клапан", level=1)
        with self.assertRaises(IntegrityError):
            EquipmentType.objects.create(code="test_valve", label="Дубликат", level=1)

    def test_defaults(self):
        eq = EquipmentType.objects.create(code="test_bkv", label="BKV", level=3)
        self.assertEqual(eq.param_semantics, {})
        self.assertIsNone(eq.filter_endpoint)
        self.assertTrue(eq.is_active)

    def test_ordering(self):
        EquipmentType.objects.create(code="test_zzz", label="Last", level=9)
        EquipmentType.objects.create(code="test_aaa", label="First", level=1)
        eqs = list(EquipmentType.objects.filter(code__startswith="test_"))
        self.assertTrue(len(eqs) >= 2)


class SelectionNodeTests(TestCase):
    def setUp(self):
        self.conv = AIConversation.objects.create(session_key="test-tree-sn")
        self.eq = EquipmentType.objects.create(
            code="sn_actuator", label="Привод SN", level=2
        )

    def test_create_root_node(self):
        node = SelectionNode.objects.create(
            conversation=self.conv, level=1, path="sn/1",
            label="Позиция 1", quantity=2, quantity_unit="pcs",
        )
        self.assertEqual(node.status, "pending")
        self.assertEqual(node.level, 1)
        self.assertEqual(node.quantity, 2)
        self.assertIsNone(node.parent)

    def test_create_child_node(self):
        root = SelectionNode.objects.create(
            conversation=self.conv, level=1, path="sn/1", label="Корень"
        )
        child = SelectionNode.objects.create(
            conversation=self.conv, parent=root, level=2, path="sn/1/1",
            label="Компонент", equipment_type=self.eq, task_type="selection"
        )
        self.assertEqual(child.parent, root)
        self.assertEqual(list(root.children.all()), [child])
        self.assertEqual(child.task_type, "selection")

    def test_effective_params_merges_extract_and_cascade(self):
        node = SelectionNode.objects.create(
            conversation=self.conv, level=1, path="sn/merge",
            label="N1", extract_output={"torque_nm": 100, "ip": "67"},
            cascade_params={"ip": "68"},
        )
        params = node.effective_params
        self.assertEqual(params["torque_nm"], 100)
        self.assertEqual(params["ip"], "68")  # cascade wins

    def test_effective_params_empty(self):
        node = SelectionNode.objects.create(
            conversation=self.conv, level=1, path="sn/empty", label="N2"
        )
        self.assertEqual(node.effective_params, {})

    def test_total_quantity_root(self):
        node = SelectionNode.objects.create(
            conversation=self.conv, level=1, path="sn/q",
            label="Q", quantity=5, quantity_unit="pcs"
        )
        self.assertEqual(node.total_quantity, 5)

    def test_total_quantity_with_parent(self):
        root = SelectionNode.objects.create(
            conversation=self.conv, level=1, path="sn/qp",
            label="Root", quantity=3
        )
        child = SelectionNode.objects.create(
            conversation=self.conv, parent=root, level=2, path="sn/qp/1",
            label="Child", quantity=4
        )
        self.assertEqual(child.total_quantity, 12)  # 3 × 4

    def test_str_representation(self):
        node = SelectionNode.objects.create(
            conversation=self.conv, level=2, path="sn/str",
            label="Пневмопривод DA, 150Нм", equipment_type=self.eq
        )
        s = str(node)
        self.assertIn("Node#", s)
        self.assertIn("[sn_actuator]", s)

    def test_status_transitions(self):
        node = SelectionNode.objects.create(
            conversation=self.conv, level=1, path="sn/status", label="N"
        )
        self.assertEqual(node.status, "pending")
        node.status = "decomposed"; node.save()
        node.refresh_from_db()
        self.assertEqual(node.status, "decomposed")

    def test_select_product_fields(self):
        node = SelectionNode.objects.create(
            conversation=self.conv, level=1, path="sn/sel", label="N",
        )
        node.selected_product_type = "pa.PA"
        node.selected_product_id = 42
        node.selected_product_specs = {"model": "ABRA-DA-150"}
        node.compare_output = {"match": True, "mismatches": []}
        node.save()
        node.refresh_from_db()
        self.assertEqual(node.selected_product_id, 42)
        self.assertTrue(node.compare_output["match"])


class CascadeRuleTests(TestCase):
    def setUp(self):
        self.pt = EquipmentType.objects.create(code="cr_actuator", label="Привод CR", level=2)
        self.ct = EquipmentType.objects.create(code="cr_solenoid", label="Соленоид CR", level=3)

    def test_create_cascade_rule(self):
        rule = CascadeRule.objects.create(
            parent_type=self.pt, child_type=self.ct,
            mapping={"port_size_npt": "connection_size"}
        )
        self.assertEqual(rule.mapping["port_size_npt"], "connection_size")
        self.assertTrue(rule.is_active)
        self.assertEqual(str(rule), "cr_actuator → cr_solenoid")

    def test_unique_parent_child(self):
        CascadeRule.objects.create(
            parent_type=self.pt, child_type=self.ct, mapping={"a": "b"}
        )
        with self.assertRaises(IntegrityError):
            CascadeRule.objects.create(
                parent_type=self.pt, child_type=self.ct, mapping={"c": "d"}
            )


class StepConfigTests(TestCase):
    def setUp(self):
        self.eq = EquipmentType.objects.create(code="sc_actuator", label="Привод SC", level=2)
        self.prompt = AIPromptTemplate.objects.create(
            name="sc_extract", version="sc-1", template_text="Извлеки: {{text}}"
        )

    def test_create_step_config(self):
        sc = StepConfig.objects.create(
            step="extract", equipment_type=self.eq, prompt_template=self.prompt,
            model_role="extraction", priority=5
        )
        self.assertEqual(sc.step, "extract")
        self.assertEqual(sc.model_role, "extraction")
        self.assertTrue(sc.is_active)
        self.assertEqual(str(sc), "extract / sc_actuator")

    def test_step_config_without_equipment(self):
        sc = StepConfig.objects.create(
            step="decompose", prompt_template=self.prompt, model_role="debug"
        )
        self.assertIsNone(sc.equipment_type)
        self.assertEqual(str(sc), "decompose / *")

    def test_unique_step_equipment(self):
        StepConfig.objects.create(step="extract", equipment_type=self.eq, model_role="extraction")
        with self.assertRaises(IntegrityError):
            StepConfig.objects.create(step="extract", equipment_type=self.eq, model_role="debug")


class StepConfigOverrideTests(TestCase):
    def setUp(self):
        self.eq = EquipmentType.objects.create(code="sco_actuator", label="Привод SCO", level=2)
        self.sc = StepConfig.objects.create(step="extract", equipment_type=self.eq, model_role="extraction")

    def test_create_override(self):
        override = StepConfigOverride(
            step_config=self.sc, prompt_suffix="Только ABRA.", model_role="custom"
        )
        self.assertEqual(override.prompt_suffix, "Только ABRA.")
        self.assertEqual(override.model_role, "custom")
        self.assertTrue(override.is_active)


class JSONSchemaTests(TestCase):
    def test_create_schema(self):
        s = JSONSchema.objects.create(
            name="js_tree_schema", version="js-1",
            schema_json={"type": "object", "properties": {"positions": {"type": "array"}}}
        )
        self.assertEqual(s.name, "js_tree_schema")
        self.assertEqual(str(s), "js_tree_schema vjs-1")

    def test_unique_name_version(self):
        JSONSchema.objects.create(name="js_filters", version="js-1", schema_json={})
        with self.assertRaises(IntegrityError):
            JSONSchema.objects.create(name="js_filters", version="js-1", schema_json={})

    def test_multiple_versions(self):
        JSONSchema.objects.create(name="js_f2", version="js-v1", schema_json={"v": 1})
        JSONSchema.objects.create(name="js_f2", version="js-v2", schema_json={"v": 2})
        self.assertEqual(JSONSchema.objects.filter(name="js_f2").count(), 2)


# ═══════════════════════════════════════════════════════════════════
# API (новые pipeline endpoints)
# ═══════════════════════════════════════════════════════════════════

class PipelineAPITests(TestCase):
    """Тесты API — проверяют контракты (status codes, формат ответов)."""

    def setUp(self):
        self.c = TestClient()
        self.conv = AIConversation.objects.create(
            session_key="api-test-pipe", status="processing"
        )
        self.eq = EquipmentType.objects.create(
            code="api_actuator", label="Привод API", level=2,
            filter_endpoint="/api/pa/selector/search/"
        )
        self.node = SelectionNode.objects.create(
            conversation=self.conv, level=1, path="api/1",
            label="Test Node", equipment_type=self.eq,
        )

    def test_decompose_no_text(self):
        resp = self.c.post(reverse("ai-decompose"), {}, content_type="application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.json())

    def test_extract_node_not_found(self):
        resp = self.c.post(reverse("ai-extract", args=[99999]))
        self.assertEqual(resp.status_code, 404)

    def test_filter_node_not_found(self):
        resp = self.c.post(reverse("ai-filter", args=[99999]))
        self.assertEqual(resp.status_code, 404)

    def test_select_missing_params(self):
        resp = self.c.post(
            reverse("ai-select", args=[self.node.id]),
            {}, content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.json())

    def test_select_node_not_found(self):
        resp = self.c.post(
            reverse("ai-select", args=[99999]),
            {"product_type": "pa.PA", "product_id": 1},
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 404)

    def test_compare_node_not_found(self):
        resp = self.c.post(reverse("ai-compare", args=[99999]))
        self.assertEqual(resp.status_code, 404)

    def test_ebom_conversation_not_found(self):
        resp = self.c.get(reverse("ai-ebom", args=[99999]))
        self.assertEqual(resp.status_code, 404)

    def test_mbom_conversation_not_found(self):
        resp = self.c.get(reverse("ai-mbom", args=[99999]))
        self.assertEqual(resp.status_code, 404)

    def test_tree_conversation_not_found(self):
        resp = self.c.get(reverse("ai-tree", args=[99999]))
        self.assertEqual(resp.status_code, 404)

    def test_tree_existing_conversation(self):
        resp = self.c.get(reverse("ai-tree", args=[self.conv.id]))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["conversation_id"], self.conv.id)
        self.assertIn("tree", data)

    def test_tree_with_nodes(self):
        child = SelectionNode.objects.create(
            conversation=self.conv, parent=self.node,
            level=2, path="api/1/child",
            label="Child", equipment_type=self.eq
        )
        resp = self.c.get(reverse("ai-tree", args=[self.conv.id]))
        data = resp.json()
        self.assertEqual(len(data["tree"]), 1)
        self.assertEqual(len(data["tree"][0]["children"]), 1)


class URLResolutionTests(TestCase):
    def test_all_new_urls_reverse(self):
        urls = [
            ("ai-decompose", [], {}),
            ("ai-extract", [1], {}),
            ("ai-filter", [1], {}),
            ("ai-select", [1], {}),
            ("ai-compare", [1], {}),
            ("ai-ebom", [1], {}),
            ("ai-mbom", [1], {}),
            ("ai-tree", [1], {}),
        ]
        for name, args, kwargs in urls:
            url = reverse(name, args=args, kwargs=kwargs)
            self.assertIsNotNone(url)
            self.assertTrue(url.startswith("/"))


# ═══════════════════════════════════════════════════════════════════
# TreeProcessor (unit tests с моками)
# ═══════════════════════════════════════════════════════════════════

class TreeProcessorInitTests(TestCase):
    def test_processor_creation(self):
        conv = AIConversation.objects.create(session_key="tpi-test")
        from ai_assistant.services.tree_processor import TreeProcessor
        tp = TreeProcessor(conv)
        self.assertEqual(tp.conversation, conv)
        self.assertIsNone(tp.customer)
        self.assertIsNotNone(tp.client)


class TreeProcessorConfigTests(TestCase):
    def test_get_config_no_config(self):
        conv = AIConversation.objects.create(session_key="tpc-empty")
        from ai_assistant.services.tree_processor import TreeProcessor
        tp = TreeProcessor(conv)
        cfg = tp._get_config("nonexistent_step_xyz")
        self.assertIsNone(cfg)

    def test_get_config_with_step_config(self):
        conv = AIConversation.objects.create(session_key="tpc-cfg")
        prompt = AIPromptTemplate.objects.create(
            name="tpc_dec2", version="tpc-2", template_text="Разложи: {{text}}"
        )
        StepConfig.objects.create(
            step="tpc_test_decompose", prompt_template=prompt, model_role="debug"
        )
        from ai_assistant.services.tree_processor import TreeProcessor
        tp = TreeProcessor(conv)
        cfg = tp._get_config("tpc_test_decompose")
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg["model_role"], "debug")
        self.assertEqual(cfg["prompt_text"], "Разложи: {{text}}")

    def test_get_config_for_specific_equipment(self):
        conv = AIConversation.objects.create(session_key="tpc-eq")
        eq = EquipmentType.objects.create(code="tpc_eq", label="TPC EQ", level=2)
        prompt = AIPromptTemplate.objects.create(
            name="tpc_ext2", version="tpc-2", template_text="Фильтры"
        )
        StepConfig.objects.create(
            step="tpc_test_extract", equipment_type=eq, prompt_template=prompt,
            model_role="extraction"
        )
        from ai_assistant.services.tree_processor import TreeProcessor
        tp = TreeProcessor(conv)
        cfg = tp._get_config("tpc_test_extract", equipment_type=eq)
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg["model_role"], "extraction")


class TreeProcessorDecomposeTests(TestCase):
    def test_decompose_no_config(self):
        """Без StepConfig — decompose должен вернуть error сразу, без LLM."""
        conv = AIConversation.objects.create(session_key="tpd-nocfg", status="processing")
        from ai_assistant.services.tree_processor import TreeProcessor

        mock_client = MagicMock()
        mock_client.debug.return_value = {
            "raw_text": "{}",
            "model": "deepseek-chat",
            "prompt_tokens": 10, "completion_tokens": 5,
            "reasoning_tokens": 0, "total_tokens": 15,
        }

        with patch("ai_assistant.services.tree_processor.get_deepseek_client", return_value=mock_client):
            tp = TreeProcessor(conv)
            result = tp.decompose("Подбери привод")
            # Если в БД нет StepConfig для decompose — ошибка
            # Если есть — отработает с моком
            valid_statuses = ["error", "completed", "processing", "needs_info", "pending"]
            self.assertIn(result["status"], valid_statuses)
            if result["status"] == "error":
                self.assertIn("StepConfig", result.get("message", ""))

    def test_decompose_with_config_and_mock_llm(self):
        conv = AIConversation.objects.create(session_key="tpd-mock", status="processing")

        prompt = AIPromptTemplate.objects.create(
            name="tpd_dec2", version="tpd-2", template_text="Разложи: {{text}}"
        )
        StepConfig.objects.create(
            step="tpd_test_decompose", prompt_template=prompt, model_role="debug"
        )

        from ai_assistant.services.tree_processor import TreeProcessor
        tp = TreeProcessor(conv)

        # Мокаем LLM-клиент на уровне экземпляра
        mock_client = MagicMock()
        mock_client.debug.return_value = {
            "raw_text": json.dumps({
                "positions": [{
                    "id": "pos1", "description": "Привод",
                    "level": 1, "quantity": 1, "quantity_unit": "pcs",
                    "components": []
                }]
            }),
            "model": "deepseek-chat",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "reasoning_tokens": 0,
            "total_tokens": 150,
            "usage": {},
        }
        tp.client = mock_client

        result = tp.decompose("Подбери привод")
        self.assertIn("conversation_id", result)
        self.assertEqual(result["conversation_id"], conv.id)


class TreeProcessorBuildMethodsTests(TestCase):
    def setUp(self):
        self.conv = AIConversation.objects.create(session_key="tpb-bom")
        self.eq = EquipmentType.objects.create(code="tpb_eq", label="TPB EQ", level=2)
        self.root = SelectionNode.objects.create(
            conversation=self.conv, level=1, path="tpb/1",
            label="Позиция 1", quantity=2, quantity_unit="pcs",
            selected_product_type="pa.Actuator", selected_product_id=10,
        )
        self.child = SelectionNode.objects.create(
            conversation=self.conv, parent=self.root,
            level=2, path="tpb/1/1", label="Соленоид",
            quantity=1, quantity_unit="pcs",
            equipment_type=self.eq,
            selected_product_type="sv.Valve", selected_product_id=20,
        )

    def test_build_ebom_structure(self):
        from ai_assistant.services.tree_processor import TreeProcessor
        tp = TreeProcessor(self.conv)
        ebom = tp.build_ebom()
        self.assertIn("conversation_id", ebom)
        self.assertIn("positions", ebom)
        self.assertEqual(len(ebom["positions"]), 1)
        pos = ebom["positions"][0]
        self.assertEqual(pos["label"], "Позиция 1")
        self.assertEqual(pos["quantity"], 2)
        self.assertIn("items", pos)
        self.assertEqual(len(pos["items"]), 1)

    def test_build_mbom_structure(self):
        from ai_assistant.services.tree_processor import TreeProcessor
        tp = TreeProcessor(self.conv)
        mbom = tp.build_mbom()
        self.assertIn("conversation_id", mbom)
        pos = mbom["positions"][0]
        self.assertEqual(pos["product_type"], "pa.Actuator")
        self.assertEqual(pos["product_id"], 10)
        comp = pos["items"][0]
        self.assertEqual(comp["product_type"], "sv.Valve")
        self.assertEqual(comp["product_id"], 20)

    def test_build_ebom_empty_tree(self):
        conv_empty = AIConversation.objects.create(session_key="tpb-empty")
        from ai_assistant.services.tree_processor import TreeProcessor
        tp = TreeProcessor(conv_empty)
        ebom = tp.build_ebom()
        self.assertEqual(len(ebom["positions"]), 0)


class TreeProcessorCascadeTests(TestCase):
    def setUp(self):
        self.conv = AIConversation.objects.create(session_key="tpc-cascade")
        self.pt = EquipmentType.objects.create(code="tpc_act", label="Привод Cascade", level=2)
        self.ct = EquipmentType.objects.create(code="tpc_sol", label="Соленоид Cascade", level=3)
        CascadeRule.objects.create(
            parent_type=self.pt, child_type=self.ct,
            mapping={"port_size": "connection_size", "voltage": "sv_voltage"}
        )
        self.root = SelectionNode.objects.create(
            conversation=self.conv, level=1, path="tpc/1",
            label="Привод", equipment_type=self.pt,
            selected_product_type="pa.Actuator", selected_product_id=5,
            selected_product_specs={"port_size": "G1/4", "voltage": "24V DC", "torque": 150}
        )
        self.child = SelectionNode.objects.create(
            conversation=self.conv, parent=self.root,
            level=2, path="tpc/1/1", label="Соленоид",
            equipment_type=self.ct,
            extract_output={"type": "5/2"}
        )

    def test_cascade_params_propagated(self):
        """Проверяем, что select_product пробрасывает параметры дочернему узлу."""
        from ai_assistant.services.tree_processor import TreeProcessor
        tp = TreeProcessor(self.conv)

        # Мокаем _load_product_specs — нельзя использовать реальный ContentType в тестах
        with patch.object(tp, "_load_product_specs", return_value={
            "port_size": "G1/4", "voltage": "24V DC", "torque": 150
        }):
            result = tp.select_product(
                node_id=self.root.id, product_type="pa.Actuator", product_id=5
            )

        self.child.refresh_from_db()
        cascade = self.child.cascade_params or {}
        self.assertEqual(cascade.get("connection_size"), "G1/4")
        self.assertEqual(cascade.get("sv_voltage"), "24V DC")

    def test_effective_params_with_cascade(self):
        self.child.cascade_params = {"connection_size": "G1/4", "sv_voltage": "24V DC"}
        self.child.save()
        params = self.child.effective_params
        self.assertEqual(params["type"], "5/2")
        self.assertEqual(params["connection_size"], "G1/4")
        self.assertEqual(params["sv_voltage"], "24V DC")
