# # options/models/coating_models.py
# from django.db import models
# from django.utils.translation import gettext_lazy as _
#
# from options.models.base_abstract_through_model import BaseThroughOption
#
#
# class BaseBodyCoatingThroughOption(BaseThroughOption) :
#     """Базовая модель для сквозных опций покрытия корпуса"""
#     body_coating_option = models.ForeignKey(
#         'params.BodyCoatingOption' ,
#         on_delete=models.CASCADE ,
#         verbose_name=_("Опция покрытия корпуса"))
#
#     class Meta :
#         abstract = True
#         ordering = ['sorting_order']
#
#     @classmethod
#     def create_default_option(cls , parent_obj) :
#         """Создать стандартную опцию покрытия корпуса"""
#         from django.apps import apps
#
#         BodyCoatingOption = apps.get_model('params' , 'BodyCoatingOption')  # Ленивая загрузка
#         # Инициализируем переменную
#         std_coating = None
#         # Последовательно ищем подходящее покрытие
#         possible_codes = ['STD' , 'STANDARD' , 'DEFAULT']
#
#         for code in possible_codes :
#             std_coating = BodyCoatingOption.objects.filter(
#                 code=code ,
#                 is_active=True
#             ).first()
#             if std_coating :
#                 break
#
#         # Если не нашли по кодам, берем первое активное
#         if not std_coating :
#             std_coating = BodyCoatingOption.objects.filter(is_active=True).first()
#
#         if std_coating :
#             parent_field = cls._get_parent_field_name()
#             return cls.objects.create(
#                 **{parent_field : parent_obj} ,
#                 body_coating_option=std_coating ,
#                 encoding=std_coating.code ,
#                 description='Стандартное покрытие корпуса' ,
#                 is_default=True ,
#                 sorting_order=0 ,
#                 is_active=True
#             )
#         return None
