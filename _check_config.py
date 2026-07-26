import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoProject1.settings'
sys.path.insert(0, os.path.dirname(__file__))
import django; django.setup()

from ai_assistant.models import StepConfig, AIPromptTemplate, JSONSchema

print("=== StepConfig (все активные) ===")
for sc in StepConfig.objects.filter(is_active=True).select_related('prompt_template','output_schema','equipment_type'):
    eq = sc.equipment_type.code if sc.equipment_type else '*'
    pt = sc.prompt_template.name if sc.prompt_template else '-'
    os_ = sc.output_schema.name if sc.output_schema else '-'
    print(f"  {sc.step:12s} / {eq:20s} | prompt={pt:20s} | schema={os_:20s} | role={sc.model_role}")

print("\n=== AIPromptTemplate (все активные) ===")
for pt in AIPromptTemplate.objects.filter(is_active=True):
    print(f"  {pt.name:25s} v{pt.version} | {pt.template_text[:120]}...")

print("\n=== JSONSchema (все активные) ===")
for js in JSONSchema.objects.filter(is_active=True):
    print(f"  {js.name:25s} v{js.version} | {str(js.schema_json)[:150]}")
