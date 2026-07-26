"""Обработка ОДНОГО сэмпла — результат в JSON-файл."""
import os, sys, json, time
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoProject1.settings'
sys.path.insert(0, os.path.dirname(__file__))
import django; django.setup()

from ai_assistant.models import AIQuerySample, StepConfig
from ai_assistant.services.deepseek_client import get_deepseek_client

sid = int(sys.argv[1])
sample = AIQuerySample.objects.get(id=sid)
text = sample.text.strip()
sc = StepConfig.objects.filter(step="decompose", is_active=True).first()
template = sc.prompt_template.template_text

try:
    prompt = template.format(system_prompt="...", user_text=text)
except KeyError:
    prompt = template

client = get_deepseek_client()

try:
    result = client.debug(prompt)
    raw = result.get("raw_text", "")
    out = {
        "id": sid,
        "text": text[:300],
        "error": False,
        "latency_ms": result.get("latency_ms"),
        "prompt_tokens": result.get("prompt_tokens"),
        "completion_tokens": result.get("completion_tokens"),
        "response": raw,
    }
except Exception as e:
    out = {"id": sid, "text": text[:300], "error": True, "message": str(e)}

fname = f"_sample_{sid}.json"
with open(fname, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"OK: {fname} ({len(out.get('response',''))} chars)", flush=True)
