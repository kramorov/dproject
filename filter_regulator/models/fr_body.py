#filter_requlator/models/fr_body.py

from django.db import models
from django.utils.translation import gettext_lazy as _


from params.models import ThreadSize


class FilterRegulatorBody(models.Model ):
    """
    Корпус корпуса фильтр-регулятора
    """

    name = models.CharField(max_length=200,
                            verbose_name=_("Название" ),
                            help_text=_('Текстовое название корпуса фильтр-регулятора'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код" ),
                            help_text=_("Код клапана"))

    description = models.TextField(blank=True, verbose_name=_("Описание" ),
                                   help_text=_('Текстовое описание корпуса фильтр-регулятора'))
    sorting_order = models.IntegerField(default= 0, verbose_name=_("Cортировка" ),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно" ),
                                    help_text=_('Активно свойство или нет'))
    weight = models.DecimalField(max_digits= 5, decimal_places= 2, blank=True,
                                 null=True, help_text=_('Вес' ),
                                 verbose_name=_("Вес, кг"))

    thread = models.ForeignKey(ThreadSize , on_delete=models.SET_NULL , null=True , blank=True ,
                               related_name='filter_body_thread' ,
                               verbose_name=_("Резьба портов") ,
                               help_text=_('Резьба портов IN/OUT'))
    gauge_port_size = models.ForeignKey(ThreadSize , on_delete=models.SET_NULL , null=True , blank=True ,
                                        related_name='filter_body_gauge_port_thread' , verbose_name=_("Резьба манометра" ),
                                        help_text=_('Резьба манометра'))
    drain_port_size = models.ForeignKey(ThreadSize , on_delete=models.SET_NULL , null=True , blank=True ,
                                        related_name='filter_body_drain_port_thread' , verbose_name=_("Резьба слива") ,
                                        help_text=_('Резьба слива'))

    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Параметры" ),
        help_text=_("signal_type, resistance, range и т.д.")
    )

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _('Корпус фильтр-регулятора')
        verbose_name_plural = _('Корпуса фильтр-регуляторов')

    def __str__(self ):
        return self.name