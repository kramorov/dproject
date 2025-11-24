# # valve_data/models/dimension_models.py
# from django.db import models
# from django.utils.translation import gettext_lazy as _
# from django.core.exceptions import ValidationError
#
# from media_library.models import MediaLibraryItem
# from params.models import DnVariety, PnVariety
# from producers.models import Brands
# from .base_models import  ValveVariety
# # from .mixins.dimension_mixins import DimensionDataMixin
#
# import logging
# logger = logging.getLogger(__name__)
#
# class ValveDimensionTable(models.Model):
#     """Таблица ВГХ для линейки арматуры - к этой таблице привязываем все данные - чертежи, таблицы значений"""
#     name = models.CharField(
#         max_length=100,
#         verbose_name=_('Название таблицы'),
#         help_text=_('Название таблицы ВГХ')
#     )
#     code = models.CharField(
#         max_length=50,
#         unique=True,
#         help_text=_('Код шаблона ВГХ'),
#         verbose_name=_('Код шаблона')
#     )
#     valve_brand = models.ForeignKey(
#         Brands,
#         blank=True,
#         null=True,
#         on_delete=models.SET_NULL,
#         related_name='dimension_table_valve_brand',
#         help_text=_('Бренд серии арматуры'),
#         verbose_name=_("Бренд")
#     )
#     valve_variety = models.ForeignKey(
#         ValveVariety,
#         blank=True,
#         null=True,
#         on_delete=models.SET_NULL,
#         related_name='dimension_table_valve_variety',
#         help_text=_('Тип арматуры'),
#         verbose_name=_("Тип арматуры")
#     )
#     # Связь с чертежами из медиабиблиотеки
#     drawings = models.ManyToManyField(
#         MediaLibraryItem,
#         through='DimensionTableDrawingItem',
#         through_fields=('dimension_table', 'drawing'),
#         related_name='dimension_tables',
#         verbose_name=_("Чертежи"),
#         help_text=_("Чертежи, связанные с этой таблицей ВГХ")
#     )
#     description = models.TextField(
#         blank=True,
#         verbose_name=_('Описание'),
#         help_text=_('Описание таблицы ВГХ')
#     )
#
#     class Meta:
#         verbose_name = _("Таблица ВГХ")
#         verbose_name_plural = _("Таблицы ВГХ")
#
#     def __str__(self):
#         return f"{self.name}"
#     def _build_param_value_table(self, data_queryset, include_objects=False):
#         """Построение таблицы параметров-значений"""
#         table = []
#
#         for data in data_queryset:
#             param_info = {
#                 'name': data.parameter.name,
#                 'legend': data.parameter.legend,
#                 'parameter_variety': data.parameter.parameter_variety.name if data.parameter.parameter_variety else None,
#                 'value': data.get_display_value()
#             }
#
#             if include_objects:
#                 param_info['parameter_object'] = data.parameter
#                 param_info['value_object'] = data
#                 if data.parameter.parameter_variety:
#                     param_info['parameter_variety_object'] = data.parameter.parameter_variety
#
#             table.append(param_info)
#
#         return table
#
#     def get_complete_dimension_data(self, dn_value, pn_value, include_objects=False):
#         """
#         Комплексный метод для получения всех данных (параметры + изображения)
#         Использует существующие геттеры класса
#         """
#         try:
#             # Используем геттер для получения данных параметров
#             paramvaluestable, response_str, alt_param_table = self.get_dimension_data_by_dn_pn(
#                 dn_value, pn_value, include_objects
#             )
#
#             # Используем геттер для получения изображений
#             images_data = self._get_images_by_dn_pn(dn_value, pn_value, include_objects)
#
#             return {
#                 'parameters': paramvaluestable,
#                 'images': images_data,
#                 'message': response_str,
#                 'alternatives': alt_param_table,
#                 'dn': dn_value,
#                 'pn': pn_value,
#                 'table_name': self.name,
#                 'table_code': self.code
#             }
#
#         except Exception as e:
#             logger.error(f"Ошибка в get_complete_dimension_data: {e}")
#             return {
#                 'parameters': None,
#                 'images': [],
#                 'message': f"Ошибка при получении данных: {str(e)}",
#                 'alternatives': None,
#                 'dn': dn_value,
#                 'pn': pn_value,
#                 'table_name': self.name,
#                 'table_code': self.code
#             }