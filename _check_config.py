import os; os.environ['DJANGO_SETTINGS_MODULE']='djangoProject1.settings'
import django; django.setup()
from pneumatic_actuators.models import PneumaticActuatorModelLine, PneumaticActuatorModelLineItem

mls = PneumaticActuatorModelLine.objects.filter(is_active=True).count()
items = PneumaticActuatorModelLineItem.objects.filter(is_active=True).count()
print(f'ModelLines: {mls}')
print(f'Items: {items}')
for ml in PneumaticActuatorModelLine.objects.filter(is_active=True)[:5]:
    cnt = ml.model_line_items.filter(is_active=True).count()
    print(f'  {ml.name} ({ml.code}) - items: {cnt}, desc: {ml.description or "(none)"}')
