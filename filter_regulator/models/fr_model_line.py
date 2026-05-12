#filter_requlator/models/fr_model_line.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from filter_regulator.models import FilterRegulatorVariety
from materials.models import MaterialGeneral , MaterialSpecified
from producers.models import Brands


class FilterRegulatorModelLine(models.Model):
    """
    Серия пневматических фитингов
    """

    name = models.CharField(max_length=100,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название фильтр-регулятора'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код фильтр-регулятора"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание разновидности серии фильтр-регуляторов'))
    name_template = models.TextField(blank=True, null=True,
                                     verbose_name=_("Шаблон названия"),
                                     help_text=_('Шаблон для текстового названия фильтр-регулятора'))
    description_template = models.TextField(blank=True, null=True,verbose_name=_("Шаблон описания"),
                                            help_text=_('Шаблон для описания фильтр-регулятора'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    brand = models.ForeignKey(Brands, related_name='filter_model_line_brand', blank=True, null=True,
                              on_delete=models.SET_NULL,
                              help_text=_('Бренд фильтр-регулятора'),
                              verbose_name=_("Бренд"))
    filter_variety = models.ForeignKey(FilterRegulatorVariety, related_name='filter_nodel_line_variety',
                                       blank=True,
                                       null=True,
                                       on_delete=models.SET_NULL,
                                       help_text=_('Тип модели фильтр-регулятора'),
                                       verbose_name=_("Тип"))
    # body_material - для фильтрации, в описание не идет
    body_material = models.ForeignKey(MaterialGeneral, related_name='filter_model_line_body_material',
                                      blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Корпус'),
                                      verbose_name=_('Тип материала корпуса'))
    # body_material_specified - для фильтрации, в описание не идет
    body_material_specified = models.ForeignKey(MaterialSpecified , related_name='filter_model_line_body_material_specified' ,
                                                blank=True , null=True ,
                                                on_delete=models.SET_NULL ,
                                                help_text=_('Материал корпуса арматуры') ,
                                                verbose_name=_('Материал корпуса'))
    # body_material_text - для описания
    body_material_text = models.CharField(max_length=200,
                                          blank=True,
                                          null=True,
                                          help_text=_('Материал корпус фильтр-регулятора'),
                                          verbose_name=_("Корпус (текст)"))
    # bowl_material - для фильтрации, в описание не идет
    bowl_material = models.ForeignKey(MaterialGeneral, related_name='filter_model_line_bowl_material',
                                      blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Стакан'),
                                      verbose_name=_('Тип материала стакана'))
    # bowl_material_text - для описания
    bowl_material_text = models.CharField(max_length=200,
                                          blank=True,
                                          null=True,
                                          help_text=_('Материал стакана фильтр-регулятора'),
                                          verbose_name=_("Стакан (текст)"))
    # protection_material - для описания
    protection_material = models.CharField(max_length=200 ,
                                           help_text=_('Материал стакана фильтр-регулятора'),
                                           verbose_name=_("Материал кожуха (текст)"))  # Алюминиевый кожух


    work_temp_min = models.IntegerField(
        null=True, blank=True, default=-40,
        help_text=_('Минимальная рабочая температура, °С'),
        verbose_name=_('Т раб.мин, °С')
    )
    work_temp_max = models.IntegerField(
        null=True, blank=True, default=120,
        help_text=_('Максимальная рабочая температура, °С'),
        verbose_name=_('Т раб.макс, °С'))

    pressure_min = models.DecimalField(decimal_places=2, max_digits=6,
                                       null=True, blank=True, default=0,
                                       help_text=_('Минимальное давление на выходе, бар'),
                                       verbose_name=_('P выход.мин, бар'))

    pressure_max = models.DecimalField(decimal_places=2, max_digits=6,
                                       null=True, blank=True, default=8,
                                       help_text=_('Максимальное давление на выходе, бар'),
                                       verbose_name=_('P выход.макс, бар'))
    pressure_inlet_max = models.DecimalField(decimal_places=2 , max_digits=6 ,
                                       null=True , blank=True , default=10 ,
                                       help_text=_('Максимальное рабочее давление, бар') ,
                                       verbose_name=_('P раб.макс, бар'))
    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict , blank=True ,
        verbose_name=_("Параметры") ,
        help_text=_("signal_type, resistance, range и т.д.")
    )

    class Meta:
        ordering = ['brand', 'code']
        verbose_name = _('Серия фильтр-регуляторов')
        verbose_name_plural = _('Серии фильтр-регуляторов')

    def __str__(self):
        return self.name

    @property
    def temperature_range_display(self):
        """Отображаемый диапазон рабочих температур"""
        return f'{self.work_temp_min}..{self.work_temp_max}'

    @property
    def pressure_range_display(self):
        """Отображаемый диапазон регулировки давления"""
        return f'{self.pressure_min}..{self.pressure_max}'