"""Enhance _introspect_model.py with filter_type/data_source_type inference + ETP diff."""
import django, os, sys, json
from collections import OrderedDict

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
django.setup()

from django.db import models
from core.models import EquipmentType
from configurator.models import EquipmentTypeParameter as ETP

SKIP_FIELD_NAMES = {
    'id', 'sorting_order', 'is_active', 'created_at', 'updated_at',
    'polymorphic_ctype', 'name', 'code', 'description', 'notes',
    'slug', 'uuid', 'image', 'image_thumb', 'image_preview',
    'created_by', 'updated_by', 'deleted_at', 'meta_title', 'meta_description',
    # Metadata M2M fields — not selection parameters
    'tech_docs', 'cert_docs', 'image_gallery', 'images',
}

# Skip M2M and FK fields at depth >= 1 that are just metadata containers
SKIP_FK_TARGETS_DEEP = {'media_library', 'cert_doc', 'contenttypes'}
SKIP_FIELD_TYPES = {'AutoField', 'BigAutoField', 'UUIDField', 'DateTimeField', 'DateField', 'TimeField', 'FileField', 'ImageField', 'BinaryField'}
EXCLUDE_PREFIXES = ('_',)
MAX_DEPTH = 2

# ── Inference rules ──
def infer_filter_type(ftype: str, fk_target: str = '') -> str:
    """Infer filter_type from Django field type."""
    if ftype == 'fk':
        if 'material' in fk_target.lower() or 'brand' in fk_target.lower():
            return 'choice'
        return 'exact'
    if ftype == 'm2m':
        return 'choice'
    if ftype in ('integer', 'positivesmallinteger', 'positiveinteger'):
        return 'gte'
    if ftype in ('decimal', 'float'):
        return 'gte'
    if ftype in ('boolean', 'bool'):
        return 'boolean'
    if ftype in ('char', 'text', 'textfield'):
        return 'icontains'
    if ftype == 'json':
        return 'icontains'
    return 'exact'

def infer_data_source(ftype: str, fk_target: str = '') -> str:
    """Infer data_source_type from Django field type."""
    if ftype == 'fk':
        return 'foreign_key'
    if ftype == 'm2m':
        return 'global_model'
    if ftype in ('integer', 'decimal', 'float', 'positivesmallinteger', 'positiveinteger'):
        return 'field_values'
    if ftype in ('boolean', 'bool'):
        return 'choices'
    if ftype in ('char', 'text', 'textfield', 'json'):
        return 'field_values'
    return 'field_values'


def get_model_from_equipment_type(et_code: str):
    et = EquipmentType.objects.filter(code=et_code, is_active=True).first()
    if not et: return None, None
    ct = et.content_type
    if not ct: return et, None
    return et, ct.model_class()

def should_skip_field(field):
    name = field.name
    if name in SKIP_FIELD_NAMES: return True
    if any(name.startswith(p) for p in EXCLUDE_PREFIXES): return True
    if type(field).__name__ in SKIP_FIELD_TYPES: return True
    if field.auto_created and name.endswith('_set'): return True
    return False

def _verbose(field):
    """Безопасно извлекает verbose_name (может быть lazy-translation)."""
    try:
        v = field.verbose_name
        return str(v) if v else ''
    except Exception:
        return ''

def _help(field):
    """Безопасно извлекает help_text (может быть lazy-translation или пустым)."""
    try:
        h = getattr(field, 'help_text', '') or ''
        return str(h)
    except Exception:
        return ''

def introspect_model(model_class, prefix='', depth=0, visited=None, max_depth=MAX_DEPTH):
    if visited is None: visited = set()
    if depth > max_depth: return OrderedDict()
    if model_class in visited: return OrderedDict()
    visited.add(model_class)
    result = OrderedDict()
    for field in model_class._meta.get_fields():
        if should_skip_field(field): continue
        param_name = f"{prefix}{field.name}"
        ftype = type(field).__name__
        if isinstance(field, (models.ForeignKey, models.OneToOneField)):
            target = f'{field.related_model._meta.app_label}.{field.related_model.__name__}'
            info = {'param_name': param_name, 'field_type': 'fk', 'source_model': f'{model_class._meta.app_label}.{model_class.__name__}', 'target_model': target, 'depth': depth}
            info['filter_type'] = infer_filter_type('fk', target)
            info['data_source_type'] = infer_data_source('fk', target)
            info['verbose_name'] = _verbose(field)
            info['help_text'] = _help(field)
            result[param_name] = info
            if depth < max_depth - 1:
                sub = introspect_model(field.related_model, f"{field.name}__", depth + 1, visited.copy(), max_depth)
                for n, i in sub.items():
                    if n not in result: result[n] = i
                    else:
                        e = result[n]; e.setdefault('duplicates', [e.get('source_model', '?')]).append(i.get('source_model', '?'))
        elif isinstance(field, models.ManyToManyField):
            # Skip M2M into metadata apps at depth >= 1
            if depth >= 1 and field.related_model._meta.app_label in SKIP_FK_TARGETS_DEEP:
                continue
            target = f'{field.related_model._meta.app_label}.{field.related_model.__name__}'
            info = {'param_name': param_name, 'field_type': 'm2m', 'source_model': f'{model_class._meta.app_label}.{model_class.__name__}', 'target_model': target, 'depth': depth}
            info['filter_type'] = infer_filter_type('m2m', target)
            info['data_source_type'] = infer_data_source('m2m', target)
            info['verbose_name'] = _verbose(field)
            info['help_text'] = _help(field)
            result[param_name] = info
        elif isinstance(field, models.Field):
            info = {'param_name': param_name, 'field_type': ftype.lower().replace('field', ''), 'source_model': f'{model_class._meta.app_label}.{model_class.__name__}', 'depth': depth, 'null': field.null}
            info['filter_type'] = infer_filter_type(info['field_type'])
            info['data_source_type'] = infer_data_source(info['field_type'])
            info['verbose_name'] = _verbose(field)
            info['help_text'] = _help(field)
            result[param_name] = info
    return result


def print_fields(fields, title="Fields"):
    print(f"\n=== {title} ({len(fields)} unique params) ===")
    by_depth = {}
    for name, info in fields.items():
        d = info.get('depth', 0)
        by_depth.setdefault(d, []).append((name, info))
    for depth in sorted(by_depth):
        indent = '  ' * depth
        print(f"\n  Level {depth} ({len(by_depth[depth])} fields):")
        for name, info in sorted(by_depth[depth]):
            dup = f" ⚠️ DUP: {info.get('duplicates', [])}" if 'duplicates' in info else ''
            ft = info.get('filter_type', '?')
            ds = info.get('data_source_type', '?')
            print(f"    {indent}{name:40s} | {info.get('field_type','?'):8s} | flt={ft:12s} | src={ds:15s}{dup}")


def diff_etp(fields, et):
    """Compare introspected fields with existing ETP records."""
    etp_existing = set(ETP.objects.filter(equipment_type=et, is_active=True).values_list('param_name', flat=True))
    introspected = set(fields.keys())
    new = introspected - etp_existing
    existing = introspected & etp_existing
    removed = etp_existing - introspected
    print(f"\n=== ETP Comparison ===")
    print(f"  In ETP:           {len(etp_existing)}")
    print(f"  Introspected:     {len(introspected)}")
    print(f"  Match:            {len(existing)}")
    print(f"  NEW (not in ETP): {len(new)}")
    if new:
        print(f"    → {sorted(new)[:15]}{'...' if len(new) > 15 else ''}")
    print(f"  ONLY in ETP:      {len(removed)}")
    if removed:
        print(f"    → {sorted(removed)[:10]}{'...' if len(removed) > 10 else ''}")

def save_to_snapshot(fields, et):
    """
    Сохранить результаты интроспекции в ModelFieldSnapshot (БД).

    - Новые поля → создаются (is_active=True).
    - Существующие → обновляются (field_type, target_model, filter_type, ...),
      НО param_name и is_active сохраняются (пользовательские правки не затираются).
    - Поля, исчезнувшие из модели → is_active=False (не удаляются).
    """
    from configurator.models import ModelFieldSnapshot
    seen_paths = set()
    created = updated = deactivated = 0

    for path, info in fields.items():
        seen_paths.add(path)
        obj, is_new = ModelFieldSnapshot.objects.update_or_create(
            equipment_type=et,
            field_path=path,
            defaults={
                'field_type': info.get('field_type', 'other'),
                'target_model': info.get('target_model', None),
                'source_model': info.get('source_model', None),
                'depth': info.get('depth', 0),
                'filter_type': info.get('filter_type', ''),
                'data_source_type': info.get('data_source_type', ''),
                'verbose_name': info.get('verbose_name', None),
                'help_text': info.get('help_text', None),
            },
        )
        if is_new:
            created += 1
        else:
            updated += 1

    # Deactivate fields no longer in model
    deactivated = (ModelFieldSnapshot.objects
                   .filter(equipment_type=et, is_active=True)
                   .exclude(field_path__in=seen_paths)
                   .update(is_active=False))

    print(f"Snapshot: {created} created, {updated} updated, {deactivated} deactivated")


def sync_to_etp(et):
    """
    Перенести активные снапшоты в EquipmentTypeParameter.

    - param_name берётся из снапшота: если привязан ParameterCatalog — его code,
      иначе — field_path.
    - product_model = equipment_type.content_type.
    """
    from configurator.models import ModelFieldSnapshot
    snaps = ModelFieldSnapshot.objects.filter(equipment_type=et, is_active=True).select_related('param_name')
    created = updated = 0
    for s in snaps:
        param_name = s.param_name.code if s.param_name else s.field_path
        defaults = {
            'equipment_type': et,
            'param_name': param_name,
            'field_path': s.field_path,
            'filter_type': s.filter_type or '',
            'data_source_type': s.data_source_type or '',
            'is_active': True,
        }
        if et.content_type:
            defaults['product_model'] = et.content_type
        if s.target_model and s.data_source_type == 'global_model':
            defaults['options_config'] = {'model': s.target_model}
        obj, is_new = ETP.objects.update_or_create(equipment_type=et, param_name=param_name, defaults=defaults)
        if is_new:
            created += 1
        else:
            updated += 1
    print(f"ETP: {created} created, {updated} updated")


def main():
    if len(sys.argv) < 2:
        print("Usage: python _introspect_model.py <code> [--depth N] [--save] [--sync-etp] [--diff] [--json]")
        return
    et_code = sys.argv[1]
    do_save = '--save' in sys.argv
    do_sync = '--sync-etp' in sys.argv
    show_diff = '--diff' in sys.argv
    as_json = '--json' in sys.argv
    depth = MAX_DEPTH
    for i, arg in enumerate(sys.argv):
        if arg == '--depth' and i + 1 < len(sys.argv):
            depth = int(sys.argv[i + 1])
    et, mc = get_model_from_equipment_type(et_code)
    if not mc: return
    print(f"EquipmentType: {et.code} ({et.name})  Model: {mc._meta.app_label}.{mc.__name__}  Depth: {depth}")
    fields = introspect_model(mc, max_depth=depth)
    if as_json:
        print(json.dumps({k: v for k, v in fields.items()}, indent=2, ensure_ascii=False))
    else:
        print_fields(fields, f"{et.code}")
        dupes = {k: v for k, v in fields.items() if 'duplicates' in v}
        if dupes:
            print(f"\n=== ⚠️ DUPLICATES ({len(dupes)}) ===")
            for name, info in dupes.items():
                print(f"  {name}: {', '.join([info.get('source_model','?')] + info.get('duplicates',[]))}")
    if show_diff:
        diff_etp(fields, et)
    if do_save:
        save_to_snapshot(fields, et)
    if do_sync:
        sync_to_etp(et)

if __name__ == '__main__':
    main()
