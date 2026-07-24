"""Реестр схем и промптов. DB-first: AIPromptTemplate → SCHEMA_REGISTRY (code fallback)."""
import logging
from typing import Dict, Any, Optional

from .actuator_selection import ACTUATOR_SELECTION_SCHEMA, ACTUATOR_SELECTION_PROMPT_TEMPLATE
from .decompose import (  # V1 — для обратной совместимости
    DECOMPOSE_SCHEMA, DECOMPOSE_PROMPT_TEMPLATE,
    SYSTEM_PROMPT_ABRA, SYSTEM_PROMPT_DEFAULT,
)

logger = logging.getLogger(__name__)

SCHEMA_REGISTRY = {
    "actuator_selection": {
        "schema": ACTUATOR_SELECTION_SCHEMA,
        "prompt_template": ACTUATOR_SELECTION_PROMPT_TEMPLATE,
    },
    "decompose": {
        "schema": None,  # decompose V2 — текстовый, без JSON-схемы
        "prompt_template": DECOMPOSE_PROMPT_TEMPLATE,
    },
}

SYSTEM_PROMPTS = {
    "abra": SYSTEM_PROMPT_ABRA,
    "default": SYSTEM_PROMPT_DEFAULT,
}


def get_schema_config(intent: str, use_db: bool = True) -> Dict[str, Any]:
    """Возвращает {schema, prompt_template} для intent. DB-first, code fallback."""
    if use_db:
        db_config = _load_from_db(intent)
        if db_config:
            return db_config
    return SCHEMA_REGISTRY.get(intent, {})


def get_system_prompt(tenant: str = "default") -> str:
    """Системный промпт для tenant. DB → code → default."""
    try:
        from ..models import AIPromptTemplate
        tmpl = (
            AIPromptTemplate.objects
            .filter(name="system_prompt", version=tenant, is_active=True)
            .first()
        )
        if tmpl and tmpl.template_text:
            return tmpl.template_text
    except Exception:
        pass
    return SYSTEM_PROMPTS.get(tenant, SYSTEM_PROMPT_DEFAULT)


def _load_from_db(intent: str) -> Optional[Dict[str, Any]]:
    """Загружает конфигурацию схемы и промпта из БД (AIPromptTemplate) для заданного intent.

    Выбирает активный шаблон с максимальной версией. При ошибке или отсутствии записи
    молча возвращает None и пишет отладочное сообщение в лог.

    Args:
        intent: Строковый идентификатор интента (например, "actuator_selection").

    Returns:
        dict с ключами "schema" и "prompt_template" или None, если запись не найдена.
    """
    try:
        from ..models import AIPromptTemplate
        tmpl = (
            AIPromptTemplate.objects
            .filter(intent=intent, is_active=True)
            .order_by("-version")
            .first()
        )
        if tmpl and tmpl.template_text:
            return {
                "schema": tmpl.schema_json,
                "prompt_template": tmpl.template_text,
            }
    except Exception as e:
        logger.debug(f"DB schema load skipped: {e}")
    return None
