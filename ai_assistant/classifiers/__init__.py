"""
Классификатор запросов на основе DeepSeek API.

Один промпт → completion_with_reasoning → _parse_json → ClassificationResult.
Instructor используется на уровне deepseek_client для response_schema (опционально).
"""
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

INTENTS = [
    "actuator_selection",
    "price_check",
    "replacement",
    "specs",
    "general",
]

CLASSIFIER_PROMPT_TEMPLATE = """Классифицируй запрос пользователя о промышленной трубопроводной арматуре.

Интенты:
- actuator_selection: подбор пневмопривода, запрос на подбор привода по параметрам арматуры
  (момент, диаметр, давление, тип DA/SR, температура и т.д.)
- price_check: запрос цены, стоимости
- replacement: подбор аналога, замена существующей модели
- specs: технические характеристики, размеры, вес, материалы
- general: всё остальное (приветствие, общий вопрос)

Верни JSON:
{{
    "intent": "<один из intent>",
    "confidence": 0.0-1.0,
    "entities": {{}}
}}

Запрос пользователя:
{user_text}"""


@dataclass
class ClassificationResult:
    """Результат классификации запроса пользователя.

    Attributes:
        intent: Определённый интент (actuator_selection, price_check, replacement, specs, general).
        confidence: Уверенность классификатора (0.0–1.0).
        entities: Извлечённые сущности запроса (опционально).
        _usage: Служебная информация об использовании токенов (не отображается в repr).
    """
    intent: str
    confidence: float
    entities: Optional[dict] = None
    _usage: Optional[Dict[str, Any]] = field(default=None, repr=False)


class InstructorClassifier:
    """Классификатор на базе Instructor + DeepSeek."""

    def __init__(self, deepseek_client):
        """Инициализирует классификатор с переданным экземпляром DeepSeekClient.

        Args:
            deepseek_client: Экземпляр DeepSeekClient для вызовов API.
        """
        self.client = deepseek_client

    def classify(self, text: str) -> ClassificationResult:
        """Классифицирует текст, возвращает intent, confidence, entities и usage."""
        prompt = CLASSIFIER_PROMPT_TEMPLATE.format(user_text=text)
        result = self.client.classify(prompt)

        content = result.get("content", {})
        if isinstance(content, dict):
            intent = content.get("intent", "general")
            confidence = content.get("confidence", 0.0)
            entities = content.get("entities", {})
        else:
            intent = "general"
            confidence = 0.0
            entities = {}

        return ClassificationResult(
            intent=intent,
            confidence=confidence,
            entities=entities,
            _usage={
                "model": result.get("model", "unknown"),
                "prompt_tokens": result.get("prompt_tokens", 0),
                "completion_tokens": result.get("completion_tokens", 0),
                "reasoning_tokens": result.get("reasoning_tokens"),
                "total_tokens": result.get("total_tokens", 0),
            },
        )
