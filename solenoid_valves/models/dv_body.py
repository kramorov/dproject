# solenoid_valves/models/dv_body.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import StructuredDataMixin
from producers.models import Brands


class DirectionValveBody(StructuredDataMixin, models.Model):
    """Корпус распределительного клапана. Связан с DirectionValve через ForeignKey body."""
    name = models.CharField(max_length=200,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название корпуса клапана'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код клапана"))

    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание корпуса клапана'))
    brand = models.ForeignKey(Brands, related_name='direction_valve_body_brand', blank=True, null=True,
                              on_delete=models.SET_NULL,
                              help_text=_('Бренд корпуса клапана'),
                              verbose_name=_("Бренд"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        ordering = ['sorting_order', 'code']
        verbose_name = _('Корпус распределительного клапана')
        verbose_name_plural = _('Корпуса распределительных клапанов')

    def __str__(self):
        return self.name
