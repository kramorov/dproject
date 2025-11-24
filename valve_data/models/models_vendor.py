# from django.db import models
# from django.utils.translation import gettext_lazy as _
#
# from params.models import BodyColor , ValveActuationVariety , OptionVariety
# from producers.models import Producer , Brands
# from valve_data.models import ValveLine
#
#
# class TestModel(models.Model) :
#     name = models.CharField(max_length=100)
#
#     class Meta :
#         app_label = 'valve_data'
#
#
# class VendorValveLine(models.Model) :
#     # Основная связь с OEM серией
#     oem_valve_line = models.ForeignKey(
#         ValveLine,  # строковая ссылка на модель в другом файле
#         related_name='vendor_valve_line_oem_valve_line' ,
#         on_delete=models.CASCADE ,
#         help_text=_('Оригинальная серия арматуры OEM производителя') ,
#         verbose_name=_("OEM серия арматуры")
#     )
#
#     # Данные вендора
#     vendor = models.ForeignKey(
#         Producer ,
#         related_name='vendor_valve_line_vendor' ,
#         on_delete=models.CASCADE ,
#         help_text=_('Вендор, который продает эту серию под своим артикулом') ,
#         verbose_name=_("Вендор")
#     )
#
#     vendor_brand = models.ForeignKey(
#         Brands ,
#         related_name='vendor_valve_line_vendor_brand' ,
#         blank=True ,
#         null=True ,
#         on_delete=models.SET_NULL ,
#         help_text=_('Бренд вендора для этой серии') ,
#         verbose_name=_("Бренд вендора")
#     )
#
#     # Артикулы вендора
#     code = models.CharField(
#         max_length=50 ,
#         verbose_name=_("Артикул серии арматуры вендора") ,
#         help_text=_("Уникальный артикул вендора для этой серии")
#     )
#
#     name = models.CharField(
#         max_length=100 ,
#         blank=True ,
#         null=True ,
#         verbose_name=_("Название серии арматуры вендора") ,
#         help_text=_("Название серии арматуры вендора")
#     )
#
#     # Описание
#     description = models.TextField(
#         blank=True ,
#         verbose_name=_("Описание серии арматуры вендора") ,
#         help_text=_("Описание серии арматуры вендора")
#     )
#
#     # Статусы
#     sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))
#     is_active = models.BooleanField(default=True , verbose_name=_("Активно"))
#     is_approved = models.BooleanField(default=False , verbose_name=_("Проверено"))
#
#
#     # Специфичные для вендора варианты (переопределяют OEM)
#     vendor_specific_body_colors = models.ManyToManyField(
#         BodyColor ,
#         through='VendorValveLineBodyColor' ,
#         related_name='vendor_valve_line_body_colors' ,
#         verbose_name=_("Цвета корпуса серии арматуры вендора") ,
#         blank=True ,
#         help_text=_("Цвета корпуса серии арматуры вендора (могут отличаться от OEM)")
#     )
#
#     vendor_specific_actuation_options = models.ManyToManyField(
#         ValveActuationVariety ,
#         through='VendorValveLineValveActuationVariety' ,
#         related_name='vendor_valve_line_actuation_options' ,
#         verbose_name=_("Типы приводов серии арматуры вендора") ,
#         blank=True ,
#         help_text=_("Типы приводов, доступные у вендора (могут быть дополнительные варианты)")
#     )
#
#     class Meta :
#         ordering = ['vendor' , 'code']
#         verbose_name = _("Серия арматуры вендора")
#         verbose_name_plural = _("Серии арматуры вендоров")
#         unique_together = ['vendor' , 'oem_valve_line', 'code']  # Уникальный артикул у каждого вендора
#
#     def __str__(self) :
#         return f"{self.code} ({self.vendor}) - {self.oem_valve_line.name}"
#
#
# class VendorValveLineBodyColor(models.Model) :
#     """Промежуточная модель для цветов корпуса у вендора"""
#     valve_line = models.ForeignKey(
#         'VendorValveLine',  # строковая ссылка на модель в этом же файле
#             on_delete=models.CASCADE ,related_name='vendor_body_colors')
#
#     body_color = models.ForeignKey(BodyColor ,on_delete=models.CASCADE ,verbose_name=_("Цвет корпуса "))
#
#     color_code = models.CharField(
#         max_length=50 ,
#         blank=True ,
#         verbose_name=_("Код цвета корпуса") ,
#         help_text=_("Артикул/код цвета у вендора")
#     )
#
#     option_variety = models.ForeignKey(OptionVariety ,on_delete=models.CASCADE ,verbose_name=_("Стандарт или опция"))
#     sorting_order = models.IntegerField(default=0 ,verbose_name=_("Порядок сортировки"))
#     is_active = models.BooleanField(default=True ,verbose_name=_("Доступно") )
#
#     additional_cost = models.DecimalField(
#         max_digits=10 ,
#         decimal_places=2 ,
#         default=0 ,
#         verbose_name=_("Дополнительная стоимость")
#     )
#
#     lead_time_days = models.IntegerField(
#         default=0 ,
#         verbose_name=_("Срок изготовления (дни)")
#     )
#
#     notes = models.TextField(
#         blank=True ,
#         verbose_name=_("Примечания")
#     )
#
#     class Meta :
#         ordering = ['valve_line' , 'sorting_order']
#         verbose_name = _("Цвет корпуса серии вендора")
#         verbose_name_plural = _("Цвета корпусов серии вендора")
#         unique_together = ['valve_line' , 'body_color' , 'option_variety']
#
#
# class VendorValveLineValveActuationVariety(models.Model) :
#     """Промежуточная модель для приводов у вендора"""
#     valve_line = models.ForeignKey(
#         'VendorValveLine',  # строковая ссылка
#         on_delete=models.CASCADE ,
#         related_name='vendor_actuation_options'
#     )
#
#     valve_actuation = models.ForeignKey(
#         ValveActuationVariety ,
#         on_delete=models.CASCADE ,
#         verbose_name=_("Тип механизма приведения в действие арматуры вендора")
#     )
#
#     option_code_template = models.CharField(
#         max_length=50 ,
#         blank=True ,
#         verbose_name=_("Шаблон кодировки для опции") ,
#         help_text=_("АШаблон кодировки для опции")
#     )
#
#     option_variety = models.ForeignKey(
#         OptionVariety ,
#         on_delete=models.CASCADE ,
#         verbose_name=_("Стандарт или опция")
#     )
#
#     sorting_order = models.IntegerField(
#         default=0 ,
#         verbose_name=_("Порядок сортировки")
#     )
#
#     is_available = models.BooleanField(
#         default=True ,
#         verbose_name=_("Доступно")
#     )
#
#     additional_cost = models.DecimalField(
#         max_digits=10 ,
#         decimal_places=2 ,
#         default=0 ,
#         verbose_name=_("Дополнительная стоимость")
#     )
#
#     lead_time_days = models.IntegerField(
#         default=0 ,
#         verbose_name=_("Срок изготовления (дни)")
#     )
#
#     notes = models.TextField(
#         blank=True ,
#         verbose_name=_("Примечания")
#     )
#
#     class Meta :
#         ordering = ['valve_line' , 'option_variety__sorting_order' , 'sorting_order']
#         verbose_name = _("Тип механизма приведения в действие арматуры в серии вендора")
#         verbose_name_plural = _("Типы механизмов приведения в действие арматуры в серии вендора")
#         unique_together = ['valve_line' , 'valve_actuation' , 'option_variety']