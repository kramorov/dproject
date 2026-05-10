# core/models/smart_catalog_mixin.py

from typing import Dict, List, Any, Optional, Type
from enum import Enum
from django.db import models
from django.db.models import QuerySet, Q
from django.core.exceptions import FieldDoesNotExist

from params.exd_models import ExdOption
from params.models import IpOption

class FilterType(Enum):
    """Типы фильтров"""
    EXACT = "exact"  # точное совпадение
    CONTAINS = "icontains"  # содержит
    MIN = "gte"  # больше или равно
    MAX = "lte"  # меньше или равно
    CHOICE = "choice"  # выбор из списка
    BOOLEAN = "boolean"  # да/нет
    TEMP_MIN = "temp_min"  # минимальная температура
    TEMP_MAX = "temp_max"  # максимальная температура
    IP_RANK = "ip_rank"  # ранг IP (>= выбранного)
    EXD_COMPATIBLE = "exd_compatible"  # поиск совместимых ExdOption (M2M или FK)
    FK_CASCADE = "fk_cascade" # ← каскадный FK: родитель → потомки → __in
    COMPATIBLE_CASCADE = "compatible_cascade" #По аналогии с EXD_COMPATIBLE, но для каскадных FK с учётом совместимости:


class DataSourceType(Enum):
    """Тип источника данных для опций фильтра
        Тип	            Что получаем	                    Производительность
        GLOBAL_MODEL	Все типы сигналов из справочника	Быстро, но много лишних
        FIELD_VALUES	Только используемые (уникальные)	Быстро, только нужные
        FOREIGN_KEY	    Все связанные (через цепочку)	    Средне
        CUSTOM	        Полный контроль	                    Зависит от реализации"""

    FIELD_VALUES = "field_values"  # уникальные значения из поля (простые типы)
    UNIQUE_FIELD_VALUES = "unique_field_values"  # уникальные значения из поля с получением объектов (для FK)
    FOREIGN_KEY = "foreign_key"  # все записи из связанной модели
    GLOBAL_MODEL = "global_model"  # все записи из глобального справочника
    CHOICES = "choices"  # из choices поля
    CUSTOM = "custom"  # кастомный метод


class FilterDefinition:
    """
    Единое определение фильтра

    Примеры:

    1. Точное совпадение по ForeignKey:
    FilterDefinition(
        param_name='model_line_id',
        model_field='model_line',
        filter_type=FilterType.EXACT,
        data_source_type=DataSourceType.FOREIGN_KEY,
        label='Серия'
    )

    2. Температура (прямое поле):
    FilterDefinition(
        param_name='work_temp_min',
        model_field='work_temp_min',
        filter_type=FilterType.TEMP_MIN,
        data_source_type=DataSourceType.FIELD_VALUES,
        label='Температура от'
    )

    3. IP ранг (связанное поле):
    FilterDefinition(
        param_name='ip_id',
        model_field='ip',
        filter_type=FilterType.IP_RANK,
        data_source_type=DataSourceType.GLOBAL_MODEL,
        source_model=IpOption,
        label='IP'
    )

    4. Бренд через серию:
    FilterDefinition(
        param_name='brand_id',
        model_field='model_line__brand',
        filter_type=FilterType.EXACT,
        data_source_type=DataSourceType.FOREIGN_KEY,
        label='Бренд'
    )
    # Для M2M:
    FilterDefinition(
        param_name='exd_id',
        model_field='exd',  # ManyToManyField
        filter_type=FilterType.EXD_COMPATIBLE,
        data_source_type=DataSourceType.CUSTOM,
        label='Взрывозащита',
    )

    # Для ForeignKey:
    FilterDefinition(
        param_name='exd_id',
        model_field='exd_option',  # ForeignKey
        filter_type=FilterType.EXD_COMPATIBLE,
        data_source_type=DataSourceType.CUSTOM,
        label='Взрывозащита',
    )
    """


    def __init__(
            self,
            param_name: str,  # имя параметра в запросе
            model_field: str,  # путь к полю в модели (поддерживает __)
            filter_type: FilterType,  # тип фильтра
            data_source_type: DataSourceType,  # откуда брать опции
            label: str = None,  # отображаемое название
            order: int = 0,  # порядок сортировки
            source_model: Type[models.Model] = None,  # для GLOBAL_MODEL
            source_field: str = None,  # для CHOICES - поле с choices
            choices: List[tuple] = None,  # для CHOICES - список вариантов
            active_only: bool = True,  # только активные
            order_by: str = 'name',  # сортировка опций
            cascade_model: Type[models.Model] = None ,  # ← для FK_CASCADE
            cascade_lookup: str = None ,  # ← для FK_CASCADE
            cascade_match_fields: List[str] = None ,  # ← для FK_CASCADE поля для сопоставления (диаметр, шаг)
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
        self.cascade_lookup = cascade_lookup
        self.cascade_match_fields = cascade_match_fields or []

    def get_options(self, model_class) -> List[Dict]:
        """Получить опции для фильтра на основе data_source_type"""

        if self.data_source_type == DataSourceType.FIELD_VALUES:
            # Уникальные значения из поля
            values = model_class.objects.filter(
                **{f"{self.model_field}__isnull": False}
            ).values_list(self.model_field, flat=True).distinct().order_by(self.model_field)
            return [
                {'id': v, 'name': str(v), 'code': ''}
                for v in values if v is not None
            ]
        elif self.data_source_type == DataSourceType.UNIQUE_FIELD_VALUES:
            # Уникальные значения из поля (с получением объектов для ForeignKey)
            values = model_class.objects.filter(
                **{f"{self.model_field}__isnull": False}
            ).values_list(self.model_field, flat=True).distinct()

            # Проверяем, является ли поле ForeignKey
            try:
                parts = self.model_field.split('__')
                rel_model = model_class
                for part in parts:
                    field = rel_model._meta.get_field(part)
                    if field.is_relation:
                        rel_model = field.remote_field.model

                # Получаем объекты по ID (только те, что используются)
                objects = rel_model.objects.filter(id__in=values)
                if self.active_only and hasattr(rel_model, 'is_active'):
                    objects = objects.filter(is_active=True)

                # Сортировка: если есть sorting_order - используем его, иначе order_by
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
                # Если не ForeignKey - возвращаем простые значения
                return [
                    {'id': v, 'name': str(v), 'code': ''}
                    for v in values if v is not None
                ]
        elif self.data_source_type == DataSourceType.FOREIGN_KEY:
            # Все записи из связанной модели
            try:
                parts = self.model_field.split('__')
                rel_model = model_class
                for part in parts:
                    field = rel_model._meta.get_field(part)
                    if field.is_relation:
                        rel_model = field.remote_field.model

                queryset = rel_model.objects.all()

                if self.active_only and hasattr(rel_model, 'is_active'):
                    queryset = queryset.filter(is_active=True)

                # Сортировка: если есть sorting_order - используем его, иначе order_by
                if hasattr(rel_model, 'sorting_order'):
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
            except (FieldDoesNotExist, AttributeError):
                return []

        elif self.data_source_type == DataSourceType.GLOBAL_MODEL:
            # Все записи из глобальной модели
            if self.source_model:
                queryset = self.source_model.objects.all()
                if self.active_only and hasattr(self.source_model, 'is_active'):
                    queryset = queryset.filter(is_active=True)
                    # Сортировка: если есть sorting_order - используем его, иначе order_by
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
            # Из choices
            if self.choices:
                return [{'id': v, 'name': str(l), 'code': v} for v, l in self.choices]
            if self.source_field:
                field = model_class._meta.get_field(self.source_field)
                if hasattr(field, 'choices'):
                    return [{'id': v, 'name': str(l), 'code': v} for v, l in field.choices]

        elif self.data_source_type == DataSourceType.CUSTOM:
            # Кастомный метод: _get_{param_name}_options
            method_name = f'_get_{self.param_name}_options'
            if hasattr(model_class, method_name):
                return getattr(model_class, method_name)()

        return []

    def build_filter_lookup(self, value: Any) -> tuple:
        """Построить lookup для фильтрации"""

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
            # Для IP нужно получить ранг выбранной записи
            try:
                selected_ip = IpOption.objects.get(id=int(value))
                return f"{self.model_field}__ip_rank__gte", selected_ip.ip_rank
            except (IpOption.DoesNotExist, ValueError, TypeError):
                return None, None
        elif self.filter_type == FilterType.EXD_COMPATIBLE:
            print(f"DEBUG: EXD_COMPATIBLE filter with value={value}, type={type(value)}")
            try:
                if isinstance(value, list):
                    # Уже список ID совместимых ExdOption
                    if not value:  # Пустой список
                        print(f"  Empty list - returning None")
                        return None, None
                    print(f"  Processing list of IDs: {value}")
                    return f"{self.model_field}__in", value
                else:
                    # Один ID - находим совместимые
                    selected_exd = ExdOption.objects.get(id=int(value))
                    compatible_ids = selected_exd.get_compatible_ids()
                    if not compatible_ids:  # Пустое множество
                        return None, None
                    print(f"  Compatible IDs: {compatible_ids}")
                    return f"{self.model_field}__in", list(compatible_ids)
            except (ExdOption.DoesNotExist, ValueError, TypeError) as e:
                print(f"  ERROR: {e}")
                return None, None

        elif self.filter_type == FilterType.FK_CASCADE:
            if not self.cascade_model or not self.cascade_lookup :
                return None , None
            try :
                value_int = int(value)

                # Определяем: value — это ID cascade_model или source_model?
                child = self.cascade_model.objects.filter(id=value_int).first()

                if child :
                    # --- Режим «от потомка»: value = ThreadSize.id ---
                    # 1. Находим его родителя (ThreadTypes)
                    parent_id = getattr(child , self.cascade_lookup + '_id')
                    # 2. Совместимые родители
                    if self.source_model and hasattr(self.source_model , 'get_compatible_ids') :
                        parent = self.source_model.objects.get(id=parent_id)
                        parent_ids = parent.get_compatible_ids()
                    else :
                        parent_ids = [parent_id]
                        # 3. Ищем потомков: совместимый тип + совпадение по cascade_match_fields
                    match_filter = {f'{self.cascade_lookup}__in' : parent_ids}
                    if self.cascade_match_fields :
                        for field in self.cascade_match_fields :
                            val = getattr(child , field)
                            if val is not None :
                                match_filter[field] = val
                    child_ids = list(
                        self.cascade_model.objects
                        .filter(**match_filter)
                        .values_list('id' , flat=True)
                    )
                elif self.source_model :
                    # --- Режим «от родителя»: value = ThreadTypes.id ---
                    if hasattr(self.source_model , 'get_compatible_ids') :
                        parent = self.source_model.objects.get(id=value_int)
                        parent_ids = parent.get_compatible_ids()
                    else :
                        parent_ids = [value_int]
                    child_ids = list(
                        self.cascade_model.objects
                        .filter(**{f'{self.cascade_lookup}__in' : parent_ids})
                        .values_list('id' , flat=True)
                    )
                else :
                    return None , None
                if not child_ids :
                        return None , None
                return f'{self.model_field}__in' , child_ids

            except Exception :
                return None , None

        elif self.filter_type == FilterType.COMPATIBLE_CASCADE :
            # value = ID родителя (ThreadTypes)
            # source_model = родитель (ThreadTypes) — должен иметь get_compatible_ids()
            # cascade_model = потомок (ThreadSize)
            # cascade_lookup = поле в потомке → родитель (thread_type)
            if not self.source_model or not self.cascade_model or not self.cascade_lookup :
                return None , None
            try :
                selected = self.cascade_model.objects.get(id=int(value))
                parent = getattr(selected , self.cascade_lookup)  # ThreadTypes-объект
                compatible_type_ids = parent.get_compatible_ids()
                # Строим фильтр: тип в совместимых + совпадение по диаметру/шагу
                match_filter = {f"{self.cascade_lookup}__in" : compatible_type_ids}
                if self.cascade_match_fields :
                    for field in self.cascade_match_fields :
                        val = getattr(selected , field)
                        if val is not None :
                            match_filter[field] = val

                child_ids = list(
                    self.cascade_model.objects
                    .filter(**match_filter)
                    .values_list('id' , flat=True)
                )
                if not child_ids :
                    return None , None
                return f"{self.model_field}__in" , child_ids
            except Exception :
                return None , None


            # EXACT, CHOICE, BOOLEAN и прочие — прямое совпадение
        return f"{self.model_field}", value


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
        """Фильтрация на основе FILTER_DEFINITIONS"""
        print(f"DEBUG filter_by_params: received params={params}")
        queryset = cls.objects.all()

        # Оптимизация
        if cls.SELECT_RELATED_FIELDS:
            queryset = queryset.select_related(*cls.SELECT_RELATED_FIELDS)
        if cls.PREFETCH_FIELDS:
            queryset = queryset.prefetch_related(*cls.PREFETCH_FIELDS)

        filters_applied = {}

        # Применяем фильтры
        for fd in cls.FILTER_DEFINITIONS:
            value = params.get(fd.param_name)
            print(f"DEBUG: Applying filter {fd.param_name}={value}")
            if value is None or value == '' or value == 'all':
                continue

            lookup, converted_value = fd.build_filter_lookup(value)

            if lookup and converted_value is not None:
                queryset = queryset.filter(**{lookup: converted_value})
                filters_applied[fd.param_name] = value
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
        for obj in queryset:
            try:
                data.append(obj.to_dict())
            except Exception as e:
                print(f"Error serializing {obj.__class__.__name__} id={obj.id}: {e}")

        return {
            'data': data,
            'total': total,
            'filters_applied': filters_applied,
            'limit': limit,
            'offset': offset
        }

    def to_dict(self) -> Dict[str, Any]:
        """Должен быть переопределен"""
        raise NotImplementedError(f"{self.__class__.__name__} должен реализовать to_dict()")