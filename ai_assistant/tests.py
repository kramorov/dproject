"""
Тесты для ai_assistant.

Покрывают: модели, _parse_json, классификатор, оркестратор (mock DeepSeek), API.
"""
import json
import uuid
from django.test import TestCase, Client as TestClient
from django.urls import reverse

from ai_assistant.models import (
    AIConversation, AIMessage, AITokenUsage,
    AIClientProvider, AIQuerySample, AIPromptTemplate,
)
from ai_assistant.services.deepseek_client import _parse_json, get_deepseek_client
from ai_assistant.schemas import get_schema_config, SCHEMA_REGISTRY
from ai_assistant.classifiers import InstructorClassifier, ClassificationResult


# ── _parse_json ──────────────────────────────────────────────────────
class ParseJsonTests(TestCase):
    def test_plain_json(self):
        self.assertEqual(_parse_json('{"a": 1}'), {"a": 1})

    def test_markdown_json_block(self):
        raw = '```json\n{"intent": "general"}\n```'
        self.assertEqual(_parse_json(raw), {"intent": "general"})

    def test_markdown_no_lang(self):
        raw = '```\n{"x": 42}\n```'
        self.assertEqual(_parse_json(raw), {"x": 42})

    def test_invalid_json(self):
        raw = "not json at all"
        self.assertEqual(_parse_json(raw), {"raw_response": "not json at all"})

    def test_empty_string(self):
        self.assertEqual(_parse_json(""), {})
        self.assertEqual(_parse_json(None), {})

    def test_markdown_with_surrounding_text(self):
        raw = 'Sure! Here is the JSON:\n```json\n{"intent": "actuator_selection"}\n```\nHope that helps!'
        self.assertEqual(_parse_json(raw), {"intent": "actuator_selection"})


# ── Модели ───────────────────────────────────────────────────────────
class ModelTests(TestCase):
    def test_create_conversation(self):
        conv = AIConversation.objects.create(session_key="test-1")
        self.assertEqual(conv.status, "incoming")
        self.assertIsNotNone(conv.created_at)

    def test_create_message_with_parent(self):
        conv = AIConversation.objects.create(session_key="test-2")
        parent = AIMessage.objects.create(conversation=conv, role="user", content="hello")
        child = AIMessage.objects.create(conversation=conv, role="classifier", content="",
                                         parent=parent, intent="general", confidence=0.95)
        self.assertEqual(child.parent, parent)

    def test_token_usage(self):
        conv = AIConversation.objects.create()
        msg = AIMessage.objects.create(conversation=conv, role="orchestrator", content="ok")
        AITokenUsage.objects.create(message=msg, model="test", prompt_tokens=10,
                                    completion_tokens=5, total_tokens=15)
        self.assertTrue(hasattr(msg, "token_usage"))

    def test_query_sample_crud(self):
        sample = AIQuerySample.objects.create(text="подбери привод", category="actuator_selection")
        self.assertEqual(sample.category, "actuator_selection")
        qs = AIQuerySample.objects.filter(category="actuator_selection")
        self.assertEqual(qs.count(), 1)

    def test_prompt_template_unique_together(self):
        AIPromptTemplate.objects.create(name="t1", version="1", template_text="...")
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            AIPromptTemplate.objects.create(name="t1", version="1", template_text="...")

    def test_client_provider(self):
        # без customer — проверим что модель создаётся без обязательных FK проверок на уровне Python
        provider = AIClientProvider(provider_type="deepseek", api_url="https://api.x.com", api_key="k")
        self.assertEqual(provider.provider_type, "deepseek")


# ── Схемы ────────────────────────────────────────────────────────────
class SchemaTests(TestCase):
    def test_registry_has_actuator_selection(self):
        self.assertIn("actuator_selection", SCHEMA_REGISTRY)

    def test_get_schema_config_valid(self):
        config = get_schema_config("actuator_selection")
        self.assertIn("schema", config)
        self.assertIn("prompt_template", config)

    def test_get_schema_config_invalid(self):
        config = get_schema_config("nonexistent")
        self.assertEqual(config, {})


# ── Классификатор ───────────────────────────────────────────────────
class ClassifierTests(TestCase):
    def test_classification_result_dataclass(self):
        r = ClassificationResult(intent="general", confidence=0.9, entities={"a": 1})
        self.assertEqual(r.intent, "general")

    def test_classifier_has_required_fields(self):
        self.assertIn("actuator_selection", InstructorClassifier.INTENTS if hasattr(InstructorClassifier, 'INTENTS')
                      else __import__('ai_assistant.classifiers', fromlist=['INTENTS']).INTENTS)


# ── DeepSeek Client (settings) ──────────────────────────────────────
class ClientSettingsTests(TestCase):
    def test_api_key_in_settings(self):
        from django.conf import settings
        self.assertTrue(hasattr(settings, "AI_ASSISTANT_DEEPSEEK_API_KEY"))

    def test_base_url_in_settings(self):
        from django.conf import settings
        self.assertTrue(hasattr(settings, "AI_ASSISTANT_DEEPSEEK_BASE_URL"))

    def test_get_deepseek_client_uses_settings(self):
        client = get_deepseek_client(api_key="test-key")
        self.assertEqual(client.api_key, "test-key")
        self.assertIsNotNone(client.model)


# ── API (mocked) ────────────────────────────────────────────────────
class APITests(TestCase):
    def setUp(self):
        self.c = TestClient()

    def test_post_empty_text(self):
        resp = self.c.post(reverse("ai-query"), {}, content_type="application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.json())

    def test_post_basic_query(self):
        """Вызывает реальный оркестратор — вернёт fallback (без API-ключа)."""
        with self.settings(AI_ASSISTANT_DEEPSEEK_API_KEY=""):
            resp = self.c.post(reverse("ai-query"),
                               {"text": "подбери привод"},
                               content_type="application/json")
            data = resp.json()
            self.assertIn("conversation_id", data)
            self.assertIn("intent", data)


# ── URLs ────────────────────────────────────────────────────────────
class URLTests(TestCase):
    def test_query_url_exists(self):
        url = reverse("ai-query")
        self.assertIsNotNone(url)

    def test_sample_list_url(self):
        url = reverse("ai-sample-list")
        self.assertIsNotNone(url)
