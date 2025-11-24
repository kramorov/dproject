# # options/models/exd_models.py
# from django.db import models
# from django.utils.translation import gettext_lazy as _
#
# from options.models.base_abstract_through_model import BaseThroughOption
#
#
# class BaseExdThroughOption(BaseThroughOption) :
#     """Базовая модель для сквозных опций Exd"""
#     exd_option = models.ForeignKey(
#         'params.ExdOption' ,
#         on_delete=models.CASCADE ,
#         verbose_name=_("Опция взрывозащиты")
#     )
#
#     class Meta :
#         abstract = True
#         ordering = ['sorting_order']
#
#     @classmethod
#     def create_default_option(cls , parent_obj) :
#         """Создать стандартную Exd опцию (STD)"""
#         from django.apps import apps
#
#         ExdOption = apps.get_model('params' , 'ExdOption')  # Ленивая загрузка
#
#         try :
#             std_option = ExdOption.objects.get(code='STD')
#         except ExdOption.DoesNotExist :
#             std_option = ExdOption.objects.filter(is_active=True).first()
#
#         if std_option :
#             parent_field = cls._get_parent_field_name()
#             return cls.objects.create(
#                 **{parent_field : parent_obj} ,
#                 exd_option=std_option ,
#                 encoding='STD' ,
#                 description='Стандартное исполнение взрывозащиты' ,
#                 is_default=True ,
#                 sorting_order=0 ,
#                 is_active=True
#             )
#         return None