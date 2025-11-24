# from django.db import models
# from django.utils.translation import gettext_lazy as _
#
# from djangoProject1.common_models.abstract_models import AbstractValveModel
# from materials.models import MaterialGeneral , MaterialSpecified
# from params.models import ValveFunctionVariety , SealingClass , BodyColor , ValveActuationVariety , \
#     WarrantyTimePeriodVariety , OptionVariety
# from producers.models import Producer , Brands
# from valve_data.models.models_valve_line_properties import ValveConnectionToPipe , ValveVariety , ConstructionVariety , PortQty
#
#
# class ValveLine(models.Model) :
#     name = models.CharField(max_length=100 , blank=True , null=True , help_text=_(
#         "Символьное обозначение (артикул) серии арматуры") ,
#                             verbose_name=_(
#                                 "Серия арматуры"))
#     code = models.CharField(max_length=50 , blank=True , null=True ,  # unique=True ,
#                             verbose_name=_("Код серии арматуры"))
#     description = models.TextField(blank=True , verbose_name=_("Описание"))
#     features_text = models.TextField(blank=True , verbose_name=_("Особенности"))
#     application_text = models.TextField(blank=True , verbose_name=_("Где применяется"))
#     sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))
#     is_active = models.BooleanField(default=True , verbose_name=_("Активно"))
#     is_approved= models.BooleanField(default=False , verbose_name=_("Проверено"))
#
#     valve_producer = models.ForeignKey(Producer , related_name='valve_line_valve_producer' , blank=True , null=True ,
#                                        on_delete=models.SET_NULL ,
#                                        help_text=_('Производитель семейства серий арматуры') ,
#                                        verbose_name=_("Производитель семейства серий арматуры"))
#     valve_brand = models.ForeignKey(Brands , related_name='valve_line_valve_brand' , blank=True , null=True ,
#                                     on_delete=models.SET_NULL ,
#                                     help_text=_('Бренд семейства серий  арматуры') ,
#                                     verbose_name=_("Бренд семейства серий  арматуры"))
#     valve_variety = models.ForeignKey(ValveVariety , related_name='valve_line_valve_variety' , blank=True , null=True ,
#                                       on_delete=models.SET_NULL ,
#                                       help_text=_('Тип арматуры семейства арматуры производителя') ,
#                                       verbose_name=_("Тип арматуры семейства арматуры производителя"))
#     valve_function = models.ForeignKey(ValveFunctionVariety , related_name='valve_line_valve_function' , blank=True ,
#                                        null=True ,
#                                        on_delete=models.SET_NULL ,
#                                        help_text=_('Тип арматуры - регулирующая, запорная') ,
#                                        verbose_name=_("Типы арматуры - регулирующая, запорная"))
#     valve_sealing_class = models.ForeignKey(SealingClass , related_name='valve_line_sealing_class' , blank=True ,
#                                             null=True ,
#                                             on_delete=models.SET_NULL ,
#                                             help_text=_('Класс герметичности арматуры ') ,
#                                             verbose_name=_("Класс герметичности арматуры "))
#     body_material = models.ForeignKey(MaterialGeneral , related_name='valve_line_body_material' , blank=True ,
#                                       null=True ,
#                                       on_delete=models.SET_NULL , help_text=_('Тип материала корпуса') ,
#                                       verbose_name=_('Тип материала корпуса'))
#     body_material_specified = models.ForeignKey(MaterialSpecified , related_name='valve_line_body_material' ,
#                                                 blank=True , null=True ,
#                                                 on_delete=models.SET_NULL ,
#                                                 help_text=_('Материал корпуса арматуры'))
#     shut_element_material = models.ForeignKey(MaterialGeneral , related_name='valve_line_shut_element_material' ,
#                                               blank=True , null=True ,
#                                               on_delete=models.SET_NULL ,
#                                               help_text=_(
#                                                   'Тип материала запорного элемента (диска, шара, ножа, клина)') ,
#                                               verbose_name=_('Тип материала запорного элемента'))
#     shut_element_material_specified = models.ForeignKey(MaterialSpecified ,
#                                                         related_name='valve_line_shut_element_material' ,
#                                                         blank=True ,
#                                                         null=True ,
#                                                         on_delete=models.SET_NULL ,
#                                                         help_text=_(
#                                                             'Марка материала запорного элемента (диска, шара, ножа, клина)') ,
#                                                         verbose_name=_('Материал запорного элемента'))
#     port_qty = models.ForeignKey(PortQty , related_name='valve_line_port_qty' , blank=True , null=True ,
#                                        on_delete=models.CASCADE ,
#                                        help_text=_('Количество портов') ,
#                                        verbose_name=_("Количество портов"))
#     construction_variety = models.ForeignKey(ConstructionVariety , related_name='valve_line_port_qty' , blank=True , null=True ,
#                                  on_delete=models.CASCADE ,
#                                  help_text=_('Тип конструкции') ,
#                                  verbose_name=_("Тип конструкции"))
#     #  поле для цветов корпуса (через промежуточную модель)
#     body_colors = models.ManyToManyField(
#         BodyColor ,
#         through='ValveLineBodyColor' ,
#         through_fields=('valve_line' , 'body_color') ,
#         related_name='valve_line_body_color' ,
#         verbose_name=_("Цвета корпуса") ,
#         blank=True
#     )
#     sealing_element_options = models.ManyToManyField(
#         MaterialSpecified ,
#         through='ValveLineSealingMaterial' ,
#         through_fields=('valve_line' , 'sealing_element_material') ,
#         related_name='valve_line_sealing_element_options' ,
#         verbose_name=_("Варианты материалов уплотнения") ,
#         blank=True
#     )
#     valve_actuation_options = models.ManyToManyField(
#         ValveActuationVariety ,
#         through='ValveLineValveActuationVariety' ,
#         through_fields=('valve_line' , 'valve_actuation') ,
#         related_name='valve_line_valve_actuation_options' ,
#         verbose_name=_("Варианты типов механизмов приведения в действие арматуры") ,
#         blank=True
#     )
#     pipe_connection = models.ForeignKey(ValveConnectionToPipe ,
#                                         related_name='valve_line_pipe_connection' ,
#                                         blank=True ,
#                                         null=True ,
#                                         on_delete=models.CASCADE ,
#                                         help_text=_('Тип присоединения арматуры к трубе'))
#
#     warranty_period_min = models.IntegerField(default=0 , help_text=_("Гарантийный срок, мес") ,
#                                               verbose_name=_("Гарантийный срок мин, мес"))
#     warranty_period_min_variety = models.ForeignKey(WarrantyTimePeriodVariety ,
#                                                     related_name='valve_line_warranty_period_min_variety' ,
#                                                     blank=True ,
#                                                     null=True ,
#                                                     on_delete=models.CASCADE ,
#                                                     help_text=_('Гарантийный срок мин описание') ,
#                                                     verbose_name=_("Гарантийный срок мин описание"))
#
#     warranty_period_max = models.IntegerField(default=0 , help_text=_("Гарантийный срок не более, мес") ,
#                                               verbose_name=_("Гарантийный срок не более, мес"))
#     warranty_period_max_variety = models.ForeignKey(WarrantyTimePeriodVariety ,
#                                                     related_name='valve_line_warranty_period_max_variety' ,
#                                                     blank=True ,
#                                                     null=True ,
#                                                     on_delete=models.CASCADE ,
#                                                     help_text=_('Гарантийный срок не более, описание') ,
#                                                     verbose_name=_("Гарантийный срок не более, описание"))
#     valve_in_service_years = models.IntegerField(default=0 ,
#                                                  help_text=_("Расчетный срок эксплуатации - не менее, лет") ,
#                                                  verbose_name=_("Расчетный срок эксплуатации - не менее, лет"))
#     valve_in_service_years_comment = models.CharField(max_length=500 , blank=True ,
#                                                       help_text=_("Условие выработки расчетного срока эксплуатации") ,
#                                                       verbose_name=_("Условие выработки расчетного срока эксплуатации"))
#
#     valve_in_service_cycles = models.IntegerField(default=0 , blank=True , help_text=_("Расчетное количество циклов") ,
#                                                   verbose_name=_("Расчетное количество циклов"))
#     valve_in_service_cycles_comment = models.CharField(max_length=500 , blank=True ,
#                                                        help_text=_("Условие выработки расчетного количества циклов") ,
#                                                        verbose_name=_("Условие выработки расчетного количества циклов"))
#
#     class Meta :
#         ordering = ['valve_variety' , 'valve_producer' , 'name']
#         verbose_name = _("Семейство серий арматуры")
#         verbose_name_plural = _("Семейство серий арматуры")
#
#     def __str__(self) :
#         return self.name
#
#
# class ValveLineBodyColor(models.Model) :
#     """Связь серии арматуры с цветами корпуса и типами исполнения"""
#     valve_line = models.ForeignKey(
#         ValveLine ,
#         on_delete=models.CASCADE ,
#         related_name='valve_line_body_colors' ,
#         verbose_name=_("Серия арматуры")
#     )
#     body_color = models.ForeignKey(
#         BodyColor ,
#         on_delete=models.CASCADE ,
#         related_name='valve_line_body_color_usages' ,
#         verbose_name=_("Цвет корпуса")
#     )
#     option_variety = models.ForeignKey(
#         OptionVariety ,
#         on_delete=models.CASCADE ,
#         related_name='valve_line_body_color_option_variety' ,
#         verbose_name=_("Стандарт или опция")
#     )
#     option_code_template = models.CharField(max_length=100 , blank=True , null=True ,
#                                             help_text=_("Шаблон кодировки для опции") ,
#                                             verbose_name=_("Шаблон кодировки для опции"))
#     sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))
#     is_available = models.BooleanField(default=True , verbose_name=_("Доступно"))
#     additional_cost = models.DecimalField(
#         max_digits=10 ,
#         decimal_places=2 ,
#         default=0 ,
#         verbose_name=_("Дополнительная стоимость") ,
#         help_text=_("Дополнительная стоимость для этого цвета и типа исполнения")
#     )
#     lead_time_days = models.IntegerField(
#         default=0 ,
#         verbose_name=_("Срок изготовления (дни)") ,
#         help_text=_("Дополнительное время изготовления в днях")
#     )
#     notes = models.TextField(blank=True , verbose_name=_("Примечания"))
#
#     class Meta :
#         ordering = ['valve_line' , 'option_variety__sorting_order' , 'sorting_order']
#         verbose_name = _("Цвет корпуса серии")
#         verbose_name_plural = _("Цвета корпусов серий")
#         unique_together = ['valve_line' , 'body_color' , 'option_variety']
#
#     def __str__(self) :
#         return f"{self.valve_line} - {self.body_color} ({self.option_variety})"
#
#     def clean(self) :
#         """Валидация связи цвета и типа исполнения"""
#         # Можно добавить дополнительные проверки, если нужно
#         super().clean()
#
#
# class ValveLineValveActuationVariety(models.Model) :
#     """Связь серии арматуры с типами механизма приведения в действие арматуры - ручка/редуктор/привод"""
#     valve_line = models.ForeignKey(
#         ValveLine ,
#         on_delete=models.CASCADE ,
#         related_name='valve_line_valve_actuation' ,
#         verbose_name=_("Серия арматуры")
#     )
#     valve_actuation = models.ForeignKey(
#         ValveActuationVariety ,
#         on_delete=models.CASCADE ,
#         related_name='valve_line_valve_actuation' ,
#         verbose_name=_("Тип механизма приведения в действие арматуры")
#     )
#     option_code_template = models.CharField(max_length=100 , blank=True , null=True ,
#                                             help_text=_("Шаблон кодировки для опции") ,
#                                             verbose_name=_("Шаблон кодировки для опции"))
#
#     option_variety = models.ForeignKey(
#         OptionVariety ,
#         on_delete=models.CASCADE ,
#         related_name='valve_line_valve_actuation_variety' ,
#         verbose_name=_("Стандарт или опция")
#     )
#     sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))
#     is_available = models.BooleanField(default=True , verbose_name=_("Доступно"))
#     additional_cost = models.DecimalField(
#         max_digits=10 ,
#         decimal_places=2 ,
#         default=0 ,
#         verbose_name=_("Дополнительная стоимость") ,
#         help_text=_("Дополнительная стоимость для этого цвета и типа исполнения")
#     )
#     lead_time_days = models.IntegerField(
#         default=0 ,
#         verbose_name=_("Срок изготовления (дни)") ,
#         help_text=_("Дополнительное время изготовления в днях")
#     )
#     notes = models.TextField(blank=True , verbose_name=_("Примечания"))
#
#     class Meta :
#         ordering = ['valve_line' , 'option_variety__sorting_order' , 'sorting_order']
#         verbose_name = _("Тип механизма приведения в действие арматуры в серии")
#         verbose_name_plural = _("Типы механизмов приведения в действие арматуры в серии")
#         unique_together = ['valve_line' , 'valve_actuation' , 'option_variety']
#
#     def __str__(self) :
#         return f"{self.valve_line} - {self.valve_actuation} ({self.option_variety})"
#
#     def clean(self) :
#         """Валидация связи цвета и типа исполнения"""
#         # Можно добавить дополнительные проверки, если нужно
#         super().clean()
#
#
# class ValveLineSealingMaterial(models.Model) :
#     """Связь серии арматуры с цветами корпуса и типами исполнения"""
#     valve_line = models.ForeignKey(
#         ValveLine ,
#         on_delete=models.CASCADE ,
#         related_name='valve_line_sealing_material' ,
#         verbose_name=_("Серия арматуры")
#     )
#     sealing_element_material = models.ForeignKey(
#         MaterialSpecified ,
#         on_delete=models.CASCADE ,
#         related_name='valve_line_sealing_material' ,
#         verbose_name=_("Материал уплотнения")
#     )
#     option_code_template = models.CharField(max_length=100 , blank=True , null=True ,
#                                             help_text=_("Шаблон кодировки для опции") ,
#                                             verbose_name=_("Шаблон кодировки для опции"))
#     option_variety = models.ForeignKey(
#         OptionVariety ,
#         on_delete=models.CASCADE ,
#         related_name='valve_line_sealing_material_option_variety' ,
#         verbose_name=_("Стандарт или опция")
#     )
#     sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))
#     is_available = models.BooleanField(default=True , verbose_name=_("Доступно"))
#     additional_cost = models.DecimalField(
#         max_digits=10 ,
#         decimal_places=2 ,
#         default=0 ,
#         verbose_name=_("Дополнительная стоимость") ,
#         help_text=_("Дополнительная стоимость для этого цвета и типа исполнения")
#     )
#     lead_time_days = models.IntegerField(
#         default=0 ,
#         verbose_name=_("Срок изготовления (дни)") ,
#         help_text=_("Дополнительное время изготовления в днях")
#     )
#     notes = models.TextField(blank=True , verbose_name=_("Примечания"))
#
#     class Meta :
#         ordering = ['valve_line' , 'option_variety__sorting_order' , 'sorting_order']
#         verbose_name = _("Материал уплотнения серии")
#         verbose_name_plural = _("Материалы уплотнения серий")
#         unique_together = ['valve_line' , 'sealing_element_material' , 'option_variety']
#
#     def __str__(self) :
#         return f"{self.valve_line} - {self.sealing_element_material} ({self.option_variety})"
#
#     def clean(self) :
#         """Валидация связи цвета и типа исполнения"""
#         # Можно добавить дополнительные проверки, если нужно
#         super().clean()
#
#
# class ValveModelData(AbstractValveModel) :
#     symbolic_code = models.CharField(max_length=50 , help_text=_('Символьное обозначение (артикул)\
#      модели арматуры производителя'))
#     valve_model_model_line = models.ForeignKey(ValveLine , related_name='valve_model_model_line' , blank=True ,
#                                                null=True ,
#                                                on_delete=models.SET_NULL , help_text=_('Серия арматуры производителя'))
#
#     class Meta :
#         ordering = ['valve_model_model_line' , 'symbolic_code']
#         verbose_name = _("Тех.данные арматуры")
#         verbose_name_plural = _("Тех.данные арматуры")
#
#     def __str__(self) :
#         return self.symbolic_code
