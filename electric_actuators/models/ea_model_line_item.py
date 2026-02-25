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
            'time_to_open': {'display_name':'Время открытия, с', 'value':self.time_to_open if self.time_to_open else None},
            'time_to_close': {'display_name':'Время закрытия, с', 'value':self.time_to_close if self.time_to_close else None},
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
        self._copy_related_options(copy_obj)

        return copy_obj

    def _copy_related_options(self, copy_obj):
        """
        Автоматически копировать все связанные опции для скопированного объекта
        и выводить их в лог
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(
            f"Начинаем копирование связанных опций для {self.name} (ID: {self.id}) -> {copy_obj.name} (ID: {copy_obj.id})")

        # Получаем все обратные связи (related objects) для текущей модели
        related_objects = []

        # Проходим по всем полям модели, которые являются обратными связями
        for related_field in self._meta.get_fields():
            # Проверяем, что это обратная связь (ForeignKey или ManyToMany с одной стороны)
            if (hasattr(related_field, 'related_model') and
                    related_field.related_model and
                    hasattr(related_field, 'field') and
                    related_field.field):

                # Проверяем, что связанная модель имеет ForeignKey на нашу модель
                fk_fields = []
                for fk_field in related_field.related_model._meta.fields:
                    if isinstance(fk_field,
                                  models.ForeignKey) and fk_field.related_model == ElectricActuatorModelLineItem:
                        fk_fields.append(fk_field.name)

                if fk_fields:
                    try:
                        # Получаем все связанные объекты через эту обратную связь
                        related_manager = getattr(self, related_field.name)

                        # Проверяем, что это менеджер (queryset)
                        if hasattr(related_manager, 'all'):
                            related_qs = related_manager.all()
                            if related_qs.exists():
                                related_count = related_qs.count()
                                logger.info(
                                    f"  Найдена связь: {related_field.name} -> {related_field.related_model.__name__} ({related_count} записей)")

                                # Сохраняем для копирования
                                related_objects.append({
                                    'manager': related_manager,
                                    'model': related_field.related_model,
                                    'name': related_field.name,
                                    'fk_fields': fk_fields,
                                    'queryset': related_qs
                                })
                    except Exception as e:
                        logger.warning(f"  Ошибка при получении {related_field.name}: {e}")

        logger.info(f"Всего найдено связанных моделей: {len(related_objects)}")

        # Копируем каждый связанный объект
        copied_count = 0
        for rel_info in related_objects:
            logger.info(f"Копирование {rel_info['name']} ({rel_info['model'].__name__})...")

            for original_obj in rel_info['queryset']:
                try:
                    # Создаем копию
                    new_obj = rel_info['model']()

                    # Копируем все поля кроме первичного ключа
                    for field in original_obj._meta.fields:
                        if field.name not in ['id', 'pk']:
                            # Если это ForeignKey на нашу модель, заменяем на copy_obj
                            if isinstance(field,
                                          models.ForeignKey) and field.related_model == ElectricActuatorModelLineItem:
                                setattr(new_obj, field.name, copy_obj)
                                logger.debug(f"    Поле {field.name} заменено на новый объект")
                            else:
                                setattr(new_obj, field.name, getattr(original_obj, field.name))

                    # Добавляем суффикс к encoding для уникальности (если есть)
                    if hasattr(new_obj, 'encoding') and new_obj.encoding:
                        old_encoding = new_obj.encoding
                        new_obj.encoding = f"{new_obj.encoding}"
                        # logger.debug(f"    Encoding изменен: '{old_encoding}' -> '{new_obj.encoding}'")

                    # Сохраняем копию
                    new_obj.save()
                    copied_count += 1

                    logger.debug(f"    Скопирован объект {original_obj.id} -> {new_obj.id}")

                except Exception as e:
                    logger.error(f"    Ошибка при копировании {original_obj.id}: {e}")

        logger.info(f"Копирование завершено. Скопировано объектов: {copied_count}")

        # Возвращаем статистику для возможного использования
        return {
            'total_relations': len(related_objects),
            'copied_objects': copied_count
        }