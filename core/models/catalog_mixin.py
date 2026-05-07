#core/models/catalog_mixin.py
from typing import Dict, List, Any, Optional, Callable, Type

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import QuerySet, Q


class FilterFieldConfig:
    """Конфигурация одного поля фильтрации"""

    def __init__(
            self,
            param_name: str,
            model_field: str,
            filter_type: str = 'exact',
            value_converter: Optional[Callable] = None,
            is_foreign_key: bool = False,
            is_related_field: bool = False,
            is_ip_filter: bool = False,
            related_path: str = None
    ):
        self.param_name = param_name
        self.model_field = model_field
        self.filter_type = filter_type
        self.value_converter = value_converter
        self.is_foreign_key = is_foreign_key
        self.is_related_field = is_related_field
        self.related_path = related_path or model_field
        self.is_ip_filter = is_ip_filter

    def apply_filter(self, queryset: QuerySet, value: Any) -> QuerySet:
        """Применяет фильтр к queryset"""
        if value is None or value == '' or value == 'all':
            return queryset

        # Специальная обработка для IP фильтра
        if self.is_ip_filter:
            # value - это ID выбранного IP
            from params.models import IpOption

            try:
                selected_ip = IpOption.objects.get(id=int(value))
                # Берем ранг выбранного IP
                rank_value = selected_ip.ip_rank

                # Фильтруем по рангу >= выбранного
                filter_lookup = f"{self.related_path}__{self.model_field}__gte"
                return queryset.filter(**{filter_lookup: rank_value})
            except (IpOption.DoesNotExist, ValueError, TypeError):
                return queryset
        if self.value_converter:
            try:
                value = self.value_converter(value)
            except (ValueError, TypeError):
                return queryset

        if self.is_related_field:
            filter_lookup = f"{self.related_path}__{self.filter_type}" if self.filter_type != 'exact' else self.related_path
        else:
            filter_lookup = f"{self.model_field}__{self.filter_type}" if self.filter_type != 'exact' else self.model_field

        return queryset.filter(**{filter_lookup: value})


class CatalogFilterMixin(models.Model):
    """
    Миксин для фильтрации каталоговых моделей
    Использует конфигурационный подход
    """

    class Meta:
        abstract = True

    # Конфигурация фильтров - переопределить в дочерней модели
    FILTER_CONFIG: List[FilterFieldConfig] = []

    # Конфигурация ManyToMany фильтров
    M2M_FILTER_CONFIG: List[Dict] = []

    # Поля для поиска по тексту (code, name и т.д.)
    SEARCH_FIELDS: List[str] = ['code']

    # Поля для select_related оптимизации
    SELECT_RELATED_FIELDS: List[str] = []

    # Поля для prefetch_related оптимизации
    PREFETCH_FIELDS: List[str] = []

    @classmethod
    def _get_numeric_field_range(cls, field_path: str) -> Dict:
        """
        Получить диапазон для числового поля (IntegerField, DecimalField, FloatField)
        Возвращает: {'min': value, 'max': value} или {'min': None, 'max': None}
        """

        # Проверяем, что путь не ведет к ManyToMany полю
        if cls._is_m2m_field_path(field_path):
            return {'min': None, 'max': None}

        try:
            # Получаем поле
            model = cls
            parts = field_path.split('__')

            for part in parts:
                field = model._meta.get_field(part)
                if field.is_relation and not field.many_to_many:
                    model = field.remote_field.model
                elif field.many_to_many:
                    return {'min': None, 'max': None}

            # Проверяем, что поле числовое
            final_field = model._meta.get_field(parts[-1])
            if not isinstance(final_field, (
                    models.IntegerField, models.DecimalField, models.FloatField,
                    models.PositiveIntegerField, models.PositiveSmallIntegerField,
                    models.SmallIntegerField
            )):
                return {'min': None, 'max': None}

        except (FieldDoesNotExist, AttributeError, IndexError):
            return {'min': None, 'max': None}

        # Получаем значения
        values = cls.objects.filter(
            **{f"{field_path}__isnull": False}
        ).values_list(field_path, flat=True)

        if values:
            try:
                return {
                    'min': float(min(values)),
                    'max': float(max(values)),
                }
            except (TypeError, ValueError):
                return {'min': None, 'max': None}

        return {'min': None, 'max': None}

    @classmethod
    def _get_text_field_unique_values(cls, field_path: str) -> List[Dict]:
        """
        Получить уникальные значения для текстового/choice поля
        Возвращает: [{'id': value, 'name': value, 'code': ''}, ...]
        """

        # Проверяем, что путь не ведет к ManyToMany полю
        if cls._is_m2m_field_path(field_path):
            return []

        try:
            # Получаем поле
            model = cls
            parts = field_path.split('__')

            for part in parts:
                field = model._meta.get_field(part)
                if field.is_relation and not field.many_to_many:
                    model = field.remote_field.model
                elif field.many_to_many:
                    return []

            # Проверяем, что поле текстовое или choice
            final_field = model._meta.get_field(parts[-1])
            is_text_or_choice = isinstance(final_field, (
                models.CharField, models.TextField,
                models.EmailField, models.URLField,
                models.SlugField
            )) or hasattr(final_field, 'choices')

            if not is_text_or_choice:
                return []

        except (FieldDoesNotExist, AttributeError, IndexError):
            return []

        # Получаем уникальные значения
        values = cls.objects.filter(
            **{f"{field_path}__isnull": False}
        ).values_list(field_path, flat=True).distinct().order_by(field_path)

        result = []
        for value in values:
            if value:
                # Если поле с choices, берем display name
                display_name = cls._get_choice_display(field_path, value)
                result.append({
                    'id': value,
                    'name': display_name,
                    'code': value
                })

        return result

    @classmethod
    def _get_choice_display(cls, field_path: str, value: Any) -> str:
        """Получить отображаемое имя для choice поля"""
        try:
            parts = field_path.split('__')
            model = cls

            for part in parts:
                field = model._meta.get_field(part)
                if field.is_relation and not field.many_to_many:
                    model = field.remote_field.model

            final_field = model._meta.get_field(parts[-1])
            if hasattr(final_field, 'choices') and final_field.choices:
                choice_dict = dict(final_field.choices)
                return choice_dict.get(value, str(value))
        except (AttributeError, FieldDoesNotExist):
            pass

        return str(value)

    @classmethod
    def _get_boolean_field_options(cls, field_path: str) -> List[Dict]:
        """
        Получить опции для булевого поля
        Возвращает: [{'id': 'true', 'name': 'Да'}, {'id': 'false', 'name': 'Нет'}]
        """

        try:
            parts = field_path.split('__')
            model = cls

            for part in parts:
                field = model._meta.get_field(part)
                if field.is_relation and not field.many_to_many:
                    model = field.remote_field.model

            final_field = model._meta.get_field(parts[-1])
            if isinstance(final_field, models.BooleanField):
                return [
                    {'id': 'true', 'name': 'Да', 'code': 'true'},
                    {'id': 'false', 'name': 'Нет', 'code': 'false'},
                ]
        except (FieldDoesNotExist, AttributeError, IndexError):
            pass

        return []

    @classmethod
    def _get_date_field_range(cls, field_path: str) -> Dict:
        """
        Получить диапазон для дат/даты-времени
        Возвращает: {'min': 'YYYY-MM-DD', 'max': 'YYYY-MM-DD'} или {'min': None, 'max': None}
        """

        if cls._is_m2m_field_path(field_path):
            return {'min': None, 'max': None}

        try:
            parts = field_path.split('__')
            model = cls

            for part in parts:
                field = model._meta.get_field(part)
                if field.is_relation and not field.many_to_many:
                    model = field.remote_field.model

            final_field = model._meta.get_field(parts[-1])
            is_date_field = isinstance(final_field, (models.DateField, models.DateTimeField))

            if not is_date_field:
                return {'min': None, 'max': None}

        except (FieldDoesNotExist, AttributeError, IndexError):
            return {'min': None, 'max': None}

        # Получаем минимальную и максимальную дату
        from django.db.models import Min, Max

        result = cls.objects.aggregate(
            min_date=Min(field_path),
            max_date=Max(field_path)
        )

        return {
            'min': result['min_date'].isoformat() if result['min_date'] else None,
            'max': result['max_date'].isoformat() if result['max_date'] else None,
        }

    @classmethod
    def _get_foreign_key_options(cls, field_path: str, active_only: bool = True) -> List[Dict]:
        """
        Получить опции для ForeignKey поля
        Возвращает: [{'id': 1, 'name': '...', 'code': '...'}, ...]
        """
        from django.db.models import ForeignKey

        try:
            # Получаем queryset с select_related для оптимизации
            queryset = cls.objects.select_related(field_path.replace('__', '_'))

            # Получаем уникальные ID связанных объектов
            ids = queryset.values_list(field_path, flat=True).distinct()

            # Определяем модель назначения
            parts = field_path.split('__')
            model = cls
            for part in parts:
                field = model._meta.get_field(part)
                if isinstance(field, ForeignKey):
                    model = field.remote_field.model

            # Получаем объекты
            objects = model.objects.filter(id__in=ids)

            if active_only and hasattr(model, 'is_active'):
                objects = objects.filter(is_active=True)

            return [
                {
                    'id': obj.id,
                    'name': getattr(obj, 'name', str(obj)),
                    'code': getattr(obj, 'code', '') or ''
                }
                for obj in objects.order_by('name')
            ]

        except Exception as e:
            return dict('Список пустой - для отладки','проверь _get_foreign_key_options в CatalogFilterMixin') #[]

    @classmethod
    def _is_m2m_field_path(cls, field_path: str) -> bool:
        """
        Проверяет, содержит ли путь к полю ManyToMany связь
        """
        try:
            parts = field_path.split('__')
            model = cls

            for part in parts:
                field = model._meta.get_field(part)
                if field.many_to_many:
                    return True
                if field.is_relation:
                    model = field.remote_field.model
            return False
        except (FieldDoesNotExist, AttributeError):
            return True

    @classmethod
    def _get_m2m_options(cls, field_path: str, active_only: bool = True) -> List[Dict]:
        """
        Получить опции для ManyToMany поля
        """
        if not field_path:
            return []

        try:
            parts = field_path.split('__')
            model = cls

            for i, part in enumerate(parts):
                if not part:  # Проверка на пустую часть
                    return []

                field = model._meta.get_field(part)
                if field.many_to_many:
                    related_model = field.remote_field.model
                    queryset = related_model.objects.all()

                    if active_only and hasattr(related_model, 'is_active'):
                        queryset = queryset.filter(is_active=True)

                    return [
                        {
                            'id': obj.id,
                            'name': getattr(obj, 'name', str(obj)),
                            'code': getattr(obj, 'code', '') or ''
                        }
                        for obj in queryset.order_by('name')
                    ]
                if field.is_relation:
                    model = field.remote_field.model
        except (FieldDoesNotExist, AttributeError, IndexError) as e:
            # Логируем ошибку для отладки
            print(f"Error in _get_m2m_options for path '{field_path}': {e}")
            return []

        return []

    @classmethod
    def get_distinct_values(cls, field_name: str, active_only: bool = True) -> List[Dict]:
        """
        Универсальный метод - работает для любой модели
        """
        try:
            field = cls._meta.get_field(field_name)
        except FieldDoesNotExist:
            if '__' in field_name:
                return cls._get_distinct_values_related(field_name, active_only)
            raise

        # Для ForeignKey полей
        if field.many_to_one:
            related_model = field.remote_field.model

            related_ids = cls.objects.filter(
                **{f"{field_name}__isnull": False}
            ).values_list(field_name, flat=True).distinct().order_by(field_name)

            queryset = related_model.objects.filter(id__in=related_ids)

            if active_only and hasattr(related_model, 'is_active'):
                queryset = queryset.filter(is_active=True)

            queryset = queryset.order_by('name')

            return [
                {
                    'id': obj.id,
                    'name': getattr(obj, 'name', str(obj)),
                    'code': getattr(obj, 'code', '') or ''
                }
                for obj in queryset
            ]

        # Для обычных полей
        values = cls.objects.filter(
            **{f"{field_name}__isnull": False}
        ).values_list(field_name, flat=True).distinct().order_by(field_name)

        return [
            {'id': v, 'name': str(v), 'code': ''}
            for v in values if v is not None
        ]

    @classmethod
    def _get_distinct_values_related(cls, field_path: str, active_only: bool = True) -> List[Dict]:
        """Для связанных полей через __"""
        parts = field_path.split('__')
        base_field = parts[0]
        related_field = parts[1]

        related_model = cls._meta.get_field(base_field).remote_field.model

        queryset = related_model.objects.filter(**{f"{related_field}__isnull": False})
        if active_only and hasattr(related_model, 'is_active'):
            queryset = queryset.filter(is_active=True)

        values = queryset.values_list('id', 'name', 'code').distinct().order_by('name')
        return [
            {'id': v[0], 'name': v[1], 'code': v[2] or ''}
            for v in values if v[0] is not None
        ]

    @classmethod
    def _apply_text_search(cls, queryset: QuerySet, search_text: str) -> QuerySet:
        """Применяет поиск по тексту во всех SEARCH_FIELDS"""
        if not search_text:
            return queryset

        if not cls.SEARCH_FIELDS:
            return queryset

        q_objects = Q()
        for field in cls.SEARCH_FIELDS:
            q_objects |= Q(**{f"{field}__icontains": search_text})

        return queryset.filter(q_objects)

    @classmethod
    def _apply_active_filter(cls, queryset: QuerySet, is_active_value) -> QuerySet:
        """Применяет фильтр по активности"""
        if is_active_value is None or is_active_value == '':
            return queryset

        if is_active_value in ['true', 'True', '1', 1, True]:
            return queryset.filter(is_active=True)
        elif is_active_value in ['false', 'False', '0', 0, False]:
            return queryset.filter(is_active=False)

        return queryset

    @classmethod
    def _get_value_range(cls, field_path: str) -> Dict:
        """Получить минимальное и максимальное значение для числового поля"""
        values = cls.objects.filter(
            **{f"{field_path}__isnull": False}
        ).values_list(field_path, flat=True)

        if values:
            return {
                'min': float(min(values)),
                'max': float(max(values)),
            }
        return {'min': None, 'max': None}

    @classmethod
    def filter_by_params(cls, params: Dict) -> Dict:
        """
        Универсальный метод фильтрации на основе конфигурации
        """
        queryset = cls.objects.all()

        # Безопасно добавляем select_related
        if hasattr(cls, 'SELECT_RELATED_FIELDS') and cls.SELECT_RELATED_FIELDS:
            # Фильтруем None значения
            clean_select_fields = [f for f in cls.SELECT_RELATED_FIELDS if f and isinstance(f, str)]
            if clean_select_fields:
                queryset = queryset.select_related(*clean_select_fields)

        # Безопасно добавляем prefetch_related
        if hasattr(cls, 'PREFETCH_FIELDS') and cls.PREFETCH_FIELDS:
            # Фильтруем None значения и проверяем тип
            clean_prefetch_fields = []
            for f in cls.PREFETCH_FIELDS:
                if f and isinstance(f, str) and f != 'None':
                    clean_prefetch_fields.append(f)
                else:
                    print(f"Warning: Skipping invalid prefetch field: {f}")

            if clean_prefetch_fields:
                try:
                    queryset = queryset.prefetch_related(*clean_prefetch_fields)
                except Exception as e:
                    print(f"Error in prefetch_related: {e}")
                    # Продолжаем без prefetch
                    pass

        filters_applied = {}

        # 1. Применяем стандартные фильтры
        for filter_config in cls.FILTER_CONFIG:
            value = params.get(filter_config.param_name)
            if value is not None and value != '' and value != 'all':
                queryset = filter_config.apply_filter(queryset, value)
                filters_applied[filter_config.param_name] = value

        # 2. Применяем m2m фильтры
        if hasattr(cls, 'M2M_FILTER_CONFIG'):
            for m2m_config in cls.M2M_FILTER_CONFIG:
                param_name = m2m_config.get('param_name')
                m2m_field = m2m_config.get('m2m_field')

                if not param_name or not m2m_field:
                    continue

                value = params.get(param_name)
                if value and value != '' and value != 'all':
                    filter_kwargs = {f"{m2m_field}__id": value}
                    queryset = queryset.filter(**filter_kwargs)
                    filters_applied[param_name] = value

        # 3. Применяем поиск по тексту
        search_text = params.get('search', '')
        if search_text:
            queryset = cls._apply_text_search(queryset, search_text)
            filters_applied['search'] = search_text

        # 4. Применяем фильтр по активности
        if hasattr(cls, 'is_active'):
            is_active = params.get('is_active')
            if is_active is not None and is_active != '':
                queryset = cls._apply_active_filter(queryset, is_active)
                filters_applied['is_active'] = is_active

        # 5. Пагинация
        total = queryset.count()
        limit = int(params.get('limit', 100))
        offset = int(params.get('offset', 0))
        queryset = queryset[offset:offset + limit]

        # 6. Сериализация
        data = []
        for obj in queryset:
            try:
                data.append(obj.to_dict())
            except Exception as e:
                # Логируем ошибку сериализации
                print(f"Error serializing {obj.__class__.__name__} id={obj.id}: {e}")
                continue

        return {
            'data': data,
            'total': total,
            'filters_applied': filters_applied,
            'limit': limit,
            'offset': offset
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Базовый метод сериализации
        Должен быть переопределен в дочерней модели
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} должен реализовать to_dict()"
        )

    @classmethod
    def get_global_options(cls, model_class: Type[models.Model],
                           order_by: str = 'name',
                           active_only: bool = True) -> List[Dict]:
        """
        Универсальный метод для получения опций из глобального справочника

        Args:
            model_class: класс модели (например, IpOption, MountingPlateTypes)
            order_by: поле для сортировки
            active_only: только активные записи

        Returns:
            List[Dict]: список словарей {id, name, code}
        """
        queryset = model_class.objects.all()

        if active_only and hasattr(model_class, 'is_active'):
            queryset = queryset.filter(is_active=True)

        queryset = queryset.order_by(order_by)

        return [
            {
                'id': obj.id,
                'name': getattr(obj, 'name', str(obj)),
                'code': getattr(obj, 'code', '') or ''
            }
            for obj in queryset
        ]

    @classmethod
    def get_filter_options(cls) -> Dict[str, List[Dict]]:
        """
        Базовый метод получения опций фильтрации для глобальных моделей справочников
        Должен быть переопределен в дочерней модели
        """
        raise NotImplementedError(
            f"{cls.__name__} должен реализовать get_filter_options()"
        )

# Предопределенные конфигурации для типовых фильтров
class CommonFilterConfigs:
    """Типовые конфигурации фильтров"""

    @staticmethod
    def min_value_filter(field_name: str,
                         param_name: str = None,
                         related_path: str = None,
                         is_related_field: bool = False) -> FilterFieldConfig:
        """
        Фильтр для минимального значения (значение >= указанного)

        СИНТАКСИС:

        # Прямое поле
        CommonFilterConfigs.min_value_filter('filtration_rating', param_name='min_filtration')

        # Связанное поле
        CommonFilterConfigs.min_value_filter(
            field_name='pressure_min',
            param_name='model_line_pressure_min',
            related_path='model_line__pressure_min',
            is_related_field=True
        )
        """
        if param_name is None:
            param_name = field_name

        return FilterFieldConfig(
            param_name=param_name,
            model_field=field_name,
            filter_type='gte',
            value_converter=float,
            is_related_field=is_related_field or bool(related_path),
            related_path=related_path or field_name
        )

    @staticmethod
    def max_value_filter(field_name: str,
                         param_name: str = None,
                         related_path: str = None,
                         is_related_field: bool = False) -> FilterFieldConfig:
        """
        Фильтр для максимального значения (значение <= указанного)

        СИНТАКСИС:

        # Прямое поле
        CommonFilterConfigs.max_value_filter('filtration_rating', param_name='max_filtration')

        # Связанное поле
        CommonFilterConfigs.max_value_filter(
            field_name='pressure_max',
            param_name='model_line_pressure_max',
            related_path='model_line__pressure_max',
            is_related_field=True
        )
        """
        if param_name is None:
            param_name = field_name

        return FilterFieldConfig(
            param_name=param_name,
            model_field=field_name,
            filter_type='lte',
            value_converter=float,
            is_related_field=is_related_field or bool(related_path),
            related_path=related_path or field_name
        )
    @staticmethod
    def temp_min_filter(field_name: str = 'temp_min',
                        param_name: str = None,
                        is_related_field: bool = False,
                        related_path: str = None) -> FilterFieldConfig:
        """
        Фильтр для минимальной температуры (значение <= указанного)

        СИНТАКСИС:

        # Прямое поле
        CommonFilterConfigs.temp_min_filter('work_temp_min')

        # Связанное поле
        CommonFilterConfigs.temp_min_filter(
            field_name='work_temp_min',
            param_name='model_line_temp_min',
            is_related_field=True,
            related_path='model_line__work_temp_min'
        )
        """
        if param_name is None:
            param_name = field_name

        return FilterFieldConfig(
            param_name=param_name,
            model_field=field_name,
            filter_type='lte',
            value_converter=int,
            is_related_field=is_related_field,
            related_path=related_path or field_name
        )

    @staticmethod
    def temp_max_filter(field_name: str = 'temp_max',
                        param_name: str = None,
                        is_related_field: bool = False,
                        related_path: str = None) -> FilterFieldConfig:
        """
        Фильтр для максимальной температуры (значение >= указанного)

        СИНТАКСИС:

        # Прямое поле
        CommonFilterConfigs.temp_max_filter('work_temp_max')

        # Связанное поле
        CommonFilterConfigs.temp_max_filter(
            field_name='work_temp_max',
            param_name='model_line_temp_max',
            is_related_field=True,
            related_path='model_line__work_temp_max'
        )
        """
        if param_name is None:
            param_name = field_name

        return FilterFieldConfig(
            param_name=param_name,
            model_field=field_name,
            filter_type='gte',
            value_converter=int,
            is_related_field=is_related_field,
            related_path=related_path or field_name
        )

    @staticmethod
    def ip_rank_gte_filter(param_name: str = 'ip_id',
                           rank_field: str = 'ip_rank',
                           related_path: str = None,
                           is_related_field: bool = False) -> FilterFieldConfig:
        """
        Фильтр для IP по рангу (>= ранг выбранного IP)
        Пользователь выбирает IP из списка, а фильтр ищет все IP с рангом >= выбранного

        СИНТАКСИС:

        1. Для поля в текущей модели:
           CommonFilterConfigs.ip_rank_gte_filter(
               param_name='ip_rank',           # имя параметра в запросе
               rank_field='ip_rank',           # имя поля с рангом
               related_path=None,              # не указываем
               is_related_field=False          # False по умолчанию
           )
           Результат: filter(ip_rank__gte=value)

        2. Для поля в связанной модели (через ForeignKey):
           CommonFilterConfigs.ip_rank_gte_filter(
               param_name='min_ip_rank',                    # имя параметра в запросе
               rank_field='ip_rank',                        # имя поля с рангом в связанной модели
               related_path='ip__ip_rank',                  # путь к полю (модель__поле)
               is_related_field=True                        # обязательно True
           )
           Результат: filter(ip__ip_rank__gte=value)

        ПРИМЕРЫ В FILTER_CONFIG:

        # Прямое поле в текущей модели
        CommonFilterConfigs.ip_rank_gte_filter('ip_rank'),

        # Связанное поле
        CommonFilterConfigs.ip_rank_gte_filter(
            param_name='min_ip_rank',
            rank_field='ip_rank',
            related_path='ip__ip_rank',
            is_related_field=True
        ),
        """
        return FilterFieldConfig(
            param_name=param_name,
            model_field=rank_field,
            filter_type='gte',
            value_converter=None,
            is_related_field=is_related_field,
            related_path=related_path or rank_field,
            is_ip_filter=True
        )

    @staticmethod
    def ip_exact_filter(param_name: str = 'ip_rank',
                        rank_field: str = 'ip_rank',
                        related_path: str = None,
                        is_related_field: bool = False) -> FilterFieldConfig:
        """
        Фильтр для IP по точному рангу (ip_rank = значение)

        СИНТАКСИС:

        1. Для поля в текущей модели:
           CommonFilterConfigs.ip_exact_filter(
               param_name='ip_rank',            # имя параметра в запросе
               rank_field='ip_rank',            # имя поля с рангом
               related_path=None,               # не указываем
               is_related_field=False           # False по умолчанию
           )
           Результат: filter(ip_rank=value)

        2. Для поля в связанной модели (через ForeignKey):
           CommonFilterConfigs.ip_exact_filter(
               param_name='exact_ip_rank',                  # имя параметра в запросе
               rank_field='ip_rank',                        # имя поля с рангом в связанной модели
               related_path='ip__ip_rank',                  # путь к полю (модель__поле)
               is_related_field=True                        # обязательно True
           )
           Результат: filter(ip__ip_rank=value)

        ПРИМЕРЫ В FILTER_CONFIG:

        # Прямое поле в текущей модели
        CommonFilterConfigs.ip_exact_filter('ip_rank'),

        # Связанное поле
        CommonFilterConfigs.ip_exact_filter(
            param_name='exact_ip_rank',
            rank_field='ip_rank',
            related_path='ip__ip_rank',
            is_related_field=True
        ),
        """
        if is_related_field and related_path:
            full_path = f"{related_path}"
        else:
            full_path = rank_field

        return FilterFieldConfig(
            param_name=param_name,
            model_field=rank_field,
            filter_type='exact',
            value_converter=int,
            is_related_field=is_related_field,
            related_path=full_path
        )

    @staticmethod
    def exact_related_filter(param_name: str,
                             related_path: str,
                             is_related_field: bool = True) -> FilterFieldConfig:
        """
        Точный фильтр по связанному полю (ForeignKey)

        СИНТАКСИС:

        CommonFilterConfigs.exact_related_filter(
            param_name='brand_id',        # имя параметра в запросе
            related_path='model_line__brand',  # путь к связанному полю
            is_related_field=True         # True по умолчанию
        )
        Результат: filter(model_line__brand_id=value)

        ПРИМЕР В FILTER_CONFIG:

        FilterFieldConfig(
            param_name='brand_id',
            model_field='model_line__brand',
            filter_type='exact',
            is_related_field=True
        ),

        # ИЛИ используя метод:
        CommonFilterConfigs.exact_related_filter('brand_id', 'model_line__brand'),
        """
        return FilterFieldConfig(
            param_name=param_name,
            model_field=related_path,
            filter_type='exact',
            is_related_field=is_related_field,
            related_path=related_path
        )