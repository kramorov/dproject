# common_models/eav_abstract_models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from .eav_mixins import EAVAttributeMixin , EAVValueMixin , EAVManyToManyValueMixin


class AbstractEAVAttribute(EAVAttributeMixin) :
    """Абстрактная модель для атрибутов EAV"""

    class Meta :
        abstract = True
        verbose_name = _('Атрибут EAV')
        verbose_name_plural = _('Атрибуты EAV')
        ordering = ['name']


class AbstractEAVValue(EAVValueMixin) :
    """Абстрактная модель для значений EAV"""
    attribute = models.ForeignKey(
        'EAVAttribute' ,  # Будет заменено на конкретную модель атрибутов
        on_delete=models.CASCADE ,
        related_name='values' ,
        verbose_name=_('Атрибут')
    )

    class Meta :
        abstract = True
        verbose_name = _('Значение EAV')
        verbose_name_plural = _('Значения EAV')
        unique_together = ['attribute' , 'entity_content_type' , 'entity_object_id']


class AbstractEAVManyToManyValue(EAVManyToManyValueMixin) :
    """Абстрактная модель для M2M связей EAV"""
    eav_value = models.ForeignKey(
        'EAVValue' ,  # Будет заменено на конкретную модель значений
        on_delete=models.CASCADE ,
        related_name='related_objects' ,
        verbose_name=_('EAV значение')
    )

    class Meta :
        abstract = True
        verbose_name = _('M2M значение EAV')
        verbose_name_plural = _('M2M значения EAV')