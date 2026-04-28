# pneumatic_actuators/models/pa_actuator_selected.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from typing import List, Optional, Tuple, Any, Dict, Union
from decimal import Decimal
from django.core.exceptions import ValidationError
import re
from tabulate import tabulate

import logging
from django.utils.html import format_html


logger = logging.getLogger(__name__)

from pneumatic_actuators.models import PneumaticActuatorModelLineItem, PneumaticActuatorBody, PneumaticCloseTimeParameter
from .py_options_constants import SAFETY_POSITION_NC_DEFAULT_CODE , \
    ACTUATOR_VARIETY_RP_DEFAULT_CODE



# Добавляем импорт абстрактного класса
from core.models import StructuredDataMixin

class PneumaticActuatorSelected(StructuredDataMixin, models.Model):
    """
    Выбранный из списка моделей привод с выбранными опциями.
    """
    name = models.CharField(max_length=200,
                            verbose_name=_("Название"),
                            help_text=_('Название привода - формируется автоматически'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код привода - формируется автоматически"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание привода - формируется автоматически'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    selected_model_line_item = models.ForeignKey(PneumaticActuatorModelLineItem,
                                       related_name='selected_pneumatic_actuator_model_line_item',
                                       on_delete=models.CASCADE,
                                       verbose_name=_('Модель'),
                                       help_text=_('Модель пневмопривода'))

    # Выбранные опции
    selected_safety_position = models.ForeignKey(
        'PneumaticSafetyPositionOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Выбранное положение безопасности"),
        help_text=_('Выбранное положение безопасности привода')
    )

    selected_springs_qty = models.ForeignKey(
        'PneumaticSpringsQtyOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Выбранное количество пружин"),
        help_text=_('Выбранное количество пружин привода')
    )

    # НОВЫЕ ОПЦИИ через model_line
    selected_temperature = models.ForeignKey(
        'PneumaticTemperatureOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Температурная опция"),
        help_text=_('Выбранная температурная опция')
    )

    selected_ip = models.ForeignKey(
        'PneumaticIpOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Степень защиты IP"),
        help_text=_('Выбранная степень защиты IP')
    )

    selected_exd = models.ForeignKey(
        'PneumaticExdOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Взрывозащита"),
        help_text=_('Выбранная опция взрывозащиты')
    )

    selected_body_coating = models.ForeignKey(
        'PneumaticBodyCoatingOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Покрытие корпуса"),
        help_text=_('Выбранное покрытие корпуса')
    )

    selected_hand_wheel = models.ForeignKey(
        'PneumaticHandWheelOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Встроенный дублер"),
        help_text=_('Встроенный ручной дублер')
    )
    is_unique = models.BooleanField(default=True, verbose_name='Это уникальная конфигурация')

    # ОБЩАЯ КОНФИГУРАЦИЯ ДЛЯ ВСЕХ ВАЛИДАЦИЙ
    _OPTION_CONFIG = {
        'selected_safety_position': {
            'model_class': 'PneumaticSafetyPositionOption',
            'label': 'положение безопасности',
            'parent_field': 'model_line_item',  # Для связи с моделью
            'model_path': 'pneumatic_actuators.models.pa_options.PneumaticSafetyPositionOption'
        },
        'selected_springs_qty': {
            'model_class': 'PneumaticSpringsQtyOption',
            'label': 'количество пружин',
            'parent_field': 'model_line_item',
            'model_path': 'pneumatic_actuators.models.pa_options.PneumaticSpringsQtyOption'
        },
        'selected_temperature': {
            'model_class': 'PneumaticTemperatureOption',
            'label': 'температурная опция',
            'parent_field': 'model_line',  # Здесь model_line, а не model_line_item
            'model_path': 'pneumatic_actuators.models.pa_options.PneumaticTemperatureOption'
        },
        'selected_ip': {
            'model_class': 'PneumaticIpOption',
            'label': 'степень защиты IP',
            'parent_field': 'model_line',
            'model_path': 'pneumatic_actuators.models.pa_options.PneumaticIpOption'
        },
        'selected_exd': {
            'model_class': 'PneumaticExdOption',
            'label': 'взрывозащита',
            'parent_field': 'model_line',
            'model_path': 'pneumatic_actuators.models.pa_options.PneumaticExdOption'
        },
        'selected_body_coating': {
            'model_class': 'PneumaticBodyCoatingOption',
            'label': 'покрытие корпуса',
            'parent_field': 'model_line',
            'model_path': 'pneumatic_actuators.models.pa_options.PneumaticBodyCoatingOption'
        },
        'selected_hand_wheel': {
            'model_class': 'PneumaticHandWheelOption',
            'label': 'ручной дублер',
            'parent_field': 'model_line',
            'model_path': 'pneumatic_actuators.models.pa_options.PneumaticHandWheelOption'
        }
    }

    @classmethod
    def get_option_fields(cls):
        """Возвращает список всех полей опций"""
        return list(cls._OPTION_CONFIG.keys())

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _('Модель пневмопривода')
        verbose_name_plural = _('Модели пневмоприводов')
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=[
        #             'name',
        #             'selected_model_line_item',
        #             'selected_safety_position',
        #             'selected_springs_qty',
        #             'selected_temperature',
        #             'selected_ip',
        #             'selected_exd',
        #             'selected_body_coating',
        #             'selected_hand_wheel'
        #         ],
        #         name='unique_actuator_configuration',  # Понятное имя
        #         # condition=models.Q(is_active=True),  # Если нужно только для активных
        #     )
        # ]

    def __str__(self):
        return self.name

        # ==================== StructuredDataMixin методы ====================

    # GET /api/core/?model=pneumatic_actuators.PneumaticActuatorSelected&id=4&fmt=compact
    # GET /api/core/?model=pneumatic_actuators.PneumaticActuatorSelected&id=4&fmt=display&view=card
    # /api/core/?model=pneumatic_actuators.PneumaticActuatorSelected&id=4&fmt=full&include=
    def get_compact_data(self) -> Dict[str , Any] :
        """
        Минимальные данные для списков и таблиц
        """
        print(f"=== DEBUG get_compact_data called ===")
        print(f"Object: {self.id} - {self.name}")
        # Безопасный доступ к метаданным
        model_name = self._get_model_name()
        app_label = self._get_app_label()

        # Основные данные
        data = {
            'id' : self.id ,
            'name' : self.name ,
            'code' : self.code ,
            'is_active' : self.is_active ,
            'model' : model_name ,
            'app' : app_label ,
            'sorting_order' : self.sorting_order ,
        }

        # Добавляем данные модели, если есть
        if self.selected_model_line_item :
            if hasattr(self.selected_model_line_item , 'get_compact_data') :
                data['selected_model'] = self.selected_model_line_item.get_compact_data()
            else :
                data['selected_model'] = {
                    'id' : self.selected_model_line_item.id ,
                    'name' : str(self.selected_model_line_item) ,
                }

        # Добавляем информацию об опциях
        option_fields = [
            'selected_safety_position' ,
            'selected_springs_qty' ,
            'selected_temperature' ,
            'selected_ip' ,
            'selected_exd' ,
            'selected_body_coating',
            'selected_hand_wheel'
        ]

        for field_name in option_fields :
            field = getattr(self , field_name)
            if field :
                if hasattr(field , 'get_compact_data') :
                    data[field_name] = field.get_compact_data()
                else :
                    data[field_name] = {
                        'id' : field.id ,
                        'name' : str(field) ,
                    }

        return data

    def get_display_data(self , view_type: str = 'detail') -> Dict[str , Any] :
        from django.utils.translation import gettext_lazy as _
        """
        Данные для отображения в UI.
        Используем существующую _generate_tech_description для конвертации
        в новый формат
        """
        print(f"=== DEBUG get_display_data called ===")
        print(f"View type: {view_type}")
        # Используем базовые поля из миксина
        fields = self._get_base_display_fields()

        # Обновляем лейблы для специфичных полей
        fields.update({
            'code' : self._format_field(
                self.code ,
                'code' ,
                label=_('Артикул') ,
                icon='🏷️' ,
                priority=2
            ) ,
            'sorting_order' : self._format_field(
                self.sorting_order ,
                'number' ,
                label=_('Порядок сортировки') ,
                icon='🔢' ,
                priority=3
            ) ,
        })

        # Добавляем связанную модель
        if self.selected_model_line_item :
            fields['selected_model'] = self._format_foreign_key(
                self.selected_model_line_item ,
                label=_('Модель') ,
                icon='⚙️' ,
                priority=4 ,
                include_data='compact'
            )

        # Добавляем опции
        option_configs = [
            ('selected_safety_position' , _('Положение безопасности') , '🔄' , 5) ,
            ('selected_springs_qty' , _('Количество пружин') , '🔗' , 6) ,
            ('selected_temperature' , _('Температурная опция') , '🌡️' , 7) ,
            ('selected_ip' , _('Степень защиты IP') , '🛡️' , 8) ,
            ('selected_exd' , _('Взрывозащита') , '⚡' , 9) ,
            ('selected_body_coating' , _('Покрытие корпуса') , '🎨' , 10) ,
            ('selected_hand_wheel' , _('Тип установленного ручного дублера') , '🎨' , 11) ,
        ]

        for field_name , label , icon , priority in option_configs :
            field_value = getattr(self , field_name)
            if field_value :
                fields[field_name] = self._format_foreign_key(
                    field_value ,
                    label=label ,
                    icon=icon ,
                    priority=priority ,
                    include_data='compact'
                )

        # Добавляем техническое описание из существующего метода
        tech_description = self._generate_tech_description_for_display()
        fields['technical_description'] = self._format_field(
            tech_description ,
            'html' ,
            label=_('Техническое описание') ,
            icon='📋' ,
            priority=20 ,
            multiline=True
        )

        # Добавляем рассчитанный вес
        weight = self.calculated_weight
        if weight :
            fields['weight'] = self._format_field(
                float(weight) ,
                'number' ,
                label=_('Вес') ,
                icon='⚖️' ,
                priority=15 ,
                unit='кг'
            )

        # Для разных типов отображения
        if view_type == self.CARD :
            return {
                'title' : self.name ,
                'subtitle' : self.code or '' ,
                'description' : self.description[:150] + '...' if self.description else '' ,
                'badges' : [
                    {'text' : self.code , 'type' : 'code'} if self.code else None ,
                    {'text' : 'Активен' , 'type' : 'success'} if self.is_active
                    else {'text' : 'Неактивен' , 'type' : 'secondary'} ,
                    {'text' : f'Вес: {weight} кг' , 'type' : 'info'} if weight else None ,
                ] ,
                'details' : [
                    {'label' : 'Модель' , 'value' : str(self.selected_model_line_item)} if self.selected_model_line_item else None ,
                    {'label' : 'Сортировка' , 'value' : self.sorting_order} ,
                ]
            }

        elif view_type == self.LIST :
            # Создаем строку с опциями для отображения в списке
            options_str = []
            for field_name , label , _ , _ in option_configs :
                field_value = getattr(self , field_name)
                if field_value :
                    options_str.append(str(field_value))

            return {
                'id' : self.id ,
                'name' : self.name ,
                'code' : self.code ,
                'model' : str(self.selected_model_line_item) if self.selected_model_line_item else '' ,
                'options' : ', '.join(options_str) if options_str else '' ,
                'weight' : float(weight) if weight else None ,
                'is_active' : self.is_active ,
                'sorting_order' : self.sorting_order ,
            }

        elif view_type == self.BADGE :
            return {
                'text' : self.name ,
                'code' : self.code ,
                'type' : 'pneumatic_actuator' ,
                'color' : 'blue' if self.is_active else 'gray' ,
                'subtitle' : f'Модель: {self.selected_model_line_item.code if self.selected_model_line_item else ""}'
            }

        # По умолчанию DETAIL
        return {
            'title' : self.name ,
            'subtitle' : f'Артикул: {self.code}' if self.code else '' ,
            'fields' : fields ,
            'actions' : self._get_actions()
        }


    # ==================== Вспомогательные методы ====================

    def _generate_tech_description_for_display(self) -> str :
        """
        Генерация технического описания для отображения в UI
        Адаптация существующего метода для нового формата
        """
        # Можно использовать существующий метод с небольшими изменениями
        return self._generate_tech_description()

    def _generate_html_description(self) -> str :
        """
        Генерация HTML описания
        """
        # Простая реализация - можно расширить
        desc_parts = []

        if self.description :
            desc_parts.append(f'<p>{self.description}</p>')

        if self.selected_model_line_item and self.selected_model_line_item.description :
            desc_parts.append(f'<p><strong>Описание модели:</strong> {self.selected_model_line_item.description}</p>')

        return '\n'.join(desc_parts)

    def get_description_data(self) -> Dict[str , Dict[str , Any]] :
        """Получить унифицированную плоскую структуру данных для описания"""
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.debug(f"logger get_description_data")

        data = {}

        # ==================== ДАННЫЕ ИЗ ГЛАВНОЙ МОДЕЛИ ====================
        try :
            data['model_name'] = {
                'category' : 'main' ,
                'title' : 'Модель' ,
                'data' : self.code if self.code else None ,
                'display_data' : self.code if self.code else 'Не указано' ,
                'text_data' : f"Модель: {self.code}" if self.code else None
            }
            logger.debug(f"model_name added: {self.code}")
        except Exception as e :
            logger.error(f"Error adding model_name: {e}")
            traceback.print_exc()

        # ==================== РАСЧЕТНЫЕ ПАРАМЕТРЫ ====================
        try :
            ttc = PneumaticCloseTimeParameter.get_time_to_close(
                self.selected_model_line_item.body_id if self.selected_model_line_item else None ,
                self.selected_springs_qty ,
                pressure=None
            )
            logger.debug(f"time_to_close calculated: {ttc}")
        except Exception as e :
            logger.error(f"Error in get_time_to_close: {e}")
            traceback.print_exc()
            ttc = None

        try :
            data['weight'] = {
                'category' : 'calculated' ,
                'title' : 'Вес' ,
                'data' : float(self.calculated_weight) if self.calculated_weight else None ,
                'display_data' : f"{float(self.calculated_weight):.1f} кг" if self.calculated_weight else 'Не указано' ,
                'text_data' : f"Вес: {float(self.calculated_weight):.1f} кг" if self.calculated_weight else None
            }
            logger.debug(f"weight added: {self.calculated_weight}")
        except Exception as e :
            logger.error(f"Error adding weight: {e}")
            traceback.print_exc()

        try :
            data['time_to_close'] = {
                'category' : 'calculated' ,
                'title' : 'Время закрытия' ,
                'data' : ttc ,
                'display_data' : f"{ttc:.1f} сек" if ttc else 'Не указано' ,
                'text_data' : f"Время закрытия: {ttc:.1f} сек" if ttc else None
            }
            logger.debug(f"time_to_close added: {ttc}")
        except Exception as e :
            logger.error(f"Error adding time_to_close: {e}")
            traceback.print_exc()

        # ==================== БАЗОВЫЕ СВОЙСТВА ====================
        try :
            data['brand'] = {
                'category' : 'basic_properties' ,
                'title' : 'Бренд' ,
                'data' : self.selected_model_line_item.brand.id if self.selected_model_line_item and self.selected_model_line_item.brand else None ,
                'display_data' : self.selected_model_line_item.brand.name if self.selected_model_line_item and self.selected_model_line_item.brand else 'Не указано' ,
                'text_data' : f"Бренд: {self.selected_model_line_item.brand.name}" if self.selected_model_line_item and self.selected_model_line_item.brand else None
            }
            logger.debug(
                f"brand added: {self.selected_model_line_item.brand.name if self.selected_model_line_item and self.selected_model_line_item.brand else None}")
        except Exception as e :
            logger.error(f"Error adding brand: {e}")
            traceback.print_exc()

        try :
            data['actuator_variety'] = {
                'category' : 'basic_properties' ,
                'title' : 'Вид привода' ,
                'data' : self.selected_model_line_item.pneumatic_actuator_variety.id if self.selected_model_line_item and self.selected_model_line_item.pneumatic_actuator_variety else None ,
                'display_data' : self.selected_model_line_item.pneumatic_actuator_variety.name if self.selected_model_line_item and self.selected_model_line_item.pneumatic_actuator_variety else 'Не указано' ,
                'text_data' : f"Вид привода: {self.selected_model_line_item.pneumatic_actuator_variety.name}" if self.selected_model_line_item and self.selected_model_line_item.pneumatic_actuator_variety else None
            }
            logger.debug(
                f"actuator_variety added: {self.selected_model_line_item.pneumatic_actuator_variety.name if self.selected_model_line_item and self.selected_model_line_item.pneumatic_actuator_variety else None}")
        except Exception as e :
            logger.error(f"Error adding actuator_variety: {e}")
            traceback.print_exc()

        try :
            data['output_type'] = {
                'category' : 'basic_properties' ,
                'title' : 'Тип выхода' ,
                'data' : self.selected_model_line_item.default_output_type.id if self.selected_model_line_item and self.selected_model_line_item.default_output_type else None ,
                'display_data' : self.selected_model_line_item.default_output_type.name if self.selected_model_line_item and self.selected_model_line_item.default_output_type else 'Не указано' ,
                'text_data' : f"Тип выхода: {self.selected_model_line_item.default_output_type.name}" if self.selected_model_line_item and self.selected_model_line_item.default_output_type else None
            }
            logger.debug(
                f"output_type added: {self.selected_model_line_item.default_output_type.name if self.selected_model_line_item and self.selected_model_line_item.default_output_type else None}")
        except Exception as e :
            logger.error(f"Error adding output_type: {e}")
            traceback.print_exc()

        try :
            data['construction_variety'] = {
                'category' : 'basic_properties' ,
                'title' : 'Конструкция' ,
                'data' : self.selected_model_line_item.pneumatic_actuator_construction_variety.id if self.selected_model_line_item and self.selected_model_line_item.pneumatic_actuator_construction_variety else None ,
                'display_data' : self.selected_model_line_item.pneumatic_actuator_construction_variety.name if self.selected_model_line_item and self.selected_model_line_item.pneumatic_actuator_construction_variety else 'Не указано' ,
                'text_data' : f"Конструкция: {self.selected_model_line_item.pneumatic_actuator_construction_variety.name}" if self.selected_model_line_item and self.selected_model_line_item.pneumatic_actuator_construction_variety else None
            }
            logger.debug(
                f"construction_variety added: {self.selected_model_line_item.pneumatic_actuator_construction_variety.name if self.selected_model_line_item and self.selected_model_line_item.pneumatic_actuator_construction_variety else None}")
        except Exception as e :
            logger.error(f"Error adding construction_variety: {e}")
            traceback.print_exc()

        # ==================== ВЫБРАННЫЕ ОПЦИИ ====================
        try :
            data['safety_position'] = {
                'category' : 'selected_options' ,
                'title' : 'Положение безопасности' ,
                'data' : self.selected_safety_position.id if self.selected_safety_position else None ,
                'display_data' : self.selected_safety_position.safety_position.name if self.selected_safety_position else 'Не указано' ,
                'text_data' : f"Положение безопасности: {self.selected_safety_position.safety_position.name}" if self.selected_safety_position else None
            }
            logger.debug(
                f"safety_position added: {self.selected_safety_position.safety_position.name if self.selected_safety_position else None}")
        except Exception as e :
            logger.error(f"Error adding safety_position: {e}")
            traceback.print_exc()

        try :
            data['springs_qty'] = {
                'category' : 'selected_options' ,
                'title' : 'Количество пружин' ,
                'data' : self.selected_springs_qty.id if self.selected_springs_qty else None ,
                'display_data' : self.selected_springs_qty.springs_qty.name if self.selected_springs_qty else 'Не указано' ,
                'text_data' : f"Количество пружин: {self.selected_springs_qty.springs_qty.name}" if self.selected_springs_qty else None
            }
            logger.debug(
                f"springs_qty added: {self.selected_springs_qty.springs_qty.name if self.selected_springs_qty else None}")
        except Exception as e :
            logger.error(f"Error adding springs_qty: {e}")
            traceback.print_exc()

        try :
            data['temperature'] = {
                'category' : 'selected_options' ,
                'title' : 'Температурное исполнение' ,
                'data' : self.selected_temperature.id if self.selected_temperature else None ,
                'display_data' : str(self.selected_temperature) if self.selected_temperature else 'Не указано' ,
                'text_data' : f"Температурное исполнение: {self.selected_temperature}" if self.selected_temperature else None
            }
            logger.debug(f"temperature added: {self.selected_temperature if self.selected_temperature else None}")
        except Exception as e :
            logger.error(f"Error adding temperature: {e}")
            traceback.print_exc()

        try :
            data['ip'] = {
                'category' : 'selected_options' ,
                'title' : 'IP защита' ,
                'data' : self.selected_ip.id if self.selected_ip else None ,
                'display_data' : str(self.selected_ip) if self.selected_ip else 'Не указано' ,
                'text_data' : f"IP защита: {self.selected_ip}" if self.selected_ip else None
            }
            logger.debug(f"ip added: {self.selected_ip if self.selected_ip else None}")
        except Exception as e :
            logger.error(f"Error adding ip: {e}")
            traceback.print_exc()

        try :
            data['exd'] = {
                'category' : 'selected_options' ,
                'title' : 'Exd взрывозащита' ,
                'data' : self.selected_exd.id if self.selected_exd else None ,
                'display_data' : str(self.selected_exd) if self.selected_exd else 'Не указано' ,
                'text_data' : f"Exd взрывозащита: {self.selected_exd}" if self.selected_exd else None
            }
            logger.debug(f"exd added: {self.selected_exd if self.selected_exd else None}")
        except Exception as e :
            logger.error(f"Error adding exd: {e}")
            traceback.print_exc()

        try :
            data['body_coating'] = {
                'category' : 'selected_options' ,
                'title' : 'Покрытие корпуса' ,
                'data' : self.selected_body_coating.id if self.selected_body_coating else None ,
                'display_data' : str(self.selected_body_coating) if self.selected_body_coating else 'Не указано' ,
                'text_data' : f"Покрытие корпуса: {self.selected_body_coating}" if self.selected_body_coating else None
            }
            logger.debug(f"body_coating added: {self.selected_body_coating if self.selected_body_coating else None}")
        except Exception as e :
            logger.error(f"Error adding body_coating: {e}")
            traceback.print_exc()

        try :
            data['hand_wheel'] = {
                'category' : 'selected_options' ,
                'title' : 'Ручной дублер' ,
                'data' : self.selected_hand_wheel.id if self.selected_hand_wheel else None ,
                'display_data' : str(self.selected_hand_wheel) if self.selected_hand_wheel else 'Не указано' ,
                'text_data' : f"Ручной дублер: {self.selected_hand_wheel}" if self.selected_hand_wheel else None
            }
            logger.debug(f"hand_wheel added: {self.selected_hand_wheel if self.selected_hand_wheel else None}")
        except Exception as e :
            logger.error(f"Error adding hand_wheel: {e}")
            traceback.print_exc()

        # ==================== ХАРАКТЕРИСТИКИ КОРПУСА (BODY) ====================
        try :
            if self.selected_model_line_item and self.selected_model_line_item.body :
                body_data = self.selected_model_line_item.body.get_description_data()
                for key , value in body_data.items() :
                    data[f'body_{key}'] = value
                logger.debug(f"body_data added, keys: {list(body_data.keys())}")
            else :
                logger.debug("No body data available")
        except Exception as e :
            logger.error(f"Error adding body_data: {e}")
            traceback.print_exc()

        # ==================== ТАБЛИЦА МОМЕНТОВ/УСИЛИЙ ====================
        try :
            spring_qty = self.selected_springs_qty.springs_qty if self.selected_springs_qty else None
            ncno_code = self.selected_safety_position.safety_position.code if self.selected_safety_position else SAFETY_POSITION_NC_DEFAULT_CODE
            construction_variety_code = self.selected_model_line_item.pneumatic_actuator_construction_variety.code if self.selected_model_line_item else ACTUATOR_VARIETY_RP_DEFAULT_CODE
            da_sr_code = self.selected_model_line_item.pneumatic_actuator_variety.code if self.selected_model_line_item else None

            logger.debug(
                f"torque table params: spring_qty={spring_qty}, ncno_code={ncno_code}, construction_variety_code={construction_variety_code}, da_sr_code={da_sr_code}")

            from pneumatic_actuators.models import BodyThrustTorqueTable
            torque_data = BodyThrustTorqueTable.get_torque_thrust_values(
                current_body=self.selected_model_line_item.body if self.selected_model_line_item else None ,
                spring_qty_list=[spring_qty] if spring_qty else None ,
                ncno_code=ncno_code ,
                construction_variety_code=construction_variety_code ,
                da_sr_code=da_sr_code
            )

            data['torque_thrust_table'] = {
                'category' : 'torque' ,
                'title' : 'Таблица моментов/усилий' ,
                'data' : torque_data ,
                'display_data' : 'Данные доступны' if torque_data else 'Не указано' ,
                'text_data' : None
            }
            logger.debug(f"torque_thrust_table added, data available: {bool(torque_data)}")
        except Exception as e :
            logger.error(f"Error getting torque/thrust table data: {e}")
            traceback.print_exc()
            data['torque_thrust_table'] = {
                'category' : 'torque' ,
                'title' : 'Таблица моментов/усилий' ,
                'data' : None ,
                'display_data' : 'Ошибка загрузки' ,
                'text_data' : None
            }

        logger.debug(f"get_description_data completed, total keys: {len(data)}")
        return data

    def _generate_short_description(self) -> str:
        """Сгенерировать краткое описание привода из структурированных данных
        записывается в поле description
        Основное предполагаемое использование - подставновка в КП в название номенклатуры.
        """
        data = self.get_description_data()
        print(data)
        desc_parts = []

        # Модель
        if data['model']['name']:
            short_description=f"{data['model']['name']}-"
        else:
            return "Модель: не выбрана" # Смысла продолжать нет. Удалить строку. Пока оставим для отладки
        # Базовые свойства
        short_description+=f"Тип: {data['basic_properties']['default_output_type']} пневмопривод" #Четвертьоборотный
        if data['basic_properties']['pneumatic_actuator_variety']=='SR':
            short_description += f" с возвратной пружиной, кол-во пружин {data['selected_options']['springs_qty']['description']};"  # SR
        else:
            short_description += f" двойного действия;"  # DA
        # short_description += f"{data['basic_properties']['pneumatic_actuator_variety']};" # SR
        # short_description += f"Ручной дублер {data['basic_properties']['default_hand_wheel']};"  # Ручной дублер
        # Выбранные опции
        short_description += f" Положение безопасности: {data['selected_options']['safety_position']['description']};"  # NC /NO
        short_description += f" Темп.исп. {data['selected_options']['temperature']['name']};"  # LT/VLT
        short_description += f" {data['selected_options']['ip']['name']};"  # ip
        short_description += f" {data['selected_options']['exd']['name']};"  # exd
        short_description += f" Покрытие корпуса: {data['selected_options']['body_coating']['name']};"  # exd
        short_description += f" Ручной дублер на корпусе:{data['selected_options']['hand_wheel']['name']};"
        # Технические характеристики корпуса
        short_description += f" Мин/Макс давл.{data['body_specs']['technical_specs']['min_pressure']}/{data['body_specs']['technical_specs']['max_pressure']};"  # min_pressure
        short_description += f" Расход откр/закр,л:{data['body_specs']['technical_specs']['air_usage_open']}/{data['body_specs']['technical_specs']['air_usage_close']};"  # Расход откр/закр

        # Информация о штоке
        print(f"Информация о штоке {data['body_specs']['mounting_specs']}")
        short_description += f" Шток:{data['body_specs']['mounting_specs']['stem']['shape']}/{data['body_specs']['mounting_specs']['stem']['size']};"  # Шток
        short_description += f" Площадка:{data['body_specs']['mounting_specs']['mounting_plates']};"  # Монтажные площадки
        short_description += f" Вес:{data['calculated_parameters']['weight']} кг;"  # Вес
        # Таблица моментов/усилий
        if 'torque_thrust_table' in data:
            desc_parts = []
            table_data = data['torque_thrust_table']

            if isinstance(table_data, dict):
                table_config = table_data.get('table_config', {})
                data_by_spring = table_data.get('data', {}).get('by_spring', {})

                if data_by_spring:
                    visible_fields = table_config.get('visible_fields', [])
                    pressure_order = table_config.get('pressure_order', [])
                    spring_order = table_config.get('spring_order', [])
                    torque_format = table_config.get('format', {}).get('torque', {})

                    # Создаем заголовки
                    headers = ["Пружины"]
                    for pressure_code in pressure_order:
                        for field in visible_fields:
                            headers.append(f"{pressure_code}\n{field.upper()}")

                    # Создаем строки таблицы
                    table_rows = []
                    for spring_code in spring_order:
                        if spring_code in data_by_spring:
                            row = [spring_code]
                            spring_data = data_by_spring[spring_code]
                            pressures_data = spring_data.get('pressures', {})

                            for pressure_code in pressure_order:
                                if pressure_code in pressures_data:
                                    pressure_values = pressures_data[pressure_code]
                                    for field in visible_fields:
                                        value = pressure_values.get(field)
                                        if value is not None:
                                            precision = torque_format.get('precision', 1)
                                            row.append(f"{value:.{precision}f}")
                                        else:
                                            row.append("—")
                                else:
                                    for _ in visible_fields:
                                        row.append("—")

                            table_rows.append(row)

                    # Формируем таблицу
                    desc_parts.append("\nТаблица моментов:")
                    desc_parts.append(tabulate(
                        table_rows,
                        headers=headers,
                        tablefmt="grid",
                        stralign="center",
                        numalign="center"
                    ))

                    desc_parts.append(f"\nПримечание: значения в {torque_format.get('unit', 'Нм')}")
        # short_description+="\n"
        short_description+="\n".join(desc_parts)
        return short_description

    def _generate_short_description(self) -> str :
        """Сгенерировать краткое описание привода из структурированных данных
        записывается в поле description
        Основное предполагаемое использование - подстановка в КП в название номенклатуры.
        """
        data = self.get_description_data()
        print(data)

        # Модель
        model_name = data.get('model_name' , {}).get('data')
        if not model_name :
            return "Модель: не выбрана"

        short_description = f"{model_name}-"

        # Базовые свойства
        output_type = data.get('output_type' , {}).get('display_data' , 'пневмопривод')
        short_description += f"Тип: {output_type}"

        # Вид привода (DA/SR) и пружины
        actuator_variety = data.get('actuator_variety' , {}).get('data')
        if actuator_variety == 'SR' :
            springs_qty = data.get('springs_qty' , {}).get('display_data' , '')
            short_description += f" с возвратной пружиной, кол-во пружин {springs_qty};"
        else :
            short_description += f" двойного действия;"

        # Выбранные опции
        safety_position = data.get('safety_position' , {}).get('display_data' , '')
        short_description += f" Положение безопасности: {safety_position};"

        temperature = data.get('temperature' , {}).get('display_data' , '')
        short_description += f" Темп.исп. {temperature};"

        ip = data.get('ip' , {}).get('display_data' , '')
        short_description += f" {ip};"

        exd = data.get('exd' , {}).get('display_data' , '')
        short_description += f" {exd};"

        body_coating = data.get('body_coating' , {}).get('display_data' , '')
        short_description += f" Покрытие корпуса: {body_coating};"

        hand_wheel = data.get('hand_wheel' , {}).get('display_data' , '')
        short_description += f" Ручной дублер на корпусе: {hand_wheel};"

        # Технические характеристики корпуса (с префиксом body_)
        min_pressure = data.get('body_min_pressure' , {}).get('display_data' , '')
        max_pressure = data.get('body_max_pressure' , {}).get('display_data' , '')
        short_description += f" Мин/Макс давл.{min_pressure}/{max_pressure};"

        air_usage_open = data.get('body_air_usage_open' , {}).get('display_data' , '')
        air_usage_close = data.get('body_air_usage_close' , {}).get('display_data' , '')
        short_description += f" Расход откр/закр,л:{air_usage_open}/{air_usage_close};"

        # Информация о штоке
        stem_shape = data.get('body_stem_shape' , {}).get('display_data' , '')
        stem_size = data.get('body_stem_size' , {}).get('display_data' , '')
        short_description += f" Шток:{stem_shape}/{stem_size};"

        mounting_plates = data.get('body_mounting_plates' , {}).get('display_data' , '')
        short_description += f" Площадка:{mounting_plates};"

        # Вес
        weight = data.get('weight' , {}).get('display_data' , '')
        short_description += f" Вес:{weight};"

        # Таблица моментов/усилий
        torque_table = data.get('torque_thrust_table' , {})
        if torque_table and torque_table.get('data') :
            table_data = torque_table.get('data')
            desc_parts = []

            if isinstance(table_data , dict) :
                table_config = table_data.get('table_config' , {})
                data_by_spring = table_data.get('data' , {}).get('by_spring' , {})

                if data_by_spring :
                    visible_fields = table_config.get('visible_fields' , [])
                    pressure_order = table_config.get('pressure_order' , [])
                    spring_order = table_config.get('spring_order' , [])
                    torque_format = table_config.get('format' , {}).get('torque' , {})

                    # Создаем заголовки
                    headers = ["Пружины"]
                    for pressure_code in pressure_order :
                        for field in visible_fields :
                            headers.append(f"{pressure_code}\n{field.upper()}")

                    # Создаем строки таблицы
                    table_rows = []
                    for spring_code in spring_order :
                        if spring_code in data_by_spring :
                            row = [spring_code]
                            spring_data = data_by_spring[spring_code]
                            pressures_data = spring_data.get('pressures' , {})

                            for pressure_code in pressure_order :
                                if pressure_code in pressures_data :
                                    pressure_values = pressures_data[pressure_code]
                                    for field in visible_fields :
                                        value = pressure_values.get(field)
                                        if value is not None :
                                            precision = torque_format.get('precision' , 1)
                                            row.append(f"{value:.{precision}f}")
                                        else :
                                            row.append("—")
                                else :
                                    for _ in visible_fields :
                                        row.append("—")

                            table_rows.append(row)

                    # Формируем таблицу
                    if table_rows :
                        desc_parts.append("\nТаблица моментов:")
                        from tabulate import tabulate
                        desc_parts.append(tabulate(
                            table_rows ,
                            headers=headers ,
                            tablefmt="grid" ,
                            stralign="center" ,
                            numalign="center"
                        ))
                        desc_parts.append(f"\nПримечание: значения в {torque_format.get('unit' , 'Нм')}")

            if desc_parts :
                short_description += "\n" + "\n".join(desc_parts)

        return short_description

    def _generate_tech_description(self) -> str :
        """Сгенерировать описание привода из плоской структуры данных"""
        import re
        data = self.get_description_data()
        desc_parts = []

        # ==================== МОДЕЛЬ ====================
        model_name = data.get('model_name' , {}).get('display_data')
        if model_name and model_name != 'Не указано' :
            desc_parts.append(f"Модель: {model_name}")
        else :
            desc_parts.append("Модель: не выбрана")

        # ==================== БАЗОВЫЕ СВОЙСТВА ====================
        brand = data.get('brand' , {}).get('display_data')
        if brand and brand != 'Не указано' :
            desc_parts.append(f"Бренд: {brand}")

        actuator_variety = data.get('actuator_variety' , {}).get('display_data')
        if actuator_variety and actuator_variety != 'Не указано' :
            desc_parts.append(f"Тип привода: {actuator_variety}")

        output_type = data.get('output_type' , {}).get('display_data')
        if output_type and output_type != 'Не указано' :
            desc_parts.append(f"Тип работы: {output_type}")

        construction_variety = data.get('construction_variety' , {}).get('display_data')
        if construction_variety and construction_variety != 'Не указано' :
            desc_parts.append(f"Тип конструкции: {construction_variety}")

        # ==================== ВЫБРАННЫЕ ОПЦИИ ====================
        selected_options = []

        safety = data.get('safety_position' , {}).get('display_data')
        if safety and safety != 'Не указано' :
            selected_options.append(f"Положение безопасности: {safety}")

        springs = data.get('springs_qty' , {}).get('display_data')
        if springs and springs != 'Не указано' :
            selected_options.append(f"Количество пружин: {springs}")

        temperature = data.get('temperature' , {}).get('display_data')
        if temperature and temperature != 'Не указано' :
            selected_options.append(f"Температурный диапазон: {temperature}")

        ip = data.get('ip' , {}).get('display_data')
        if ip and ip != 'Не указано' :
            selected_options.append(f"Степень защиты IP: {ip}")

        exd = data.get('exd' , {}).get('display_data')
        if exd and exd != 'Не указано' :
            selected_options.append(f"Взрывозащита: {exd}")

        coating = data.get('body_coating' , {}).get('display_data')
        if coating and coating != 'Не указано' :
            selected_options.append(f"Покрытие корпуса: {coating}")

        hand_wheel = data.get('hand_wheel' , {}).get('display_data')
        if hand_wheel and hand_wheel != 'Не указано' :
            selected_options.append(f"Ручной дублер: {hand_wheel}")

        if selected_options :
            desc_parts.append("\nВыбранные опции:")
            desc_parts.extend(f"  {opt}" for opt in selected_options)

        # ==================== ХАРАКТЕРИСТИКИ КОРПУСА ====================
        body_specs = []

        piston = data.get('body_piston_diameter' , {}).get('display_data')
        if piston and piston != 'Не указано' :
            body_specs.append(f"Диаметр поршня: {piston}")

        turn_angle = data.get('body_turn_angle' , {}).get('display_data')
        if turn_angle and turn_angle != 'Не указано' :
            body_specs.append(f"Угол поворота: {turn_angle}")

        turn_limit = data.get('body_turn_tuning_limit' , {}).get('display_data')
        if turn_limit and turn_limit != 'Не указано' :
            body_specs.append(f"Ограничитель поворота: {turn_limit}")

        weight_spring = data.get('body_weight_spring' , {}).get('display_data')
        if weight_spring and weight_spring != 'Не указано' :
            body_specs.append(f"Вес пружины: {weight_spring}")

        min_pressure = data.get('body_min_pressure' , {}).get('display_data')
        max_pressure = data.get('body_max_pressure' , {}).get('display_data')
        if min_pressure or max_pressure :
            body_specs.append(f"Давление: {min_pressure} / {max_pressure}")

        air_open = data.get('body_air_usage_open' , {}).get('display_data')
        air_close = data.get('body_air_usage_close' , {}).get('display_data')
        if air_open or air_close :
            body_specs.append(f"Расход воздуха: открытие {air_open}, закрытие {air_close}")

        if body_specs :
            desc_parts.append("\nХарактеристики корпуса:")
            desc_parts.extend(f"  {spec}" for spec in body_specs)

        # ==================== ИНФОРМАЦИЯ О ШТОКЕ ====================
        stem_parts = []
        stem_shape = data.get('body_stem_shape' , {}).get('display_data')
        if stem_shape and stem_shape != 'Не указано' :
            stem_parts.append(f"форма: {stem_shape}")

        stem_size = data.get('body_stem_size' , {}).get('display_data')
        if stem_size and stem_size != 'Не указано' :
            stem_parts.append(f"размер: {stem_size}")

        stem_height = data.get('body_max_stem_height' , {}).get('display_data')
        if stem_height and stem_height != 'Не указано' :
            stem_parts.append(f"макс. высота: {stem_height}")

        stem_diameter = data.get('body_max_stem_diameter' , {}).get('display_data')
        if stem_diameter and stem_diameter != 'Не указано' :
            stem_parts.append(f"макс. диаметр: {stem_diameter}")

        if stem_parts :
            desc_parts.append("\nПрисоединение к арматуре:")
            desc_parts.append(f"  Шток: {', '.join(stem_parts)}")

        # Монтажные площадки
        mounting_plates = data.get('body_mounting_plates' , {}).get('display_data')
        if mounting_plates and mounting_plates != 'Не указано' :
            desc_parts.append(f"  Монтажные площадки: {mounting_plates}")

        # ==================== ПОДКЛЮЧЕНИЯ ====================
        connections = []
        thread_in = data.get('body_thread_in' , {}).get('display_data')
        if thread_in and thread_in != 'Не указано' :
            connections.append(f"Пневмовход: {thread_in}")

        thread_out = data.get('body_thread_out' , {}).get('display_data')
        if thread_out and thread_out != 'Не указано' :
            connections.append(f"Пневмовыход: {thread_out}")

        pneum_conn = data.get('body_pneumatic_connections' , {}).get('display_data')
        if pneum_conn and pneum_conn != 'Не указано' :
            connections.append(f"Типы пневмоподключений: {pneum_conn}")

        if connections :
            desc_parts.append("\nПодключения корпуса:")
            desc_parts.extend(f"  {conn}" for conn in connections)

        # ==================== ВЕС ====================
        weight = data.get('weight' , {}).get('display_data')
        if weight and weight != 'Не указано' :
            desc_parts.append(f"\nВес: {weight}")

        # ==================== ТАБЛИЦА МОМЕНТОВ/УСИЛИЙ ====================
        torque_table = data.get('torque_thrust_table' , {})
        table_data = torque_table.get('data')

        if table_data and isinstance(table_data , dict) :
            table_config = table_data.get('table_config' , {})
            data_by_spring = table_data.get('data' , {}).get('by_spring' , {})

            if data_by_spring :
                visible_fields = table_config.get('visible_fields' , [])
                pressure_order = table_config.get('pressure_order' , [])
                spring_order = table_config.get('spring_order' , [])
                torque_format = table_config.get('format' , {}).get('torque' , {})

                desc_parts.append("\nТаблица моментов:")

                # Начинаем HTML таблицу
                desc_parts.append('<table border="1" style="border-collapse: collapse; margin: 10px 0; width: 100%;">')
                desc_parts.append('<thead>')
                desc_parts.append('<tr><th rowspan="2">Пружины</th>')

                for pressure_code in pressure_order :
                    col_span = len(visible_fields)
                    desc_parts.append(f'<th colspan="{col_span}">{pressure_code}</th>')
                desc_parts.append('</tr>')

                desc_parts.append('<tr>')
                for _ in pressure_order :
                    for field in visible_fields :
                        desc_parts.append(f'<th>{field.upper()}</th>')
                desc_parts.append('</tr>')
                desc_parts.append('</thead>')

                desc_parts.append('<tbody>')
                for spring_code in spring_order :
                    if spring_code in data_by_spring :
                        desc_parts.append(f'<tr><td>{spring_code}</td>')
                        spring_data = data_by_spring[spring_code]
                        pressures_data = spring_data.get('pressures' , {})

                        for pressure_code in pressure_order :
                            if pressure_code in pressures_data :
                                pressure_values = pressures_data[pressure_code]
                                for field in visible_fields :
                                    value = pressure_values.get(field)
                                    if value is not None :
                                        precision = torque_format.get('precision' , 1)
                                        desc_parts.append(f'<td>{value:.{precision}f}</td>')
                                    else :
                                        desc_parts.append('<td>—</td>')
                            else :
                                for _ in visible_fields :
                                    desc_parts.append('<td>—</td>')
                        desc_parts.append('</tr>')
                desc_parts.append('</tbody>')
                desc_parts.append('</table>')

                desc_parts.append(f"Примечание: значения в {torque_format.get('unit' , 'Нм')}")

        # Собираем и чистим текст
        full_text = "\n".join(desc_parts)
        cleaned_text = re.sub(r'\n{3,}' , '\n\n' , full_text)

        return cleaned_text

    def _get_structured_description_data(self) -> Dict[str , Any] :
        """
        Структурированные данные описания для API
        """
        data = self.get_description_data()

        # Преобразуем плоскую структуру в группированную для API
        structured_data = {
            'basic_info' : {
                'model' : data.get('model_name' , {}).get('display_data') ,
                'brand' : data.get('brand' , {}).get('display_data') ,
                'actuator_variety' : data.get('actuator_variety' , {}).get('display_data') ,
                'output_type' : data.get('output_type' , {}).get('display_data') ,
                'construction_variety' : data.get('construction_variety' , {}).get('display_data') ,
            } ,
            'selected_options' : {
                'safety_position' : data.get('safety_position' , {}).get('display_data') ,
                'springs_qty' : data.get('springs_qty' , {}).get('display_data') ,
                'temperature' : data.get('temperature' , {}).get('display_data') ,
                'ip' : data.get('ip' , {}).get('display_data') ,
                'exd' : data.get('exd' , {}).get('display_data') ,
                'body_coating' : data.get('body_coating' , {}).get('display_data') ,
                'hand_wheel' : data.get('hand_wheel' , {}).get('display_data') ,
            } ,
            'technical_specs' : {
                'piston_diameter' : data.get('body_piston_diameter' , {}).get('display_data') ,
                'turn_angle' : data.get('body_turn_angle' , {}).get('display_data') ,
                'turn_tuning_limit' : data.get('body_turn_tuning_limit' , {}).get('display_data') ,
                'weight_spring' : data.get('body_weight_spring' , {}).get('display_data') ,
                'min_pressure' : data.get('body_min_pressure' , {}).get('display_data') ,
                'max_pressure' : data.get('body_max_pressure' , {}).get('display_data') ,
                'air_usage_open' : data.get('body_air_usage_open' , {}).get('display_data') ,
                'air_usage_close' : data.get('body_air_usage_close' , {}).get('display_data') ,
                'stem_shape' : data.get('body_stem_shape' , {}).get('display_data') ,
                'stem_size' : data.get('body_stem_size' , {}).get('display_data') ,
                'max_stem_height' : data.get('body_max_stem_height' , {}).get('display_data') ,
                'max_stem_diameter' : data.get('body_max_stem_diameter' , {}).get('display_data') ,
                'mounting_plates' : data.get('body_mounting_plates' , {}).get('display_data') ,
                'thread_in' : data.get('body_thread_in' , {}).get('display_data') ,
                'thread_out' : data.get('body_thread_out' , {}).get('display_data') ,
                'pneumatic_connections' : data.get('body_pneumatic_connections' , {}).get('display_data') ,
            } ,
            'calculated_parameters' : {
                'weight' : data.get('weight' , {}).get('display_data') ,
                'time_to_close' : data.get('time_to_close' , {}).get('display_data') ,
            } ,
            'torque_thrust_table' : data.get('torque_thrust_table' , {}).get('data') ,
            'formatted' : {
                'short' : self._generate_short_description() ,
                'technical' : self._generate_tech_description() ,
                'html' : self._generate_html_description() ,
            }
        }

        return structured_data
    @property
    def generated_model_item_code(self) -> str:
        """Сгенерировать артикул по шаблону из model_line"""
        if not self.selected_model_line_item or not self.selected_model_line_item.model_line:
            return self.code or ""

        # Проверьте, что self.selected_model_line_item здесь еще объект
        print(f"=== DEBUG generated_model_item_code ===")
        print(f"self.selected_model_line_item: {self.selected_model_line_item}")
        print(f"type: {type(self.selected_model_line_item)}")

        template = self.selected_model_line_item.model_line.model_item_code_template
        if not template:
            print(f"Template for {self.selected_model_line_item.model_line} not found. Generating from fallback")
            return self._generate_fallback_code()

        """Простой рендеринг шаблона - заменяем переменные значениями"""
        result = template
        print(f"template: {result}")
        # Простая замена переменных
        result = result.replace('{model_code}', self._get_value_old('selected_model_line_item__name'))
        # if
        result = result.replace('{springs_qty}', self._get_value_old('selected_springs_qty__encoding'))
        result = result.replace('{temperature}', self._get_value_old('selected_temperature__encoding'))
        result = result.replace('{safety_position}', self._get_value_old('selected_safety_position__encoding'))
        result = result.replace('{hand_wheel}', self._get_value_old('selected_hand_wheel__encoding'))
        result = result.replace('{coating}', self._get_value_old('selected_body_coating__encoding'))
        result = result.replace('{ip}', self._get_value_old('selected_ip__encoding'))
        result = result.replace('{exd}', self._get_value_old('selected_exd__encoding'))

        print(f"До очистки: {result}")
        # Очистка лишних точек (две точки подряд -> одна точка)
        result = re.sub(r'\.{2,}', '.', result)
        print(f"две точки подряд -> одна точка: {result}")
        # Удаляем точку в начале и конце
        result = re.sub(r'\.\s+', ' ', result)  # Заменяет точку и любые пробельные символы после нее
        print(f"удалили точки в начале и конце: {result}")
        result = re.sub(r'\s*\(DA\)', '', result)  # Удалит (DA) с любым количеством пробелов перед ним
        print(f"удалили (DA): {result}")
        # if not self.is_da_model():
        #     result = result + str('('+self._get_value('selected_springs_qty__encoding')+')')

        return result

    def _get_value_old(self, field_path: str) -> str:
        """Простое получение значения поля"""
        try:
            current_obj = self
            for field_name in field_path.split('__'):
                current_obj = getattr(current_obj, field_name, None)
                if current_obj is None:
                    return ""
            return str(current_obj) if current_obj else ""
        except Exception:
            return ""

    def _generate_fallback_code(self) -> str:
        """Простая резервная генерация"""
        parts = [
            self._get_value_old('selected_model__code'),
            self._get_value_old('selected_springs_qty__encoding'),
            self._get_value_old('selected_temperature__encoding'),
            self._get_value_old('selected_safety_position__encoding'),
            self._get_value_old('selected_hand_wheel__encoding'),
            self._get_value_old('selected_body_coating__encoding'),
            self._get_value_old('selected_ip__encoding'),
            self._get_value_old('selected_exd__encoding'),
        ]
        # Фильтруем пустые значения и соединяем
        return '.'.join(filter(None, parts))

    def _adjust_for_duplicate(self):
        """Настройка для дублирующей конфигурации"""
        if not self.name:
            return

        import re
        from datetime import datetime

        # Определяем следующий номер для копии
        base_name_for_search = re.sub(r'\s*\(copy\s*#\d+\)$', '', self.name, flags=re.IGNORECASE).strip()

        # Ищем все существующие копии с таким же базовым именем
        from django.db.models import Q
        existing_copies = self.__class__.objects.filter(
            Q(name=self.name) |
            Q(name__iregex=r'^' + re.escape(base_name_for_search) + r'\s*\(copy\s*#\d+\)$')
        )

        # Определяем максимальный номер копии
        max_number = 0
        for copy in existing_copies:
            match = re.search(r'\(copy\s*#(\d+)\)$', copy.name, re.IGNORECASE)
            if match:
                num = int(match.group(1))
                max_number = max(max_number, num)
            elif copy.name == self.name:
                # Если есть точное совпадение, это тоже считается копией
                max_number = max(max_number, 1)

        new_number = max_number + 1

        # Форматируем номер с ведущими нулями (01, 02, ...)
        formatted_number = f"{new_number:02d}"

        # Обновляем имя: добавляем (copy#XX) к существующему имени
        self.name = f"{self.name} (copy#{formatted_number})"

        # Обновляем код: добавляем (copy#XX) к существующему коду
        if self.code:
            # Убираем возможные предыдущие суффиксы copy
            clean_code = re.sub(r'\s*\(copy\s*#\d+\)$', '', self.code, flags=re.IGNORECASE)
            self.code = f"{clean_code} (copy#{formatted_number})"


    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        # Получаем оригинальный объект
        original = None
        if self.pk:
            try:
                original = self.__class__._default_manager.get(pk=self.pk)
            except self.__class__.DoesNotExist:
                pass

        # Проверяем, изменилась ли модель привода
        model_changed = (original and original.selected_model_line_item and
                         self.selected_model_line_item and
                         original.selected_model_line_item != self.selected_model_line_item)

        # ЕДИНАЯ ВАЛИДАЦИЯ И КОРРЕКТИРОВКА ОПЦИЙ
        self._ensure_valid_options()
        # self.name = self.generated_model_item_code()
        # self.code = self.generated_model_item_code()
        # Остальная логика без изменений
        duplicate_message = self._check_for_duplicates()
        if duplicate_message:
            self.is_unique = False
            self._adjust_for_duplicate()
            logger.warning(f"Создается дубликат: {duplicate_message}")
        else:
            self.is_unique = True

        # Валидация полей
        try:
            self.clean()
        except ValidationError as e:
            logger.error(f"Validation error in save(): {e}")
            raise

        # Автозаполнение полей
        # self._auto_fill_fields()
        self.name = self.generated_model_item_code
        self.code = self.generated_model_item_code
        self.description = self._generate_short_description()

         # Сохраняем
        super().save(*args, **kwargs)

    def _ensure_valid_options(self):
        """
        Гарантирует, что все опции валидны для текущей модели
        (заменяет и _set_default_options и _adjust_options_for_new_model)
        """
        if not self.selected_model_line_item:
            return

        # Сначала устанавливаем дефолты для пустых полей
        for field_name, config in self._OPTION_CONFIG.items():
            if not getattr(self, field_name):
                self._set_default_option(field_name, config)

        # Затем проверяем валидность всех заполненных полей
        for field_name, config in self._OPTION_CONFIG.items():
            current_value = getattr(self, field_name)
            if current_value:
                self._validate_option(field_name, current_value, config)

    def _set_default_option(self, field_name, config):
        """Установить дефолтную опцию для пустого поля"""
        try:
            module_name, class_name = config['model_path'].rsplit('.', 1)
            module = __import__(module_name, fromlist=[class_name])
            option_model = getattr(module, class_name)

            parent_obj = self._get_parent_for_option(config)
            if not parent_obj:
                return

            default_option = option_model.get_default_or_any_allowed(parent_obj)
            if default_option:
                setattr(self, field_name, default_option)

        except Exception as e:
            logger.error(f"Error setting default for {field_name}: {e}")

    def _validate_option(self, field_name, current_value, config):
        """Проверить валидность опции"""
        try:
            module_name, class_name = config['model_path'].rsplit('.', 1)
            module = __import__(module_name, fromlist=[class_name])
            option_model = getattr(module, class_name)

            parent_obj = self._get_parent_for_option(config)
            if not parent_obj:
                return

            # Проверка существования опции для родителя
            filter_kwargs = {
                'id': current_value.id,
                f"{config['parent_field']}": parent_obj,
                'is_active': True
            }

            if not option_model.objects.filter(**filter_kwargs).exists():
                # Заменяем на дефолтную
                default_option = option_model.get_default_or_any_allowed(parent_obj)
                if default_option:
                    setattr(self, field_name, default_option)

        except Exception as e:
            logger.error(f"Error validating {field_name}: {e}")

    def _get_parent_for_option(self, config):
        """Получить родительский объект для опции"""
        if config['parent_field'] == 'model_line':
            return getattr(self.selected_model_line_item, 'model_line', None)
        else:
            return self.selected_model_line_item

    def _check_for_duplicates(self):
        """Проверка на дубликаты в базе данных"""
        if not self.pk:  # Только для новых записей
            # Собираем фильтры для всех полей опций
            filters = {}

            # Используем общую конфигурацию
            for field_name in self.get_option_fields():
                field_value = getattr(self, field_name)
                if field_value:  # Только если значение установлено
                    filters[field_name] = field_value
                else:
                    # Для NULL значений используем __isnull
                    filters[f'{field_name}__isnull'] = True

            # Если есть хотя бы одно поле для фильтрации
            if filters:
                # Ищем дубликаты
                from pneumatic_actuators.models  import PneumaticActuatorSelected
                duplicates = PneumaticActuatorSelected.objects.filter(**filters)

                # Исключаем самого себя если это обновление
                if self.pk:
                    duplicates = duplicates.exclude(pk=self.pk)

                if duplicates.exists():
                    duplicate = duplicates.first()
                    return f"Найдена похожая конфигурация: {duplicate} (ID: {duplicate.id})"

        return None

    def _auto_fill_fields(self):
        """Автозаполнение полей name, code, description"""
        if self.selected_model_line_item:
            if hasattr(self, 'generated_model_item_code'):
                if not self.name or len(self.name) == 0:
                    self.name = self.generated_model_item_code
                if not self.code or len(self.code) == 0:
                    self.code = self.generated_model_item_code
            if hasattr(self, '_generate_short_description') and not self.description:
                self.description = self._generate_short_description()

    def clean(self):
        """Мягкая валидация выбранных опций"""
        logger.info("=== MODEL CLEAN DEBUG: Starting validation")

        if not self.selected_model_line_item:
            return  # Если модель не выбрана, пропускаем валидацию опций

        # Используем общую конфигурацию для всех проверок
        for field_name, config in self._OPTION_CONFIG.items():
            field_value = getattr(self, field_name)
            if field_value:
                try:
                    # Импортируем модель опции
                    option_model = getattr(
                        __import__('pneumatic_actuators.models.pa_options', fromlist=[config['model_class']]),
                        config['model_class']
                    )

                    # Определяем параметры фильтрации
                    filter_kwargs = {
                        'id': field_value.id,
                        'is_active': True
                    }

                    # Для разных типов опций разные parent_field
                    if config['parent_field'] == 'model_line':
                        # Для temperature, ip, exd, body_coating, hand_wheel
                        if hasattr(self.selected_model_line_item, 'model_line'):
                            filter_kwargs['model_line'] = self.selected_model_line_item.model_line
                        else:
                            logger.warning(f"Cannot validate {field_name}: model_line not available")
                            continue
                    else:
                        # Для safety_position и springs_qty
                        filter_kwargs['model_line_item'] = self.selected_model_line_item

                    # Проверяем валидность
                    valid_option = option_model.objects.filter(**filter_kwargs).exists()
                    logger.info(f"=== MODEL CLEAN DEBUG: {field_name} valid={valid_option}")

                    if not valid_option:
                        logger.warning(
                            f'Выбранная {config["label"]} не доступна для модели {self.selected_model_line_item}. '
                            f'Будет сброшена при сохранении.'
                        )
                        # Мягкая валидация: только предупреждение
                        # setattr(self, field_name, None)  # Раскомментировать для сброса

                except Exception as e:
                    logger.error(f"Error validating {field_name}: {e}")

        logger.info("=== MODEL CLEAN DEBUG: Validation completed")

    # Свойства для доступа к доступным опциям
    @property
    def selected_model_display(self):
        return str(self.selected_model_line_item) if self.selected_model_line_item else "-"

    @property
    def safety_position_display(self):
        return str(self.selected_safety_position) if self.selected_safety_position else "-"

    @property
    def springs_qty_display(self):
        return str(self.selected_springs_qty) if self.selected_springs_qty else "-"

    @property
    def temperature_display(self):
        return str(self.selected_temperature) if self.selected_temperature else "-"

    @property
    def ip_display(self):
        return str(self.selected_ip) if self.selected_ip else "-"

    @property
    def exd_display(self):
        return str(self.selected_exd) if self.selected_exd else "-"

    @property
    def body_coating_display(self):
        return str(self.selected_body_coating) if self.selected_body_coating else "-"

    # @property
    def is_da_model(self):
        return (self.selected_model_line_item.pneumatic_actuator_variety and
                       self.selected_model_line_item.pneumatic_actuator_variety.code == 'DA')

    def get_available_options(self) -> Dict[str, List[Dict]]:
        """Получить все доступные опции для выбранной модели"""
        from pneumatic_actuators.models.pa_options import (
            PneumaticSafetyPositionOption, PneumaticSpringsQtyOption,
            PneumaticTemperatureOption, PneumaticIpOption,
            PneumaticExdOption, PneumaticBodyCoatingOption,PneumaticHandWheelOption
        )

        print(f"=== DEBUG get_available_options ===")
        print(f"Selected actuator ID: {self.id}")
        print(f"Selected model: {self.selected_model_line_item}")
        print(f"Selected model ID: {self.selected_model_line_item.id if self.selected_model_line_item else 'None'}")
        print(f"Selected model name: {self.selected_model_line_item.name if self.selected_model_line_item else 'None'}")

        if not self.selected_model_line_item:
            print("=== DEBUG: No selected model - returning empty options")
            return self._get_empty_options()

        try:
            # Опции через model_line_item
            safety_options = PneumaticSafetyPositionOption.objects.filter(
                model_line_item=self.selected_model_line_item,
                is_active=True
            ).select_related('safety_position')

            springs_options = PneumaticSpringsQtyOption.objects.filter(
                model_line_item=self.selected_model_line_item,
                is_active=True
            ).select_related('springs_qty')
            #
            print(f"Safety options SQL: {safety_options.query}")
            print(f"Springs options SQL: {springs_options.query}")
            print(f"Safety options count: {safety_options.count()}")
            print(f"Springs options count: {springs_options.count()}")

            # Выводим найденные опции
            for i , opt in enumerate(safety_options) :
                print(f"Safety option {i + 1}: {opt.id} - {opt.safety_position.name} - encoding: '{opt.encoding}'")

            for i , opt in enumerate(springs_options) :
                print(f"Springs option {i + 1}: {opt.id} - {opt.springs_qty.name} - encoding: '{opt.encoding}'")

            # Опции через model_line
            temperature_options = []
            ip_options = []
            exd_options = []
            body_coating_options = []
            hand_wheel_options = []

            if self.selected_model_line_item.model_line:
                # print(f"Model line: {self.selected_model.model_line}")

                temperature_options = PneumaticTemperatureOption.objects.filter(
                    model_line=self.selected_model_line_item.model_line,
                    is_active=True
                )
                # ДИАГНОСТИКА temperature_options
                print(f"🔧 MODEL temperature_options count: {temperature_options.count()}")
                for opt in temperature_options:
                    print(f"🔧   id={opt.id}, encoding={opt.encoding}")

                ip_options = PneumaticIpOption.objects.filter(
                    model_line=self.selected_model_line_item.model_line,
                    is_active=True
                )

                exd_options = PneumaticExdOption.objects.filter(
                    model_line=self.selected_model_line_item.model_line,
                    is_active=True
                )

                body_coating_options = PneumaticBodyCoatingOption.objects.filter(
                    model_line=self.selected_model_line_item.model_line,
                    is_active=True
                )
                hand_wheel_options = PneumaticHandWheelOption.objects.filter(
                    model_line=self.selected_model_line_item.model_line,
                    is_active=True
                )
                # print(f"Temperature options count: {temperature_options.count()}")
                # print(f"IP options count: {ip_options.count()}")
                # print(f"Exd options count: {exd_options.count()}")
                # print(f"Coating options count: {body_coating_options.count()}")

            result = {
                'safety_positions': [
                    {
                        'id': opt.id,
                        'encoding': opt.encoding,
                        'name': opt.safety_position.name,
                        'description': opt.description,
                        'is_default': opt.is_default
                    } for opt in safety_options
                ],
                'springs_qty': [
                    {
                        'id': opt.id,
                        'encoding': opt.encoding,
                        'name': opt.springs_qty.name,
                        'description': opt.description,
                        'is_default': opt.is_default
                    } for opt in springs_options
                ],
                'temperature_options': [
                    {
                        'id': opt.id,
                        'encoding': opt.encoding,
                        'name': opt.get_display_name(),
                        'description': opt.description,
                        'is_default': opt.is_default
                    } for opt in temperature_options
                ],
                'ip_options': [
                    {
                        'id': opt.id,
                        'encoding': opt.encoding,
                        'name': str(opt),
                        'description': opt.description,
                        'is_default': opt.is_default
                    } for opt in ip_options
                ],
                'exd_options': [
                    {
                        'id': opt.id,
                        'encoding': opt.encoding,
                        'name': str(opt),
                        'description': opt.description,
                        'is_default': opt.is_default
                    } for opt in exd_options
                ],
                'body_coating_options': [
                    {
                        'id': opt.id,
                        'encoding': opt.encoding,
                        'name': str(opt),
                        'description': opt.description,
                        'is_default': opt.is_default
                    } for opt in body_coating_options
                ],
                'hand_wheel_options': [
                    {
                        'id': opt.id,
                        'encoding': opt.encoding,
                        'name': str(opt),
                        'description': opt.description,
                        'is_default': opt.is_default
                    } for opt in hand_wheel_options
                ]
            }

            # print(f"=== DEBUG: Final result structure ===")
            for key, value in result.items():
                # print(f"=== DEBUG get_available_options: {key}: {len(value)} items")
                for item in value[:5]:  # Покажем первые 2 элемента каждого типа
                    print(f"  - {item}")

            return result

        except Exception as e:
            print(f"=== DEBUG: Error in get_available_options: {e}")
            import traceback
            traceback.print_exc()
            return self._get_empty_options()

    def _get_empty_options(self):
        """Пустые опции"""
        return {
            'safety_positions': [], 'springs_qty': [],
            'temperature_options': [], 'ip_options': [],
            'exd_options': [], 'body_coating_options': [], 'hand_wheel_options':[]
        }

    def get_weight(self) -> Optional[Decimal]:
        """Рассчитать вес привода"""
        from pneumatic_actuators.models import PneumaticWeightParameter
        if not self.selected_model_line_item or not self.selected_model_line_item.body:
            return None

        body = self.selected_model_line_item.body

        try:
            # Для приводов DA
            if (self.selected_model_line_item.pneumatic_actuator_variety and
                    self.selected_model_line_item.pneumatic_actuator_variety.code == 'DA'):
                da_weight = PneumaticWeightParameter.objects.filter(
                    body=body,
                    spring_qty__code='DA'
                ).first()
                return da_weight.weight if da_weight else None

            # Для приводов SR
            if not self.selected_springs_qty:
                return None

            # Получаем вес для максимального количества пружин
            max_springs_qty = PneumaticWeightParameter.objects.filter(
                body=body
            ).exclude(spring_qty__code='DA').order_by('-spring_qty__code').first()

            if not max_springs_qty:
                return None

            # Если выбрано максимальное количество пружин
            if self.selected_springs_qty.springs_qty.code == max_springs_qty.spring_qty.code:
                return max_springs_qty.weight

            # Вычисляем разницу в количестве пружин
            try:
                selected_springs = int(self.selected_springs_qty.springs_qty.code)
                max_springs = int(max_springs_qty.spring_qty.code)

                spring_difference = max_springs - selected_springs

                # Вычисляем вес с учетом разницы пружин
                if body.weight_spring and spring_difference > 0:
                    return max_springs_qty.weight - (spring_difference * body.weight_spring)
                else:
                    return max_springs_qty.weight

            except (ValueError, TypeError):
                # Если не удалось преобразовать в числа
                return max_springs_qty.weight

        except Exception:
            return None

    @property
    def calculated_weight(self) -> Optional[Decimal]:
        """Рассчитанный вес (property)"""
        return self.get_weight()

    def create_duplicate(self):
        """Создать дубликат текущего объекта"""
        from datetime import datetime

        # Создаем новый объект с пустыми name и code
        duplicate = self.__class__(
            # Копируем ForeignKey поля
            selected_model_line_item=self.selected_model_line_item,
            selected_safety_position=self.selected_safety_position,
            selected_springs_qty=self.selected_springs_qty,
            selected_temperature=self.selected_temperature,
            selected_ip=self.selected_ip,
            selected_exd=self.selected_exd,
            selected_body_coating=self.selected_body_coating,
            selected_hand_wheel=self.selected_hand_wheel,

            # Копируем остальные поля
            sorting_order=self.sorting_order,
            is_active=self.is_active,
            is_unique=False,

            # Пустые поля - будут сгенерированы автоматически в save()
            name='',  # Будет сгенерировано автоматически
            code='',  # Будет сгенерировано автоматически

            # Добавляем пометку о дублировании в описание
            description=self.description
        )

        # Сохраняем - автоматически сгенерируются name и code
        duplicate.save()

        # Теперь добавляем суффикс к уже сгенерированному имени и коду
        if duplicate.name:
            # Используем существующий метод _adjust_for_duplicate
            duplicate._adjust_for_duplicate()
            duplicate.save()

        return duplicate