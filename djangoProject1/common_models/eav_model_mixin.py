# common_models/eav_model_mixin.py
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation


class EAVModelMixin :
    """Миксин для моделей, которые поддерживают EAV атрибуты"""

    def get_eav_value(self , attribute_name , default=None) :
        """Получить значение атрибута по имени"""
        try :
            value_obj = self.eav_values.get(attribute__name=attribute_name)
            return value_obj.get_typed_value()
        except self.eav_value_model.DoesNotExist :
            return default

    def set_eav_value(self , attribute_name , value) :
        """Установить значение атрибута"""
        attribute , created = self.eav_attribute_model.objects.get_or_create(
            name=attribute_name ,
            defaults={'value_type' : self._detect_value_type(value)}
        )

        value_obj , created = self.eav_value_model.objects.get_or_create(
            attribute=attribute ,
            **{self.eav_entity_field : self}
        )

        value_obj.set_value(value)
        value_obj.save()

    def _detect_value_type(self , value) :
        """Определяет тип значения автоматически"""
        if value is None :
            return 'string'
        elif isinstance(value , (int , float)) :
            return 'number'
        elif isinstance(value , bool) :
            return 'boolean'
        elif isinstance(value , (list , dict)) :
            return 'json'
        elif hasattr(value , '_meta') :  # Это модель Django
            return 'foreign_key'
        return 'string'

    @property
    def eav_data(self) :
        """Возвращает все EAV данные как словарь"""
        return {
            value.attribute.name : value.get_typed_value()
            for value in self.eav_values.all().select_related('attribute')
        }

    def get_eav_attributes(self) :
        """Возвращает все доступные атрибуты для этой модели"""
        return self.eav_attribute_model.objects.all()