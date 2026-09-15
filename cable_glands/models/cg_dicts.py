# cable_glands/models/cg_dicts.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union

class CableGlandItemType(models.Model):
    """Тип кабельного ввода (справочник).

    Исторический классификатор назначения изделия: кабельный ввод, адаптер,
    заглушка, кольцо заземления и т.п. text_description — краткое обозначение,
    использовавшееся в старых текстовых описаниях.

    В текущей структуре серия (CableGlandModelLine) на этот справочник НЕ
    ссылается — единственным типом серии является equipment_type
    (core.EquipmentType, для SKU/каталога). Модель сохранена для данных;
    решение об удалении или переносе признака на другую модель — открыто.
    """
    text_description = models.CharField(max_length=200)
    name = models.CharField(max_length=255,
                            verbose_name=_("Название"),
                            help_text=_('Название типа КВ'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа КВ"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа КВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    class Meta:
        verbose_name = _("Тип кабельного ввода")
        verbose_name_plural = _("Типы кабельных вводов")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class CableType(models.Model):
    """Тип кабеля, под который спроектирован кабельный ввод (справочник).

    Заменяет исторические булевы флаги серии (for_armored_cable / for_metal_sleeve_cable /
    for_pipelines_cable): вместо комбинаций флагов на серии заводится готовая запись
    справочника с понятным названием (например «Под бронированный кабель в металлорукаве»),
    а сама комбинация сохраняется в булевых атрибутах записи — для фильтрации/семантики
    и будущих расширений (привязка к маркам кабеля и т.п.).

    Серия (CableGlandModelLine) ссылается на одну запись через FK cable_type.
    """
    name = models.CharField(max_length=100,
                            verbose_name=_("Название"),
                            help_text=_('Название типа кабеля'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа кабеля"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа кабеля'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    for_armored_cable = models.BooleanField(default=False, verbose_name=_("Бронированный кабель"),
                                            help_text=_('Тип подходит для бронированного кабеля'))
    for_metal_sleeve_cable = models.BooleanField(default=False, verbose_name=_("Металлорукав"),
                                                 help_text=_('Тип подходит для кабеля в металлорукаве'))
    for_pipelines_cable = models.BooleanField(default=False, verbose_name=_("Трубопровод"),
                                              help_text=_('Тип подходит для кабеля в трубопроводе'))

    class Meta:
        verbose_name = _("Тип кабеля")
        verbose_name_plural = _("Типы кабеля")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class CableGlandBodyMaterial( models.Model):
    """Материал корпуса кабельного ввода (справочник).

    name — название материала (латунь, нерж., никелированная сталь...),
    code — символьный код для артикулов (body_material артикула CableGland:
    path/name в реестре и code_path при автогенерации кода),
    text_description — полное наименование для старых описаний.
    """
    text_description = models.CharField(max_length=200)
    name = models.CharField(max_length=50,
                            verbose_name=_("Название"),
                            help_text=_('Название материала корпуса КВ'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код материала корпуса КВ"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание материала корпуса КВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    class Meta:
        verbose_name = _("Тип материала корпуса кабельного ввода")
        verbose_name_plural = _("Типы материала корпуса кабельных вводов")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name
