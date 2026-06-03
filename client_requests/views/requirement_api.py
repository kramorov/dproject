# client_requests/views/requirement_api.py
"""
API for equipment requirements.

GET  /api/client_requests/requirements/schema/?type=gearbox
     Returns field metadata (name, label, type, choices, defaults for FK fields).

POST /api/client_requests/requirements/preview/
     Accepts field values, returns filter_params for EngineerSelection API.
     No database writes.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models.fields import IntegerField, DecimalField, BooleanField
from django.db.models.fields.related import ForeignKey

from client_requests.models.gearbox_requirement import GearboxRequirement
from client_requests.models.filter_regulator_requirement import FilterRegulatorRequirement
from client_requests.models.limit_switch_requirement import LimitSwitchRequirement

REQUIREMENT_CLASSES = {
    'gearbox': GearboxRequirement,
    'filter_regulator': FilterRegulatorRequirement,
    'limit_switch': LimitSwitchRequirement,
}

SKIP_FIELDS = {'id', 'request_item', 'created_at', 'updated_at'}


def _get_field_schema(klass):
    """Introspect Django model fields and return frontend-friendly schema."""
    fields = []
    for f in klass._meta.get_fields():
        if f.auto_created or f.name in SKIP_FIELDS:
            continue

        entry = {
            'name': f.name,
            'label': str(getattr(f, 'verbose_name', f.name)),
        }

        if isinstance(f, ForeignKey):
            entry['field_type'] = 'fk'
            # Fetch choices from related model
            try:
                rel_model = f.remote_field.model
                qs = rel_model.objects.filter(is_active=True) if hasattr(rel_model, 'is_active') else rel_model.objects.all()
                entry['choices'] = [{'id': obj.pk, 'name': str(obj)} for obj in qs[:500]]
            except Exception:
                entry['choices'] = []
        elif isinstance(f, IntegerField):
            entry['field_type'] = 'integer'
            if hasattr(f, 'validators'):
                for v in f.validators:
                    if hasattr(v, 'limit_value'):
                        entry['min'] = v.limit_value if hasattr(v, 'compare') and 'min' in str(v) else entry.get('min')
        elif isinstance(f, DecimalField):
            entry['field_type'] = 'decimal'
            entry['max_digits'] = f.max_digits
            entry['decimal_places'] = f.decimal_places
        elif isinstance(f, BooleanField):
            entry['field_type'] = 'boolean'
        else:
            entry['field_type'] = 'string'

        if f.null or f.blank:
            entry['optional'] = True

        fields.append(entry)

    return {
        'type': klass.__name__.replace('Requirement', '').lower(),
        'label': str(klass._meta.verbose_name),
        'fields': fields,
    }


class RequirementsSchemaView(APIView):
    """GET ?type=gearbox → field schema for frontend form."""
    permission_classes = [AllowAny]

    def get(self, request):
        req_type = request.query_params.get('type', '')
        klass = REQUIREMENT_CLASSES.get(req_type)
        if not klass:
            return Response(
                {'error': f'Unknown requirement type: "{req_type}". '
                          f'Valid: {list(REQUIREMENT_CLASSES.keys())}'},
                status=400,
            )
        schema = _get_field_schema(klass)
        schema['defaults'] = klass.get_defaults()
        return Response(schema)


class RequirementsPreviewView(APIView):
    """
    POST — dry-run: принимает значения полей, возвращает filter_params.
    Без сохранения в БД.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        req_type = request.data.get('type', '')
        klass = REQUIREMENT_CLASSES.get(req_type)
        if not klass:
            return Response(
                {'error': f'Unknown requirement type: "{req_type}". '
                          f'Valid: {list(REQUIREMENT_CLASSES.keys())}'},
                status=400,
            )

        field_names = {f.name for f in klass._meta.get_fields()
                       if not f.auto_created and f.name not in SKIP_FIELDS}

        kwargs = {}
        for key, value in request.data.items():
            if key in ('type',):
                continue
            if key in field_names:
                kwargs[key] = value if value != '' else None

        try:
            req = klass(**kwargs)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

        filter_params = req.to_filter_params()
        # Handle exd sentinel from cascade form
        if request.data.get('exd_id_override'):
            filter_params['exd_id'] = request.data['exd_id_override']
        return Response({'filter_params': filter_params})
