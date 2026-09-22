# core/template_field_registry.py
"""Единый реестр полей шаблонов для админок типов оборудования.

Собирает доступные ключи/плейсхолдеры из ``TEMPLATE_FIELDS`` моделей-каталогов
(единый источник правды, см. template_mixin.md §7), чтобы редакторы
``EquipmentType`` могли показывать:

  * справочник плейсхолдеров для ``title_template`` (``{model_code}`` и т.п.);
  * пикер ключей для ``spec_template`` (``ip``, ``body_material`` и т.п.).

Состав можно получить как по всем каталогам сразу (``collect_template_fields``),
так и для конкретного типа оборудования (``collect_template_fields_for_equipment_type``) —
последний используется фронтом, чтобы показывать плейсхолдеры только выбранного
типа, а не всего проекта.

Записи нормализуются через ``TemplateFieldSpec``; дубликаты по ``key``
отбрасываются (предпочтение — записи с заполненным ``label``).
"""

from django.apps import apps

from core.models.template_fields import TemplateFieldSpec


# У части типов ``content_type`` всё ещё указывает на старую (переходную) модель
# без реестра ``TEMPLATE_FIELDS``. Явный мостик на актуальную модель-каталог.
_EQUIPMENT_TYPE_MODEL_OVERRIDES = {
    'pneumatic-actuator': 'pneumatic_actuators.PneumaticActuatorItem',
}


def _normalize(spec):
    """Привести запись реестра к TemplateFieldSpec (или None, если некорректна)."""
    if isinstance(spec, TemplateFieldSpec):
        return spec
    if isinstance(spec, dict):
        try:
            return TemplateFieldSpec.from_dict(spec)
        except (TypeError, ValueError):
            return None
    return None


def _dedupe_and_sort(specs):
    """Дедупликация по ``key`` (предпочтение записи с ``label``) и сортировка."""
    by_key = {}
    for s in specs:
        if s is None or not s.key:
            continue
        existing = by_key.get(s.key)
        if existing is None or (not existing.label and s.label):
            by_key[s.key] = s
    result = list(by_key.values())
    result.sort(key=lambda s: (s.group or '', s.label or '', s.key))
    return result


def collect_template_fields_for_model(model_class):
    """Спецификации полей одной модели-каталога.

    Источник: ``TEMPLATE_FIELDS`` реестра; для старых моделей без реестра —
    fallback на ручной ``_get_data_dict()`` (плейсхолдеры + пути).
    """
    specs = []
    raw = getattr(model_class, 'TEMPLATE_FIELDS', None)
    if raw:
        try:
            items = list(raw)
        except TypeError:
            items = []
        specs = [s for s in (_normalize(item) for item in items) if s is not None]

    if not specs:
        getter = getattr(model_class, '_get_data_dict', None)
        if callable(getter):
            try:
                data_dict = model_class()._get_data_dict()
            except Exception:
                data_dict = None
            if isinstance(data_dict, dict):
                for ph, path in data_dict.items():
                    if isinstance(ph, str) and ph.startswith('{') and ph.endswith('}'):
                        specs.append(TemplateFieldSpec(
                            key=ph.strip('{}'),
                            placeholder=ph,
                            path=path if isinstance(path, str) else None,
                        ))
    return _dedupe_and_sort(specs)


def collect_template_fields_for_equipment_type(equipment_type):
    """Спецификации полей для конкретного типа оборудования.

    Резолв модели — через ``EquipmentType.content_type`` (Django-модель товара);
    при пустом/устаревшем ``content_type`` — через ``_EQUIPMENT_TYPE_MODEL_OVERRIDES``.
    """
    code = getattr(equipment_type, 'code', None)
    ct = getattr(equipment_type, 'content_type', None)
    if ct:
        try:
            model = ct.model_class()
        except Exception:
            model = None
        if model is not None:
            specs = collect_template_fields_for_model(model)
            if specs:
                return specs

    label = _EQUIPMENT_TYPE_MODEL_OVERRIDES.get(code)
    if label:
        try:
            return collect_template_fields_for_model(apps.get_model(*label.split('.')))
        except (LookupError, ValueError):
            pass
    return []


def collect_template_fields():
    """Спецификации полей по всем каталогам (объединение ``TEMPLATE_FIELDS``)."""
    specs = []
    for model in apps.get_models():
        raw = getattr(model, 'TEMPLATE_FIELDS', None)
        if not raw:
            continue
        try:
            items = list(raw)
        except TypeError:
            continue
        for item in items:
            try:
                specs.append(_normalize(item))
            except Exception:
                pass
    return _dedupe_and_sort(specs)


def collect_placeholder_choices(specs=None):
    """Список плейсхолдеров (``{model_code}``, ``{brand}``, ...) для чипов."""
    if specs is None:
        specs = collect_template_fields()
    return sorted({s.placeholder for s in specs if s.placeholder})


def collect_field_choices(specs=None):
    """Список словарей ``{key, placeholder, label, unit, group}`` для пикера."""
    if specs is None:
        specs = collect_template_fields()
    return [
        {
            'key': s.key,
            'placeholder': s.placeholder,
            'label': s.label,
            'unit': s.unit,
            'group': s.group,
        }
        for s in specs
    ]
