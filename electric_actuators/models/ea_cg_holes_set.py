#electric_actuators/models/ea_cg_holes_set.py
from datetime import datetime
from typing import List, Optional, Tuple, Any, Dict, Union
from django.db import models


class CableGlandHolesSet(models.Model):
    name = models.CharField(max_length=20, blank=True,
                            help_text='Название варианта набора отверстий под КВ')
    cg1 = models.ForeignKey('params.ThreadSize', related_name='cable_gland1', blank=True, null=True, on_delete=models.SET_NULL,
                            verbose_name='Отверстие под КВ1')
    cg2 = models.ForeignKey('params.ThreadSize', related_name='cable_gland2', blank=True, null=True, on_delete=models.SET_NULL,
                            verbose_name='Отверстие под КВ2')
    cg3 = models.ForeignKey('params.ThreadSize', related_name='cable_gland3', blank=True, null=True, on_delete=models.SET_NULL,
                            verbose_name='Отверстие под КВ3')
    cg4 = models.ForeignKey('params.ThreadSize', related_name='cable_gland4', blank=True, null=True, on_delete=models.SET_NULL,
                            verbose_name='Отверстие под КВ4')
    text_description = models.CharField(max_length=200, blank=True,
                                        help_text='Текстовое описание набора отверстий под КВ')

    def __str__(self):
        return self.text_description

    def get_description_data(self) -> Dict[str , Any] :
        """Получить структурированные данные для набора кабельных вводов"""
        data = {
            'cg_set' : {'display_name' : 'Кабельные вводы' , 'value' : self.name} ,
            'cg1' : {'display_name' : 'Отверстие под КВ1' , 'value' : self.cg1.name if self.cg1 else None} ,
            'cg2' : {'display_name' : 'Отверстие под КВ2' , 'value' : self.cg2.name if self.cg2 else None} ,
            'cg3': {'display_name': 'Отверстие под КВ3', 'value': self.cg3.name if self.cg3 else None},
            'cg4': {'display_name': 'Отверстие под КВ4', 'value': self.cg4.name if self.cg4 else None},
        }
        return data

