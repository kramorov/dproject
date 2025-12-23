# cable_glands/models/cg_model_line_item.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union

from params.models import ThreadSize, IpOption, ExdOption, ThreadSizeThroughOption

"""
ModelLine - серия. В/з, ИП, сертификаты - все сюда
Body - размеры, сюда же чертеж
MOdelLineItem - Модель в серии
    Объединяет в себе общие для всех моделей серии свойства
    и доступные опции - резьба, материал корпуса...
"""


class CableGlandItem(models.Model):
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
    cable_gland_body_material = models.ForeignKey(
        'CableGlandBodyMaterial', blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name='cable_gland_body_material', help_text='Материал')
    exd_same_as_model_line = models.BooleanField(default=True,
                                                 help_text='Взрывозащита такая же, как у всей серии. Если да, '
                                                           'то новое значение Exd вводить не надо')
    exd = models.ManyToManyField(ExdOption, blank=True, default=1,
                                 related_name='cable_gland_item_exd', help_text='Степень взрывозащиты')
    thread_a = models.ForeignKey(ThreadSize, blank=True, null=True, on_delete=models.SET_NULL,
                                 related_name='thread_a_items', help_text='Резьба под привод')
    thread_b = models.ForeignKey(ThreadSize, blank=True, null=True, on_delete=models.SET_NULL,
                                 related_name='thread_b_items', help_text='Резьба под другой КВ')
    temp_min = models.SmallIntegerField(blank=True, null=True, help_text='Минимальная температура окружающей среды')
    temp_max = models.PositiveIntegerField(blank=True, null=True, help_text='Максимальная температура окружающей среды')

    cable_diameter_inner_min = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True,
                                                        help_text='Минимальный внутренний диаметр обжимаемого кабеля')
    cable_diameter_inner_max = models.DecimalField(max_digits = 5, decimal_places =1, default=0,blank=True, null=True,
                                                        help_text='Минимальный внутренний диаметр обжимаемого кабеля')
    cable_diameter_outer_min = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True,
                                                           help_text='Минимальный внешний диаметр обжимаего кабеля (Здесь '
                                                                     'указываем значения для кабеля без бронирования)')
    cable_diameter_outer_max = models.DecimalField(max_digits = 5, decimal_places =1, default=0, blank=True, null=True,
                                                           help_text='Минимальный внешний диаметр обжимаего кабеля (Здесь '
                                                                     'указываем значения для кабеля без бронирования)')
    dn_metal_sleeve = models.PositiveIntegerField(blank=True, null=True, help_text='Диаметр металлорукава')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text='Состав комплекта'
    )

    class Meta:
        verbose_name = _("Модель кабельного ввода")
        verbose_name_plural = _("Модели кабельных вводов")
        ordering = ['sorting_order']

    def get_full_description(self):
        # Нумерация в БД по умолчанию:
        # 1- Кабельный ввод
        # 2 - Адаптер
        # 3 - Заглушка
        # 4 - Кольцо заземления
        result_table = []
        result_table_model_line = self.model_line.get_full_description()
        if not self.exd_same_as_model_line:
            exd_description = ' / '.join([exd.text_description \
                                          for exd in sorted(self.exd.all(), key=lambda exd: exd.text_description)])
            next(param for param in result_table_model_line \
                 if param['param_name'] == 'exd')['param_value'] = exd_description
        name_str = self.name + ' ' + self.model_line.cable_gland_type.name
        result_table.extend([
            {'param_name': 'name', 'param_text': 'Наименование', 'param_value': name_str}])
        result_table.extend(result_table_model_line)
        t_min = self.model_line.temp_min if self.temp_min is None else self.temp_min
        t_max = self.model_line.temp_max if self.temp_max is None else self.temp_max
        t_str = 'От ' + str(t_min) + ' до +' + str(t_max)
        result_table.extend([
            {'param_name': 'temp_min', 'param_text': 'Температура окружающей среды', 'param_value': t_str},
            # {'param_name': 'temp_max', 'param_text': 'Минимальная температура окружающей среды', 'param_value': \
            #     self.temp_max if self.temp_max is None else self.model_line.temp_max},
            {'param_name': 'cable_gland_body_material', 'param_text': 'Материал', 'param_value': \
                self.cable_gland_body_material.text_description},
        ])

        if self.model_line.cable_gland_type == 3:  # 3 - Заглушка
            result_table.extend([
                {'param_name': 'thread_a', 'param_text': 'Резьба заглушки к приводу', 'param_value': self.thread_a}])
        elif self.model_line.cable_gland_type == 4:  # 4 - Кольцо заземления
            result_table.extend([
                {'param_name': 'dn_metal_sleeve', 'param_text': 'Диаметр', 'param_value': \
                    self.dn_metal_sleeve}])
        elif self.model_line.cable_gland_type == 2:  # 2 - Адаптер
            result_table.extend([
                {'param_name': 'thread_a', 'param_text': 'Резьба адаптера A - к приводу', 'param_value': \
                    self.thread_a},
                {'param_name': 'thread_b', 'param_text': 'Резьба адаптера B - к вводу', 'param_value': \
                    self.thread_b},
            ])
        else:  # 1- Кабельный ввод
            if self.model_line.for_armored_cable:  #
                result_table.extend([
                    {'param_name': 'd_inner', 'param_text': 'Диаметр обжимаемого кабеля внешний ØD, мм', 'param_value': \
                        '' + str(self.cable_diameter_inner_min) + ' - ' + str(self.cable_diameter_inner_max)},
                    {'param_name': 'd_outer', 'param_text': 'Диаметр обжимаемого кабеля внутренний Ød, мм',
                     'param_value': \
                         '' + str(self.cable_diameter_outer_min) + ' - ' + str(self.cable_diameter_outer_max)},
                ])
            else:
                result_table.extend([
                    {'param_name': 'd_outer', 'param_text': 'Диаметр обжимаемого кабеля внутренний Ød, мм',
                     'param_value': \
                         '' + str(self.cable_diameter_outer_min) + ' - ' + str(self.cable_diameter_outer_max)},
                ])
            if self.model_line.for_metal_sleeve_cable:  #
                result_table.extend([
                    {'param_name': 'd_inner', 'param_text': 'Ду металлорукава, мм', 'param_value': \
                        str(self.dn_metal_sleeve)},
                ])
            if self.model_line.for_pipelines_cable:  #
                result_table.extend([
                    {'param_name': 'd_inner', 'param_text': 'Ду трубопровода, мм', 'param_value': \
                        str(self.dn_metal_sleeve)},
                ])
        return result_table

    def __str__(self):
        return self.name
