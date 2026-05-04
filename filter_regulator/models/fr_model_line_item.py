#filter_requlator/models/fr_model_line_item.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from filter_regulator.models import FilterRegulatorBody
from filter_regulator.models.fr_model_line import FilterRegulatorModelLine
from filter_regulator.models.fr_options import FilterRegulatorVariety , DrainVariety


class FilterRegulator(models.Model):
    """Модель фильтр-регулятора (каталог)"""
    name = models.CharField(max_length=100 ,
                            verbose_name=_("Название") ,
                            help_text=_('Текстовое название модели фильтр-регулятора'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код модели фильтр-регулятора"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание модели фильтр-регулятора'))

    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    GAUGE_CHOICES = [
        (0, _('Без манометра')),
        (1, _('1 манометр в комплекте')),
        (2, _('2 манометра в комплекте')),
    ]
    gauge_quantity = models.IntegerField(
        choices=GAUGE_CHOICES,
        default=1,
        verbose_name=_("Комплектация манометром")
    )

    model_line = models.ForeignKey(FilterRegulatorModelLine , related_name='filter_model_line' ,
                                   blank=True ,
                                   null=True ,
                                   on_delete=models.SET_NULL ,
                                   help_text=_('Серия модели фильтр-регулятора') ,
                                   verbose_name=_("Серия"))
    filter_variety = models.ForeignKey(FilterRegulatorVariety , related_name='filter_variety' ,
                                        blank=True ,
                                        null=True ,
                                        on_delete=models.SET_NULL ,
                                        help_text=_('Тип модели фильтр-регулятора') ,
                                        verbose_name=_("Тип"))
    body = models.ForeignKey(FilterRegulatorBody , related_name='filter_body' ,
                                blank=True ,
                                null=True ,
                                on_delete=models.SET_NULL ,
                                help_text=_('Корпус фильтр-регулятора') ,
                                verbose_name=_("Корпус"))
    drain_variety = models.ForeignKey(DrainVariety , related_name='filter_drain_variety' ,
                                blank=True ,
                                null=True ,
                                on_delete=models.SET_NULL ,
                                help_text=_('Тип модели фильтр-регулятора') ,
                                verbose_name=_("Тип"))
    filtration_rating = models.DecimalField(
        max_digits=5 , decimal_places=1 ,
        null=True , blank=True ,
        verbose_name=_("Тонкость фильтрации (мкм)")
    )
    MATERIAL_CHOICES = [
        ('bronze' , 'Спеченная бронза') ,
        ('plastic' , 'Пористый полимер') ,
        ('ss' , 'Нержавеющая сетка') ,
    ]
    filter_element_material = models.CharField(max_length=20 , choices=MATERIAL_CHOICES , verbose_name=_("Материал фильтрующего элемента"))





    flow_rate = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name=_("Макс. расход (л/мин)")
    )
    WALL_MOUNTING_CHOICES = [
        ('no' , 'Нет') ,
        ('yes' , 'В комплекте') ,
    ]
    wall_mounting_included = models.CharField(max_length=20 , choices=WALL_MOUNTING_CHOICES, default='yes',
                                               verbose_name=_("Настенное крепление в комплекте"))
    has_shut_off_valve = models.BooleanField(default=False, verbose_name=_("Отсечной клапан в комплекте"))
    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict , blank=True ,
        verbose_name=_("Параметры") ,
        help_text=_("signal_type, resistance, range и т.д.")
    )
    class Meta:
        verbose_name = _("Фильтр-регулятор")
        verbose_name_plural = _("Фильтр-регуляторы")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.name} ({self.code})"