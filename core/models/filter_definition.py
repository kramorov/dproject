# core/models/filter_definition.py
"""
FilterDefinition — declarative filter configuration.

Extracted from smart_catalog_mixin.py to separate the building block
(FilterDefinition) from the consumer (SmartCatalogMixin).

FilterType   — how the filter matches (exact, min, max, compatible, etc.)
DataSourceType — where filter options come from (field values, FK, global model, etc.)
FilterDefinition — one filter: param name, model field, type, data source, label.
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional, Type
from enum import Enum

from django.db import models
from django.db.models import QuerySet
from django.core.exceptions import FieldDoesNotExist

from params.exd_models import ExdOption
from params.models import IpOption, ThreadSize, ThreadTypes


class FilterType(Enum):
    """Filter matching strategies."""
    EXACT = "exact"
    CONTAINS = "icontains"
    MIN = "gte"
    MAX = "lte"
    CHOICE = "choice"
    BOOLEAN = "boolean"
    TEMP_MIN = "temp_min"
    TEMP_MAX = "temp_max"
    IP_RANK = "ip_rank"
    EXD_COMPATIBLE = "exd_compatible"
    FK_CASCADE = "fk_cascade"
    COMPATIBLE_CASCADE = "compatible_cascade"
    CLIMATE_CASCADE = "climate_cascade"
    THREAD_COMPATIBLE = "thread_compatible"
    FUNCTION_COMPATIBLE = "function_compatible"


class DataSourceType(Enum):
    """Where filter option values come from."""
    FIELD_VALUES = "field_values"
    UNIQUE_FIELD_VALUES = "unique_field_values"
    FOREIGN_KEY = "foreign_key"
    GLOBAL_MODEL = "global_model"
    CHOICES = "choices"
    CUSTOM = "custom"


class FilterDefinition:
    """
    Declarative filter definition for catalog models.

    Examples:
        FilterDefinition(
            param_name='model_line_id',
            model_field='model_line',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.FOREIGN_KEY,
            label='Серия',
        )

        FilterDefinition(
            param_name='work_temp_min',
            model_field='work_temp_min',
            filter_type=FilterType.TEMP_MIN,
            data_source_type=DataSourceType.FIELD_VALUES,
            label='Температура от',
        )

    See catalog_concept.md for the full architecture.
    """

    # Types that support exact/compatible splitting
    SPLITTABLE_TYPES = (
        FilterType.TEMP_MIN, FilterType.TEMP_MAX,
        FilterType.MIN, FilterType.MAX,
        FilterType.EXD_COMPATIBLE, FilterType.THREAD_COMPATIBLE,
        FilterType.FUNCTION_COMPATIBLE, FilterType.IP_RANK,
    )

    def __init__(
            self,
            param_name: str,
            model_field: str,
            filter_type: FilterType,
            data_source_type: DataSourceType,
            label: str = None,
            order: int = 0,
            source_model: Type[models.Model] = None,
            source_field: str = None,
            choices: List[tuple] = None,
            active_only: bool = True,
            order_by: str = 'name',
            cascade_model: Type[models.Model] = None,
            is_parent_filter: bool = False,
            cascade_lookup: str = None,
            cascade_match_fields: List[str] = None,
            show_code: bool = False,
            default_value: str = None,
    ):
        self.param_name = param_name
        self.model_field = model_field
        self.filter_type = filter_type
        self.data_source_type = data_source_type
        self.label = label or param_name
        self.order = order
        self.source_model = source_model
        self.source_field = source_field
        self.choices = choices
        self.active_only = active_only
        self.order_by = order_by
        self.cascade_model = cascade_model
        self.is_parent_filter = is_parent_filter
        self.cascade_lookup = cascade_lookup
        self.cascade_match_fields = cascade_match_fields or []
        self.show_code = show_code
        self.default_value = default_value

    # ── Options ──

    def get_options(self, model_class, queryset=None) -> List[Dict]:
        """
        Get filter options. If queryset is provided (scoped mode), values
        are limited to what appears in that queryset instead of the full table.
        """

        if self.data_source_type == DataSourceType.FIELD_VALUES:
            base_qs = queryset if queryset is not None else model_class.objects
            values = base_qs.filter(
                **{f"{self.model_field}__isnull": False}
            ).values_list(self.model_field, flat=True).distinct().order_by(self.model_field)
            return [
                {'id': v, 'name': str(v), 'code': ''}
                for v in values if v is not None
            ]
        elif self.data_source_type == DataSourceType.UNIQUE_FIELD_VALUES:
            try:
                base_qs = queryset if queryset is not None else model_class.objects
                values = base_qs.filter(
                    **{f"{self.model_field}__isnull": False}
                ).values_list(self.model_field, flat=True).distinct()
            except Exception as e:
                import traceback
                print(f"[UNIQUE_FIELD_VALUES ERROR] model={model_class.__name__}, field={self.model_field}: {e}")
                traceback.print_exc()
                return []

            try:
                parts = self.model_field.split('__')
                rel_model = model_class
                for part in parts:
                    field = rel_model._meta.get_field(part)
                    if field.is_relation:
                        rel_model = field.remote_field.model

                objects = rel_model.objects.filter(id__in=values)
                if self.active_only and hasattr(rel_model, 'is_active'):
                    objects = objects.filter(is_active=True)

                if hasattr(rel_model, 'sorting_order'):
                    objects = objects.order_by('sorting_order', self.order_by)
                else:
                    objects = objects.order_by(self.order_by)

                return [
                    {
                        'id': obj.id,
                        'name': getattr(obj, 'name', str(obj)),
                        'code': getattr(obj, 'code', '') or ''
                    }
                    for obj in objects
                ]
            except (FieldDoesNotExist, AttributeError):
                return [
                    {'id': v, 'name': str(v), 'code': ''}
                    for v in values if v is not None
                ]
        elif self.data_source_type == DataSourceType.FOREIGN_KEY:
            try:
                if queryset is not None:
                    fk_ids = queryset.filter(
                        **{f"{self.model_field}__isnull": False}
                    ).values_list(f"{self.model_field}_id", flat=True).distinct()
                    parts = self.model_field.split('__')
                    rel_model = model_class
                    for part in parts:
                        field = rel_model._meta.get_field(part)
                        if field.is_relation:
                            rel_model = field.remote_field.model
                    qs = rel_model.objects.filter(id__in=fk_ids)
                else:
                    parts = self.model_field.split('__')
                    rel_model = model_class
                    for part in parts:
                        field = rel_model._meta.get_field(part)
                        if field.is_relation:
                            rel_model = field.remote_field.model
                    qs = rel_model.objects.all()

                if self.active_only and hasattr(rel_model, 'is_active'):
                    qs = qs.filter(is_active=True)

                if hasattr(rel_model, 'sorting_order'):
                    qs = qs.order_by('sorting_order', self.order_by)
                else:
                    qs = qs.order_by(self.order_by)

                return [
                    {
                        'id': obj.id,
                        'name': getattr(obj, 'name', str(obj)),
                        'code': getattr(obj, 'code', '') or ''
                    }
                    for obj in qs
                ]
            except (FieldDoesNotExist, AttributeError):
                return []

        elif self.data_source_type == DataSourceType.GLOBAL_MODEL:
            if self.source_model:
                queryset = self.source_model.objects.all()
                if self.active_only and hasattr(self.source_model, 'is_active'):
                    queryset = queryset.filter(is_active=True)
                if hasattr(self.source_model, 'sorting_order'):
                    queryset = queryset.order_by('sorting_order', self.order_by)
                else:
                    queryset = queryset.order_by(self.order_by)

                return [
                        {
                            'id': obj.id,
                            'name': getattr(obj, 'name', str(obj)),
                            'code': getattr(obj, 'code', '') or ''
                        }
                        for obj in queryset
                    ]
            return []

        elif self.data_source_type == DataSourceType.CHOICES:
            if self.choices:
                return [{'id': v, 'name': str(l), 'code': v} for v, l in self.choices]
            if self.source_field:
                field = model_class._meta.get_field(self.source_field)
                if hasattr(field, 'choices'):
                    return [{'id': v, 'name': str(l), 'code': v} for v, l in field.choices]

        elif self.data_source_type == DataSourceType.CUSTOM:
            method_name = f'_get_{self.param_name}_options'
            if hasattr(model_class, method_name):
                return getattr(model_class, method_name)()

        return []

    # ── Filter lookup ──

    def build_filter_lookup(self, value: Any) -> tuple:
        """Build a Django ORM lookup tuple from a user-supplied value."""

        if self.filter_type == FilterType.TEMP_MIN:
            return f"{self.model_field}__lte", value
        elif self.filter_type == FilterType.TEMP_MAX:
            return f"{self.model_field}__gte", value
        elif self.filter_type == FilterType.MIN:
            return f"{self.model_field}__gte", value
        elif self.filter_type == FilterType.MAX:
            return f"{self.model_field}__lte", value
        elif self.filter_type == FilterType.CONTAINS:
            return f"{self.model_field}__icontains", value
        elif self.filter_type == FilterType.IP_RANK:
            try:
                selected_ip = IpOption.objects.get(id=int(value))
                return f"{self.model_field}__ip_rank__gte", selected_ip.ip_rank
            except (IpOption.DoesNotExist, ValueError, TypeError):
                return None, None
        elif self.filter_type == FilterType.EXD_COMPATIBLE:
            # Принимает: одиночный ExdOption ID (→ get_compatible_ids),
            # список ID, comma-separated строку, или sentinel'ы:
            #   _none_  — общепромышленное (exd отсутствует: exd__isnull=True)
            #   _empty_ — нет совместимых (возвращает пустой queryset)
            # Для одиночного ID — расширяет до всех совместимых (rating__gte).
            try:
                if value == '_none_':
                    return f"{self.model_field}__isnull", True
                if value == '_empty_':
                    return f"{self.model_field}__in", []
                if isinstance(value, list):
                    if not value:
                        return None, None
                    return f"{self.model_field}__in", [int(v) for v in value]
                if isinstance(value, str) and ',' in value:
                    ids = [int(v.strip()) for v in value.split(',') if v.strip()]
                    if ids:
                        return f"{self.model_field}__in", ids
                    return None, None
                else:
                    selected_exd = ExdOption.objects.get(id=int(value))
                    compatible_ids = selected_exd.get_compatible_ids()
                    if not compatible_ids:
                        return None, None
                    return f"{self.model_field}__in", list(compatible_ids)
            except (ExdOption.DoesNotExist, ValueError, TypeError):
                return None, None
        elif self.filter_type == FilterType.FK_CASCADE:
            if not self.cascade_model or not self.cascade_lookup:
                return None, None
            try:
                value_int = int(value)
                if self.cascade_match_fields:
                    child = self.cascade_model.objects.filter(id=value_int).first()
                    if not child:
                        return None, None
                    parent_id = getattr(child, self.cascade_lookup + '_id')
                    if self.source_model and hasattr(self.source_model, 'get_compatible_ids'):
                        parent = self.source_model.objects.get(id=parent_id)
                        parent_ids = parent.get_compatible_ids()
                    else:
                        parent_ids = [parent_id]
                    match_filter = {f'{self.cascade_lookup}__in': parent_ids}
                    for field in self.cascade_match_fields:
                        val = getattr(child, field)
                        if val is not None:
                            match_filter[field] = val
                    child_ids = list(
                        self.cascade_model.objects
                        .filter(**match_filter)
                        .values_list('id', flat=True)
                    )
                else:
                    if hasattr(self.source_model, 'get_compatible_ids'):
                        parent = self.source_model.objects.get(id=value_int)
                        parent_ids = parent.get_compatible_ids()
                    else:
                        parent_ids = [value_int]
                    child_ids = list(
                        self.cascade_model.objects
                        .filter(**{f'{self.cascade_lookup}__in': parent_ids})
                        .values_list('id', flat=True)
                    )
                if not child_ids:
                    return None, None
                return f'{self.model_field}__in', child_ids
            except Exception:
                return None, None
        elif self.filter_type == FilterType.COMPATIBLE_CASCADE:
            if not self.source_model or not self.cascade_model or not self.cascade_lookup:
                return None, None
            try:
                selected = self.cascade_model.objects.get(id=int(value))
                parent = getattr(selected, self.cascade_lookup)
                compatible_type_ids = parent.get_compatible_ids()
                match_filter = {f"{self.cascade_lookup}__in": compatible_type_ids}
                if self.cascade_match_fields:
                    for field in self.cascade_match_fields:
                        val = getattr(selected, field)
                        if val is not None:
                            match_filter[field] = val
                child_ids = list(
                    self.cascade_model.objects
                    .filter(**match_filter)
                    .values_list('id', flat=True)
                )
                if not child_ids:
                    return None, None
                return f"{self.model_field}__in", child_ids
            except Exception:
                return None, None
        elif self.filter_type == FilterType.THREAD_COMPATIBLE:
            try:
                value_int = int(value)
                if self.is_parent_filter:
                    thread_type = ThreadTypes.objects.filter(id=value_int).first()
                    compatible_type_ids = [value_int]
                    child_ids = list(
                        ThreadSize.objects.filter(thread_type__in=compatible_type_ids)
                        .values_list('id', flat=True)
                    )
                else:
                    thread_size = ThreadSize.objects.filter(id=value_int).first()
                    if thread_size and thread_size.thread_type:
                        tt = thread_size.thread_type
                        if thread_size.thread_diameter is None and thread_size.thread_pitch is None:
                            child_ids = [value_int]
                            if child_ids:
                                return f'{self.model_field}__in', child_ids
                            return None, None
                        try:
                            if hasattr(tt, 'get_compatible_ids'):
                                compatible_type_ids = tt.get_compatible_ids()
                            else:
                                compatible_type_ids = [tt.id]
                        except Exception:
                            compatible_type_ids = [tt.id]
                        match_filter = {'thread_type__in': compatible_type_ids}
                        if thread_size.thread_diameter is not None:
                            match_filter['thread_diameter'] = thread_size.thread_diameter
                        if thread_size.thread_pitch is not None:
                            match_filter['thread_pitch'] = thread_size.thread_pitch
                        child_ids = list(
                            ThreadSize.objects.filter(**match_filter).values_list('id', flat=True)
                        )
                    else:
                        return None, None
                if not child_ids:
                    return None, None
                return f'{self.model_field}__in', child_ids
            except Exception:
                return None, None
        elif self.filter_type == FilterType.FUNCTION_COMPATIBLE:
            try:
                value_int = int(value)
                if self.source_model and hasattr(self.source_model, 'get_compatible_ids'):
                    func = self.source_model.objects.filter(id=value_int).first()
                    if func:
                        ids = func.get_compatible_ids()
                        return f'{self.model_field}__in', ids
                return f'{self.model_field}', value_int
            except Exception:
                return None, None

        return f"{self.model_field}", value

    # ── Exact/Compatible split ──

    def supports_split(self) -> bool:
        """True if this filter can distinguish exact vs compatible matches."""
        return self.filter_type in self.SPLITTABLE_TYPES

    @staticmethod
    def _get_nested_attr(obj, path: str):
        """Traverse nested attributes via __ (e.g. 'body__max_work_torque')."""
        parts = path.split('__')
        value = obj
        for part in parts:
            value = getattr(value, part, None)
            if value is None:
                return None
        return value

    def classify_match(self, obj, requested_value):
        """
        Classify one object as 'exact', 'compatible', or None.

        obj is already in the filtered queryset (it passed the filter).
        requested_value is the raw value from the user's request.
        """
        try:
            requested_num = float(requested_value)
        except (ValueError, TypeError):
            return None

        # ── FK-based: compare by ID ──
        if self.filter_type in (
            FilterType.EXD_COMPATIBLE, FilterType.THREAD_COMPATIBLE,
            FilterType.FUNCTION_COMPATIBLE, FilterType.IP_RANK,
        ):
            fk_field = f"{self.model_field}_id"
            obj_fk_id = self._get_nested_attr(obj, fk_field)
            try:
                requested_id = int(requested_value)
            except (ValueError, TypeError):
                return None
            if obj_fk_id is None:
                return None
            return 'exact' if obj_fk_id == requested_id else 'compatible'

        # ── Value-based: compare by field value (with float tolerance) ──
        EPS = 1e-9

        if self.filter_type in (FilterType.TEMP_MIN, FilterType.MIN):
            actual = self._get_nested_attr(obj, self.model_field)
            if actual is None:
                return None
            try:
                return 'exact' if abs(float(actual) - requested_num) < EPS else 'compatible'
            except (ValueError, TypeError):
                return 'compatible'

        if self.filter_type in (FilterType.TEMP_MAX, FilterType.MAX):
            actual = self._get_nested_attr(obj, self.model_field)
            if actual is None:
                return None
            try:
                return 'exact' if abs(float(actual) - requested_num) < EPS else 'compatible'
            except (ValueError, TypeError):
                return 'compatible'

        return None