# from django.db import models
# from django.utils.translation import gettext_lazy as _
#
#
# class ValveConnectionToPipe(models.Model) :
#     name = models.CharField(max_length=100 ,
#                             help_text=_("Символьное обозначение типа присоединения арматуры к трубе") ,
#                             verbose_name=_("Символьное обозначение типа присоединения арматуры к трубе"))
#     code = models.CharField(max_length=50 , unique=True ,
#                             verbose_name=_("Код типа присоединения арматуры к трубе"))
#     description = models.TextField(blank=True , verbose_name=_("Описание"))
#     sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))
#     is_active = models.BooleanField(default=True , verbose_name=_("Активно"))
#
#     class Meta :
#         ordering = ['sorting_order']
#         verbose_name = _("Тип присоединения арматуры к трубе")
#         verbose_name_plural = _("Типы присоединения арматуры к трубе")
#
#     def __str__(self) :
#         return self.name
#
#
# class ValveVariety(models.Model) :
#     symbolic_code = models.CharField(max_length=2 , help_text='Символьное обозначение \
#     типа арматуры' , verbose_name=_("Символьное обозначение типа арматуры"))
#     actuator_gearbox_combinations = models.CharField(max_length=10 , help_text='Символьное обозначение \
#     подходящего типа привода и редуктора' , verbose_name=_("Символьное обозначение \
#     подходящего типа привода и редуктора"))
#     text_description = models.CharField(max_length=200 , blank=True , help_text='Текстовое описание \
#     типа арматуры' , verbose_name=_("Текстовое описание типа арматуры"))
#
#     class Meta :
#         ordering = ['text_description']
#         verbose_name = _("Тип арматуры")
#         verbose_name_plural = _("Типы арматуры")
#
#     def __str__(self) :
#         return self.text_description
#
#
# class ConstructionVariety(models.Model) :
#     name = models.CharField(max_length=100 , help_text=_(
#         "Название типа конструкции вида арматуры") ,
#                             verbose_name=_("Название типа конструкции"))
#     valve_variety = models.ForeignKey(ValveVariety , related_name='construction_variety_valve_variety' ,
#                                       on_delete=models.CASCADE ,
#                                       help_text=_('Тип конструкции вида арматуры') ,
#                                       verbose_name=_("Тип конструкции вида арматуры"))
#     code = models.CharField(max_length=50 , unique=True ,
#                             verbose_name=_("Код типа конструкции"))
#     description = models.TextField(blank=True , verbose_name=_("Описание"))
#     sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))
#     is_active = models.BooleanField(default=True , verbose_name=_("Активно"))
#
#     class Meta :
#         ordering = ['sorting_order']
#         verbose_name = _("Название типа конструкции вида арматуры")
#         verbose_name_plural = _("Названия типа конструкции вида арматуры")
#
#     def __str__(self) :
#         return self.name
#
#
# class PortQty(models.Model) :
#     name = models.CharField(max_length=100 , help_text=_(
#         "Количество портов арматуры") , verbose_name=_("Количество портов арматуры"))
#     code = models.CharField(max_length=50 , unique=True , help_text=_(
#         "Код количества портов арматуры") ,
#                             verbose_name=_("Код количества портов арматуры"))
#     description = models.TextField(blank=True , verbose_name=_("Описание"))
#     sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))
#     is_active = models.BooleanField(default=True , verbose_name=_("Активно"))
#
#     class Meta :
#         ordering = ['sorting_order']
#         verbose_name = _("Количество портов арматуры")
#         verbose_name_plural = _("Количество портов арматуры")
#
#     def __str__(self) :
#         return self.name
