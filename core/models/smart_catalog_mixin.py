# core/models/smart_catalog_mixin.py

from typing import Dict, List, Any, Optional
from django.db import models
from django.db.models import QuerySet, Q

from core.models.filter_definition import FilterType, DataSourceType, FilterDefinition


class SmartCatalogMixin(models.Model):
    """
    Улучшенный миксин для фильтрации каталоговых моделей
    Использует декларативную конфигурацию FILTER_DEFINITIONS
    """

    class Meta:
        abstract = True

    # ========== КОНФИГУРАЦИЯ ==========
    FILTER_DEFINITIONS: List[FilterDefinition] = []
    SEARCH_FIELDS: List[str] = ['code', 'name', 'description']
    SELECT_RELATED_FIELDS: List[str] = []
    PREFETCH_FIELDS: List[str] = []

    def get_cert_docs_list(self):
        """Список сертификатов, привязанных к этой записи через cert_docs M2M."""
        if hasattr(self, 'cert_docs'):
            return list(self.cert_docs.all())
        return []

    def get_cert_docs_description(self) -> str:
        """
        Строка для шаблона описания вида:
        'ТР ТС 012  АВ-001  Срок: 2024-01-01 до 2026-01-01; Декларация  ДК-002  Срок: 2025-06-01 до 2027-06-01'

        Если сертификатов нет — пустая строка.
        """
        certs = self.get_cert_docs_list()
        if not certs:
            return ''

        parts = []
        for c in certs:
            variety = c.cert_variety.name if c.cert_variety else ''
            code = c.code or ''
            date_from = c.valid_from.isoformat() if c.valid_from else '...'
            date_until = c.valid_until.isoformat() if c.valid_until else '...'
            parts.append(f'{variety}  {code}  Срок: {date_from} до {date_until}')

        return '; '.join(parts)

    @classmethod
    def get_filter_options(cls) -> Dict[str, List[Dict]]:
        """Автоматически собрать все опции из FILTER_DEFINITIONS"""
        result = {}

        for fd in cls.FILTER_DEFINITIONS:
            if fd.data_source_type != DataSourceType.CUSTOM:
                options = fd.get_options(cls)
                if options:
                    result[fd.param_name] = options

        return result

    @classmethod
    def get_cascade_options(cls , parent_param_name: str , parent_value: Any) -> List[Dict] :
        """
        Опции для дочернего дропдауна, отфильтрованные по родителю.
        Использует cascade_model и cascade_lookup из FilterDefinition родителя.
        Пример: get_cascade_options('thread_type_id', 3) → все ThreadSize с thread_type=3
        """
        for fd in cls.FILTER_DEFINITIONS :
            if fd.param_name == parent_param_name and fd.cascade_model and fd.cascade_lookup :
                try :
                    parent_id = int(parent_value)
                    if fd.source_model and hasattr(fd.source_model , 'get_compatible_ids') :
                        parent = fd.source_model.objects.get(id=parent_id)
                        parent_ids = parent.get_compatible_ids()
                    else :
                        parent_ids = [parent_id]

                    qs = fd.cascade_model.objects.filter(
                        **{f'{fd.cascade_lookup}__in' : parent_ids}
                    )
                    if hasattr(fd.cascade_model , 'is_active') :
                        qs = qs.filter(is_active=True)
                    if hasattr(fd.cascade_model , 'sorting_order') :
                        qs = qs.order_by('sorting_order' , 'name')
                    else :
                        qs = qs.order_by('name')
                    return [
                        {'id' : obj.id , 'name' : str(obj) , 'code' : getattr(obj , 'code' , '') or ''}
                        for obj in qs
                    ]
                except Exception :
                    return []
        return []

    @classmethod
    def _apply_text_search(cls, queryset: QuerySet, search_text: str) -> QuerySet:
        """Поиск по тексту"""
        if not search_text:
            return queryset
        if not cls.SEARCH_FIELDS:
            return queryset

        q_objects = Q()
        for field in cls.SEARCH_FIELDS:
            q_objects |= Q(**{f"{field}__icontains": search_text})
        return queryset.filter(q_objects)

    @classmethod
    def filter_by_params(cls, params: Dict) -> Dict:
        """
        Фильтрация на основе FILTER_DEFINITIONS.

        NOTE: только для Streamlit-страниц (pages/*.py).
        Для production API использовать apply_filters_and_split().
        """
        print(f"DEBUG filter_by_params: received params={params}")
        queryset = cls.objects.all()

        # Оптимизация
        if cls.SELECT_RELATED_FIELDS:
            queryset = queryset.select_related(*cls.SELECT_RELATED_FIELDS)
        if cls.PREFETCH_FIELDS:
            queryset = queryset.prefetch_related(*cls.PREFETCH_FIELDS)

        filters_applied = {}

        # Применяем фильтры
        split_fk_id = None  # точный ID для разделения (thread / function)
        split_fk_field = None  # имя поля (thread_id / function_id)
        for fd in cls.FILTER_DEFINITIONS:
            value = params.get(fd.param_name)
            print(f"DEBUG: Applying filter {fd.param_name}={value}")
            if value is None or value == '' or value == 'all':
                continue

            lookup, converted_value = fd.build_filter_lookup(value)

            if lookup and converted_value is not None:
                queryset = queryset.filter(**{lookup: converted_value})
                filters_applied[fd.param_name] = value
                # Запомнить точный ID для разделения выдачи (thread / function)
                if fd.filter_type in (FilterType.THREAD_COMPATIBLE, FilterType.FUNCTION_COMPATIBLE) and not fd.is_parent_filter:
                    split_fk_id = int(value)
                    split_fk_field = fd.model_field + '_id'  # thread → thread_id, function → function_id
                print(f"  lookup={lookup}, converted={converted_value}")
            else:
                print(f" SmartCatalogMixin fd.build_filter_lookup(value) return None")

        # Поиск
        search_text = params.get('search', '')
        if search_text:
            queryset = cls._apply_text_search(queryset, search_text)
            filters_applied['search'] = search_text

        # Активность
        is_active = params.get('is_active')
        if is_active is not None and is_active != '':
            if is_active in ['true', 'True', '1', 1, True]:
                queryset = queryset.filter(is_active=True)
                filters_applied['is_active'] = True
            elif is_active in ['false', 'False', '0', 0, False]:
                queryset = queryset.filter(is_active=False)
                filters_applied['is_active'] = False

        # Пагинация
        total = queryset.count()
        limit = int(params.get('limit', 100))
        offset = int(params.get('offset', 0))
        queryset = queryset[offset:offset + limit]

        # Сериализация
        data = []
        compatible_data = []
        for obj in queryset:
            try:
                item = obj.to_dict()
                if split_fk_id is not None and split_fk_field:
                    obj_fk_id = getattr(obj, split_fk_field, None)
                    if obj_fk_id == split_fk_id:
                        data.append(item)
                    else:
                        compatible_data.append(item)
                else:
                    data.append(item)
            except Exception as e:
                print(f"Error serializing {obj.__class__.__name__} id={obj.id}: {e}")

        result = {
            'data': data,
            'total': total,
            'filters_applied': filters_applied,
            'limit': limit,
            'offset': offset
        }
        if split_fk_id is not None:
            result['compatible_data'] = compatible_data
            result['exact_total'] = len(data)
            result['compatible_total'] = len(compatible_data)
        return result

    @classmethod
    def apply_filters_and_split(
        cls,
        params: Dict,
        filter_definitions: List,
        base_queryset: QuerySet = None,
        split_mode: str = 'auto',
        serializer=None,
    ) -> Dict:
        """
        Unified filtering + optional exact/compatible split.

        Args:
            params: Request query params (limit, offset, search,
                    show_compatible, and filter values).
            filter_definitions: The FilterDefinition objects to apply
                                (from a FilterSet).
            base_queryset: Optional pre-filtered queryset (visibility
                           scope already applied).
            split_mode: 'auto' — split if show_compatible=true and a
                        splittable filter is active; 'off' — never split.

        Returns:
            {
                data: [...], total: int, filters_applied: {...},
                # Only when split:
                compatible_data: [...], exact_total: int,
                compatible_total: int, split_filter: str, split_value: any,
            }
        """
        queryset = base_queryset if base_queryset is not None else cls.objects.all()

        filters_applied = {}

        # ── Track the "primary" splittable filter ──
        split_fd: Optional[FilterDefinition] = None
        split_raw_value = None

        for fd in filter_definitions:
            value = params.get(fd.param_name)
            if value is None or value == '' or value == 'all':
                continue

            lookup, converted = fd.build_filter_lookup(value)
            if lookup and converted is not None:
                queryset = queryset.filter(**{lookup: converted})
                filters_applied[fd.param_name] = value

                # Remember the LAST splittable filter for classification
                if fd.supports_split():
                    split_fd = fd
                    split_raw_value = value

        # ── Text search ──
        search_text = params.get('search', '').strip()
        if search_text:
            queryset = cls._apply_text_search(queryset, search_text)
            filters_applied['search'] = search_text

        # ── Pagination ──
        total = queryset.count()
        limit = min(int(params.get('limit', 24)), 200)
        offset = max(int(params.get('offset', 0)), 0)
        qs_page = queryset[offset:offset + limit]

        # ── Serializer ──
        if serializer is None:
            serializer = (lambda obj: obj.to_values_dict()) if hasattr(cls, 'to_values_dict') else (lambda obj: obj.to_dict())

        show_compatible = params.get('show_compatible', '').lower() in ('true', '1')
        do_split = (
            split_mode == 'auto'
            and show_compatible
            and split_fd is not None
            and split_raw_value is not None
        )

        data = []
        compatible_data = []

        for obj in qs_page:
            try:
                item = serializer(obj)
            except Exception:
                item = {'id': obj.id}

            if do_split:
                classification = split_fd.classify_match(obj, split_raw_value)
                if classification == 'exact':
                    data.append(item)
                else:
                    compatible_data.append(item)
            else:
                data.append(item)

        result: Dict[str, Any] = {
            'data': data,
            'total': total,
            'filters_applied': filters_applied,
            'limit': limit,
            'offset': offset,
        }

        if do_split:
            result['compatible_data'] = compatible_data
            result['exact_count'] = len(data)
            result['compatible_count'] = len(compatible_data)
            result['split_filter'] = split_fd.param_name
            result['split_value'] = split_raw_value
            result['split_page_note'] = 'exact_count/compatible_count are per-page (not full totals)'

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Должен быть переопределен"""
        raise NotImplementedError(f"{self.__class__.__name__} должен реализовать to_dict()")