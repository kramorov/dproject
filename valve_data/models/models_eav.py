# from django.db import models
# from django.utils.translation import gettext_lazy as _
#
# from .models_valve_line_properties import ValveVariety
#
#
# class EAVAttribute(models.Model) :
#     """Атрибут EAV системы"""
#     name = models.CharField(max_length=100 , verbose_name=_("Название атрибута"))
#     code = models.CharField(max_length=50 , unique=True , verbose_name=_("Код атрибута"))
#     description = models.TextField(blank=True , verbose_name=_("Описание"))
#     data_type = models.CharField(
#         max_length=20 ,
#         choices=[
#             ('string' , _('Строка')) ,
#             ('integer' , _('Целое число')) ,
#             ('float' , _('Десятичное число')) ,
#             ('boolean' , _('Да/Нет')) ,
#         ] ,
#         default='string' ,
#         verbose_name=_("Тип данных")
#     )
#     unit = models.CharField(max_length=20 , blank=True , verbose_name=_("Единица измерения"))
#
#     class Meta :
#         verbose_name = _("Атрибут")
#         verbose_name_plural = _("Атрибуты")
#         ordering = ['name']
#
#     def __str__(self) :
#         return f"{self.name}"
#
#
# class EAVValue(models.Model) :
#     """Справочник значений для атрибутов"""
#     attribute = models.ForeignKey(
#         EAVAttribute ,
#         on_delete=models.CASCADE ,
#         related_name='possible_values' ,
#         verbose_name=_("Атрибут")
#     )
#     value = models.CharField(max_length=200 , verbose_name=_("Значение"))
#     display_name = models.CharField(max_length=200 , verbose_name=_("Отображаемое название"))
#     description = models.TextField(blank=True , verbose_name=_("Описание"))
#     order = models.IntegerField(default=0 , verbose_name=_("Порядок"))
#     is_active = models.BooleanField(default=True , verbose_name=_("Активно"))
#
#     class Meta :
#         verbose_name = _("Значение атрибута")
#         verbose_name_plural = _("Значения атрибутов")
#         ordering = ['attribute' , 'order' , 'value']
#         unique_together = ['attribute' , 'value']
#
#     def __str__(self) :
#         return f"{self.display_name}"
#
#
# class ValveVarietyAttribute(models.Model) :
#     """Связь разновидности арматуры с допустимыми атрибутами"""
#     valve_variety = models.ForeignKey(
#         ValveVariety ,
#         on_delete=models.CASCADE ,
#         related_name='allowed_attributes' ,
#         verbose_name=_("Разновидность арматуры")
#     )
#     attribute = models.ForeignKey(
#         EAVAttribute ,
#         on_delete=models.CASCADE ,
#         related_name='valve_varieties' ,
#         verbose_name=_("Атрибут")
#     )
#     is_required = models.BooleanField(default=False , verbose_name=_("Обязательный"))
#     order = models.IntegerField(default=0 , verbose_name=_("Порядок"))
#
#     class Meta :
#         verbose_name = _("Атрибут разновидности")
#         verbose_name_plural = _("Атрибуты разновидностей")
#         ordering = ['valve_variety' , 'order']
#         unique_together = ['valve_variety' , 'attribute']
#
#     def __str__(self) :
#         return f"{self.attribute}"
#
# #
# # class ValveSeriesAttributeValue(models.Model) :
# #     """Значения атрибутов для конкретной серии арматуры"""
# #     valve_series = models.ForeignKey(
# #         ValveLineSeries ,
# #         on_delete=models.CASCADE ,
# #         related_name='attribute_values' ,
# #         verbose_name=_("Серия арматуры")
# #     )
# #     attribute = models.ForeignKey(
# #         EAVAttribute ,
# #         on_delete=models.CASCADE ,
# #         related_name='series_values' ,
# #         verbose_name=_("Атрибут")
# #     )
# #     # Может быть либо ссылкой на справочное значение, либо произвольным значением
# #     predefined_value = models.ForeignKey(
# #         EAVValue ,
# #         on_delete=models.CASCADE ,
# #         null=True ,
# #         blank=True ,
# #         related_name='series_usages' ,
# #         verbose_name=_("Значение из справочника")
# #     )
# #     custom_value = models.CharField(
# #         max_length=500 ,
# #         blank=True ,
# #         verbose_name=_("Произвольное значение")
# #     )
# #
# #     class Meta :
# #         verbose_name = _("Значение атрибута серии")
# #         verbose_name_plural = _("Значения атрибутов серий")
# #         unique_together = ['valve_series' , 'attribute']
# #
# #     def __str__(self) :
# #         return f"{self.get_display_value()}"
# #
# #     def clean(self) :
# #         """Валидация: либо справочное значение, либо произвольное"""
# #         # Сначала проверяем базовые условия
# #         if self.predefined_value and self.custom_value :
# #             raise ValidationError(_("Можно указать либо значение из справочника, либо произвольное значение"))
# #
# #         if not self.predefined_value and not self.custom_value :
# #             # Разрешаем сохранение без значения (может быть заполнено позже)
# #             # Вместо ошибки просто предупреждаем
# #             pass
# #
# #         # Проверяем, что атрибут допустим для разновидности арматуры
# #         if (self.valve_series and self.valve_series.valve_line and
# #                 self.valve_series.valve_line.valve_variety and self.attribute_id) :
# #             allowed_attributes = self.valve_series.valve_line.valve_variety.allowed_attributes.values_list(
# #                 'attribute_id' , flat=True)
# #             if self.attribute_id not in allowed_attributes :
# #                 raise ValidationError(_("Этот атрибут не допустим для данной разновидности арматуры"))
# #
# #         # Проверяем, что predefined_value соответствует attribute
# #         if self.predefined_value and self.attribute and self.predefined_value.attribute != self.attribute :
# #             raise ValidationError(_("Выбранное значение не соответствует атрибуту"))
# #
# #     def get_display_value(self) :
# #         """Получить отображаемое значение"""
# #         if self.predefined_value :
# #             return self.predefined_value.display_name
# #         return self.custom_value or _("Не указано")
# #
# #     def get_actual_value(self) :
# #         """Получить фактическое значение"""
# #         if self.predefined_value :
# #             return self.predefined_value.value
# #         return self.custom_value