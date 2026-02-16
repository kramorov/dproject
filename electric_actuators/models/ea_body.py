# electric_actuators/models/ea_body.py
from django.db import models

# from electric_actuators.models import ModelLine , CableGlandHolesSet
from params.models import StemShapes, StemSize, MountingPlateTypes
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union
from django.db.models.signals import pre_save , post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from params.models import MountingPlateTypes , StemShapes , StemSize , ThreadTypes , PneumaticConnection , ThreadSize



class ElectricActuatorBodyTable(models.Model) :
    """
    Таблица для групповой обработки значений - импорта и экспорта
    """
    name = models.CharField(max_length=100 , blank=True , null=True ,
                            verbose_name=_("Название") ,
                            help_text=_("Название таблицы корпусов")
                            )
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код таблицы корпусов"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание таблицы корпусов'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Таблица корпусов')
        verbose_name_plural = _('Таблица корпусов для их логического объединения для групповой обработки')

    def __str__(self) :
        return self.name

    @property
    def related_bodies_display(self) :
        """Отображает связанные корпуса"""
        bodies = self.model_body_body_table.all()
        if bodies :
            return ", ".join([f"{body.name}" for body in bodies])
        return _("Нет связанных моделей корпусов")

    related_bodies_display.fget.short_description = _('Связанные модели корпуса')




# class ModelBody(models.Model):
#     name = models.CharField(max_length=200, verbose_name='Текстовое название типа корпуса')
#     model_line = models.ForeignKey('ModelLine', on_delete=models.PROTECT,
#                                    related_name='model_body_model_line', help_text='Серия приводов')
#     default_cable_glands_holes = \
#         models.ForeignKey('CableGlandHolesSet', null=True, blank=True,
#                           related_name='model_body_default_cable_glands_holes',
#                           on_delete=models.SET_NULL,
#                           help_text='Стандартные отверстия под кабельные вводы')
#     allowed_cable_glands_holes = \
#         models.ManyToManyField('CableGlandHolesSet', blank=True,
#                                related_name='model_body_allowed_cable_glands_holes',
#                                help_text='Возможные для выбора варианты отверстий под кабельные вводы для корпуса ('
#                                          'можно выбрать несколько)')
#     mounting_plate = models.ManyToManyField(MountingPlateTypes, blank=True,
#                                             related_name='model_body_cable_mounting_plate',
#                                             help_text='Монтажная площадка')
#     stem_shape = models.ForeignKey(StemShapes, on_delete=models.SET_NULL, null=True, blank=True,
#                                    related_name='model_body_stem_shape', help_text='Тип отверстия под шток арматуры')
#     stem_size = models.ForeignKey(StemSize, on_delete=models.SET_NULL, null=True, blank=True,
#                                   related_name='model_body_stem_size', help_text='Размер отверстия под шток арматуры')
#     max_stem_height = models.PositiveIntegerField(blank=True, null=True,
#                                                   help_text='Глубина отверстия под шток арматуры')
#     max_stem_diameter = models.PositiveIntegerField(blank=True, null=True, help_text='Максимальный диаметр отверстия '
#                                                                                      'под шток арматуры')
#     text_description = models.CharField(max_length=500, blank=True, null=True, help_text='Описание типа корпуса')
#
#     def __str__(self):
#         return self.name
class ElectricActuatorBody(models.Model) :
    """
    Корпус привода электроприводв
    Для каждого корпуса уникальны
        размеры
        площадка
        квадрат
        отверстия под КВ
    общей является принадлежность к какой-то серии электроприводов - в серии описываются
    общие для всех моделей параметры это model_line
    Опции корпуса:
        резьба КВ и их количество
        SPDT/DPDT
    Опции model_line:
        угол поворота (90-180-270)
        LT
        IP
        Ex
        QC быстросъемное соединение
        MID	Опция 3х позиционный (по доп.концевикам)
        PowerSupply
        Control Unit (POSI, TR, INT...)
    """
    name = models.CharField(max_length=100 , blank=True , null=True ,
                            verbose_name=_("Название") ,
                            help_text=_("Название модели корпуса привода")
                            )
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код модели корпуса привода"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание модели корпуса привода'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    body_table = models.ForeignKey(ElectricActuatorBodyTable , on_delete=models.PROTECT ,
                                   verbose_name=_("Таблица") ,
                                   related_name='model_body_body_table' ,
                                   help_text=_(
                                       'Таблица корпусов для их логического объединения для групповой обработки'))
    mounting_plate = models.ManyToManyField(MountingPlateTypes , blank=True ,
                                            related_name='model_body_mounting_plate_electric_model_line' ,
                                            verbose_name=_("Монт.площадка") ,
                                            help_text=_('Монтажная площадка'))
    stem_shape = models.ForeignKey(StemShapes , on_delete=models.SET_NULL , null=True , blank=True ,
                                   related_name='model_body_stem_shape_electric_model_line' ,
                                   verbose_name=_("Тип штока") ,
                                   help_text=_('Тип отверстия под шток арматуры'))
    stem_size = models.ForeignKey(StemSize , on_delete=models.SET_NULL , null=True , blank=True ,
                                  related_name='model_body_stem_size_electric_model_line' ,
                                  verbose_name=_("Размер штока") ,
                                  help_text=_('Размер отверстия под шток арматуры'))
    max_stem_height = models.DecimalField(max_digits=6 , decimal_places=2 ,
                                        default=0 , blank=True , null=True ,
                                                  verbose_name=_("Высота штока") ,
                                                  help_text=_('Глубина отверстия под шток арматуры'))
    max_stem_diameter = models.DecimalField(max_digits=6 , decimal_places=2 ,
                                        default=0 , blank=True , null=True ,
                                                    verbose_name=_("Макс шток") ,
                                                    help_text=_('Максимальный диаметр отверстия '
                                                                'под шток арматуры'))


    # Для фильтрации
    model_line = models.ForeignKey('ElectricActuatorModelLine', on_delete=models.PROTECT,
                                   related_name='ea_body_model_line', help_text='Серия приводов')
    # В get_weight добавить расчет веса инт блока
    weight_body = models.DecimalField(max_digits=6 , decimal_places=2 ,
                                        default=0 , blank=True , null=True ,
                                        verbose_name=_("Вес:") ,
                                        help_text=_(
                                            'Вес корпуса, кг'))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Модель корпуса электропривода')
        verbose_name_plural = _('Модели корпусов электроприводов')

    def __str__(self) :
        return self.name

    @property
    def mounting_plate_display(self) :
        """Отображает монтажные площадки через разделитель /"""
        plates = self.mounting_plate.all()
        if plates :
            return " / ".join([str(plate) for plate in plates])
        return "-"

    mounting_plate_display.fget.short_description = _('Площадка')

    @property
    def stem_info_display(self) :
        """Отображает информацию о штоке"""
        info = []
        if self.stem_shape :
            info.append(str(self.stem_shape))
        if self.stem_size :
            info.append(str(self.stem_size))
        if self.max_stem_height :
            info.append(f"высота: {self.max_stem_height}мм")
        if self.max_stem_diameter :
            info.append(f"∅: {self.max_stem_diameter}мм")
        return " | ".join(info) if info else "-"

    stem_info_display.fget.short_description = _('Шток')

    def create_copy(self , name_suffix=None , code_suffix=None) :
        """Создает копию модели со всеми связанными данными"""
        if name_suffix is None :
            name_suffix = _(" (Копия)")
        if code_suffix is None :
            code_suffix = _(" (Копия)")
        return None

    def get_description_data(self) -> Dict[str , Any] :
        """Получить структурированные данные для описания корпуса"""
        print(f"EA BODY model line item print get_description_data")
        data = {
            'mounting_plate': {'display_name':'Монтажные площадки', 'value':self.mounting_plate_display},
            'stem_shape': {'display_name':'Форма отверстия под шток', 'value':self.stem_shape if self.stem_shape else None},
            'stem_size': {'display_name':'Размер отверстия под шток', 'value':self.stem_size if self.stem_size else None},
            'max_stem_height': {'display_name':'Максимальная высота штока', 'value':self.max_stem_height if self.max_stem_height else None},
            'max_stem_diameter': {'display_name':'Максимально возможный диаметр штока', 'value':self.max_stem_diameter if self.max_stem_diameter else None},
            'weight_body': {'display_name':'Вес корпуса', 'value':self.weight_body if self.weight_body else None},
        }
        # print(data)
        return data
    #
    # def get_text_description(self) -> str :
    #     """Сгенерировать текстовое описание корпуса из структурированных данных"""
    #     data = self.get_description_data()
    #     desc_parts = []
    #
    #     # Базовая информация
    #     basic_info = data['basic_info']
    #     if basic_info['name'] :
    #         desc_parts.append(f"Модель корпуса: {basic_info['name']}")
    #     if basic_info['code'] :
    #         desc_parts.append(f"Код: {basic_info['code']}")
    #     if basic_info['description'] :
    #         desc_parts.append(f"Описание: {basic_info['description']}")
    #
    #     # Технические характеристики
    #     tech_specs = data['technical_specs']
    #     if tech_specs :
    #         desc_parts.append("\nТехнические характеристики:")
    #         for spec_name , spec_value in tech_specs.items() :
    #             display_name = {
    #                 'piston_diameter' : 'Диаметр поршня' ,
    #                 'turn_angle' : 'Угол поворота' ,
    #                 'turn_tuning_limit' : 'Ограничитель поворота' ,
    #                 'weight_spring' : 'Вес пружины' ,
    #                 'min_pressure' : 'Минимальное давление' ,
    #                 'max_pressure' : 'Максимальное давление' ,
    #                 'air_usage_open' : 'Расход воздуха (открытие)' ,
    #                 'air_usage_close' : 'Расход воздуха (закрытие)'
    #             }.get(spec_name , spec_name)
    #             desc_parts.append(f"  {display_name}: {spec_value}")
    #
    #     # Информация о штоке
    #     mounting_specs = data['mounting_specs']
    #     if mounting_specs:
    #         if 'stem' in mounting_specs :
    #             stem_parts = []
    #             stem_data = tech_specs['stem']
    #             if 'shape' in stem_data :
    #                 stem_parts.append(f"форма: {stem_data['shape']}")
    #             if 'size' in stem_data :
    #                 stem_parts.append(f"размер: {stem_data['size']}")
    #             if 'max_height' in stem_data :
    #                 stem_parts.append(f"макс. высота: {stem_data['max_height']}")
    #             if 'max_diameter' in stem_data :
    #                 stem_parts.append(f"макс. диаметр: {stem_data['max_diameter']}")
    #
    #             if stem_parts :
    #                 desc_parts.append(f"  Шток: {', '.join(stem_parts)}")
    #         if 'mounting_plates' in mounting_specs:
    #             desc_parts.append(f"  Монтажные площадки: {', '.join(mounting_specs['mounting_plates'])}")
    #
    #     # Подключения
    #     pipe_connections_specs = data['pipe_connections_specs']
    #     if pipe_connections_specs :
    #         desc_parts.append("\nПодключения:")
    #
    #         if 'thread_in' in pipe_connections_specs :
    #             desc_parts.append(f"  Пневмовход: {pipe_connections_specs['thread_in']}")
    #         if 'thread_out' in pipe_connections_specs :
    #             desc_parts.append(f"  Пневмовыход: {pipe_connections_specs['thread_out']}")
    #         if 'pneumatic_connections' in pipe_connections_specs :
    #             desc_parts.append(f"  Типы пневмоподключений: {', '.join(pipe_connections_specs['pneumatic_connections'])}")
    #
    #
    #     return "\n".join(desc_parts)
    #
    # @property
    # def full_description(self) -> str :
    #     """Полное описание корпуса (property)"""
    #     return self.get_text_description()

