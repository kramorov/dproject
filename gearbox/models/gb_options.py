#gearbox/admin/gb_options_admin.py
from typing import Dict

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import CopyMixin, TemplateMixin

class OverrideMechanism(models.Model):
    """Справочник механизмов отключения/дублирования для редукторов
    Declutchable Lever (Эксцентриковый рычаг): Самый частый вариант для пневмоприводов.
        Рычаг физически выводит червяк из зацепления с сектором.
    Handwheel Push/Pull (Сдвижной штурвал): Нужно нажать или вытянуть штурвал вдоль оси, чтобы войти в зацепление. Часто встречается на электроприводах.
    Auto-declutch (Автоматическое отключение): При подаче питания/воздуха механизм сам «выщелкивается» из ручного режима.
    Side-mounted Lever (Боковой переключатель): Механическая муфта, переключающая управление «Ручное/Авто».
    Direct Drive (Без отключения): Штурвал вращается всегда (встречается на очень простых/дешевых редукторах, не рекомендуется для автоматики).
    """
    name = models.CharField(max_length=100,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название тип механизма отключения'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код механизма отключения"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа механизма отключения'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    class Meta:
        verbose_name = _("Механизм отключения (вид дублера)")
        verbose_name_plural = _("Механизмы отключения (виды дублеров)")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name

class TransmissionVariety(models.Model):
    """Простой справочник: Червячная, Коническая, Планетарная"""
    name = models.CharField(max_length=100,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название тип механизма передачи'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код серии редукторов"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа механизма отключения'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    class Meta:
        verbose_name = _("Механизм передачи")
        verbose_name_plural = _("Механизмы передачи")
        ordering = ['sorting_order']
    def __str__(self):
        return self.name

class GearboxVariety(models.Model):
    """Простой справочник: Ручной дублер, Редуктор под привод"""
    name = models.CharField(max_length=100,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название разновидности редуктора'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код разновидности редуктора"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание разновидности редуктора'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    class Meta:
        verbose_name = _("Разновидность редуктора")
        verbose_name_plural = _("Разновидности редукторов")
        ordering = ['sorting_order']
    def __str__(self):
        return self.name

