# models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union

from cert_doc.models import AbstractCertRelation
from core.models import StructuredDataMixin
from producers.models import Producer, Brands

from params.models import ThreadSize , IpOption , ExdOption , ThreadSizeThroughOption

"""
ModelLine - серия. В/з, ИП, сертификаты - все сюда
Body - размеры, сюда же чертеж
MOdelLineItem - Модель в серии
    Объединяет в себе общие для всех моделей серии свойства
    и доступные опции - резьба, материал корпуса...
"""


class CableGlandItemType(models.Model):
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
    def __str__(self):
        return self.name


class CableGlandBodyMaterial( models.Model):
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

    def __str__(self):
        return self.name

class MetalSleeve( models.Model):
    name = models.CharField(max_length=200,
                            verbose_name=_("Название"),
                            help_text=_('Название металлорукава'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код металлорукава"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание металлорукава'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    class Meta:
        verbose_name = _("Тип и диаметр металлорукава")
        verbose_name_plural = _("Типы и диаметры металлорукавов")
        ordering = ['sorting_order']

    def create_copy(self , name_suffix=None , code_suffix=None) :
        """Создает копию модели со всеми связанными данными"""
        if name_suffix is None :
            name_suffix = _(" (Копия)")
        if code_suffix is None :
            code_suffix = _(" (Копия)")
        # Создаем новый объект с теми же данными
        copy = MetalSleeve(
            name=f"{self.name}{name_suffix}" if self.name else "Копия",
            code=f"{self.code}{code_suffix}" if self.code else "Копия",
            description=self.description,
            sorting_order=self.sorting_order,
            is_active=self.is_active,

        )
        copy.save()
        return copy

    def __str__(self):
        return self.name



class CableGlandModelLine(StructuredDataMixin, models.Model):
    name = models.CharField(max_length=200 ,
                            verbose_name=_("Название") ,
                            help_text=_('Название серии кабельных вводов'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код серии кабельных вводов"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание модели корпуса КВ'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    symbolic_code = models.CharField(max_length=20)
    brand = models.ForeignKey(Brands, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("Бренд") ,
                              related_name='cable_gland_brand', help_text=_('Бренд (производитель) кабельных вводов'))
    cable_gland_type = models.ForeignKey(CableGlandItemType, blank=True, null=True, on_delete=models.SET_NULL,
                                         verbose_name=_("Тип"),
                                         related_name='cable_gland_type', help_text=_('Тип КВ'))
    ip = models.ManyToManyField(IpOption, blank=True, default=1, related_name='cable_gland_model_line_ip',
                                verbose_name=_("IP"),
                                help_text=_('Степень защиты IP (можно выбрать несколько)'))
    exd = models.ManyToManyField(ExdOption, blank=True, default=1, verbose_name=_("Взрывозащита") ,
                                 related_name='cable_gland_model_line_exd', help_text=_('Тип взрывозащиты'))
    for_armored_cable = models.BooleanField(blank=True, null=True, verbose_name=_("Бронированный кабель") ,help_text=_('Для бронированного кабеля'))
    for_metal_sleeve_cable = models.BooleanField(blank=True, null=True, verbose_name=_("Металлорукав") ,help_text=_('Для кабеля в металлорукаве'))
    for_pipelines_cable = models.BooleanField(blank=True, null=True,  verbose_name=_("Трубопровод"), help_text=_('Для кабеля в трубопроводе'))
    thread_external = models.BooleanField(blank=True, null=True,  verbose_name=_("Наружная резьба"), help_text=_('Наружная резьба для внешнего присоединения'))
    thread_internal = models.BooleanField(blank=True, null=True, verbose_name=_("Внутренняя резьба"),
                                          help_text=_('Внутренняя резьба для внешнего присоединения'))
    temp_min = models.SmallIntegerField(blank=True, null=True, verbose_name=_("Темп.мин"),
                                        help_text=_('Минимальная температура окружающей среды'))
    temp_max = models.SmallIntegerField(blank=True, null=True, verbose_name=_("Темп.макс"),
                                        help_text=_('Максимальная температура окружающей среды'))
    gost = models.CharField(max_length=1000, blank=True, null=True, verbose_name=_("ГОСТ"),
                            help_text=_('Соответвие ГОСТ, ТУ, другим стандартам - перечень'))
    text_description = models.CharField(max_length=500, blank=True, null=True, help_text='Описание серии')

    def get_full_description(self):
        result_table = []
        result_table.extend([
            {'param_name': 'description',
             'param_text': 'Описание', 'param_value': '' + self.text_description + ' Производитель:' + self.brand.name},
            {'param_name': 'ip',
             'param_text': 'Исполнение IP', 'param_value': \
                 ' / '.join([ip.symbolic_code for ip in sorted(self.ip.all(), key=lambda ip: ip.symbolic_code)])},
            {'param_name': 'exd',
             'param_text': 'Взрывозащита', 'param_value': ' / '.join(
                [exd.text_description for exd in sorted(self.exd.all(), key=lambda exd: exd.text_description)])},
            {'param_name': 'gost',
             'param_text': 'Соответствие ГОСТ, ТУ, другим стандартам', 'param_value': self.gost},
        ])
        return result_table
    class Meta:
        verbose_name = _("Серия кабельных вводов")
        verbose_name_plural = _("Серии кабельных вводов")
        ordering = ['sorting_order']

    def __str__(self):
        return self.symbolic_code

class CableGlandBody(StructuredDataMixin, models.Model):
    name = models.CharField(max_length=200 ,
                            verbose_name=_("Название") ,
                            help_text=_('Название модели корпуса кабельного ввода'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код модели корпуса кабельного ввода"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание модели корпуса КВ'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    model_line = models.ForeignKey(CableGlandModelLine , blank=True , null=True , on_delete=models.SET_NULL , verbose_name=_("Серия") ,
                              related_name='cg_body_model_line' , help_text=_('Серия модели корпуса кабельного ввода'))
    metal_sleeve = models.ManyToManyField(MetalSleeve , blank=True ,
                                            related_name='metal_sleeve_cg_model_body' ,
                                            verbose_name=_("Металлорукав") ,
                                            help_text=_('Металлорукава, подходящие для этого корпуса'))

    @property
    def metal_sleeve_display(self) :
        """Отображает металлорукава через разделитель /"""
        metal_sleeves = self.metal_sleeve.all()
        if metal_sleeves :
            return " / ".join([str(metal_sleeve) for metal_sleeve in metal_sleeves])
        return "-"

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

    model_line = models.ForeignKey(CableGlandModelLine, blank=True, null=True, on_delete=models.SET_NULL,
                                   related_name='cable_gland_model_line', help_text='Серия кабельных вводов/адаптеров')
    cable_gland_body_material = models.ForeignKey(CableGlandBodyMaterial, blank=True, null=True, \
                                                  on_delete=models.SET_NULL, \
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

    cable_diameter_inner_min = models.SmallIntegerField(blank=True, null=True,
                                                        help_text='Минимальный внутренний диаметр обжимаего кабеля')
    cable_diameter_inner_max = models.SmallIntegerField(blank=True, null=True,
                                                        help_text='Минимальный внутренний диаметр обжимаего кабеля')
    cable_diameter_outer_min = models.PositiveIntegerField(blank=True, null=True,
                                                           help_text='Минимальный внешний диаметр обжимаего кабеля (Здесь '
                                                                     'указываем значения для кабеля без бронирования)')
    cable_diameter_outer_max = models.PositiveIntegerField(blank=True, null=True,
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

class CableGlandThreadOption(ThreadSizeThroughOption):
    """Опции типов и размеров резьб для корпуса кабельного ввода"""
    cable_gland_body = models.ForeignKey(
        CableGlandBody,
        on_delete=models.CASCADE,
        related_name='cg_thread_body',
        verbose_name=_("Корпус кабельного ввода")
    )

    class Meta:
        verbose_name = _("Резьба модели корпуса кабельного ввода")
        verbose_name_plural = _("Типы резьбы модели корпуса кабельного ввода")
        ordering = ['sorting_order']
        unique_together = ['cable_gland_body', 'thread_size']

    def __str__(self) :
        return f"{self.thread_size.name}"

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'cable_gland_body'


class CableGlandModelLineCertRelation(AbstractCertRelation) :
    """
    Связь сертификатов с сериями пневмоприводов.
    """
    model_line = models.ForeignKey(
        CableGlandModelLine ,  # Замените на реальный путь к модели Project
        on_delete=models.CASCADE ,
        verbose_name=_("Серия кабельных вводов") ,
        related_name='cert_data_cg_model_line'
    )

    class Meta(AbstractCertRelation.Meta) :
        verbose_name = _("Связь сертификата с серией кабельных вводов")
        verbose_name_plural = _("Связи сертификатов с сериями кабельных вводов")
        unique_together = ['cert_data' , 'model_line']

    def get_related_object(self) :
        return self.model_line