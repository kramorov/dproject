"""Клиент для AI-провайдеров (DeepSeek, OpenAI, etc.).

Модель AIProvider хранит ключ, URL и маппинг моделей в БД.
get_deepseek_client() читает активного провайдера из БД.
"""
import json
import re
import time
import logging
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"


def _get_provider():
    """Возвращает активного AI провайдера из БД."""
    from ai_assistant.models import AIProvider
    return AIProvider.objects.filter(is_active=True).first()


def _parse_json(raw: str) -> Dict[str, Any]:
    """Парсит JSON из ответа LLM, обрабатывая markdown-обёртки."""
    if not raw:
        return {}
    text = raw.strip()
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_response": text}


def _dict_to_pydantic_model(name: str, schema: dict):
    """Создаёт Pydantic модель из JSON Schema dict для Instructor."""
    from pydantic import BaseModel, create_model
    from typing import Optional as Opt
    type_map = {"string": str, "integer": int, "number": float, "boolean": bool}
    fields = {}
    for key, prop in schema.get("properties", {}).items():
        py_type = type_map.get(prop.get("type", "string"), str)
        fields[key] = (Opt[py_type], None)
    return create_model(name, **fields)


class DeepSeekClient:
    """Обёртка над OpenAI-совместимым API. Ключ — из AIProvider в БД."""

    def __init__(self, provider=None):
        provider = provider or _get_provider()
        if not provider:
            raise RuntimeError("No active AI provider configured in DB")
        import openai
        self.provider = provider
        self.api_key = provider.api_key
        self.base_url = provider.base_url or DEFAULT_BASE_URL
        self.raw_client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _model_for(self, role: str) -> str:
        """Возвращает модель для роли: classification, extraction, debug."""
        mapping = self.provider.model_mapping or {}
        return mapping.get(role, "deepseek-chat")

    def classify(self, prompt: str, temperature: float = 0.3, max_tokens: int = 500) -> dict:
        """Классификация запроса."""
        return self._complete(prompt, self._model_for("classification"), temperature, max_tokens)

    def extract_filters(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> dict:
        """Извлечение фильтров."""
        return self._complete(prompt, self._model_for("extraction"), temperature, max_tokens)

    def debug(self, prompt: str, temperature: float = 0.7, max_tokens: int = 8000) -> dict:
        """Отладка промптов с reasoning."""
        return self._complete(prompt, self._model_for("debug"), temperature, max_tokens)

    def structured_completion(self, prompt: str, response_schema=None, temperature=0.7, max_tokens=2000):
        """Структурированный вызов с Instructor."""
        model = self._model_for("extraction")
        messages = [
            {"role": "system", "content": "Ты полезный ассистент. Отвечай строго в формате JSON."},
            {"role": "user", "content": prompt},
        ]
        try:
            if response_schema:
                return self._run_instructor(model, messages, response_schema, temperature, max_tokens)
            return self._complete(prompt, model, temperature, max_tokens)
        except Exception as e:
            logger.error(f"API error: {e}")
            return {"error": str(e)}

    def _complete(self, prompt, model, temperature, max_tokens):
        messages = [{"role": "user", "content": prompt}]
        start = time.monotonic()
        try:
            resp = self.raw_client.chat.completions.create(
                model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return {"error": str(e)}
        msg = resp.choices[0].message
        usage = resp.usage
        raw = msg.content or ""
        return {
            "content": _parse_json(raw),
            "raw_text": raw,
            "reasoning": getattr(msg, "reasoning_content", None),
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "reasoning_tokens": getattr(usage, "reasoning_tokens", None) if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
            "model": resp.model,
            "latency_ms": int((time.monotonic() - start) * 1000),
        }

    def _run_instructor(self, model, messages, schema, temperature, max_tokens):
        import instructor
        pydantic_model = _dict_to_pydantic_model("ResponseModel", schema)
        client = instructor.from_openai(self.raw_client)
        resp = client.chat.completions.create(
            model=model, messages=messages, response_model=pydantic_model,
            temperature=temperature, max_tokens=max_tokens)
        if hasattr(resp, "model_dump"):
            return resp.model_dump()
        if hasattr(resp, "dict"):
            return resp.dict()
        return resp

    def completion_with_reasoning(self, prompt, model=None, temperature=0.7, max_tokens=4000):
        model = model or self._model_for("extraction")
        return self._complete(prompt, model, temperature, max_tokens)


_client = None


def get_deepseek_client() -> DeepSeekClient:
    global _client
    if _client is None:
        _client = DeepSeekClient()
    return _client
