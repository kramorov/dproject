# # valve_data/mixins/dimension_base_mixins.py
# from collections import defaultdict
# import logging
#
# logger = logging.getLogger(__name__)
#
#
# class DimensionBaseMixin:
#     """Базовый миксин с общими методами без импортов моделей"""
#
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
#         """
#         paramvaluestable, response_str, alt_param_table = self.get_dimension_data_by_dn_pn(
#             dn_value, pn_value, include_objects
#         )
#
#         images_data = self._get_images_by_dn_pn(dn_value, pn_value, include_objects)
#
#         # Получаем название и код таблицы
#         table_name = getattr(self, 'name', 'Неизвестная таблица')
#         table_code = getattr(self, 'code', 'Неизвестный код')
#
#         return {
#             'parameters': paramvaluestable,
#             'images': images_data,
#             'message': response_str,
#             'alternatives': alt_param_table,
#             'dn': dn_value,
#             'pn': pn_value,
#             'table_name': table_name,
#             'table_code': table_code
#         }