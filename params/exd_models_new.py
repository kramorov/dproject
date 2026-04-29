# params/exd_models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Dict, List, Optional, Any
from core.models.mixins import TextDescriptionMixin, OptionListToSelectMixin

# #
# class HazardousGroup(models.Model) :
#     """Группа взрывоопасной среды (газ и пыль в одном справочнике)"""
#
#     class GroupType(models.TextChoices) :
#         GAS = 'GAS' , _('Газ')
#         DUST = 'DUST' , _('Пыль')
#
#     code = models.CharField(max_length=5 , unique=True)  # IIA, IIB, IIC, IIIA, IIIB, IIIC
#     name = models.CharField(max_length=100 , blank=True)
#     description = models.TextField(blank=True , verbose_name=_("Описание") ,
#                                    help_text=_('Текстовое группы взрывоопасной среды'))
#     group_type = models.CharField(max_length=5 , choices=GroupType.choices)
#     rating = models.IntegerField(help_text="Чем выше рейтинг, тем более опасная среда")
#
#     class Meta :
#         ordering = ['group_type' , 'rating']
#
#     def __str__(self) :
#         return self.code
#
#     def is_compatible(self , required_code) :
#         """
#         Проверяет, подходит ли данная группа для требуемой
#         Оборудование с IIC (рейтинг 3) подходит для IIB (рейтинг 2)
#         """
#         if not required_code :
#             return True
#
#         try :
#             required = HazardousGroup.objects.get(code=required_code , group_type=self.group_type)
#             return self.rating >= required.rating
#         except HazardousGroup.DoesNotExist :
#             return False
#
# class GasGroup(models.Model, TextDescriptionMixin):
#     """Группа газа (IIA, IIB, IIC, etc.)"""
#     name = models.CharField(max_length=10, verbose_name=_("Название"))
#     code = models.CharField(max_length=10, verbose_name=_("Код"))
#     description = models.TextField(blank=True, verbose_name=_("Описание"))
#
#     class Meta:
#         verbose_name = _("Группа газа")
#         verbose_name_plural = _("Группы газов")
#
#     def __str__(self):
#         return self.code
#
#     def get_text_description(self) -> str:
#         """Генерирует описание группы газа"""
#         descriptions = {
#             'IIA': _("пропан, метан, аммиак (наименее опасная)"),
#             'IIB': _("этилен, коксовый газ (средняя опасность)"),
#             'IIC': _("водород, ацетилен, сероуглерод (наиболее опасная)"),
#         }
#         return descriptions.get(self.code, self.description or self.name)
#
#
# class DustGroup(models.Model, TextDescriptionMixin):
#     """Группа пыли (IIIA, IIIB, IIIC)"""
#     name = models.CharField(max_length=10, verbose_name=_("Название"))
#     code = models.CharField(max_length=10, verbose_name=_("Код"))
#     description = models.TextField(blank=True, verbose_name=_("Описание"))
#
#     class Meta:
#         verbose_name = _("Группа пыли")
#         verbose_name_plural = _("Группы пыли")
#
#     def __str__(self):
#         return self.code
#
#     def get_text_description(self) -> str:
#         """Генерирует описание группы пыли"""
#         descriptions = {
#             'IIIA': _("легковоспламеняющиеся летучие частицы (мука, зерно)"),
#             'IIIB': _("непроводящая пыль (древесная, угольная)"),
#             'IIIC': _("проводящая пыль (металлическая, графитовая)"),
#         }
#         return descriptions.get(self.code, self.description or self.name)
#
#
# class TemperatureClass(models.Model, TextDescriptionMixin):
#     """Температурный класс (T1-T6)"""
#     temperature_class = models.CharField(max_length=5, verbose_name=_("Класс"))
#     max_surface_temp = models.IntegerField(verbose_name=_("Макс. температура поверхности, °C"))
#     gas_ignition_temp = models.IntegerField(
#         null=True, blank=True,
#         verbose_name=_("Температура воспламенения газа, °C")
#     )
#
#     class Meta:
#         verbose_name = _("Температурный класс")
#         verbose_name_plural = _("Температурные классы")
#
#     def __str__(self):
#         return f"{self.temperature_class}"
#
#     def get_text_description(self) -> str:
#         """Генерирует описание температурного класса"""
#         return _(
#             "Максимальная температура поверхности %(temp)s°C, допустима для газов с температурой воспламенения выше %(ignition)s°C"
#         ) % {
#             'temp': self.max_surface_temp,
#             'ignition': self.max_surface_temp
#         }
#
#
# class ExplosionProtectionType(models.Model, TextDescriptionMixin):
#     """Тип взрывозащиты (Ex d, Ex e, Ex i, etc.)"""
#
#     class ProtectionCategory(models.TextChoices):
#         GAS = 'GAS', _('Газ')
#         DUST = 'DUST', _('Пыль')
#
#     code = models.CharField(max_length=10, verbose_name=_("Код"))
#     name = models.CharField(max_length=100, verbose_name=_("Название"))
#     description = models.TextField(blank=True, verbose_name=_("Описание"))
#     category = models.CharField(
#         max_length=10,
#         choices=ProtectionCategory.choices,
#         default=ProtectionCategory.GAS,
#         verbose_name=_("Категория")
#     )
#
#     class Meta:
#         verbose_name = _("Тип взрывозащиты")
#         verbose_name_plural = _("Типы взрывозащиты")
#
#     def __str__(self):
#         return f"Ex{self.code}"
#
#     def get_text_description(self) -> str:
#         """Генерирует описание типа взрывозащиты"""
#         descriptions = {
#             'd': _("Взрывонепроницаемая оболочка - оборудование выдерживает внутреннее давление взрыва"),
#             'e': _("Повышенная надежность - отсутствие искр и дуг в нормальном режиме"),
#             'i': _("Искробезопасная электрическая цепь - энергия ограничена"),
#             'ia': _("Искробезопасная цепь - очень высокая степень защиты"),
#             'ib': _("Искробезопасная цепь - высокая степень защиты"),
#             'n': _("Неискрящее оборудование для Зоны 2"),
#             'nA': _("Неискрящее оборудование для Зоны 2"),
#             'm': _("Герметизация компаундом"),
#             'p': _("Заполнение или продувка оболочки под избыточным давлением"),
#             't': _("Защита оболочкой для пыли"),
#             'tb': _("Защита оболочкой для пыли - высокая степень"),
#         }
#         return descriptions.get(self.code, self.description or self.name)
#
#
# class ExplosionProtectionLevel(models.Model, TextDescriptionMixin):
#     """Уровень взрывозащиты (Ga, Gb, Gc, Da, Db, Dc)"""
#     name = models.CharField(max_length=10, verbose_name=_("Название"))
#     code = models.CharField(max_length=10, verbose_name=_("Код"))
#     description = models.TextField(blank=True, verbose_name=_("Описание"))
#     equipment_category = models.CharField(
#         max_length=20,
#         choices=[
#             ('MINING', _('Горнорудная')),
#             ('SURFACE', _('Поверхностная')),
#         ],
#         verbose_name=_("Категория оборудования")
#     )
#     zone = models.CharField(
#         max_length=10,
#         blank=True,
#         help_text=_("Зона взрывоопасности")
#     )
#
#     class Meta:
#         verbose_name = _("Уровень взрывозащиты")
#         verbose_name_plural = _("Уровни взрывозащиты")
#
#     def __str__(self):
#         return self.code
#
#     def get_text_description(self) -> str:
#         """Генерирует описание уровня взрывозащиты"""
#         descriptions = {
#             'Ga': _("Оборудование для Зоны 0 - очень высокая степень защиты"),
#             'Gb': _("Оборудование для Зоны 1 - высокая степень защиты"),
#             'Gc': _("Оборудование для Зоны 2 - нормальная степень защиты"),
#             'Da': _("Оборудование для Зоны 20 - очень высокая степень защиты"),
#             'Db': _("Оборудование для Зоны 21 - высокая степень защиты"),
#             'Dc': _("Оборудование для Зоны 22 - нормальная степень защиты"),
#         }
#         return descriptions.get(self.code, self.description or self.name)
#
#
# class ExdOption(models.Model , OptionListToSelectMixin) :
#     """Маркировка взрывозащиты"""
#
#     # Основные поля
#     name = models.CharField(max_length=200 , verbose_name=_("Название"))
#     code = models.CharField(max_length=100 , blank=True , verbose_name=_("Код"))
#     description = models.TextField(blank=True , verbose_name=_("Описание"))
#     sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))
#     is_active = models.BooleanField(default=True , verbose_name=_("Активно"))
#
#     # Компоненты маркировки (только нужные связи)
#     # protection_type = models.ForeignKey(
#     #     'ExplosionProtectionType' ,
#     #     on_delete=models.SET_NULL ,
#     #     null=True ,
#     #     blank=True ,
#     #     verbose_name=_("Тип взрывозащиты") ,
#     #     help_text=_("Ex d, Ex e, Ex i, Ex t, Ex tb и т.д.")
#     # )
#
#     hazardous_group = models.ForeignKey(
#         'HazardousGroup' ,
#         on_delete=models.SET_NULL ,
#         null=True ,
#         blank=True ,
#         verbose_name=_("Группа взрывоопасной среды") ,
#         help_text=_("IIA, IIB, IIC для газа; IIIA, IIIB, IIIC для пыли")
#     )
#
#     temperature_class = models.ForeignKey(
#         'TemperatureClass' ,
#         on_delete=models.SET_NULL ,
#         null=True ,
#         blank=True ,
#         verbose_name=_("Температурный класс") ,
#         help_text=_("T1-T6")
#     )
#
#     protection_level = models.ForeignKey(
#         'ExplosionProtectionLevel' ,
#         on_delete=models.SET_NULL ,
#         null=True ,
#         blank=True ,
#         verbose_name=_("Уровень взрывозащиты") ,
#         help_text=_("Ga, Gb, Gc для газа; Da, Db, Dc для пыли")
#     )
#
#     dust_temperature = models.IntegerField(
#         null=True ,
#         blank=True ,
#         verbose_name=_("Температура для пыли, °C") ,
#         help_text=_("Например: 85, 95, 100")
#     )
#
#     # Суффиксы (нужны, так как встречаются в реальной маркировке)
#     has_x_suffix = models.BooleanField(
#         default=False ,
#         verbose_name=_("Специальные условия (X)") ,
#         help_text=_("Добавляется, когда требуются особые условия монтажа или эксплуатации")
#     )
#
#     has_u_suffix = models.BooleanField(
#         default=False ,
#         verbose_name=_("Только компонент (U)") ,
#         help_text=_("Обозначает, что изделие является компонентом взрывозащищенного оборудования")
#     )
#
#     # Готовая маркировка
#     full_code = models.CharField(max_length=300 , blank=True , verbose_name=_("Полный код"))
#
#     class Meta :
#         verbose_name = _('Маркировка взрывозащиты')
#         verbose_name_plural = _('Маркировки взрывозащиты')
#         ordering = ['sorting_order']
#
#     def __str__(self) :
#         return self.full_code or self.name or "—"
#
#     def build_marking(self) :
#         """Собирает маркировку из компонентов"""
#         parts = []
#
#         # Тип защиты
#         if self.protection_type :
#             parts.append(self.protection_type.name)
#
#         # Группа
#         if self.hazardous_group :
#             parts.append(self.hazardous_group.code)
#
#         # Температура
#         if self.temperature_class :
#             parts.append(self.temperature_class.temperature_class)
#         elif self.dust_temperature :
#             parts.append(f"T{self.dust_temperature}°C")
#
#         # Уровень защиты
#         if self.protection_level :
#             parts.append(self.protection_level.code)
#
#         # Суффиксы
#         suffix = ""
#         if self.has_x_suffix :
#             suffix += " X"
#         if self.has_u_suffix :
#             suffix += " U"
#
#         result = " ".join(parts) + suffix
#         return result.strip()
#
#     def save(self , *args , **kwargs) :
#         if not self.full_code :
#             self.full_code = self.build_marking()
#             if not self.name :
#                 self.name = self.full_code
#         super().save(*args , **kwargs)
#
#     def is_compatible(self , requirement) :
#         """
#         Проверяет, подходит ли маркировка под требование
#         """
#         # Тип защиты должен совпадать
#         if requirement.protection_type and self.protection_type :
#             if self.protection_type.code != requirement.protection_type.code :
#                 return False
#
#         # Группа (IIC подходит для IIB, IIB для IIA)
#         if requirement.hazardous_group and self.hazardous_group :
#             # Группы должны быть одного типа (газ или пыль)
#             if self.hazardous_group.group_type != requirement.hazardous_group.group_type :
#                 return False
#             if self.hazardous_group.rating < requirement.hazardous_group.rating :
#                 return False
#
#         # Температурный класс (T6 подходит для T1-T5)
#         if requirement.temperature_class and self.temperature_class :
#             if self.temperature_class.max_surface_temp > requirement.temperature_class.max_surface_temp :
#                 return False
#
#         # Уровень защиты (Ga подходит для Gb и Gc)
#         if requirement.protection_level and self.protection_level :
#             if self.protection_level.level > requirement.protection_level.level :
#                 return False
#
#         # Пылевая температура
#         if requirement.dust_temperature and self.dust_temperature :
#             if self.dust_temperature > requirement.dust_temperature :
#                 return False
#
#         return True