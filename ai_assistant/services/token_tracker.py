"""Token tracking and latency estimation."""
import logging

logger = logging.getLogger(__name__)

MAX_LATENCY_SAMPLES = 5


def save_token_usage(message, usage_data, customer=None):
    """Create AITokenUsage for an AIMessage."""
    from ..models import AITokenUsage
    lat = usage_data.get("latency_ms")
    if lat is None:
        lat = getattr(message, "latency_ms", None)
    obj = AITokenUsage(
        message=message,
        customer=customer,
        model=usage_data.get("model", "unknown"),
        prompt_tokens=usage_data.get("prompt_tokens", 0),
        completion_tokens=usage_data.get("completion_tokens", 0),
        reasoning_tokens=usage_data.get("reasoning_tokens", 0),
        total_tokens=usage_data.get("total_tokens", 0),
        cost_estimate=usage_data.get("cost_estimate"),
        latency_ms=lat,
    )
    obj.save()
    return obj


def estimate_cost(model, prompt_tokens, completion_tokens):
    if "deepseek" in model.lower():
        return (prompt_tokens / 1_000_000) * 2.0 + (completion_tokens / 1_000_000) * 8.0
    return 0.0


def update_skill_latency(skill, lat):
    if lat is None:
        return
    old = skill.avg_latency_ms or 0
    cnt = min(skill.latency_sample_count or 0, MAX_LATENCY_SAMPLES - 1)
    new = round((old * cnt + lat) / (cnt + 1))
    skill.avg_latency_ms = new
    skill.latency_sample_count = cnt + 1
    skill.save(update_fields=["avg_latency_ms", "latency_sample_count"])


def get_estimated_latency(skill):
    return skill.avg_latency_ms or 5000