# # options/models/ip_models.py
# from django.db import models
# from django.utils.translation import gettext_lazy as _
#
# from options.models.base_abstract_through_model import BaseThroughOption
#
#
# class BaseIpThroughOption(BaseThroughOption):
#     """Базовая модель для сквозных опций IP"""
#     ip_option = models.ForeignKey(
#         'params.IpOption',
#         on_delete=models.CASCADE,
#         verbose_name=_("Опция IP")
#     )
#
#     class Meta:
#         abstract = True
#         ordering = ['sorting_order']
#
#     @classmethod
#     def create_default_option(cls , parent_obj) :
#         """Создать стандартную IP опцию (IP54)"""
#         from django.apps import apps
#
#         IpOption = apps.get_model('params' , 'IpOption')  # Ленивая загрузка
#
#         try :
#             ip54_option = IpOption.objects.get(code='IP54')
#         except IpOption.DoesNotExist :
#             ip54_option = IpOption.objects.filter(is_active=True).first()
#
#         if ip54_option :
#             parent_field = cls._get_parent_field_name()
#             return cls.objects.create(
#                 **{parent_field : parent_obj} ,
#                 ip_option=ip54_option ,
#                 encoding='IP54' ,
#                 description='Стандартная степень защиты IP54' ,
#                 is_default=True ,
#                 sorting_order=0 ,
#                 is_active=True
#             )
#         return None
#
#     # Специфичные методы для IP опций
#     @property
#     def ip_rank(self):
#         """Ранг IP защиты"""
#         return getattr(self.ip_option, 'ip_rank', 0) if self.ip_option else 0
#
#     @classmethod
#     def get_highest_ip_option(cls, parent_obj):
#         """Получить опцию с наивысшим рангом IP"""
#         return cls.get_available_options(parent_obj).order_by(
#             '-ip_option__ip_rank'
#         ).first()