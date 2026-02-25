# electric_actuators/models/ea_model_line_item_options.py
from django.db import models

from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union
from django.core.exceptions import ValidationError

from core.models import StructuredDataMixin
from electric_actuators.models.ea_model_line_item import ElectricActuatorModelLineItem
from options.models import BaseThroughOptionNoDefault, BaseThroughOption

import logging

from params.models import PowerSupplies

logger = logging.getLogger(__name__)

class ElectricSafetyPositionOption(BaseThroughOption):
    """Опции покрытия корпуса для пневмоприводов
       может делаться не на все напряжения и не на все модели - привязываем к напряжению, которое привязывается к
       model_line_item - подобно ControlUnit"""
    power_supply_option = models.ForeignKey(
        'ElectricPowerSupplyOption',
        on_delete=models.CASCADE,
        related_name='control_unit_options',
        verbose_name=_("Опция напряжения питания")
    )
    safety_position = models.ForeignKey(
        'params.SafetyPositionOption',
        on_delete=models.CASCADE,
        verbose_name=_("Положение безопасности"),
        help_text=_('Положения безопасности'))

    encoding = models.CharField(
        max_length=50,
        verbose_name=_("Кодировка"),
        help_text=_("Код для генерации артикула"),
        blank=True,  # ДОБАВЛЯЕМ - разрешаем пустые значения
        null=True,  # ДОБАВЛЯЕМ - разрешаем NULL в базе
        default=''  # ДОБАВЛЯЕМ - значение по умолчанию пустая строка
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name=_("По умолчанию"),
        help_text=_("Выбирать этот блок управления по умолчанию")
    )

    class Meta:
        verbose_name = _("Положение безопасности модели электропривода")
        verbose_name_plural = _("Положения безопасности моделей электроприводов")
        ordering = ['sorting_order']
        # unique_together = ['power_supply_option', 'safety_position']

    def get_description_data(self) -> Dict[str, Any]:
        """Получить структурированные данные для описания"""
        # logger.debug(f"EA logger get_description_data")
        # print(f"EA model line item print get_description_data")
        data = {
            'power_supply_option': {'display_name':'Опция напряжения', 'value':self.power_supply_option if self.power_supply_option else None},
            'safety_position': {'display_name':'Положение безопасности', 'value':self.safety_position.name if self.safety_position else None},
            'is_default': {'display_name':'Стандарт', 'value':self.is_default},
        }

        return data

class ElectricControlUnitOption(BaseThroughOption):
    """Through-модель для блоков управления с encoding и дефолтами"""

    power_supply_option = models.ForeignKey(
        'ElectricPowerSupplyOption',
        on_delete=models.CASCADE,
        related_name='ea_model_lene_item_options_power_supply_options',
        verbose_name=_("Опция напряжения питания"),
        help_text=_("Опция напряжения питания")
    )

    control_unit = models.ForeignKey(
        'params.ControlUnitInstalledOption',
        on_delete=models.CASCADE,
        related_name='ea_model_lene_item_options_control_unit_options',
        verbose_name=_("Блок управления"),
        help_text=_("Тип блока управления")
    )

    encoding = models.CharField(
        max_length=50,
        verbose_name=_("Кодировка"),
        help_text=_("Код для генерации артикула"),
        blank=True,  # ДОБАВЛЯЕМ - разрешаем пустые значения
        null=True,  # ДОБАВЛЯЕМ - разрешаем NULL в базе
        default=''  # ДОБАВЛЯЕМ - значение по умолчанию пустая строка
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name=_("По умолчанию"),
        help_text=_("Выбирать этот блок управления по умолчанию")
    )

    # Дополнительные технические параметры если нужно
    # power_consumption = models.DecimalField(
    #     max_digits=6, decimal_places=2,
    #     null=True, blank=True,
    #     verbose_name=_("Потребляемая мощность, Вт"),
    #     help_text=_("Мощность потребления блока управления")
    # )

    class Meta:
        verbose_name = _("Опция блока управления для напряжения")
        verbose_name_plural = _("Опции блоков управления для напряжений")
        ordering = ['sorting_order']
        # unique_together = ['power_supply_option', 'control_unit']

    def __str__(self):
        return f"{self.power_supply_option} -> {self.control_unit}"
    def get_description_data(self) -> Dict[str, Any]:

        """Получить структурированные данные для описания """
        # logger.debug(f"EA logger get_description_data")
        # print(f"EA model line item print get_description_data")
        data = {
            'control_unit': {'display_name':'Тип установленного блока управления', 'value':self.control_unit.name if self.control_unit else None,
                             'description':self.control_unit.description if self.control_unit.description  else None, 'feature_list':self.control_unit.feature_list if self.control_unit.feature_list  else []},
            'is_default' : {'display_name' : 'Стандарт' , 'value' : self.is_default} ,
            'is_installed': False if self.control_unit.name =='none' else True
        }
        return data
    def clean(self):
        """Валидация перед сохранением"""
        # Убедимся что encoding уникален в рамках power_supply_option
        # if self.encoding and self.power_supply_option:
        #     exists = ElectricControlUnitOption.objects.filter(
        #         power_supply_option=self.power_supply_option,
        #         encoding=self.encoding
        #     ).exclude(pk=self.pk).exists()
        #     if exists:
        #         raise ValidationError({
        #             'encoding': _('Кодировка должна быть уникальной для данного напряжения')
        #         })
        return

class ElectricPowerSupplyOption(BaseThroughOptionNoDefault):
    """Опции напряжения питания для модели в серии электроприводов"""
    """
        through-модель для температурных опций
        Наследует от BaseThroughOptionNoDefault (нет напряжения питания по дефолту и добавляет температурные поля
        """
    model_line_item = models.ForeignKey(
        ElectricActuatorModelLineItem,
        on_delete=models.CASCADE,
        related_name='model_line_item_power_supply_option',
        verbose_name=_("Модель"),
        help_text=_('Модель в серии электроприводов'))
    power_supply = models.ForeignKey(PowerSupplies,
                                     related_name='electric_actuator_data_model_power_supply', null=False,
                                     on_delete=models.CASCADE,
                                     verbose_name=_("Напряжение"),
                                     help_text=_('Напряжение питания модели'))

    motor_current_rated = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True,
                                              default=0,
                                              verbose_name=_('Ток ном,А'),
                                              help_text=_('Номинальный ток двигателя'))

    motor_current_starting = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True,
                                                 default=0,
                                                 verbose_name=_('Ток пуск,А'),
                                                 help_text=_('Пусковой ток двигателя'))
    motor_power = models.DecimalField(max_digits=7, decimal_places=3, blank=True, null=True,
                                      default=0,
                                      verbose_name=_('Мощн,кВт'),
                                      help_text=_('Мощность двигателя, кВт'))
    time_to_open = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True,
                                       default=0,
                                       verbose_name=_('Откр, с'),
                                       help_text=_(
                                           'Альтернативное время открытия, сек - 0 если совпадает с базовой моделью'))
    time_to_close = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True,
                                        default=0,
                                        verbose_name=_('Закр, с'),
                                        help_text=_(
                                            'Альтернативное время закрытия, с - 0 если совпадает с базовой моделью'))
    torque_min = models.DecimalField(max_digits=5, decimal_places=0,
                                     default=0,
                                     verbose_name=_('Мин. усилие'),
                                     help_text=_('Альтернативное Мин.усилие - 0 если совпадает с базовой моделью'))
    torque_max = models.DecimalField(max_digits=5, decimal_places=0,
                                     default=0,
                                     verbose_name=_('Макс.усилие'),
                                     help_text=_(
                                         'Альтернативное Максимальное усилие - 0 если совпадает с базовой моделью'))

    class Meta:
        verbose_name = _("Опция напряжения питания для модели в серии электроприводов")
        verbose_name_plural = _("Опции напряжения питания для модели в серии электроприводов")
        ordering = ['sorting_order']
        # unique_together = ['model_line' , 'encoding']

    def get_description_data(self) -> Dict[str, Any]:
        """Получить структурированные данные для описания """
        # logger.debug(f"EA logger get_description_data")
        # print(f"EA model line item print get_description_data")
        data = {
            'power_supply': {'display_name':'Напряжение питания, В', 'value':self.power_supply.name if self.power_supply else None},
            'motor_current_rated': {'display_name':'Ток номинальный, А', 'value':self.motor_current_rated},
            'motor_current_starting': {'display_name':'Пусковой ток, А', 'value':self.motor_current_starting},
            'motor_power': {'display_name': 'Мощность электродвигателя, кВт', 'value': self.motor_power},
            'time_to_open': {'display_name': 'Время открытия', 'value': self.time_to_open},
            'time_to_close': {'display_name': 'Время закрытия', 'value': self.time_to_close},
            'torque_min': {'display_name': 'Вращающий момент мин, Нм', 'value': self.time_to_close},
            'torque_max': {'display_name': 'Вращающий момент макс, Нм', 'value': self.time_to_close},
        }
        return data

    @property
    def available_control_units(self):
        """Доступные блоки управления для этого напряжения"""
        return self.control_unit_options.filter(is_active=True)

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'

    @property
    def is_default(self):
        """Всегда False для опций напряжения питания (так как нет дефолтного)"""
        return False

    def clean(self):
        """Валидация перед сохранением"""
        errors = {}

        # Проверка обязательных полей
        if not self.model_line_item:
            errors['model_line_item'] = _('Необходимо указать модель в серии')

        if not self.power_supply:
            errors['power_supply'] = _('Необходимо указать напряжение питания')

        # Валидация числовых полей
        if self.motor_current_rated is not None and self.motor_current_rated < 0:
            errors['motor_current_rated'] = _('Ток не может быть отрицательным')

        if self.motor_current_starting is not None and self.motor_current_starting < 0:
            errors['motor_current_starting'] = _('Пусковой ток не может быть отрицательным')

        if self.motor_power is not None and self.motor_power < 0:
            errors['motor_power'] = _('Мощность не может быть отрицательной')

        # Проверка логики: пусковой ток должен быть больше или равен номинальному
        if (self.motor_current_starting is not None and
                self.motor_current_rated is not None and
                self.motor_current_starting < self.motor_current_rated):
            errors['motor_current_starting'] = _(
                'Пусковой ток должен быть больше или равен номинальному току'
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Сохранение с установкой encoding и валидацией

        Параметры:
            preserve_encoding (bool): Если True - сохраняет текущий encoding без изменений
                                       Если False или не указан - автоматически устанавливает из power_supply
        """
        # Извлекаем наш кастомный параметр из kwargs
        preserve_encoding = kwargs.pop('preserve_encoding', False)
        if not preserve_encoding :
            # Автоматически устанавливаем encoding из имени power_supply
            if self.power_supply and self.model_line_item and self.encoding:
                self.encoding = str(self.power_supply.encoding)

        # Если encoding слишком длинный, обрезаем его
        if self.encoding and len(self.encoding) > 50:
            self.encoding = self.encoding[:50]

        # Выполняем валидацию
        self.full_clean()

        # Сохраняем объект
        super().save(*args, **kwargs)

    def __str__(self):
        """Строковое представление"""
        if self.model_line_item and self.power_supply:
            return f"{self.power_supply.name}"
        return super().__str__()

    def display_name(self):
        """Строковое представление для отображения в списке"""
        if self.model_line_item and self.power_supply:
            return f"{self.model_line_item.name}.{self.power_supply.encoding}"
        return super().__str__()

    def create_copy(self) :
        """Создать копию элемента с добавлением ' Копия' к name и code"""
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"=" * 50)
        logger.info(f"НАЧАЛО КОПИРОВАНИЯ ОПЦИИ ПИТАНИЯ ID: {self.id}")
        logger.info(f"Исходный объект: {self.display_name() if hasattr(self , 'display_name') else self}")

        # Создаем копию объекта
        copy_obj = ElectricPowerSupplyOption()
        logger.info(f"Создан пустой объект-копия")

        # Копируем все поля кроме первичного ключа
        for field in self._meta.fields :
            if field.name not in ['id' , 'pk'] :
                old_value = getattr(self , field.name)
                setattr(copy_obj , field.name , old_value)
                logger.debug(f"  Поле {field.name}: '{old_value}' скопировано")

        # Обрабатываем encoding
        if copy_obj.encoding :
            if not copy_obj.encoding.endswith('_copy') :
                old_encoding = copy_obj.encoding
                copy_obj.encoding = f"{copy_obj.encoding}_copy"
                logger.info(f"  Encoding изменен: '{old_encoding}' -> '{copy_obj.encoding}'")
        else :
            copy_obj.encoding = f"copy_{self.id}"
            logger.info(f"  Encoding установлен: '{copy_obj.encoding}'")

        # Сохраняем копию
        copy_obj.save(preserve_encoding=True)
        logger.info(f"Копия сохранена с ID: {copy_obj.id}")
        logger.info(f"  model_line_item ID в копии: {copy_obj.model_line_item_id}")

        # Копируем связанные опции
        logger.info(f"НАЧАЛО КОПИРОВАНИЯ СВЯЗАННЫХ ОПЦИЙ")
        result = self._copy_related_options(copy_obj)
        logger.info(f"Скопировано связанных опций: {result.get('copied_objects' , 0)}")

        logger.info(f"КОПИРОВАНИЕ ЗАВЕРШЕНО. Итоговый объект ID: {copy_obj.id}")
        logger.info(f"=" * 50)

        return copy_obj

    def _copy_related_options(self , copy_obj) :
        """
        Копировать связанные опции (ElectricControlUnitOption) для скопированной опции питания
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"  _copy_related_options: target copy_obj ID = {copy_obj.id}")
        logger.info(f"  _copy_related_options: исходная опция питания ID = {self.id}")

        # Правильный related_name из модели ElectricControlUnitOption
        related_name = 'ea_model_lene_item_options_power_supply_options'

        try :
            # Проверяем, есть ли связанные объекты
            if not hasattr(self , related_name) :
                logger.error(f"  У объекта нет атрибута {related_name}")
                # Покажем все доступные атрибуты для отладки
                attrs = [attr for attr in dir(self) if not attr.startswith('_') and 'power' in attr.lower()]
                logger.info(f"  Доступные атрибуты с 'power': {attrs}")
                return {'total_relations' : 0 , 'copied_objects' : 0}

            related_manager = getattr(self , related_name)
            related_qs = related_manager.all()

            logger.info(f"  Найдено блоков управления: {related_qs.count()}")

            # Выведем их для отладки
            for obj in related_qs :
                logger.info(f"    - ID: {obj.id}, encoding: {obj.encoding}")

            if not related_qs.exists() :
                logger.info(f"  Нет связанных блоков управления для копирования")
                return {'total_relations' : 0 , 'copied_objects' : 0}

            copied_count = 0
            for original_obj in related_qs :
                try :
                    logger.info(
                        f"    Копирование блока управления ID: {original_obj.id}, encoding: {original_obj.encoding}")

                    # Создаем копию
                    new_obj = ElectricControlUnitOption()

                    # Копируем все поля кроме первичного ключа
                    for field in original_obj._meta.fields :
                        if field.name not in ['id' , 'pk'] :
                            # Если это ForeignKey на опцию питания, заменяем на copy_obj
                            if (isinstance(field , models.ForeignKey) and
                                    field.related_model == ElectricPowerSupplyOption) :
                                setattr(new_obj , field.name , copy_obj)
                                logger.info(f"      Поле {field.name} установлено на copy_obj ID: {copy_obj.id}")
                            else :
                                setattr(new_obj , field.name , getattr(original_obj , field.name))

                    # Добавляем суффикс к encoding для уникальности (если нужно)
                    # if new_obj.encoding and not new_obj.encoding.endswith('_copy') :
                    #     new_obj.encoding = f"{new_obj.encoding}_copy"

                    # Сохраняем
                    new_obj.save()
                    copied_count += 1
                    logger.info(f"      СОЗДАН НОВЫЙ БЛОК УПРАВЛЕНИЯ ID: {new_obj.id}")

                except Exception as e :
                    logger.error(f"    Ошибка при копировании блока управления {original_obj.id}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())

            logger.info(f"Копирование завершено. Скопировано блоков управления: {copied_count}")
            return {'total_relations' : 1 , 'copied_objects' : copied_count}

        except Exception as e :
            logger.error(f"  Ошибка при получении связанных блоков управления: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'total_relations' : 0 , 'copied_objects' : 0}