#gearbox/models/gb_model_line.py
from typing import Dict

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import CopyMixin, TemplateMixin
from params.models import ActuatorGearboxOutputType
from producers.models import Brands


class GearBoxModelLine(models.Model):
    """
    Серия пневматических фитингов
    """

    name = models.CharField(max_length=100,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название серии редуктора'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код серии редукторов"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание разновидности серии редукторов'))
    name_template = models.TextField(blank=True, null=True,
                                     verbose_name=_("Шаблон названия"),
                                     help_text=_('Шаблон для текстового названия редуктора'))
    description_template = models.TextField(blank=True, null=True,verbose_name=_("Шаблон описания"),
                                            help_text=_('Шаблон для описания редуктора'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    brand = models.ForeignKey(Brands, related_name='gearbox_line_brand', blank=True, null=True,
                              on_delete=models.SET_NULL,
                              help_text=_('Бренд серии редукторов'),
                              verbose_name=_("Бренд"))
    gearbox_output_variety = models.ForeignKey(ActuatorGearboxOutputType, related_name='gearbox_variety_model_line',
                                       blank=True,
                                       null=True,
                                       on_delete=models.SET_NULL,
                                       help_text=_('Тип выхода редуктора'),
                                       verbose_name=_("Тип"))

    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict , blank=True ,
        verbose_name=_("Параметры") ,
        help_text=_("signal_type, resistance, range и т.д.")
    )

    class Meta:
        ordering = ['brand', 'code']
        verbose_name = _('Серия редукторов')
        verbose_name_plural = _('Серии редукторов')

    def __str__(self):
        return self.name
