import os, sys, json, traceback
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
sys.path.insert(0, os.path.dirname(__file__))
import django; django.setup()

from ai_assistant.models import AIConversation, StepConfig
from ai_assistant.services.tree_processor import TreeProcessor

conv = AIConversation.objects.create(status='processing')
tp = TreeProcessor(conv)

# Смотрим, что возвращает LLM
text = 'подбери пневмопривод к затвору дисковому ДУ300 момент без запаса 186 Нм'

config = tp._get_config("decompose")
if not config:
    print("Нет StepConfig для decompose!")
else:
    print(f"Config: step={config['step']} model_role={config['model_role']}")
    print(f"Prompt text (первые 300): {config['prompt_text'][:300]}")
    
# Вызываем LLM вручную
try:
    llm_result = tp.client.debug(config['prompt_text'].format(
        system_prompt=tp._get_system_prompt(), user_text=text
    ))
    print(f"\n=== LLM RESULT KEYS: {list(llm_result.keys())}")
    raw_text = llm_result.get("raw_text", "")
    print(f"=== RAW TEXT (первые 2000):")
    print(raw_text[:2000])
    print(f"\n=== RAW TEXT LENGTH: {len(raw_text)}")
    
    # Пробуем распарсить
    tree_data = tp._parse_tree_output(raw_text)
    print(f"\n=== PARSED TREE DATA:")
    print(json.dumps(tree_data, ensure_ascii=False, indent=2)[:2000])
    
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
