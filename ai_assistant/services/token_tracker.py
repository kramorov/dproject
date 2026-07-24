"""Подсчёт и сохранение токенов для сообщения."""
import logging

logger = logging.getLogger(__name__)


def save_token_usage(message, usage_data: dict):
    """Создаёт AITokenUsage для AIMessage."""
    from ..models import AITokenUsage

    token_usage = AITokenUsage.objects.create(
        message=message,
        model=usage_data.get("model", "unknown"),
        prompt_tokens=usage_data.get("prompt_tokens", 0),
        completion_tokens=usage_data.get("completion_tokens", 0),
        reasoning_tokens=usage_data.get("reasoning_tokens"),
        total_tokens=usage_data.get("total_tokens", 0),
        cost_estimate=usage_data.get("cost_estimate"),
    )
    return token_usage


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Приблизительная оценка стоимости в USD."""
    if "deepseek" in model.lower():
        # $2 / 1M input, $8 / 1M output (приблизительно)
        return (prompt_tokens / 1_000_000) * 2.0 + (completion_tokens / 1_000_000) * 8.0
    return 0.0
