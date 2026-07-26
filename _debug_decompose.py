"""
Прогон ВСЕХ 8 сэмплов через DeepSeek API (decompose).
Результат: _sample_output.txt
"""
import os, sys, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoProject1.settings'
sys.path.insert(0, os.path.dirname(__file__))
import django; django.setup()

from ai_assistant.models import AIQuerySample, StepConfig
from ai_assistant.services.deepseek_client import get_deepseek_client

OUT = open("_sample_output.txt", "w", encoding="utf-8")

def log(*args):
    line = " ".join(str(a) for a in args)
    print(line, flush=True)
    OUT.write(line + "\n")
    OUT.flush()

client = get_deepseek_client()
sc = StepConfig.objects.filter(step="decompose", is_active=True).first()
template = sc.prompt_template.template_text if sc.prompt_template else ""

for sample in AIQuerySample.objects.all().order_by("id"):
    sid = sample.id
    text = sample.text.strip()

    log(f"\n{'='*70}")
    log(f"СЭМПЛ #{sid}")
    log(f"{'='*70}")
    log(f"ЗАПРОС: {text[:300]}\n")

    try:
        prompt = template.format(
            system_prompt="Ты — инженер по подбору промышленного оборудования.",
            user_text=text
        )
    except KeyError:
        prompt = template

    log(f"Промпт: {len(prompt)} знаков (шаблон: {sc.prompt_template.name})\n")
    log("── ОТВЕТ LLM ──")

    result = client.debug(prompt)
    raw = result.get("raw_text", "")
    log(raw)
    log(f"\n(всего {len(raw)} знаков, latency={result.get('latency_ms','?')}ms)")
    log(f"tokens: prompt={result.get('prompt_tokens','?')} completion={result.get('completion_tokens','?')}")

    # Краткий разбор
    log(f"\n── РАЗБОР ──")
    if "needs_info" in raw[:200]:
        log("  Статус: NEEDS_INFO — не хватает данных")
    elif "```json" in raw[:500]:
        log("  Статус: есть JSON-дерево (можно парсить)")
    elif "СТАТУС" in raw[:200]:
        log("  Статус: определён (см. выше)")

OUT.close()
print("\nГотово: _sample_output.txt")
