#electric_actuators/models/ea_cg_holes_set.py
from datetime import datetime

from django.db import models
from params.models import ThreadSize


class CableGlandHolesSet(models.Model):
    name = models.CharField(max_length=20, blank=True,
                            help_text='Название варианта набора отверстий под КВ')
    cg1 = models.ForeignKey(ThreadSize, related_name='cable_gland1', blank=True, null=True, on_delete=models.SET_NULL,
                            verbose_name='Отверстие под КВ1')
    cg2 = models.ForeignKey(ThreadSize, related_name='cable_gland2', blank=True, null=True, on_delete=models.SET_NULL,
                            verbose_name='Отверстие под КВ2')
    cg3 = models.ForeignKey(ThreadSize, related_name='cable_gland3', blank=True, null=True, on_delete=models.SET_NULL,
                            verbose_name='Отверстие под КВ3')
    cg4 = models.ForeignKey(ThreadSize, related_name='cable_gland4', blank=True, null=True, on_delete=models.SET_NULL,
                            verbose_name='Отверстие под КВ4')
    text_description = models.CharField(max_length=200, blank=True,
                                        help_text='Текстовое описание набора отверстий под КВ')

    def __str__(self):
        return self.text_description

