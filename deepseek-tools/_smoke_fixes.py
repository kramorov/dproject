# deepseek-tools/_smoke_fixes.py — временный смоук фиксов 1,3,4
from ai_assistant.services.filter_handlers import (
    pneumatic_fittings_filter, pneumatic_silencers_filter, pneumatic_plugs_filter,
)
from pneumatic_fittings.models import PneumaticFitting, PneumaticSilencer, PneumaticPlug
from pneumatic_fittings.admin import (
    PneumaticFittingAdmin, PneumaticSilencerAdmin, PneumaticPlugAdmin,
)
from django.contrib import admin
from django.core.exceptions import ValidationError

print('AI fittings total:', pneumatic_fittings_filter({}).get('total'))
print('AI silencers total:', pneumatic_silencers_filter({}).get('total'))
print('AI plugs total:', pneumatic_plugs_filter({}).get('total'))

for Model, AdminCls in (
    (PneumaticFitting, PneumaticFittingAdmin),
    (PneumaticSilencer, PneumaticSilencerAdmin),
    (PneumaticPlug, PneumaticPlugAdmin),
):
    a = AdminCls(Model, admin.site)
    obj = Model.objects.first()
    print(Model.__name__, 'fieldsets:', [f[0] for f in a.get_fieldsets(None, obj)])

tube = PneumaticFitting.objects.first()
sil = PneumaticSilencer.objects.first()

# Проверка clean(): вид артикула должен совпадать с видом серии.
for Model, ml, et in (
    (PneumaticFitting, tube.model_line if tube else None, sil.equipment_type if sil else None),
    (PneumaticSilencer, sil.model_line if sil else None, tube.equipment_type if tube else None),
):
    if not ml or not et:
        continue
    bad = Model(name='_X', code='_X1', model_line=ml, equipment_type=et)
    try:
        bad.clean()
        print(Model.__name__, 'clean: NO ERROR (unexpected)')
    except ValidationError as e:
        print(Model.__name__, 'clean raises on mismatch:', 'equipment_type' in e.message_dict)
