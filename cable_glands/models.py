# models.py
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from producers.models import Producer, Brands

from params.models import ThreadSize, IpOption, ExdOption


class CableGlandItemType(models.Model):
    name = models.CharField(max_length=255)
    text_description = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class CableGlandBodyMaterial(models.Model):
    name = models.CharField(max_length=50)
    text_description = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class CableGlandModelLine(models.Model):
    symbolic_code = models.CharField(max_length=20)
    brand = models.ForeignKey(Brands, blank=True, null=True, on_delete=models.SET_NULL,
                              related_name='cable_gland_brand', help_text='Бренд (производитель) кабельных вводов')
    cable_gland_type = models.ForeignKey(CableGlandItemType, blank=True, null=True, on_delete=models.SET_NULL,
                                         related_name='cable_gland_type', help_text='Степень защиты IP')
    ip = models.ManyToManyField(IpOption, blank=True, default=1, related_name='cable_gland_model_line_ip',
                                help_text='Степень защиты IP (можно выбрать несколько)')
    exd = models.ManyToManyField(ExdOption, blank=True, default=1,
                                 related_name='cable_gland_model_line_exd', help_text='Степень взрывозащиты')
    for_armored_cable = models.BooleanField(blank=True, null=True, help_text='Для бронированного кабеля')
    for_metal_sleeve_cable = models.BooleanField(blank=True, null=True, help_text='Для кабеля в металлорукаве')
    for_pipelines_cable = models.BooleanField(blank=True, null=True, help_text='Для кабеля в трубопроводе')
    thread_external = models.BooleanField(blank=True, null=True, help_text='Наружная резьба для внешнего присоединения')
    thread_internal = models.BooleanField(blank=True, null=True,
                                          help_text='Внутренняя резьба для внешнего присоединения')
    temp_min = models.SmallIntegerField(blank=True, null=True, help_text='Минимальная температура окружающей среды')
    temp_max = models.SmallIntegerField(blank=True, null=True, help_text='Максимальная температура окружающей среды')
    gost = models.CharField(max_length=1000, blank=True, null=True,
                            help_text='Соответвие ГОСТ, ТУ, другим стандартам - перечень')
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

    def __str__(self):
        return self.symbolic_code


class CableGlandItem(models.Model):
    name = models.CharField(max_length=255)
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
