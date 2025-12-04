# core/models/mixins.py
from django.db import models
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _
from typing import Dict , List , Optional , Any
from django.utils.html import escape
from ..constants import DataFormat , DisplayView


class StructuredDataMixin :
    """
    Миксин для структурированных данных.
    Должен быть реализован в каждой модели.
    """
    # Константы для удобства
    COMPACT = DataFormat.COMPACT
    DISPLAY = DataFormat.DISPLAY
    FULL = DataFormat.FULL
    """Типы отображения
    LIST = 'list'
    CARD = 'card'
    DETAIL = 'detail'
    BADGE = 'badge'
    INLINE = 'inline'"""
    LIST = DisplayView.LIST
    CARD = DisplayView.CARD
    DETAIL = DisplayView.DETAIL
    BADGE = DisplayView.BADGE

    def get_compact_data(self) -> Dict[str , Any] :
        """
        Минимальные данные для списков и таблиц.
        Должен быть переопределен в каждой модели.
        """
        obj_id = getattr(self , 'id' , None)  # Безопасное получение id
        # Безопасный доступ к метаданным модели
        model_name = self._get_model_name()
        app_label = self._get_app_label()

        return {
            'id' : obj_id,  # Используем безопасное значение
            'name' : getattr(self , 'name' , None) ,
            'code' : getattr(self , 'code' , None) ,
            'is_active' : getattr(self , 'is_active' , True) ,
            'model' : model_name ,
            'app' : app_label ,
        }

    def get_display_data(self , view_type: str = DETAIL) -> Dict[str , Any] :
        """
        Данные для отображения в UI.
        Должен быть переопределен в каждой модели.

        Args:
            view_type: тип отображения (LIST, CARD, DETAIL, BADGE)
        """
        raise NotImplementedError(
            f"Модель {self.__class__.__name__} должна реализовать get_display_data()"
        )

    def get_full_data(self , include: Optional[List[str]] = None) -> Dict[str , Any] :
        """
        Полные данные для форм и API.
        Должен быть переопределен в каждой модели.

        Args:
            include: что включать ['form', 'metadata', 'related', 'audit']
        """
        raise NotImplementedError(
            f"Модель {self.__class__.__name__} должна реализовать get_full_data()"
        )

    # Общие вспомогательные методы
    def _format_field(self , value , field_type: str = 'text' , **kwargs) -> Dict[str , Any] :
        """Форматирование поля с метаданными"""


        default_value = kwargs.get('default' , '—')

        if value is None or value == '' :
            formatted_value = default_value
            is_empty = True
        else :
            formatted_value = str(value)
            is_empty = False

        result = {
            'value' : value ,
            'formatted' : formatted_value ,
            'type' : field_type ,
            'is_empty' : is_empty ,
            'raw' : value ,
        }

        # Добавляем дополнительные параметры
        for key in ['label' , 'icon' , 'priority' , 'multiline' , 'required'] :
            if key in kwargs :
                result[key] = kwargs[key]

        return result

    def _format_date(self , date_obj , format_str: str = 'd.m.Y') -> Dict[str , Any] :
        """Форматирование даты"""
        if not date_obj :
            return self._format_field(None , 'date' , default='Не указана')

        return self._format_field(
            date_obj ,
            'date' ,
            formatted=date_format(date_obj , format_str) ,
            iso_format=date_obj.isoformat() if hasattr(date_obj , 'isoformat') else None
        )

    def _format_datetime(self , datetime_obj , format_str: str = 'd.m.Y H:i' , **kwargs) -> Dict[str , Any] :
        """
        Форматирование даты-времени
        """
        if not datetime_obj :
            default_text = kwargs.pop('default' , _('Не указано'))
            return self._format_field(None , 'datetime' , default=default_text , **kwargs)

        formatted = date_format(datetime_obj , format_str)
        return self._format_field(
            datetime_obj ,
            'datetime' ,
            formatted=formatted ,
            iso_format=datetime_obj.isoformat() if hasattr(datetime_obj , 'isoformat') else None ,
            **kwargs
        )

    def _format_foreign_key(self , obj , **kwargs) -> Dict[str , Any] :
        """
        Форматирование ForeignKey поля

        Args:
            obj: связанный объект
            **kwargs: дополнительные параметры:
                - label: подпись поля
                - icon: иконка
                - priority: приоритет
                - include_data: какие данные включать ('compact', 'display', 'full')
        """
        if not obj :
            default_text = kwargs.pop('default' , _('Не указан'))
            return self._format_field(None , 'foreign_key' , default=default_text , **kwargs)

        # Безопасный доступ к метаданным связанного объекта
        model_name = self._safe_get_model_name(obj)
        app_label = self._safe_get_app_label(obj)

        # Базовые данные
        include_data = kwargs.pop('include_data' , 'compact')
        data = {
            'value' : obj.id ,
            'formatted' : str(obj) ,
            'type' : 'foreign_key' ,
            'is_empty' : False ,
            'model' : model_name ,
            'app' : app_label ,
        }

        # Добавляем данные связанного объекта
        if include_data == 'compact' and hasattr(obj , 'get_compact_data') :
            data['compact'] = obj.get_compact_data()
        elif include_data == 'display' and hasattr(obj , 'get_display_data') :
            data['display'] = obj.get_display_data('badge')
        elif include_data == 'full' and hasattr(obj , 'get_full_data') :
            data['full'] = obj.get_full_data(['form'])

        # Добавляем дополнительные параметры
        for key in ['label' , 'icon' , 'priority' , 'required' , 'help_text'] :
            if key in kwargs :
                data[key] = kwargs[key]

        return data

    def _format_many_to_many(self , queryset , **kwargs) -> Dict[str , Any] :
        """
        Форматирование ManyToMany поля

        Args:
            queryset: QuerySet связанных объектов
            **kwargs: дополнительные параметры
        """
        if not queryset.exists() :
            default_text = kwargs.pop('default' , _('Нет данных'))
            return self._format_field([] , 'many_to_many' , default=default_text , **kwargs)

        items = list(queryset)
        include_data = kwargs.pop('include_data' , 'compact')

        formatted_items = []
        for item in items :
            item_data = {
                'id' : item.id ,
                'name' : str(item) ,
                'model' : self._safe_get_model_name(item) ,
            }

            if include_data == 'compact' and hasattr(item , 'get_compact_data') :
                item_data.update(item.get_compact_data())
            elif include_data == 'display' and hasattr(item , 'get_display_data') :
                item_data['display'] = item.get_display_data('badge')

            formatted_items.append(item_data)

        return self._format_field(
            items ,
            'many_to_many' ,
            formatted=', '.join([str(item) for item in items]) ,
            items=formatted_items ,
            count=len(items) ,
            **kwargs
        )

    def _format_boolean(self , value: bool , **kwargs) -> Dict[str , Any] :
        """
        Форматирование булевого поля
        """
        true_text = kwargs.pop('true_text' , _('Да'))
        false_text = kwargs.pop('false_text' , _('Нет'))

        formatted = true_text if value else false_text
        return self._format_field(
            value ,
            'boolean' ,
            formatted=formatted ,
            **kwargs
        )

    def _format_choice(self , value: str , choices: list , **kwargs) -> Dict[str , Any] :
        """
        Форматирование поля с выбором
        """
        # Преобразуем choices в словарь для поиска
        choices_dict = dict(choices)
        formatted = choices_dict.get(value , value)

        return self._format_field(
            value ,
            'choice' ,
            formatted=formatted ,
            choices=choices ,
            **kwargs
        )

    def _get_base_display_fields(self) -> Dict[str , Dict] :
        """
        Базовые поля для отображения (общие для всех моделей)
        """
        fields = {}

        # Добавляем name, если есть в модели
        if hasattr(self , 'name') :
            fields['name'] = self._format_field(
                self.name ,
                'text' ,
                label=_('Название') ,
                icon='📄' ,
                priority=1
            )

        # Добавляем code, если есть в модели
        if hasattr(self , 'code') :
            fields['code'] = self._format_field(
                self.code ,
                'code' ,
                label=_('Код') ,
                icon='🔢' ,
                priority=2
            )

        # Добавляем is_active, если есть в модели
        if hasattr(self , 'is_active') :
            fields['is_active'] = self._format_field(
                self.is_active ,
                'boolean' ,
                label=_('Статус') ,
                formatted=_('Активен') if self.is_active else _('Неактивен') ,
                icon='✅' if self.is_active else '❌' ,
                priority=100
            )

        # Добавляем description, если есть в модели
        if hasattr(self , 'description') :
            fields['description'] = self._format_field(
                self.description ,
                'text' ,
                label=_('Описание') ,
                icon='📄' ,
                priority=50 ,
                multiline=True
            )

        return fields

    def _get_status_badge(self) -> Dict[str , Any] :
        """
        Получить статус объекта в виде бейджа
        """
        status = 'active'
        text = _('Активен')

        if hasattr(self , 'is_active') and not self.is_active :
            status = 'inactive'
            text = _('Неактивен')
        elif hasattr(self , 'is_deleted') and self.is_deleted :
            status = 'deleted'
            text = _('Удален')
        elif hasattr(self , 'is_published') and not self.is_published :
            status = 'draft'
            text = _('Черновик')

        return {
            'text' : text ,
            'type' : status ,
            'color' : {
                'active' : 'green' ,
                'inactive' : 'gray' ,
                'deleted' : 'red' ,
                'draft' : 'yellow'
            }.get(status , 'blue')
        }

    def _get_actions(self , request=None) -> List[Dict[str , Any]] :
        """
        Получить список действий для объекта
        """
        actions = [
            {
                'label' : _('Редактировать') ,
                'url' : self.get_admin_url() ,
                'icon' : '✏️' ,
                'type' : 'edit' ,
                'permission' : 'change'
            } ,
            {
                'label' : _('Удалить') ,
                'url' : f"{self.get_admin_url()}delete/" ,
                'icon' : '🗑️' ,
                'type' : 'delete' ,
                'permission' : 'delete' ,
                'confirm' : True
            }
        ]

        # Добавляем просмотр, если есть get_absolute_url
        if hasattr(self , 'get_absolute_url') :
            actions.insert(0 , {
                'label' : _('Просмотреть') ,
                'url' : self.get_absolute_url() ,
                'icon' : '👁️' ,
                'type' : 'view' ,
                'external' : True
            })

        return actions

    def _get_metadata_template(self) -> Dict[str , Any] :
        """
        Шаблон метаданных для переопределения в моделях
        """
        return {
            'field_schema' : [] ,
            'validation_rules' : {} ,
            'permissions' : {
                'view' : True ,
                'add' : True ,
                'change' : True ,
                'delete' : True ,
            }
        }

    # ==================== УТИЛИТАРНЫЕ МЕТОДЫ ====================

    def _safe_get_model_name(self , obj=None) :
        """Безопасное получение имени модели"""
        if obj is None :
            obj = self
        try :
            return obj._meta.model_name
        except AttributeError :
            return obj.__class__.__name__.lower()

    def _safe_get_app_label(self , obj=None) :
        """Безопасное получение метки приложения"""
        if obj is None :
            obj = self
        try :
            return obj._meta.app_label
        except AttributeError :
            return 'unknown'

    def _get_model_name(self) :
        """Получить имя модели (alias для совместимости)"""
        return self._safe_get_model_name()

    def _get_app_label(self) :
        """Получить метку приложения (alias для совместимости)"""
        return self._safe_get_app_label()

    def get_admin_url(self) -> str :
        """
        URL в админке Django
        """
        app_label = self._safe_get_app_label()
        model_name = self._safe_get_model_name()
        obj_id = getattr(self , 'id' , '')
        return f"/admin/{app_label}/{model_name}/{obj_id}/change/"

    def get_absolute_url(self) -> str :
        """
        Базовый URL для объекта.
        Переопределите в моделях, если нужно.
        """
        app_label = self._safe_get_app_label()
        model_name = self._safe_get_model_name()
        obj_id = getattr(self , 'id' , '')
        return f"/{app_label}/{model_name}/{obj_id}/"

    def get_api_url(self) -> str :
        """
        URL для API
        """
        app_label = self._safe_get_app_label()
        model_name = self._safe_get_model_name()
        obj_id = getattr(self , 'id' , '')
        return f"/api/{app_label}/{model_name}/{obj_id}/"

    def get_export_data(self , format_type: str = 'csv') -> Dict[str , Any] :
        """
        Данные для экспорта
        """
        data = self.get_compact_data()

        # Добавляем дополнительные поля для экспорта
        if hasattr(self , 'created_at') :
            data['created_at'] = self.created_at.isoformat() if self.created_at else None

        if hasattr(self , 'updated_at') :
            data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None

        # Форматируем для разных типов экспорта
        if format_type == 'csv' :
            # Преобразуем в плоскую структуру для CSV
            flat_data = {}
            for key , value in data.items() :
                if isinstance(value , dict) :
                    for sub_key , sub_value in value.items() :
                        flat_data[f"{key}_{sub_key}"] = sub_value
                else :
                    flat_data[key] = value
            return flat_data

        return data

    def is_editable(self , user=None) -> bool :
        """
        Проверка, можно ли редактировать объект
        """
        if hasattr(self , 'is_active') and not self.is_active :
            return False

        if hasattr(self , 'is_deleted') and self.is_deleted :
            return False

        # Дополнительная логика проверки прав пользователя
        if user and hasattr(self , 'can_edit') :
            return self.can_edit(user)

        return True

    def get_field_value(self , field_name: str , default: Any = None) -> Any :
        """
        Безопасное получение значения поля
        """
        try :
            value = getattr(self , field_name)
            if callable(value) :
                value = value()
            return value
        except (AttributeError , ValueError) :
            return default

    # ==================== МЕТОДЫ ДЛЯ РАБОТЫ С СВЯЗЯМИ ====================

    def get_related_objects(self , relation_name: str , **filters) -> List[Any] :
        """
        Получить связанные объекты
        """
        try :
            if hasattr(self , relation_name) :
                relation = getattr(self , relation_name)
                if hasattr(relation , 'all') :
                    queryset = relation.all()
                    if filters :
                        queryset = queryset.filter(**filters)
                    return list(queryset)
        except Exception :
            pass

        return []

    # ==================== МЕТОДЫ ДЛЯ РАБОТЫ С ПРАВАМИ ====================

    def check_permission(self , permission_type: str , user=None) -> bool :
        """
        Проверка прав доступа
        """
        # Базовая реализация, можно расширить
        if permission_type == 'view' :
            return True

        if permission_type == 'edit' :
            return self.is_editable(user)

        if permission_type == 'delete' :
            if hasattr(self , 'is_deleted') and self.is_deleted :
                return False
            return True

        return True


class TimestampMixin(models.Model) :
    """
    Миксин для временных меток создания/обновления
    """
    created_at = models.DateTimeField(
        auto_now_add=True ,
        verbose_name=_("Дата создания") ,
        editable=False
    )

    updated_at = models.DateTimeField(
        auto_now=True ,
        verbose_name=_("Дата обновления") ,
        editable=False
    )

    class Meta :
        abstract = True


class SoftDeleteMixin(models.Model) :
    """
    Миксин для мягкого удаления
    """
    is_deleted = models.BooleanField(
        default=False ,
        verbose_name=_("Удален") ,
        help_text=_("Объект помечен как удаленный")
    )

    deleted_at = models.DateTimeField(
        null=True ,
        blank=True ,
        verbose_name=_("Дата удаления")
    )

    class Meta :
        abstract = True

    def delete(self , using=None , soft: bool = True) :
        """Мягкое удаление"""
        if soft :
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save()
        else :
            super().delete(using=using)

    def restore(self) :
        """Восстановление удаленного"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()