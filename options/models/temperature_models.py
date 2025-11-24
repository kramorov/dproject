# options/models/temperature_models.py
# from django.db import models
# from django.utils.translation import gettext_lazy as _
# from django.core.exceptions import ValidationError
# from typing import List, Optional, Tuple, Any, Dict, Union
# from options.models.base_abstract_through_model import BaseThroughOption


# class BaseTemperatureThroughOption(BaseThroughOption):
#     """
#     Универсальная through-модель для температурных опций
#     Наследует от BaseThroughOption и добавляет температурные поля
#     """
#     work_temp_min = models.IntegerField(
#         default=0,
#         verbose_name=_('Т мин, °С'),
#         help_text=_('Минимальная рабочая температура, °С')
#     )
#     work_temp_max = models.IntegerField(
#         default=0,
#         verbose_name=_('Т макс, °С'),
#         help_text=_('Максимальная рабочая температура, °С')
#     )
#
#     class Meta:
#         abstract = True
#         ordering = ['is_default', 'sorting_order']  # Сначала стандартные опции
#
#     @classmethod
#     def create_default_option(cls , parent_obj) :
#         """Создать стандартную температурную опцию"""
#         parent_field = cls._get_parent_field_name()
#         return cls.objects.create(
#             **{parent_field : parent_obj} ,
#             work_temp_min=-20 ,
#             work_temp_max=80 ,
#             encoding='' ,  # Пустая кодировка для стандартного исполнения
#             description='Стандартный температурный диапазон' ,
#             is_default=True ,
#             sorting_order=0 ,
#             is_active=True
#         )
#     def get_display_name(self):
#         """Отображаемое имя с кодировкой или без"""
#         if self.encoding and self.encoding.strip():
#             return f"{self.encoding} ({self.work_temp_min}...{self.work_temp_max}°C)"
#         else:
#             return f"{self.work_temp_min}...{self.work_temp_max}°C"
#
#     def get_option_info(self , option_instance: Optional['BaseTemperatureThroughOption'] = None) -> Dict[str , Any] :
#         """Полная информация об опции с температурными данными"""
#         # Вызываем родительский метод
#         info = super().get_option_info(option_instance)
#
#         # Определяем, с каким экземпляром работаем
#         current_instance = option_instance or self
#
#         # Добавляем температурные данные
#         info.update({
#             'work_temp_min' : current_instance.work_temp_min ,
#             'work_temp_max' : current_instance.work_temp_max ,
#             'temperature_range' : f"{current_instance.work_temp_min}...{current_instance.work_temp_max}°C" ,
#         })
#         return info
#
#     def clean(self):
#         """Дополнительная валидация для температурных опций"""
#         super().clean()
#
#         # Валидация температурного диапазона
#         if self.work_temp_min and self.work_temp_max:
#             if self.work_temp_min >= self.work_temp_max:
#                 raise ValidationError({
#                     'work_temp_max': _('Максимальная температура должна быть больше минимальной')
#                 })
#
#     def __str__(self):
#         return self.get_display_name()