# pneumatic_actuators/models/pa_actuator_selected.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from typing import List, Optional, Tuple, Any, Dict, Union
from decimal import Decimal
from django.core.exceptions import ValidationError
import re
from tabulate import tabulate

import logging
from django.utils.html import format_html
logger = logging.getLogger(__name__)

from pneumatic_actuators.models import PneumaticActuatorModelLineItem
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

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _('Модель пневмопривода')
        verbose_name_plural = _('Модели пневмоприводов')
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'name',
                    'selected_model_line_item',
                    'selected_safety_position',
                    'selected_springs_qty',
                    'selected_temperature',
                    'selected_ip',
                    'selected_exd',
                    'selected_body_coating',
                    'selected_hand_wheel'
                ],
                name='unique_actuator_configuration',  # Понятное имя
                # condition=models.Q(is_active=True),  # Если нужно только для активных
            )
        ]

    def __str__(self):
        return self.name

        # ==================== StructuredDataMixin методы ====================

    # GET /api/core/?model=pneumatic_actuators.PneumaticActuatorSelected&id=4&fmt=compact
    # GET /api/core/?model=pneumatic_actuators.PneumaticActuatorSelected&id=4&fmt=display&view=card
    # /api/core/?model=pneumatic_actuators.PneumaticActuatorSelected&id=4&fmt=full&include=
    def get_compact_data(self) -> Dict[str , Any] :
        from django.utils.translation import gettext_lazy as _
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

    def get_full_data(self , include: Optional[List[str]] = None) -> Dict[str , Any] :
        """
        Полные данные для форм и API
        """
        if include is None :
            include = ['form' , 'metadata' , 'related' , 'description_data']

        # Базовые данные
        data = {
            'id' : self.id ,
            'model' : self._get_model_name() ,
            'app' : self._get_app_label() ,
            'is_active' : self.is_active ,
            'sorting_order' : self.sorting_order ,
            'display' : self.get_display_data() ,
            'compact' : self.get_compact_data() ,
        }

        if 'form' in include :
            data['form'] = self._get_form_data()

        if 'metadata' in include :
            data['metadata'] = self._get_metadata()

        if 'related' in include :
            data['related'] = self._get_related_data()

        if 'description_data' in include :
            # Используем существующий метод, но в новом формате
            data['description_data'] = self._get_structured_description_data()

        return data

    # ==================== Вспомогательные методы ====================

    def _get_form_data(self) -> Dict[str , Any] :
        """Данные для форм"""
        return {
            'name' : self.name ,
            'code' : self.code ,
            'description' : self.description ,
            'sorting_order' : self.sorting_order ,
            'is_active' : self.is_active ,
            'selected_model_id' : self.selected_model_line_item.id if self.selected_model_line_item else None ,
            'selected_safety_position_id' : self.selected_safety_position.id if self.selected_safety_position else None ,
            'selected_springs_qty_id' : self.selected_springs_qty.id if self.selected_springs_qty else None ,
            'selected_temperature_id' : self.selected_temperature.id if self.selected_temperature else None ,
            'selected_ip_id' : self.selected_ip.id if self.selected_ip else None ,
            'selected_exd_id' : self.selected_exd.id if self.selected_exd else None ,
            'selected_body_coating_id' : self.selected_body_coating.id if self.selected_body_coating else None ,
            'selected_hand_wheel' : self.selected_hand_wheel.id if self.selected_hand_wheel else None ,
        }


    def _get_metadata(self) -> Dict[str , Any] :
        """Метаданные для форм"""
        return {
            'field_schema' : [
                {
                    'name' : 'name' ,
                    'type' : 'text' ,
                    'required' : True ,
                    'label' : _('Название привода') ,
                    'help_text' : _('Название привода') ,
                    'max_length' : 200 ,
                    'widget' : 'text_input'
                } ,
                {
                    'name' : 'code' ,
                    'type' : 'text' ,
                    'required' : False ,
                    'label' : _('Код/Артикул') ,
                    'help_text' : _('Код привода') ,
                    'max_length' : 50 ,
                    'widget' : 'text_input'
                } ,
                {
                    'name' : 'description' ,
                    'type' : 'text' ,
                    'required' : False ,
                    'label' : _('Описание') ,
                    'help_text' : _('Описание привода') ,
                    'widget' : 'textarea' ,
                    'rows' : 4
                } ,
                {
                    'name' : 'selected_model' ,
                    'type' : 'foreign_key' ,
                    'required' : True ,
                    'label' : _('Модель') ,
                    'help_text' : _('Модель пневмопривода') ,
                    'model' : 'pneumatic_actuators.PneumaticActuatorModelLineItem' ,
                    'widget' : 'select'
                } ,
                {
                    'name' : 'selected_safety_position' ,
                    'type' : 'foreign_key' ,
                    'required' : False ,
                    'label' : _('Положение безопасности') ,
                    'help_text' : _('Выбранное положение безопасности') ,
                    'model' : 'pneumatic_actuators.PneumaticSafetyPositionOption' ,
                    'widget' : 'select'
                } ,
                {
                    'name' : 'selected_springs_qty' ,
                    'type' : 'foreign_key' ,
                    'required' : False ,
                    'label' : _('Количество пружин') ,
                    'help_text' : _('Выбранное количество пружин') ,
                    'model' : 'pneumatic_actuators.PneumaticSpringsQtyOption' ,
                    'widget' : 'select'
                } ,
                {
                    'name' : 'selected_temperature' ,
                    'type' : 'foreign_key' ,
                    'required' : False ,
                    'label' : _('Температурная опция') ,
                    'help_text' : _('Выбранная температурная опция') ,
                    'model' : 'pneumatic_actuators.PneumaticTemperatureOption' ,
                    'widget' : 'select'
                } ,
                {
                    'name' : 'selected_ip' ,
                    'type' : 'foreign_key' ,
                    'required' : False ,
                    'label' : _('Степень защиты IP') ,
                    'help_text' : _('Выбранная степень защиты IP') ,
                    'model' : 'pneumatic_actuators.PneumaticIpOption' ,
                    'widget' : 'select'
                } ,
                {
                    'name' : 'selected_hand_wheel' ,
                    'type' : 'foreign_key' ,
                    'required' : False ,
                    'label' : _('Ручной дублер') ,
                    'help_text' : _('Тип установленного ручного дублера') ,
                    'model' : 'pneumatic_actuators.PneumaticHandWheelOption' ,
                    'widget' : 'select'
                } ,
                {
                    'name' : 'selected_exd' ,
                    'type' : 'foreign_key' ,
                    'required' : False ,
                    'label' : _('Взрывозащита') ,
                    'help_text' : _('Выбранная опция взрывозащиты') ,
                    'model' : 'pneumatic_actuators.PneumaticExdOption' ,
                    'widget' : 'select'
                } ,
                {
                    'name' : 'selected_body_coating' ,
                    'type' : 'foreign_key' ,
                    'required' : False ,
                    'label' : _('Покрытие корпуса') ,
                    'help_text' : _('Выбранное покрытие корпуса') ,
                    'model' : 'pneumatic_actuators.PneumaticBodyCoatingOption' ,
                    'widget' : 'select'
                } ,
                {
                    'name' : 'sorting_order' ,
                    'type' : 'number' ,
                    'required' : False ,
                    'label' : _('Порядок сортировки') ,
                    'help_text' : _('Порядок сортировки в списке') ,
                    'min_value' : -100 ,
                    'max_value' : 100 ,
                    'default' : 0
                } ,
                {
                    'name' : 'is_active' ,
                    'type' : 'boolean' ,
                    'required' : False ,
                    'label' : _('Активно') ,
                    'help_text' : _('Активно свойство или нет') ,
                    'default' : True
                }
            ] ,
            'validation_rules' : {
                'name' : {
                    'required' : True ,
                    'min_length' : 2 ,
                    'max_length' : 200
                } ,
                'code' : {
                    'max_length' : 50
                }
            }
        }

    def _get_related_data(self) -> Dict[str , Any] :
        """Связанные данные"""
        related_data = {}

        # Данные модели
        if self.selected_model_line_item and hasattr(self.selected_model_line_item , 'get_compact_data') :
            related_data['selected_model'] = self.selected_model_line_item.get_compact_data()

        # Данные опций
        option_fields = [
            'selected_safety_position' ,
            'selected_springs_qty' ,
            'selected_temperature' ,
            'selected_ip' ,
            'selected_exd' ,
            'selected_body_coating',
            'selected_hand_wheel' ,
        ]

        for field_name in option_fields :
            field = getattr(self , field_name)
            if field and hasattr(field , 'get_compact_data') :
                related_data[field_name] = field.get_compact_data()

        # Доступные опции
        related_data['available_options'] = self.get_available_options()

        return related_data

    def _get_structured_description_data(self) -> Dict[str , Any] :
        """
        Структурированные данные описания
        Конвертируем существующий get_description_data в новый формат
        """
        # Используем существующий метод
        existing_data = self.get_description_data()

        # Конвертируем в новый формат
        structured_data = {
            'basic_info' : {
                'model' : existing_data.get('model' , {}) ,
                'basic_properties' : existing_data.get('basic_properties' , {}) ,
                'selected_options' : existing_data.get('selected_options' , {}) ,
            } ,
            'technical_specs' : {
                'body_specs' : existing_data.get('body_specs' , {}) ,
                'calculated_parameters' : existing_data.get('calculated_parameters' , {}) ,
                'torque_thrust_table' : existing_data.get('torque_thrust_table') ,
            } ,
            'formatted' : {
                'short' : self._generate_short_description() ,
                'technical' : self._generate_tech_description_for_display() ,
                'html' : self._generate_html_description() ,
            }
        }

        return structured_data

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
    # def get_description_preview(self) :
    #     """Краткий предпросмотр описания"""
    #     if not self.description :
    #         return "Нет описания"
    #
    #     # Первые 100 символов
    #     preview = self.description[:100]
    #     if len(self.description) > 100 :
    #         preview += "..."
    #
    #     return format_html(
    #         '<span title="{}">{}</span>' ,
    #         self.description.replace('"' , '&quot;') ,
    #         preview
    #     )
    #
    # get_description_preview.short_description = "Описание"

    def get_description_data(self) -> Dict[str, Any]:
        """Получить структурированные данные для описания"""
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"logger get_description_data")
        print(f"print get_description_data")
        data = {
            'model': {
                'name': self.code if self.code else None
            },
            'basic_properties': {},
            'selected_options': {},
            'body_specs': {},  # ПОЛЕ ДЛЯ ХАРАКТЕРИСТИК КОРПУСА
            'calculated_parameters': {  # НОВОЕ ПОЛЕ ДЛЯ РАСЧЕТНЫХ ПАРАМЕТРОВ
                'weight': float(self.calculated_weight) if self.calculated_weight else None
            },
            'torque_thrust_table': None,
            'cert_data' : None
        }

        # Базовые свойства из модели
        if self.selected_model_line_item:
            if self.selected_model_line_item.brand:
                data['basic_properties']['brand'] = self.selected_model_line_item.brand.name
            if self.selected_model_line_item.pneumatic_actuator_variety:
                data['basic_properties'][
                    'pneumatic_actuator_variety'] = self.selected_model_line_item.pneumatic_actuator_variety.name
            if self.selected_model_line_item.default_output_type:
                data['basic_properties']['default_output_type'] = self.selected_model_line_item.default_output_type.name
            if self.selected_model_line_item.pneumatic_actuator_construction_variety:
                data['basic_properties'][
                    'pneumatic_actuator_construction_variety'] = self.selected_model_line_item.pneumatic_actuator_construction_variety.name
            # if self.selected_model.default_hand_wheel:
            #     data['basic_properties']['selected_hand_wheel'] = self.selected_model.selected_hand_wheel.name

        # Опции через model_line_item
        # print(f"\n=== DEBUG: Checking model_line_item options ===")
        # print(f"Has selected_safety_position: {hasattr(self , 'selected_safety_position')}")
        if self.selected_safety_position:
            data['selected_options']['safety_position'] = {
                'name': self.selected_safety_position.safety_position.name,
                'description': self.selected_safety_position.description
            }
        # print(f"Has selected_springs_qty: {hasattr(self , 'selected_springs_qty')}")
        if self.selected_springs_qty:
            data['selected_options']['springs_qty'] = {
                'name': self.selected_springs_qty.springs_qty.name,
                'description': self.selected_springs_qty.description
            }

        # Опции через model_line
        if self.selected_temperature:
            data['selected_options']['temperature'] = {
                'name': str(self.selected_temperature),
                'description': self.selected_temperature.description
            }

        if self.selected_ip:
            data['selected_options']['ip'] = {
                'name': str(self.selected_ip),
                'description': self.selected_ip.description
            }

        if self.selected_exd:
            data['selected_options']['exd'] = {
                'name': str(self.selected_exd),
                'description': self.selected_exd.description
            }

        if self.selected_body_coating:
            data['selected_options']['body_coating'] = {
                'name': str(self.selected_body_coating),
                'description': self.selected_body_coating.description
            }
        if self.selected_hand_wheel:
            data['selected_options']['hand_wheel'] = {
                'name': str(self.selected_hand_wheel),
                'description': self.selected_hand_wheel.description
            }

        # Характеристики корпуса
        if self.selected_model_line_item and self.selected_model_line_item.body:
            data['body_specs'] = self.selected_model_line_item.body.get_description_data()

        # Таблица моментов/усилий
        if self.selected_model_line_item and self.selected_model_line_item.body:
            try:
                if self.selected_springs_qty:
                    spring_qty = self.selected_springs_qty.springs_qty
                else:
                    spring_qty = None

                ncno_code = self.selected_safety_position.safety_position.code if self.selected_safety_position else SAFETY_POSITION_NC_DEFAULT_CODE
                construction_variety_code = self.selected_model_line_item.pneumatic_actuator_construction_variety.code if self.selected_model_line_item else ACTUATOR_VARIETY_RP_DEFAULT_CODE
                da_sr_code = self.selected_model_line_item.pneumatic_actuator_variety.code if self.selected_model_line_item else None
                # Получаем структурированные данные
                from pneumatic_actuators.models import BodyThrustTorqueTable
                torque_data = BodyThrustTorqueTable.get_torque_thrust_values(
                    current_body=self.selected_model_line_item.body,
                    spring_qty_list=[spring_qty] if spring_qty else None,
                    ncno_code=ncno_code,
                    construction_variety_code=construction_variety_code, da_sr_code=da_sr_code
                )

                data['torque_thrust_table'] = torque_data
                print(f"data['torque_thrust_table'] {data['torque_thrust_table']}")
            except Exception as e:
                logger.error(f"Error getting torque/thrust table data: {e}")
                data['torque_thrust_table'] = {
                    'error': str(e),
                    'format': 'error'
                }

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

    def _generate_tech_description(self) -> str:
        """Сгенерировать описание привода из структурированных данных"""
        import re  # Добавляем импорт

        data = self.get_description_data()
        desc_parts = []

        # Модель
        if data['model']['name']:
            desc_parts.append(f"Модель: {data['model']['name']}")
        else:
            desc_parts.append("Модель: не выбрана")

        # Базовые свойства
        for prop_name, prop_value in data['basic_properties'].items():
            if prop_value:
                display_name = {
                    'brand': 'Бренд',
                    'pneumatic_actuator_variety': 'Тип привода',
                    'default_output_type': 'Тип работы',
                    'pneumatic_actuator_construction_variety': 'Тип конструкции',
                    # 'default_hand_wheel': 'Ручной дублер'
                }.get(prop_name, prop_name)
                desc_parts.append(f"{display_name}: {prop_value}")
        # print(f"# Базовые свойства {desc_parts}")
        # Выбранные опции
        for option_type, option_data in data['selected_options'].items():
            display_name = {
                'safety_position': 'Положение безопасности',
                'springs_qty': 'Количество пружин',
                'temperature': 'Температурный диапазон',
                'ip': 'Степень защиты IP',
                'exd': 'Взрывозащита',
                'body_coating': 'Покрытие корпуса',
                'hand_wheel': 'Встроенный ручной дублер'
            }.get(option_type, option_type)

            desc_parts.append(f"{display_name}: {option_data['name']}")
        # print(f"# Выбранные опции {desc_parts}")
        # Характеристики корпуса
        if data.get('body_specs'):
            body_data = data['body_specs']

            # Технические характеристики корпуса
            tech_specs = body_data.get('technical_specs', {})
            if tech_specs:
                desc_parts.append("Характеристики корпуса:")

                for spec_name, spec_value in tech_specs.items():
                    display_name = {
                        'piston_diameter': 'Диаметр поршня',
                        'turn_angle': 'Угол поворота',
                        'turn_tuning_limit': 'Ограничитель поворота',
                        'weight_spring': 'Вес пружины',
                        'min_pressure': 'Минимальное давление',
                        'max_pressure': 'Максимальное давление',
                        'air_usage_open': 'Расход воздуха (открытие)',
                        'air_usage_close': 'Расход воздуха (закрытие)'
                    }.get(spec_name, spec_name)
                    desc_parts.append(f"  {display_name}: {spec_value}")
            # print(f"# tech_specs {desc_parts}")
            # Информация о штоке
            mounting_specs = body_data.get('mounting_specs', {})
            if mounting_specs:
                desc_parts.append("Присоединение к арматуре:")
                if 'stem' in mounting_specs:
                    stem_data = mounting_specs['stem']
                    stem_parts = []
                    if 'shape' in stem_data:
                        stem_parts.append(f"форма: {stem_data['shape']}")
                    if 'size' in stem_data:
                        stem_parts.append(f"размер: {stem_data['size']}")
                    if 'max_height' in stem_data:
                        stem_parts.append(f"макс. высота: {stem_data['max_height']}")
                    if 'max_diameter' in stem_data:
                        stem_parts.append(f"макс. диаметр: {stem_data['max_diameter']}")
                    if stem_parts:
                        desc_parts.append(f"  Шток: {', '.join(stem_parts)}")

                if 'mounting_plates' in mounting_specs:
                    desc_parts.append(f"  Монтажные площадки: {', '.join(mounting_specs['mounting_plates'])}")
            # print(f"# mounting_specs {desc_parts}")
            # Подключения корпуса
            pipe_connections_specs = body_data.get('pipe_connections_specs', {})
            if pipe_connections_specs:
                desc_parts.append("Подключения корпуса:")  # Убрали \n

                if 'thread_in' in pipe_connections_specs:
                    desc_parts.append(f"  Пневмовход: {pipe_connections_specs['thread_in']}")
                if 'thread_out' in pipe_connections_specs:
                    desc_parts.append(f"  Пневмовыход: {pipe_connections_specs['thread_out']}")
                if 'pneumatic_connections' in pipe_connections_specs:
                    desc_parts.append(f"  Типы пневмоподключений: {', '.join(pipe_connections_specs['pneumatic_connections'])}")


        # Расчетные параметры
        calc_params = data.get('calculated_parameters', {})
        if calc_params.get('weight'):
            desc_parts.append(f"Вес: {calc_params['weight']} кг")

        # Таблица моментов/усилий - УБРАЛИ ОДНУ ИЗ ДУБЛИРУЮЩИХ СТРОК
        if 'torque_thrust_table' in data:
            table_data = data['torque_thrust_table']

            if isinstance(table_data, dict):
                table_config = table_data.get('table_config', {})
                data_by_spring = table_data.get('data', {}).get('by_spring', {})

                if data_by_spring:
                    visible_fields = table_config.get('visible_fields', [])
                    pressure_order = table_config.get('pressure_order', [])
                    spring_order = table_config.get('spring_order', [])
                    torque_format = table_config.get('format', {}).get('torque', {})

                    desc_parts.append("Таблица моментов:")  # Убрали \n

                    # Начинаем HTML таблицу
                    desc_parts.append('<table border="1" style="border-collapse: collapse; margin: 10px 0;">')
                    desc_parts.append('<thead><tr><th rowspan="2">Пружины</th>')

                    # Первая строка заголовка - давления
                    for pressure_code in pressure_order:
                        col_span = len(visible_fields)
                        desc_parts.append(f'<th colspan="{col_span}">{pressure_code}</th>')
                    desc_parts.append('</tr>')

                    # Вторая строка заголовка - поля
                    desc_parts.append('<tr>')
                    for _ in pressure_order:
                        for field in visible_fields:
                            desc_parts.append(f'<th>{field.upper()}</th>')
                    desc_parts.append('</tr></thead>')

                    # Тело таблицы
                    desc_parts.append('<tbody>')
                    for spring_code in spring_order:
                        if spring_code in data_by_spring:
                            desc_parts.append(f'<tr><td>{spring_code}</td>')
                            spring_data = data_by_spring[spring_code]
                            pressures_data = spring_data.get('pressures', {})

                            for pressure_code in pressure_order:
                                if pressure_code in pressures_data:
                                    pressure_values = pressures_data[pressure_code]
                                    for field in visible_fields:
                                        value = pressure_values.get(field)
                                        if value is not None:
                                            precision = torque_format.get('precision', 1)
                                            desc_parts.append(f'<td>{value:.{precision}f}</td>')
                                        else:
                                            desc_parts.append('<td>—</td>')
                                else:
                                    for _ in visible_fields:
                                        desc_parts.append('<td>—</td>')

                            desc_parts.append('</tr>')
                    desc_parts.append('</tbody></table>')

                    desc_parts.append(f"Примечание: значения в {torque_format.get('unit', 'Нм')}")  # Убрали \n

        # Собираем и чистим текст
        full_text = "\n".join(desc_parts)

        # Убираем множественные пустые строки (2 и более подряд)
        cleaned_text = re.sub(r'\n{2,}', '\n', full_text)

        return cleaned_text

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
            return self._generate_fallback_code()

        """Простой рендеринг шаблона - заменяем переменные значениями"""
        result = template

        # Простая замена переменных
        result = result.replace('{model_code}', self._get_value('selected_model_line_item__name'))
        result = result.replace('{springs_qty}', self._get_value('selected_springs_qty__encoding'))
        result = result.replace('{temperature}', self._get_value('selected_temperature__encoding'))
        result = result.replace('{safety_position}', self._get_value('selected_safety_position__encoding'))
        result = result.replace('{hand_wheel}', self._get_value('selected_hand_wheel__encoding'))
        result = result.replace('{coating}', self._get_value('selected_body_coating__encoding'))
        result = result.replace('{ip}', self._get_value('selected_ip__encoding'))
        result = result.replace('{exd}', self._get_value('selected_exd__encoding'))


        # Очистка лишних точек (две точки подряд -> одна точка)
        result = re.sub(r'\.{2,}', '.', result)
        # Удаляем точку в начале и конце
        result = result.strip('.')
        result = re.sub(' (DA)', '', result)
        # if not self.is_da_model():
        #     result = result + str('('+self._get_value('selected_springs_qty__encoding')+')')

        return result

    def _get_value(self, field_path: str) -> str:
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
            self._get_value('selected_model__code'),
            self._get_value('selected_springs_qty__encoding'),
            self._get_value('selected_temperature__encoding'),
            self._get_value('selected_safety_position__encoding'),
            self._get_value('selected_hand_wheel__encoding'),
            self._get_value('selected_body_coating__encoding'),
            self._get_value('selected_ip__encoding'),
            self._get_value('selected_exd__encoding'),
        ]
        # Фильтруем пустые значения и соединяем
        return '.'.join(filter(None, parts))

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        # Словарь опций для обработки
        option_config = {
            'selected_safety_position': 'pneumatic_actuators.models.pa_options.PneumaticSafetyPositionOption',
            'selected_springs_qty': 'pneumatic_actuators.models.pa_options.PneumaticSpringsQtyOption',
            'selected_temperature': 'pneumatic_actuators.models.pa_options.PneumaticTemperatureOption',
            'selected_ip': 'pneumatic_actuators.models.pa_options.PneumaticIpOption',
            'selected_exd': 'pneumatic_actuators.models.pa_options.PneumaticExdOption',
            'selected_body_coating': 'pneumatic_actuators.models.pa_options.PneumaticBodyCoatingOption',
            'selected_hand_wheel': 'pneumatic_actuators.models.PneumaticHandWheelOption',
        }

        # Получаем оригинальный объект
        original = None
        if self.pk:
            try:
                original = self.__class__._default_manager.get(pk=self.pk)
            except self.__class__.DoesNotExist:
                pass

        # Проверяем, изменилась ли модель привода
        if original and original.selected_model_line_item and self.selected_model_line_item:
            if original.selected_model_line_item != self.selected_model_line_item:
                # Импортируем модели опций
                for field_name, model_path in option_config.items():
                    module_name, class_name = model_path.rsplit('.', 1)
                    module = __import__(module_name, fromlist=[class_name])
                    option_model = getattr(module, class_name)

                    current_option = getattr(self, field_name)
                    if current_option:
                        # Проверяем допустимость опции
                        if not option_model.is_option_allowed_for_parent(
                                parent_obj=self.selected_model_line_item,
                                option_to_check=current_option
                        ):
                            # Устанавливаем дефолтную
                            default_option = option_model.get_default_or_any_allowed(
                                self.selected_model_line_item
                            )
                            setattr(self, field_name, default_option)

        # Устанавливаем дефолтные значения для пустых опций
        self._set_default_options()

        # Валидация
        try:
            self.clean()
        except ValidationError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Validation error in save(): {e}")
            raise

        # Автозаполнение полей
        if self.selected_model_line_item:
            if hasattr(self, 'generated_model_item_code'):
                if len(self.name) > 0:
                    self.name = self.generated_model_item_code
                self.code = self.generated_model_item_code
            if hasattr(self, '_generate_short_description'):
                self.description = self._generate_short_description()

        # Сохраняем
        super().save(*args, **kwargs)

    def _set_default_options(self) :
        """Установить значения по умолчанию для всех None опций"""
        if not hasattr(self , 'selected_model_line_item') or not self.selected_model_line_item :
            return

        print(f"=== DEBUG _set_default_options ===")

        from pneumatic_actuators.models.pa_options import (
            PneumaticTemperatureOption ,
            PneumaticSafetyPositionOption ,
            PneumaticSpringsQtyOption ,
            PneumaticIpOption ,
            PneumaticExdOption ,
            PneumaticBodyCoatingOption
        )
        from pneumatic_actuators.models import PneumaticHandWheelOption

        # Все опции, которые должны иметь дефолтные значения
        option_configs = [
            ('selected_safety_position' , PneumaticSafetyPositionOption , 'model_line_item') ,
            ('selected_springs_qty' , PneumaticSpringsQtyOption , 'model_line_item') ,
            ('selected_temperature' , PneumaticTemperatureOption , 'model_line') ,
            ('selected_ip' , PneumaticIpOption , 'model_line') ,
            ('selected_exd' , PneumaticExdOption , 'model_line') ,
            ('selected_body_coating' , PneumaticBodyCoatingOption , 'model_line') ,
            ('selected_hand_wheel' , PneumaticHandWheelOption , 'model_line') ,
        ]

        missing_defaults = []  # Список опций без дефолтных значений

        for field_name , option_model , parent_type in option_configs :
            current_value = getattr(self , field_name)
            print(f"  Checking {field_name}: {current_value}")

            if not current_value :
                print(f"    Field is empty, getting default option...")

                # Определяем правильный parent объект
                if parent_type == 'model_line' :
                    parent_obj = self.selected_model_line_item.model_line
                    if not parent_obj :
                        print(f"    No model_line for {field_name}")
                        missing_defaults.append(f"{field_name} (отсутствует model_line)")
                        continue
                else :  # 'model_line_item'
                    parent_obj = self.selected_model_line_item

                try :
                    # Получаем дефолтную опцию для этой модели
                    default_option = option_model.get_default_or_any_allowed(parent_obj)
                    print(f"    Default option: {default_option}")

                    if default_option :
                        setattr(self , field_name , default_option)
                        print(f"    ✓ Установлена дефолтная опция: {default_option}")
                    else :
                        # Нет дефолтной опции
                        error_msg = f"{field_name} (нет дефолтной опции для {parent_obj})"
                        missing_defaults.append(error_msg)
                        print(f"    ✗ {error_msg}")

                except Exception as e :
                    error_msg = f"{field_name} (ошибка: {str(e)})"
                    missing_defaults.append(error_msg)
                    print(f"    ERROR: {error_msg}")
                    import traceback
                    traceback.print_exc()

        # Проверяем, есть ли опции без дефолтных значений
        if missing_defaults :
            error_message = "Отсутствуют дефолтные опции:\n" + "\n".join(f"- {msg}" for msg in missing_defaults)
            print(f"=== ВНИМАНИЕ: {error_message}")

            # Если в режиме DEBUG или тестирования, можно вывести предупреждение
            # В продакшене возможно нужно логировать, но не прерывать выполнение
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Missing default options for {self.selected_model_line_item}: {missing_defaults}")


    def clean(self):
        """Валидация выбранных опций"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("=== MODEL CLEAN DEBUG: Starting validation")

        if self.selected_model_line_item:


            # Проверяем safety_position только если оно выбрано И модель не DA
            if self.selected_safety_position:
                # if not is_da_model:
                from pneumatic_actuators.models.pa_options import PneumaticSafetyPositionOption
                valid_safety = PneumaticSafetyPositionOption.objects.filter(
                    model_line_item=self.selected_model_line_item,
                    id=self.selected_safety_position.id,
                    is_active=True
                ).exists()
                logger.info(
                    f"=== MODEL CLEAN DEBUG: safety_position valid={valid_safety}")
                if not valid_safety:
                    from django.core.exceptions import ValidationError
                    raise ValidationError({
                        'selected_safety_position': 'Выбранное положение безопасности не доступно для этой модели'
                    })
                # else:
                #     # Для DA моделей safety_position должно быть None
                #     logger.info(f"=== MODEL CLEAN DEBUG: DA model with safety_position - will be cleared")
                #     from django.core.exceptions import ValidationError
                #     raise ValidationError({
                #         'selected_safety_position': 'Положение безопасности не доступно для приводов двойного действия (DA)'
                #     })

            # Проверяем springs_qty
            if self.selected_springs_qty:
                from pneumatic_actuators.models.pa_options import PneumaticSpringsQtyOption
                valid_springs = PneumaticSpringsQtyOption.objects.filter(
                    model_line_item=self.selected_model_line_item,
                    id=self.selected_springs_qty.id,
                    is_active=True
                ).exists()
                logger.info(f"=== MODEL CLEAN DEBUG: springs_qty valid={valid_springs}")
                if not valid_springs:
                    from django.core.exceptions import ValidationError
                    raise ValidationError({
                        'selected_springs_qty': 'Выбранное количество пружин не доступно для этой модели'
                    })

            # ИСПРАВЛЕННАЯ ПРОВЕРКА ОСТАЛЬНЫХ ОПЦИЙ
            option_checks = {
                'selected_temperature': ('PneumaticTemperatureOption', 'температурная опция'),
                'selected_ip': ('PneumaticIpOption', 'степень защиты IP'),
                'selected_exd': ('PneumaticExdOption', 'взрывозащита'),
                'selected_body_coating': ('PneumaticBodyCoatingOption', 'покрытие корпуса'),
                'selected_hand_wheel' : ('PneumaticHandWheelOption' , 'ручной дублер')
            }

            for field_name, (model_class_name, field_label) in option_checks.items():
                field_value = getattr(self, field_name)
                if field_value:
                    try:
                        # Импортируем модель по имени
                        option_model = getattr(
                            __import__('pneumatic_actuators.models.pa_options', fromlist=[model_class_name]),
                            model_class_name)

                        # Для этих опций используем model_line вместо model_line_item
                        if field_name in ['selected_temperature', 'selected_ip', 'selected_exd',
                                          'selected_body_coating','selected_hand_wheel']:
                            valid_option = option_model.objects.filter(
                                model_line=self.selected_model_line_item.model_line,
                                id=field_value.id,
                                is_active=True
                            ).exists()
                        else:
                            valid_option = option_model.objects.filter(
                                model_line_item=self.selected_model_line_item,
                                id=field_value.id,
                                is_active=True
                            ).exists()

                        logger.info(f"=== MODEL CLEAN DEBUG: {field_name} valid={valid_option}")
                        if not valid_option:
                            from django.core.exceptions import ValidationError
                            raise ValidationError({
                                field_name: f'Выбранная {field_label} не доступна для этой модели'
                            })
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
