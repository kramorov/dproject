# electric_actuators/models/ea_model_line_item_options.py
"""
Through-модели опций уровня model_line_item.

Привязываются к конкретной модели в серии (ElectricActuatorModelLineItem)
и её напряжению питания (ElectricPowerSupplyOption).

Модели:
    ElectricPowerSupplyOption     — напряжение + моторные параметры
    ElectricSafetyPositionOption  — положение безопасности
    ElectricControlUnitOption     — блок управления + счётчики + сигналы
"""
from django.db import models
from django.utils.functional import cached_property

from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union
from django.core.exceptions import ValidationError

from core.models import StructuredDataMixin
from electric_actuators.models.ea_model_line_item import ElectricActuatorModelLineItem
from options.models import BaseThroughOptionNoDefault, BaseThroughOption

import logging

from params.models import PowerSupplies
from electric_actuators.models.ea_allowed_options import AllowedControlUnitOption

logger = logging.getLogger(__name__)

class ElectricSafetyPositionOption(BaseThroughOption):
    """Положение безопасности для опции напряжения питания.
       Привязывается к конкретному напряжению (как ControlUnit),
       может различаться для разных model_line_item."""
    power_supply_option = models.ForeignKey(
        'ElectricPowerSupplyOption',
        on_delete=models.CASCADE,
        related_name='safety_position_power_supply_option',
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
        related_name='ea_model_line_item_options_power_supply_options',
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

    # ── Счётчики оборотов ──
    default_turn_counter = models.ForeignKey(
        'params.TurnCounterOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='default_for_control_unit_options',
        verbose_name=_("Счётчик оборотов по умолчанию"),
        help_text=_("Значение по умолчанию для этой пары БУ×напряжение")
    )
    allowed_turn_counters = models.ManyToManyField(
        'params.TurnCounterOption',
        blank=True,
        related_name='allowed_in_control_unit_options',
        verbose_name=_("Доступные счётчики оборотов"),
        help_text=_("Все допустимые счётчики для этой пары БУ×напряжение")
    )

    # ── Профили сигналов ──
    default_signal_profile = models.ForeignKey(
        'params.ControlUnitSignalProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='default_for_control_unit_options',
        verbose_name=_("Профиль сигналов по умолчанию"),
        help_text=_("Значение по умолчанию для этой пары БУ×напряжение")
    )
    allowed_signal_profiles = models.ManyToManyField(
        'params.ControlUnitSignalProfile',
        blank=True,
        related_name='allowed_in_control_unit_options',
        verbose_name=_("Доступные профили сигналов"),
        help_text=_("Все допустимые профили сигналов для этой пары БУ×напряжение")
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
            'control_unit': {
                'display_name': 'Тип установленного блока управления',
                'value': self.control_unit.name if self.control_unit else None,
                'description': self.control_unit.description if self.control_unit else None,
                'feature_list': self.control_unit.feature_list if self.control_unit else [],
            },
            'encoding': {
                'display_name': 'Кодировка',
                'value': self.resolved_encoding,
            },
            'is_default': {'display_name': 'Стандарт', 'value': self.is_default},
            'is_installed': False if (self.control_unit and self.control_unit.name == 'none') else True,
            'default_turn_counter': {
                'display_name': 'Счётчик оборотов',
                'value': self.default_turn_counter.name if self.default_turn_counter else None,
            },
            'default_signal_profile': {
                'display_name': 'Профиль сигналов',
                'value': self.default_signal_profile.name if self.default_signal_profile else None,
            },
        }
        return data

    @cached_property
    def resolved_encoding(self) -> str:
        """Encoding БУ для данной серии — из AllowedControlUnitOption.
        Если записи нет — собственный encoding (обратная совместимость).
        Результат кешируется на время жизни объекта.
        """
        if not (self.power_supply_option_id and self.control_unit_id):
            return self.encoding or ''
        try:
            ml = self.power_supply_option.model_line_item.model_line
            allowed = AllowedControlUnitOption.objects.get(
                model_line=ml, control_unit=self.control_unit
            )
            return allowed.encoding
        except (AllowedControlUnitOption.DoesNotExist, AttributeError):
            return self.encoding or ''

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
            'torque_min': {'display_name': 'Вращающий момент мин, Нм', 'value': self.torque_min},
            'torque_max': {'display_name': 'Вращающий момент макс, Нм', 'value': self.torque_max},
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

    @property
    def display_name(self):
        """Строковое представление для отображения в списке"""
        if self.model_line_item and self.power_supply:
            return f"{self.model_line_item.name}.{self.power_supply.encoding}"
        return super().__str__()

    # Явно указываем through-модели для копирования
    COPY_THROUGH_MODELS = [
        'ea_model_line_item_options_power_supply_options' ,  # ElectricControlUnitOption
    ]

    def create_copy(self) :
        """Создать копию элемента с копированием through-моделей"""
        logger.info(f"=" * 50)
        logger.info(f"НАЧАЛО КОПИРОВАНИЯ {self.__class__.__name__} ID: {self.id}")
        logger.info(f"Исходный объект: {self.display_name}")

        # Копируем основной объект
        copy_obj = self._copy_self()

        # Копируем through-модели
        total_copied = 0
        for through_field in self.COPY_THROUGH_MODELS :
            copied_count = self._copy_through_relations(through_field , copy_obj)
            total_copied += copied_count

        logger.info(f"КОПИРОВАНИЕ ЗАВЕРШЕНО. ID копии: {copy_obj.id}, скопировано through-моделей: {total_copied}")
        logger.info(f"=" * 50)

        return copy_obj

    def _copy_self(self) :
        """Копирование основного объекта"""
        logger.debug(f"Начало копирования основного объекта {self.__class__.__name__} ID: {self.id}")

        # Создаем пустую копию
        copy_obj = self.__class__()
        logger.debug(f"Создан пустой объект-копия")

        # Копируем все поля кроме первичного ключа
        for field in self._meta.fields :
            if field.name not in ['id' , 'pk'] :
                old_value = getattr(self , field.name)
                setattr(copy_obj , field.name , old_value)
                logger.debug(f"  Поле {field.name}: '{old_value}' скопировано")

        # Обрабатываем encoding
        if hasattr(copy_obj , 'encoding') :
            if copy_obj.encoding :
                if not copy_obj.encoding.endswith('_copy') :
                    old_encoding = copy_obj.encoding
                    copy_obj.encoding = f"{copy_obj.encoding}_copy"
                    logger.info(f"Encoding изменен: '{old_encoding}' -> '{copy_obj.encoding}'")
            else :
                copy_obj.encoding = f"copy_{self.id}"
                logger.info(f"Encoding установлен: '{copy_obj.encoding}'")

        # Сохраняем копию
        copy_obj.save(preserve_encoding=True)
        logger.info(f"Основной объект скопирован. ID оригинала: {self.id} -> ID копии: {copy_obj.id}")

        return copy_obj

    def _copy_through_relations(self , through_field , parent_copy) :
        """
        Копирование through-моделей

        Args:
            through_field: имя related_name through-модели
            parent_copy: копия родительского объекта

        Returns:
            int: количество скопированных through-объектов
        """
        logger.info(f"Начинаем копирование through-модели '{through_field}'")

        # Получаем менеджер through-модели
        through_manager = getattr(self , through_field , None)

        # Проверяем существование менеджера
        if not through_manager :
            logger.warning(f"Поле '{through_field}' не найдено в объекте {self.__class__.__name__}")
            return 0

        # Проверяем, что это менеджер связанных объектов
        if not hasattr(through_manager , 'all') :
            logger.warning(f"Поле '{through_field}' не является менеджером связанных объектов")
            return 0

        # Получаем queryset through-объектов
        through_objects = through_manager.all()
        objects_count = through_objects.count()

        if objects_count == 0 :
            logger.info(f"Нет through-объектов для копирования в '{through_field}'")
            return 0

        logger.info(f"Найдено {objects_count} through-объектов для копирования")

        # Копируем каждый through-объект
        copied_count = 0
        errors_count = 0

        for idx , original_through in enumerate(through_objects , 1) :
            try :
                logger.debug(
                    f"  [{idx}/{objects_count}] Копирование through-объекта {original_through.__class__.__name__} ID: {original_through.id}")

                # Копируем through-объект
                new_through = self._copy_through_object(original_through , parent_copy)

                logger.info(f"    Скопирован through-объект: ID {original_through.id} -> {new_through.id}")
                copied_count += 1

            except Exception as e :
                errors_count += 1
                logger.error(f"    ОШИБКА при копировании through-объекта ID {original_through.id}: {e}")
                import traceback
                logger.error(f"    Traceback: {traceback.format_exc()}")

        # Логируем итоги
        logger.info(
            f"Завершено копирование through-модели '{through_field}': скопировано {copied_count}/{objects_count}, ошибок: {errors_count}")

        return copied_count

    def _copy_through_object(self , original_through , parent_copy) :
        """
        Копирование одного through-объекта

        Args:
            original_through: исходный through-объект
            parent_copy: копия родительского объекта

        Returns:
            Model: скопированный through-объект
        """
        logger.debug(f"    Копирование through-объекта {original_through.__class__.__name__}")

        # Создаем новый through-объект
        new_through = original_through.__class__()

        # Копируем все поля
        for field in original_through._meta.fields :
            # Пропускаем первичный ключ
            if field.name in ['id' , 'pk'] :
                continue

            # Получаем значение поля
            value = getattr(original_through , field.name)

            # Обрабатываем ForeignKey поля
            if isinstance(field , models.ForeignKey) :
                # Если это ForeignKey на родительскую модель (ElectricPowerSupplyOption)
                if field.related_model == self.__class__ :
                    setattr(new_through , field.name , parent_copy)
                    logger.debug(f"      Поле {field.name}: FK на родителя заменен на копию ID {parent_copy.id}")

                # Если это ForeignKey на другую модель (ControlUnitInstalledOption)
                elif hasattr(value , 'create_copy') :
                    # Создаем копию связанного объекта
                    logger.debug(f"      Поле {field.name}: создаем копию {value.__class__.__name__}")
                    copied_value = value.create_copy()
                    setattr(new_through , field.name , copied_value)
                    logger.debug(f"      Поле {field.name}: FK заменен на скопированный объект ID {copied_value.id}")

                # Если это ForeignKey на другую модель без create_copy
                else :
                    setattr(new_through , field.name , value)
                    logger.debug(f"      Поле {field.name}: скопировано значение FK ID {value.id if value else None}")

            # Обрабатываем обычные поля
            else :
                setattr(new_through , field.name , value)
                logger.debug(f"      Поле {field.name}: скопировано значение '{value}'")

        # Обрабатываем encoding для through-объекта
        # if hasattr(new_through , 'encoding') and new_through.encoding :
        #     if not new_through.encoding.endswith('_copy') :
        #         old_encoding = new_through.encoding
        #         new_through.encoding = f"{new_through.encoding}_copy"
        #         logger.debug(f"      Encoding изменен: '{old_encoding}' -> '{new_through.encoding}'")

        # Сохраняем through-объект
        new_through.save()
        logger.debug(f"      Through-объект сохранен с ID {new_through.id}")

        return new_through