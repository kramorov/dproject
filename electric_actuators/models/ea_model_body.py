#electric_actuators/models/ea_model_body.py
from django.db import models

# from electric_actuators.models import ModelLine , CableGlandHolesSet
from params.models import StemShapes, StemSize, MountingPlateTypes


class ModelBody(models.Model):
    name = models.CharField(max_length=200, verbose_name='Текстовое название типа корпуса')
    model_line = models.ForeignKey('ModelLine', on_delete=models.PROTECT,
                                   related_name='model_body_model_line', help_text='Серия приводов')
    default_cable_glands_holes = \
        models.ForeignKey('CableGlandHolesSet', null=True, blank=True,
                          related_name='model_body_default_cable_glands_holes',
                          on_delete=models.SET_NULL,
                          help_text='Стандартные отверстия под кабельные вводы')
    allowed_cable_glands_holes = \
        models.ManyToManyField('CableGlandHolesSet', blank=True,
                               related_name='model_body_allowed_cable_glands_holes',
                               help_text='Возможные для выбора варианты отверстий под кабельные вводы для корпуса ('
                                         'можно выбрать несколько)')
    mounting_plate = models.ManyToManyField(MountingPlateTypes, blank=True,
                                            related_name='model_body_cable_mounting_plate',
                                            help_text='Монтажная площадка')
    stem_shape = models.ForeignKey(StemShapes, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='model_body_stem_shape', help_text='Тип отверстия под шток арматуры')
    stem_size = models.ForeignKey(StemSize, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='model_body_stem_size', help_text='Размер отверстия под шток арматуры')
    max_stem_height = models.PositiveIntegerField(blank=True, null=True,
                                                  help_text='Глубина отверстия под шток арматуры')
    max_stem_diameter = models.PositiveIntegerField(blank=True, null=True, help_text='Максимальный диаметр отверстия '
                                                                                     'под шток арматуры')
    text_description = models.CharField(max_length=500, blank=True, null=True, help_text='Описание типа корпуса')

    def __str__(self):
        return self.name