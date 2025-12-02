# core/models/base.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from .mixins import StructuredDataMixin , TimestampMixin , SoftDeleteMixin


class BaseModel(StructuredDataMixin , TimestampMixin , SoftDeleteMixin , models.Model) :
    """
    Абстрактная базовая модель для всех моделей проекта
    """
    name = models.CharField(
        max_length=255 ,
        verbose_name=_("Название") ,
        help_text=_("Основное название объекта") ,
        blank=True ,
        null=True
    )

    code = models.CharField(
        max_length=100 ,
        verbose_name=_("Код") ,
        help_text=_("Уникальный код объекта") ,
        blank=True ,
        null=True ,
        unique=True
    )

    description = models.TextField(
        verbose_name=_("Описание") ,
        help_text=_("Подробное описание объекта") ,
        blank=True
    )

    sorting_order = models.IntegerField(
        default=0 ,
        verbose_name=_("Порядок сортировки") ,
        help_text=_("Порядок в списках (меньше = выше)")
    )

    is_active = models.BooleanField(
        default=True ,
        verbose_name=_("Активно") ,
        help_text=_("Отображать ли объект в интерфейсе")
    )

    class Meta :
        abstract = True
        ordering = ['sorting_order' , 'name' , 'id']

    def __str__(self) :
        return self.name or self.code or f"#{self.id}"

    # Общие методы для всех моделей
    def get_absolute_url(self) :
        """Базовый URL для объекта"""
        app_label = self._meta.app_label
        model_name = self._meta.model_name
        return f"/{app_label}/{model_name}/{self.id}/"

    def get_admin_url(self) :
        """URL в админке"""
        app_label = self._meta.app_label
        model_name = self._meta.model_name
        return f"/admin/{app_label}/{model_name}/{self.id}/change/"