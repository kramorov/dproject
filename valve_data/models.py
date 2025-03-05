from django.db import models

from djangoProject1.common_models.abstract_models import AbstractValveModel
from params.models import ValveTypes, MeasureUnits, MountingPlateTypes, StemSize
from producers.models import Producer, Brands


class ValveLine(models.Model):
    symbolic_code = models.CharField(max_length=20, help_text='Символьное обозначение (артикул)\
         серии арматуры производителя')
    valve_producer = models.ForeignKey(Producer, related_name='valve_line_valve_producer', blank=True, null=True,
                                       on_delete=models.SET_NULL, help_text='Производитель серии арматуры')
    valve_brand = models.ForeignKey(Brands, related_name='valve_line_valve_brand', blank=True, null=True,
                                    on_delete=models.SET_NULL, help_text='Бренд серии арматуры')
    valve_type = models.ForeignKey(ValveTypes, related_name='valve_line_valve_type', blank=True, null=True,
                                   on_delete=models.SET_NULL, help_text='Тип арматуры серии арматуры производителя')
    def __str__(self):
        return self.symbolic_code


class ValveModelData(AbstractValveModel):
    symbolic_code = models.CharField(max_length=50, help_text='Символьное обозначение (артикул)\
     модели арматуры производителя')
    valve_model_model_line = models.ForeignKey(ValveLine, related_name='valve_model_model_line', blank=True,
                                               null=True,
                                               on_delete=models.SET_NULL, help_text='Серия арматуры производителя')

    def __str__(self):
        return self.symbolic_code
