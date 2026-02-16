# electric_actuators/models/ea_model_line_item.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List , Optional , Tuple , Any , Dict , Union
from django.core.exceptions import ValidationError

from cert_doc.models import AbstractCertRelation
from electric_actuators.models import ElectricActuatorModelLine , ElectricActuatorBody

import logging

logger = logging.getLogger(__name__)

# ======================================  Модель в серии ==================================
class ElectricActuatorModelLineItem(models.Model) :
    """
    Модель в серии электроприводов
    Объединяет в себе общие для всех моделей серии свойства
    и доступные опции
    """
    name = models.CharField(max_length=200 ,
                            verbose_name=_("Название") ,
                            help_text=_('Название модели'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код модели"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание модели'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    model_line = \
        models.ForeignKey(ElectricActuatorModelLine , blank=True , null=True ,
                          related_name='model_line_item_model_line' ,
                          on_delete=models.SET_NULL ,
                          help_text=_('Серия'))
    body = \
        models.ForeignKey(ElectricActuatorBody , blank=True , null=True ,
                          related_name='electric_model_line_item_body' ,
                          on_delete=models.SET_NULL ,
                          help_text=_('Корпус модели'))
    time_to_open = models.DecimalField(max_digits=6 , decimal_places=2 , blank=True , null=True ,
                                       default=0 ,
                                       verbose_name=_('Откр, с') ,
                                       help_text=_('Время открытия, сек'))
    time_to_close = models.DecimalField(max_digits=6 , decimal_places=2 , blank=True , null=True ,
                                        default=0 ,
                                        verbose_name=_('Закр, с') ,
                                        help_text=_('Время закрытия, с'))
    rotation_speed = models.DecimalField(max_digits=3 , decimal_places=0 , blank=True , null=True ,
                                         default=0 ,
                                         verbose_name=_('Об/мин') ,
                                         help_text=_('Скорость, об/мин'))
    torque_min = models.DecimalField(max_digits=5 , decimal_places=0 ,
                                     default=0 ,
                                     verbose_name=_('Мин.усилие') ,
                                     help_text=_('Минимальное усилие'))
    torque_max = models.DecimalField(max_digits=5 , decimal_places=0 ,
                                     default=0 ,
                                     verbose_name=_('Макс.усилие') ,
                                     help_text=_('Максимальное усилие'))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Модель электропривода')
        verbose_name_plural = _('Модели электропривода в серии')

    def __str__(self) :
        return self.name

    # ==================== ГЕТТЕРЫ С ПРИОРИТЕТОМ ИЗ MODEL_LINE ИЛИ BODY ====================
    def get_description_data(self) -> Dict[str, Any]:
        """Получить структурированные данные для описания"""
        logger.debug(f"EA logger get_description_data")
        print(f"EA model line item print get_description_data")
        data = {
            'time_to_open': {'display_name':'Время открытия', 'value':self.time_to_open if self.time_to_open else None},
            'time_to_close': {'display_name':'Время закрытия', 'value':self.time_to_close if self.time_to_close else None},
            'rotation_speed': {'display_name':'Скорость вращения, об/мин', 'value':self.rotation_speed if self.rotation_speed else None},
            'torque_min': {'display_name':'Вращающий момент мин, Нм', 'value':self.torque_min if self.torque_min else None},
            'torque_max': {'display_name':'Вращающий момент макс, Нм', 'value':self.torque_max if self.torque_max else None}
        }
        # print(data)
        return data

    @property
    def brand(self) :
        """Бренд из model_line"""
        return self.model_line.brand if self.model_line else None

    @property
    def default_output_type(self) :
        """Тип работы по умолчанию из model_line"""
        return self.model_line.default_output_type if self.model_line else None

    # ==================== ОТОБРАЖАЕМЫЕ СВОЙСТВА (С ПРИОРИТЕТОМ) ====================

    @property
    def ip_display(self) :
        """Отображаемое имя стандартной IP опции из model_line"""
        return self.model_line.ip_display if self.model_line else "Не указано"

    @property
    def exd_display(self) :
        """Отображаемое имя стандартной Exd опции из model_line"""
        return self.model_line.exd_display if self.model_line else "Не указано"

    @property
    def body_coating_display(self) :
        """Отображаемое имя стандартной опции покрытия из model_line или своя"""
        return self.model_line.body_coating_display if self.model_line else "Не указано"

    @property
    def temperature_range_display(self) :
        """Отображаемый диапазон стандартной температуры из model_line"""
        return self.model_line.temperature_range_display if self.model_line else "Не указано"

    # ==================== ФУНКЦИЯ КОПИРОВАНИЯ ====================

    def create_copy(self) :
        """Создать копию элемента с добавлением ' Копия' к name и code"""
        # Создаем копию объекта
        copy_obj = ElectricActuatorModelLineItem()

        # Копируем все поля кроме первичного ключа
        for field in self._meta.fields :
            if field.name not in ['id' , 'pk'] :
                setattr(copy_obj , field.name , getattr(self , field.name))

        # Добавляем " Копия" к name и code
        if copy_obj.name :
            copy_obj.name = f"{copy_obj.name} Копия"
        if copy_obj.code :
            copy_obj.code = f"{copy_obj.code} Копия"

        # Сохраняем копию
        copy_obj.save()

        # Копируем связанные опции
        # self._copy_related_options(copy_obj)

        return copy_obj

    # def _copy_related_options(self , copy_obj) :
    #     """Копировать связанные опции для скопированного объекта"""
    #     # Список всех through-моделей для копирования
    #     through_models = [
    #         ('safety_position_option_model_line_item' , None) ,
    #         ('springs_qty_option_model_line_item' , None) ,
    #     ]
    #
    #     for relation_name , fk_field_name in through_models :
    #         if hasattr(self , relation_name) :
    #             related_objects = getattr(self , relation_name).all()
    #             for obj in related_objects :
    #                 obj.pk = None
    #
    #                 # Автоматически находим поле ForeignKey к модели
    #                 for field in obj._meta.fields :
    #                     if isinstance(field , models.ForeignKey) :
    #                         # Проверяем, ссылается ли поле на нужную модель
    #                         if field.related_model == ElectricActuatorModelLineItem :
    #                             setattr(obj , field.name , copy_obj)
    #                             break
    #
    #                 # Добавляем суффикс к encoding для уникальности
    #                 if hasattr(obj , 'encoding') and obj.encoding :
    #                     obj.encoding = f"{obj.encoding}_copy"
    #
    #                 obj.save()
