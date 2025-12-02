# core/models/mixins.py
from django.db import models
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _
from typing import Dict , List , Optional , Any
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

    LIST = DisplayView.LIST
    CARD = DisplayView.CARD
    DETAIL = DisplayView.DETAIL
    BADGE = DisplayView.BADGE

    def get_compact_data(self) -> Dict[str , Any] :
        """
        Минимальные данные для списков и таблиц.
        Должен быть переопределен в каждой модели.
        """
        return {
            'id' : self.id ,
            'name' : getattr(self , 'name' , None) ,
            'code' : getattr(self , 'code' , None) ,
            'is_active' : getattr(self , 'is_active' , True) ,
            'model' : self._meta.model_name ,
            'app' : self._meta.app_label ,
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
        from django.utils.html import escape

        default_value = kwargs.get('default' , '—')

        if value is None or value == '' :
            formatted_value = default_value
            is_empty = True
        else :
            formatted_value = str(value)
            is_empty = False

        return {
            'value' : value ,
            'formatted' : formatted_value ,
            'type' : field_type ,
            'is_empty' : is_empty ,
            'raw' : value ,
        }

    def _format_date(self , date_obj , format_str: str = 'd.m.Y') -> Dict[str , Any] :
        """Форматирование даты"""
        if not date_obj :
            return self._format_field(None , 'date' , default='Не указана')

        return self._format_field(
            date_obj ,
            'date' ,
            formatted=date_format(date_obj , format_str) ,
            iso_format=date_obj.isoformat()
        )

    def _format_foreign_key(self , obj , field_name: str = None) -> Dict[str , Any] :
        """Форматирование ForeignKey поля"""
        if not obj :
            return self._format_field(None , 'foreign_key' , default='Не указан')

        data = {
            'value' : obj.id ,
            'formatted' : str(obj) ,
            'type' : 'foreign_key' ,
            'is_empty' : False ,
            'model' : obj._meta.model_name ,
        }

        # Добавляем дополнительные данные если есть
        if hasattr(obj , 'get_compact_data') :
            data['compact'] = obj.get_compact_data()

        return data

    def _get_base_display_fields(self) -> Dict[str , Dict] :
        """Базовые поля для отображения (общие для всех моделей)"""
        return {
            'name' : self._format_field(
                self.name ,
                'text' ,
                label=_('Название') ,
                icon='📄' ,
                priority=1
            ) ,
            'code' : self._format_field(
                self.code ,
                'code' ,
                label=_('Код') ,
                icon='🔢' ,
                priority=2
            ) ,
            'is_active' : self._format_field(
                self.is_active ,
                'boolean' ,
                label=_('Статус') ,
                formatted='Активен' if self.is_active else 'Неактивен' ,
                icon='✅' if self.is_active else '❌' ,
                priority=100
            )
        }


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

    def get_timestamps_display(self) -> Dict[str , Dict] :
        """Данные временных меток для отображения"""
        return {
            'created_at' : self._format_date(
                self.created_at ,
                label=_('Создан') ,
                icon='🕒'
            ) ,
            'updated_at' : self._format_date(
                self.updated_at ,
                label=_('Обновлен') ,
                icon='🔄'
            )
        }


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