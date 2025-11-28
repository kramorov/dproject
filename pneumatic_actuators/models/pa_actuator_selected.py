# pneumatic_actuators/models/pa_actuator_selected.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from typing import List, Optional, Tuple, Any, Dict, Union
from decimal import Decimal
from django.core.exceptions import ValidationError
import re

import logging

logger = logging.getLogger(__name__)

from pneumatic_actuators.models import PneumaticActuatorModelLineItem


class PneumaticActuatorSelected(models.Model):
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

    selected_model = models.ForeignKey(PneumaticActuatorModelLineItem,
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

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _('Выбранный пневмопривод')
        verbose_name_plural = _('Выбранные пневмоприводы')

    def __str__(self):
        return self.name

    def get_description_data(self) -> Dict[str, Any]:
        """Получить структурированные данные для описания"""
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"logger get_description_data")
        print(f"print get_description_data")
        data = {
            'model': {
                'name': self.selected_model.name if self.selected_model else None
            },
            'basic_properties': {},
            'selected_options': {},
            'body_specs': {},  # ПОЛЕ ДЛЯ ХАРАКТЕРИСТИК КОРПУСА
            'calculated_parameters': {  # НОВОЕ ПОЛЕ ДЛЯ РАСЧЕТНЫХ ПАРАМЕТРОВ
                'weight': float(self.calculated_weight) if self.calculated_weight else None
            },
            'torque_thrust_table': None
        }

        # Базовые свойства из модели
        if self.selected_model:
            if self.selected_model.brand:
                data['basic_properties']['brand'] = self.selected_model.brand.name
            if self.selected_model.pneumatic_actuator_variety:
                data['basic_properties'][
                    'pneumatic_actuator_variety'] = self.selected_model.pneumatic_actuator_variety.name
            if self.selected_model.default_output_type:
                data['basic_properties']['default_output_type'] = self.selected_model.default_output_type.name
            if self.selected_model.pneumatic_actuator_construction_variety:
                data['basic_properties'][
                    'pneumatic_actuator_construction_variety'] = self.selected_model.pneumatic_actuator_construction_variety.name
            if self.selected_model.default_hand_wheel:
                data['basic_properties']['default_hand_wheel'] = self.selected_model.default_hand_wheel.name

        # Опции через model_line_item
        if self.selected_safety_position:
            data['selected_options']['safety_position'] = {
                'name': self.selected_safety_position.safety_position.name,
                'description': self.selected_safety_position.description
            }

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

        # Характеристики корпуса
        if self.selected_model and self.selected_model.body:
            data['body_specs'] = self.selected_model.body.get_description_data()

        # Таблица моментов/усилий
        if self.selected_model and self.selected_model.body:
            try:
                from pneumatic_actuators.models import BodyThrustTorqueTable

                # Определяем spring_qty на основе выбранных опций
                # Исправляем получение spring_qty
                if self.selected_springs_qty:
                    # Получаем связанный объект PneumaticActuatorSpringsQty
                    # self.selected_springs_qty - это PneumaticSpringsQtyOption
                    # self.selected_springs_qty.springs_qty - это PneumaticActuatorSpringsQty
                    spring_qty = self.selected_springs_qty.springs_qty
                    print(f"🔧 Spring QTY object: {spring_qty}")
                    print(f"🔧 Spring QTY type: {type(spring_qty)}")
                    print(f"🔧 Spring QTY id: {spring_qty.id if spring_qty else 'None'}")
                else:
                    spring_qty = None
                    print("🔧 Spring QTY: None")
                # Проверяем что получили правильный тип
                from pneumatic_actuators.models import PneumaticActuatorSpringsQty
                if spring_qty and not isinstance(spring_qty, PneumaticActuatorSpringsQty):
                    print(f"🔧 ❌ ERROR: Wrong type! Got {type(spring_qty)}, expected PneumaticActuatorSpringsQty")
                    spring_qty = None  # или обработайте ошибку
                else:
                    print(f"🔧 ✅ Correct type: PneumaticActuatorSpringsQty")
                pass
                # Определяем тип привода (NC/NO) на основе safety_position
                ncno = 'NC'  # по умолчанию нормально закрытый
                if self.selected_safety_position:
                    safety_code = getattr(self.selected_safety_position.safety_position, 'encoding', '')
                    if safety_code == 'NO':
                        ncno = 'NO'
                print(f"self.selected_safety_position {self.selected_safety_position}")
                # Получаем данные из таблицы с фильтрацией по конкретной пружине
                print(f"We are about to get torque_data: ")
                torque_data = BodyThrustTorqueTable.get_torque_thrust_values(
                    body_list=[self.selected_model.body],
                    spring_qty=spring_qty,  # передаем конкретную пружину
                    ncno=ncno
                )
                print(f"We got torque_data: {torque_data}")
                # Форматируем данные для описания
                if self.selected_model and self.selected_model.body:
                    try:
                        from pneumatic_actuators.models import BodyThrustTorqueTable

                        # Определяем spring_qty на основе выбранных опций
                        spring_qty = self.selected_springs_qty

                        # Определяем тип привода (NC/NO) на основе safety_position
                        ncno = 'NC'  # по умолчанию нормально закрытый
                        if self.selected_safety_position:
                            safety_code = getattr(self.selected_safety_position, 'encoding', '')
                            if safety_code == 'NO':
                                ncno = 'NO'

                        # Получаем данные из таблицы с фильтрацией по конкретной пружине
                        torque_data = BodyThrustTorqueTable.get_torque_thrust_values(
                            body_list=[self.selected_model.body],
                            spring_qty=spring_qty,  # передаем конкретную пружину
                            ncno=ncno
                        )
                        #
                        # # ПЕРЕДАЕМ САМУ ТАБЛИЦУ
                        # if torque_data and torque_data.get('data'):
                        #     data['torque_thrust_table'] = {
                        #         'headers': torque_data.get('headers', []),
                        #         'data': torque_data.get('data', []),
                        #         'pressures': torque_data.get('pressures', []),
                        #         'body': self.selected_model.body.name,
                        #         'spring_qty': spring_qty.springs_qty if spring_qty else 'DA',
                        #         'ncno': ncno
                        #     }
                        # else:
                        #     data['torque_thrust_table'] = {
                        #         'headers': [],
                        #         'data': [],
                        #         'pressures': [],
                        #         'body': self.selected_model.body.name,
                        #         'message': "Данные не найдены"
                        #     }

                    except Exception as e:
                        # data['torque_thrust_table'] = {
                        #     'headers': [],
                        #     'data': [],
                        #     'pressures': [],
                        #     'error': str(e)
                        # }
                        pass

            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error getting torque/thrust table data: {e}")
                data['torque_thrust_table'] = {
                    'error': 'Ошибка при получении данных по моментам/усилиям',
                    'details': str(e)
                }
        return data

    def _generate_description(self) -> str:
        """Сгенерировать описание привода из структурированных данных"""
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
                    'default_hand_wheel': 'Ручной дублер'
                }.get(prop_name, prop_name)
                desc_parts.append(f"{display_name}: {prop_value}")

        # Выбранные опции
        for option_type, option_data in data['selected_options'].items():
            display_name = {
                'safety_position': 'Положение безопасности',
                'springs_qty': 'Количество пружин',
                'temperature': 'Температурный диапазон',
                'ip': 'Степень защиты IP',
                'exd': 'Взрывозащита',
                'body_coating': 'Покрытие корпуса'
            }.get(option_type, option_type)

            desc_parts.append(f"{display_name}: {option_data['name']}")
            if option_data.get('description'):
                desc_parts.append(f"Описание {display_name.lower()}: {option_data['description']}")
        # Характеристики корпуса
        if data.get('body_specs'):
            body_data = data['body_specs']

            # Базовая информация о корпусе
            if body_data['basic_info']['name']:
                desc_parts.append(f"Корпус: {body_data['basic_info']['name']}")

            # Технические характеристики корпуса
            tech_specs = body_data.get('technical_specs', {})
            if tech_specs:
                desc_parts.append("\nХарактеристики корпуса:")

                for spec_name, spec_value in tech_specs.items():
                    if spec_name != 'stem':  # Шток обрабатываем отдельно
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

                # Информация о штоке
                if 'stem' in tech_specs:
                    stem_data = tech_specs['stem']
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

            # Подключения корпуса
            connections = body_data.get('connections', {})
            if connections:
                desc_parts.append("\nПодключения корпуса:")

                if 'thread_in' in connections:
                    desc_parts.append(f"  Пневмовход: {connections['thread_in']}")
                if 'thread_out' in connections:
                    desc_parts.append(f"  Пневмовыход: {connections['thread_out']}")
                if 'pneumatic_connections' in connections:
                    desc_parts.append(f"  Типы пневмоподключений: {', '.join(connections['pneumatic_connections'])}")
                if 'mounting_plates' in connections:
                    desc_parts.append(f"  Монтажные площадки: {', '.join(connections['mounting_plates'])}")
            # НОВОЕ: Расчетные параметры
            calc_params = data.get('calculated_parameters', {})
            if calc_params.get('weight'):
                desc_parts.append(f"Вес: {calc_params['weight']} кг")

        return "\n".join(desc_parts)

    @property
    def generated_model_item_code(self) -> str:
        """Сгенерировать артикул по шаблону из model_line"""
        if not self.selected_model or not self.selected_model.model_line:
            return self.code or ""

        template = self.selected_model.model_line.model_item_code_template
        if not template:
            return self._generate_fallback_code()

        return self._render_template(template)

    def _render_template(self, template: str) -> str:
        """Простой рендеринг шаблона - заменяем переменные значениями"""
        result = template

        # Простая замена переменных
        result = result.replace('{model_code}', self._get_value('selected_model__code'))
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
        # Получаем оригинальный объект из базы данных, если он существует
        original = None
        if self.pk:
            try:
                original = PneumaticActuatorSelected.objects.get(pk=self.pk)
            except PneumaticActuatorSelected.DoesNotExist:
                original = None

        # Проверяем, изменилась ли модель привода
        if original and original.selected_model and self.selected_model:
            if original.selected_model.model_line != self.selected_model.model_line:
                # Если изменилась модель - обнуляем все опции
                self.selected_safety_position = None
                self.selected_springs_qty = None
                self.selected_temperature = None
                self.selected_ip = None
                self.selected_exd = None
                self.selected_body_coating = None
        else:
            # Если это новая запись или нет оригинала - устанавливаем опции по умолчанию
            self._set_default_options()

        # ВАЖНО: Вызываем clean() для валидации перед сохранением
        try:
            self.clean()
        except ValidationError as e:
            # Логируем ошибки валидации
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"=== MODEL SAVE VALIDATION ERROR: {e}")
            raise e

        # Устанавливаем значения по умолчанию для None опций
        self._ensure_default_options()

        # ДОПОЛНИТЕЛЬНО: Автоматически очищаем safety_position для DA моделей
        if self.selected_model and self.selected_safety_position:
            is_da_model = (self.selected_model.pneumatic_actuator_variety and
                           self.selected_model.pneumatic_actuator_variety.code == 'DA')
            if is_da_model:
                self.selected_safety_position = None
        # Автозаполнение
        if self.selected_model:
            self.name = self.generated_model_item_code
            self.code = self.generated_model_item_code
            self.description = self._generate_description()
        super().save(*args, **kwargs)
        super().save(*args, **kwargs)

    def _set_default_options(self):
        """Устанавливает опции по умолчанию для новой записи"""
        if self.selected_model:
            model_line = self.selected_model.model_line

            # Устанавливаем опции по умолчанию из связанной модели
            if not self.selected_temperature and hasattr(model_line, 'default_temperature'):
                self.selected_temperature = model_line.default_temperature

            if not self.selected_ip and hasattr(model_line, 'default_ip'):
                self.selected_ip = model_line.default_ip

            if not self.selected_body_coating and hasattr(model_line, 'default_body_coating'):
                self.selected_body_coating = model_line.default_body_coating

    def _ensure_default_options(self):
        """Обеспечивает, что обязательные опции имеют значения по умолчанию"""
        if self.selected_model:
            model_line = self.selected_model.model_line

            # Если опции все еще None, пытаемся найти подходящие значения по умолчанию
            if not self.selected_temperature:
                try:
                    from pneumatic_actuators.models.pa_options import PneumaticTemperatureOption
                    # Ищем опции, связанные с выбранной моделью
                    default_temp = PneumaticTemperatureOption.objects.filter(
                        model_line_item=self.selected_model,
                        is_active=True
                    ).first()
                    if not default_temp:
                        # Если нет связанных опций, берем первую активную
                        default_temp = PneumaticTemperatureOption.objects.filter(
                            is_active=True
                        ).first()
                    if default_temp:
                        self.selected_temperature = default_temp
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error setting default temperature: {e}")

            if not self.selected_ip:
                try:
                    from pneumatic_actuators.models.pa_options import PneumaticIpOption
                    default_ip = PneumaticIpOption.objects.filter(
                        model_line_item=self.selected_model,
                        is_active=True
                    ).first()
                    if not default_ip:
                        default_ip = PneumaticIpOption.objects.filter(
                            is_active=True
                        ).first()
                    if default_ip:
                        self.selected_ip = default_ip
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error setting default IP: {e}")

            if not self.selected_body_coating:
                try:
                    from pneumatic_actuators.models.pa_options import PneumaticBodyCoatingOption
                    default_coating = PneumaticBodyCoatingOption.objects.filter(
                        model_line_item=self.selected_model,
                        is_active=True
                    ).first()
                    if not default_coating:
                        default_coating = PneumaticBodyCoatingOption.objects.filter(
                            is_active=True
                        ).first()
                    if default_coating:
                        self.selected_body_coating = default_coating
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error setting default coating: {e}")

    def clean(self):
        """Валидация выбранных опций"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("=== MODEL CLEAN DEBUG: Starting validation")

        if self.selected_model:
            # Определяем тип модели
            is_da_model = (self.selected_model.pneumatic_actuator_variety and
                           self.selected_model.pneumatic_actuator_variety.code == 'DA')

            # Проверяем safety_position только если оно выбрано И модель не DA
            if self.selected_safety_position:
                if not is_da_model:
                    from pneumatic_actuators.models.pa_options import PneumaticSafetyPositionOption
                    valid_safety = PneumaticSafetyPositionOption.objects.filter(
                        model_line_item=self.selected_model,
                        id=self.selected_safety_position.id,
                        is_active=True
                    ).exists()
                    logger.info(
                        f"=== MODEL CLEAN DEBUG: safety_position valid={valid_safety}, is_da_model={is_da_model}")
                    if not valid_safety:
                        from django.core.exceptions import ValidationError
                        raise ValidationError({
                            'selected_safety_position': 'Выбранное положение безопасности не доступно для этой модели'
                        })
                else:
                    # Для DA моделей safety_position должно быть None
                    logger.info(f"=== MODEL CLEAN DEBUG: DA model with safety_position - will be cleared")
                    from django.core.exceptions import ValidationError
                    raise ValidationError({
                        'selected_safety_position': 'Положение безопасности не доступно для приводов двойного действия (DA)'
                    })

            # Проверяем springs_qty
            if self.selected_springs_qty:
                from pneumatic_actuators.models.pa_options import PneumaticSpringsQtyOption
                valid_springs = PneumaticSpringsQtyOption.objects.filter(
                    model_line_item=self.selected_model,
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
                'selected_body_coating': ('PneumaticBodyCoatingOption', 'покрытие корпуса')
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
                                          'selected_body_coating']:
                            valid_option = option_model.objects.filter(
                                model_line=self.selected_model.model_line,
                                id=field_value.id,
                                is_active=True
                            ).exists()
                        else:
                            valid_option = option_model.objects.filter(
                                model_line_item=self.selected_model,
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
        return str(self.selected_model) if self.selected_model else "-"

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

    def get_available_options(self) -> Dict[str, List[Dict]]:
        """Получить все доступные опции для выбранной модели"""
        from pneumatic_actuators.models.pa_options import (
            PneumaticSafetyPositionOption, PneumaticSpringsQtyOption,
            PneumaticTemperatureOption, PneumaticIpOption,
            PneumaticExdOption, PneumaticBodyCoatingOption
        )
        #
        # print(f"=== DEBUG get_available_options ===")
        # print(f"Selected actuator ID: {self.id}")
        # print(f"Selected model: {self.selected_model}")
        # print(f"Selected model ID: {self.selected_model.id if self.selected_model else 'None'}")
        # print(f"Selected model name: {self.selected_model.name if self.selected_model else 'None'}")

        if not self.selected_model:
            # print("=== DEBUG: No selected model - returning empty options")
            return self._get_empty_options()

        try:
            # Опции через model_line_item
            safety_options = PneumaticSafetyPositionOption.objects.filter(
                model_line_item=self.selected_model,
                is_active=True
            ).select_related('safety_position')

            springs_options = PneumaticSpringsQtyOption.objects.filter(
                model_line_item=self.selected_model,
                is_active=True
            ).select_related('springs_qty')
            #
            # print(f"Safety options SQL: {safety_options.query}")
            # print(f"Springs options SQL: {springs_options.query}")
            # print(f"Safety options count: {safety_options.count()}")
            # print(f"Springs options count: {springs_options.count()}")

            # # Выводим найденные опции
            # for i , opt in enumerate(safety_options) :
            #     print(f"Safety option {i + 1}: {opt.id} - {opt.safety_position.name} - encoding: '{opt.encoding}'")
            #
            # for i , opt in enumerate(springs_options) :
            #     print(f"Springs option {i + 1}: {opt.id} - {opt.springs_qty.name} - encoding: '{opt.encoding}'")

            # Опции через model_line
            temperature_options = []
            ip_options = []
            exd_options = []
            body_coating_options = []

            if self.selected_model.model_line:
                # print(f"Model line: {self.selected_model.model_line}")

                temperature_options = PneumaticTemperatureOption.objects.filter(
                    model_line=self.selected_model.model_line,
                    is_active=True
                )
                # ДИАГНОСТИКА temperature_options
                print(f"🔧 MODEL temperature_options count: {temperature_options.count()}")
                for opt in temperature_options:
                    print(f"🔧   id={opt.id}, encoding={opt.encoding}")

                ip_options = PneumaticIpOption.objects.filter(
                    model_line=self.selected_model.model_line,
                    is_active=True
                )

                exd_options = PneumaticExdOption.objects.filter(
                    model_line=self.selected_model.model_line,
                    is_active=True
                )

                body_coating_options = PneumaticBodyCoatingOption.objects.filter(
                    model_line=self.selected_model.model_line,
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
            'exd_options': [], 'body_coating_options': []
        }

    def get_weight(self) -> Optional[Decimal]:
        """Рассчитать вес привода"""
        from pneumatic_actuators.models import PneumaticWeightParameter
        if not self.selected_model or not self.selected_model.body:
            return None

        body = self.selected_model.body

        try:
            # Для приводов DA
            if (self.selected_model.pneumatic_actuator_variety and
                    self.selected_model.pneumatic_actuator_variety.code == 'DA'):
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
