# deepseek-tools/_smoke_fixes.py — временный смоук фиксов 1,3,4
from ai_assistant.services.filter_handlers import pneumatic_fittings_filter
from pneumatic_fittings.models import PneumaticFitting
from pneumatic_fittings.admin import PneumaticFittingAdmin
from django.contrib import admin
from django.core.exceptions import ValidationError

print('AI total (no params):', pneumatic_fittings_filter({}).get('total'))

a = PneumaticFittingAdmin(PneumaticFitting, admin.site)
sil = PneumaticFitting.objects.filter(equipment_type__code='fitting-silencer').first()
tube = PneumaticFitting.objects.filter(equipment_type__code='fitting-thread-pipe').first()
print('silencer fieldsets:', [f[0] for f in a.get_fieldsets(None, sil)])
print('tube fieldsets:', [f[0] for f in a.get_fieldsets(None, tube)])

bad = PneumaticFitting(name='_X', code='_X1', model_line=tube.model_line, equipment_type=sil.equipment_type)
try:
    bad.clean()
    print('clean: NO ERROR (unexpected)')
except ValidationError as e:
    print('clean raises on mismatch:', 'equipment_type' in e.message_dict)

ok = PneumaticFitting(name='_Y', code='_Y1', model_line=sil.model_line, equipment_type=sil.equipment_type)
try:
    ok.clean()
    print('clean passes on match: True')
except ValidationError:
    print('clean passes on match: False')
