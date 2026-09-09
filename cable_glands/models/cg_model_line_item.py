# cable_glands/models/cg_model_line_item.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union

from core.models.mixins import CopyMixin

from params.models import ThreadSize, IpOption, ThreadSizeThroughOption
from params.exd_models import ExdOption

class CableGlandModelLineItem(CopyMixin, models.Model):
    """«Модель в серии» — структурная связка «корпус + крепление металлорукава + вес».

    Промежуточный уровень иерархии каталога:

        CableGlandModelLine (серия)
          └─ CableGlandModelLineItem   ← эта модель: фиксирует КОМПОЗИЦИЮ
          |    корпуса (body), крепления металлорукава (metal_sleeve_body)
          |    и веса (weight)
          └─ CableGland (артикул каталога: добавляет резьбу thread
              и материал корпуса body_material)

    Зачем нужен уровень: у одной серии может быть несколько «размерных»
    исполнений (разные корпуса / устройства под металлорукав), а у одного
    исполнения — несколько артикулов (разные резьбы и материалы). Корпуса и
    крепления переиспользуются между «моделями в серии».

    Поля-связи:
      * model_line — серия (источник общих атрибутов и шаблонов текста);
      * body — корпус: диапазон обжимаемого ⌀ кабеля, длина резьбы; варианты
        резьб корпуса — через CableGlandThreadOption;
      * metal_sleeve_body — устройство подключения металлорукава (внутр./внеш. ⌀,
        M2M совместимых металлорукавов);
      * weight — вес данного исполнения, кг.

    Артикулом каталога является CableGland, поэтому TemplateMixin сюда
    намеренно НЕ подключается. CopyMixin — копирование «модели в серии».
    """
    name = models.CharField(max_length=255,
                            verbose_name=_("Название"),
                            help_text=_('Название модели кабельного ввода'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код модели кабельного ввода"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание модели кабельного ввода'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    model_line = models.ForeignKey(
        'CableGlandModelLine',
        blank=True, null=True, on_delete=models.SET_NULL,
        related_name='cable_gland_model_line', help_text='Серия кабельных вводов/адаптеров')
    body = models.ForeignKey(
        'CableGlandBody', blank=True, null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Корпус"), help_text=_('Модель корпуса'))
    metal_sleeve_body = models.ForeignKey(
        'CableGlandMetalSleeveBody', blank=True, null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Крепление МР"), help_text=_('Модель устройства для подключения металлорукава'))
    cable_diameter_outer_min = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True,  verbose_name=_("Мин внешний диаметр (броня)"),
                                                            help_text='Минимальный внешний диаметр обжимаемого кабеля (Здесь '
                                                                      'указываем значения для бронирования)')
    cable_diameter_outer_max = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True, verbose_name=_("Макс внешний диаметр (броня)"),
                                                            help_text='Максимальный внешний диаметр обжимаемого кабеля (Здесь '
                                                                      'указываем значения для бронирования)')
    
    weight =models.DecimalField(max_digits = 5, decimal_places =3, default=0, blank=True, null=True, verbose_name=_("Вес,кг"),
                                                help_text='Вес,кг')
    # cable_gland_body_material = models.ForeignKey(
    #     'CableGlandBodyMaterial', blank=True, null=True,
    #     on_delete=models.SET_NULL,
    #     related_name='cable_gland_body_material', help_text='Материал')
    # exd_same_as_model_line = models.BooleanField(default=True,
    #                                              help_text='Взрывозащита такая же, как у всей серии. Если да, '
    #                                                        'то новое значение Exd вводить не надо')
    # exd = models.ManyToManyField(ExdOption, blank=True, default=1,
    #                              related_name='cable_gland_item_exd', help_text='Степень взрывозащиты')
    # thread_a = models.ForeignKey(ThreadSize, blank=True, null=True, on_delete=models.SET_NULL,
    #                              related_name='thread_a_items', help_text='Резьба под привод')
    # thread_b = models.ForeignKey(ThreadSize, blank=True, null=True, on_delete=models.SET_NULL,
    #                              related_name='thread_b_items', help_text='Резьба под другой КВ')
    # temp_min = models.SmallIntegerField(blank=True, null=True, help_text='Минимальная температура окружающей среды')
    # temp_max = models.PositiveIntegerField(blank=True, null=True, help_text='Максимальная температура окружающей среды')

    # cable_diameter_inner_min = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True,
    #                                                     help_text='Минимальный внутренний диаметр обжимаемого кабеля')
    # cable_diameter_inner_max = models.DecimalField(max_digits = 5, decimal_places =1, default=0,blank=True, null=True,
    #                                                     help_text='Минимальный внутренний диаметр обжимаемого кабеля')
    # cable_diameter_outer_min = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True,
    #                                                        help_text='Минимальный внешний диаметр обжимаемого кабеля (Здесь '
    #                                                                  'указываем значения для бронирования)')
    # cable_diameter_outer_max = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True,
    #                                                        help_text='Минимальный внешний диаметр обжимаемого кабеля (Здесь '
    #                                                                  'указываем значения для бронирования)')
    # dn_metal_sleeve = models.PositiveIntegerField(blank=True, null=True, help_text='Диаметр металлорукава')
    # parent = models.ForeignKey(
    #     'self',
    #     on_delete=models.CASCADE,
    #     null=True,
    #     blank=True,
    #     related_name='children',
    #     help_text='Состав комплекта'
    # )

    class Meta:
        verbose_name = _("Модель КВ в серии")
        verbose_name_plural = _("Модели КВ в серии")
        ordering = ['sorting_order']

    def __str__(self):
        return self.name

