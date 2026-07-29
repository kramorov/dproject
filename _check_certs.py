import os; os.environ['DJANGO_SETTINGS_MODULE']='djangoProject1.settings'
import django; django.setup()
from pneumatic_actuators.models import PneumaticActuatorModelLine

ml = PneumaticActuatorModelLine.objects.filter(is_active=True).first()
print(f'ML: {ml.name}')
print(f'hasattr cert_data_model_line: {hasattr(ml, "cert_data_model_line")}')
if hasattr(ml, 'cert_data_model_line'):
    count = ml.cert_data_model_line.filter(cert_data__is_active=True).count()
    print(f'cert_data_model_line count: {count}')
    cert_ids = list(ml.cert_data_model_line.filter(cert_data__is_active=True).values_list('cert_data_id', flat=True))
    print(f'cert ids: {cert_ids}')
