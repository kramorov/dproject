#electric_actuators/models/ea_model_line.py
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.translation import gettext_lazy as _
from typing import List , Optional , Tuple , Any , Dict , Union
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
import logging


from cert_doc.models import AbstractCertRelation
from core.models import StructuredDataMixin

from producers.models import Brands
from params.models import ExdOption, BodyCoatingOption, BlinkerOption, SwitchesParameters, \
    EnvTempParameters, IpOption, ControlUnitInstalledOption, ActuatorGearboxOutputType, HandWheelInstalledOption, \
    OperatingModeOption, CertData, \
    MechanicalIndicatorInstalledOption

logger = logging.getLogger(__name__)


class ElectricActuatorModelLine(StructuredDataMixin , models.Model) :
    """
    Серия электроприводов - объединяет в себе общие для всех моделей серии свойства
    и доступные опции
    Опции корпуса:

        резьба КВ и их количество
        End_switches type (mechanical, electronic) qty (SPDT/DPDT)
        Torque switch - type (mechanical, electronic) qty (SPDT/DPDT)
    Опции model_line:
        ElectricTurnAngleOption угол поворота (90-180-270), точность регулировки +-
        ElectricHandWheelOption - вид ручного дублера
        ElectricTemperatureOption - LT
        ElectricIpOption - IP
        ElectricExdOption - Ex
        ElectricBodyCoatingOption - Опции покрытия корпуса для электроприводов
        QC быстросъемное соединение
        ElectricWaySwitchesOption MID	Опция 3х позиционный (по доп.концевикам) - Путевые выключатели SwitchesParameters
        ElectricControlUnitInstalledOption  Control Unit (POSI, TR, INT...)
        ElectricBlinkerOption  Блинкер BlinkerOption
    Опции model_line_item:
        ElectricPowerSupplyOption PowerSupply (time to close, rotation_speed,
        torque_min, torque_max,
        Current_rated, current_max, motor_power
        torque_switches
    """
    name = models.CharField(max_length=200 ,
                            verbose_name=_("Название") ,
                            help_text=_('Название серии'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код серии приводов"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание модели корпуса привода'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    model_item_code_template = models.CharField(max_length=500 , blank=True , null=True ,
                                                verbose_name=_("Шаблон артикула") ,
                                                help_text=_('Шаблон артикула для конкретной модели серии'))
    brand = models.ForeignKey(Brands , blank=True , null=True ,
                              related_name='electric_model_line_brand' ,
                              on_delete=models.SET_NULL ,
                              verbose_name=_('Бренд'),
                              help_text=_('Бренд производителя'))
    default_output_type = \
        models.ForeignKey(ActuatorGearboxOutputType , blank=True , null=True ,
                          related_name='electric_model_line_default_output_type' ,
                          on_delete=models.SET_NULL ,
                          verbose_name=_('Тип привода'),
                          help_text=_('Тип работы серии приводов'))

    allowed_operating_mode = \
        models.ManyToManyField(OperatingModeOption, blank=True, default=1,
                               related_name='electric_actuator_model_line_allowed_operating_mode',
                               verbose_name=_('Режим работы'),
                               help_text=_('Возможные для выбора режимы работы двигателя для серии (можно выбрать '
                                         'несколько)'))
    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Серия моделей электроприводов')
        verbose_name_plural = _('Серии моделей электроприводов')

    def __str__(self) :
        return self.name

    def _get_metadata(self) -> Dict[str , Any] :
        """
        Метаданные для форм
        """
        return {
            'field_schema' : [
                {
                    'name' : 'name' ,
                    'type' : 'text' ,
                    'required' : True ,
                    'label' : _('Название серии') ,
                    'help_text' : _('Название серии электроприводов') ,
                    'max_length' : 200 ,
                    'widget' : 'text_input'
                } ,
                {
                    'name' : 'code' ,
                    'type' : 'text' ,
                    'required' : False ,
                    'label' : _('Код серии') ,
                    'help_text' : _('Код серии приводов') ,
                    'max_length' : 50 ,
                    'widget' : 'text_input'
                } ,
                {
                    'name' : 'description' ,
                    'type' : 'text' ,
                    'required' : False ,
                    'label' : _('Описание') ,
                    'help_text' : _('Текстовое описание модели корпуса привода') ,
                    'widget' : 'textarea' ,
                    'rows' : 4
                } ,
                {
                    'name' : 'model_item_code_template' ,
                    'type' : 'text' ,
                    'required' : False ,
                    'label' : _('Шаблон артикула') ,
                    'help_text' : _('Шаблон артикула для конкретной модели серии') ,
                    'max_length' : 500 ,
                    'widget' : 'text_input'
                } ,
                {
                    'name' : 'brand_id' ,
                    'type' : 'foreign_key' ,
                    'required' : False ,
                    'label' : _('Бренд') ,
                    'help_text' : _('Бренд производителя') ,
                    'model' : 'brands.Brand'
                } ,
                {
                    'name' : 'default_output_type' ,
                    'type' : 'foreign_key' ,
                    'required' : False ,
                    'label' : _('Тип работы') ,
                    'help_text' : _('Тип работы серии приводов') ,
                    'model' : 'params.ActuatorGearboxOutputType'
                } ,
            ] ,
            'validation_rules' : {
                'name' : {
                    'required' : True ,
                    'min_length' : 2 ,
                    'max_length' : 200
                } ,
                'code' : {
                    'pattern' : r'^[A-Z0-9_-]*$' ,
                    'message' : _('Код должен содержать только буквы, цифры, дефисы и подчеркивания')
                }
            }
        }

    def get_compact_data(self) -> Dict[str , Any] :
        """
        Минимальные данные для списков и таблиц
        """
        data = super().get_compact_data()

        data.update({
            'brand' : self.brand.get_compact_data() if self.brand else None ,
            'default_output_type' :
                self.default_output_type.get_compact_data()
                if self.default_output_type else None ,
            'model_item_code_template' : self.model_item_code_template ,
            'sorting_order' : self.sorting_order ,
        })

        # Сертификаты берем через связь
        if hasattr(self , 'cert_relations') :
            data['cert_data_list'] = [
                {
                    'cert_data' : relation.cert_data.get_compact_data() ,
                    'relation_sorting_order' : relation.sorting_order ,
                    'relation_is_active' : relation.is_active ,
                }
                for relation in self.cert_relations.filter(is_active=True)
                if relation.cert_data.is_active
            ]
        return data

    def get_display_data(self , view_type: str = 'detail') -> Dict[str , Any] :
        """
        Данные для отображения в UI
        """
        # Базовые поля - используем метод из миксина
        fields = self._get_base_display_fields()

        # Обновляем лейблы и приоритеты
        if 'name' in fields :
            fields['name']['label'] = _('Название серии')
            fields['name']['icon'] = '⚡'
            fields['name']['priority'] = 1

        if 'code' in fields :
            fields['code']['label'] = _('Код серии')
            fields['code']['icon'] = '🔢'
            fields['code']['priority'] = 2

        # Добавляем связанные объекты
        fields.update({
            'brand' : self._format_foreign_key(
                self.brand ,
                label=_('Бренд') ,
                icon='🏷️' ,
                priority=3 ,
                include_data='compact'
            ) ,
            'default_output_type' : self._format_foreign_key(
                self.default_output_type ,
                label=_('Тип работы по умолчанию') ,
                icon='🔄' ,
                priority=4 ,
                include_data='compact'
            ) ,
            'model_item_code_template' : self._format_field(
                self.model_item_code_template ,
                'text' ,
                label=_('Шаблон артикула') ,
                icon='📝' ,
                priority=5
            ) ,
        })

        # Переопределяем description
        fields['description'] = self._format_field(
            self.description ,
            'text' ,
            label=_('Описание') ,
            icon='📄' ,
            priority=6 ,
            multiline=True
        )

        # Получаем данные сертификатов
        certificates = []
        if hasattr(self , 'cert_relations') :
            cert_relations = self.cert_relations.filter(
                is_active=True ,
                cert_data__is_active=True
            ).select_related('cert_data').order_by('sorting_order')

            for relation in cert_relations :
                cert = relation.cert_data
                if view_type == self.CARD or view_type == self.BADGE :
                    cert_display = cert.get_display_data('badge')
                else :
                    cert_display = cert.get_display_data()

                certificates.append({
                    'id' : cert.id ,
                    'display' : cert_display ,
                    'compact' : cert.get_compact_data() ,
                    'relation' : {
                        'sorting_order' : relation.sorting_order ,
                        'is_active' : relation.is_active ,
                    }
                })

        if certificates :
            fields['certificates'] = {
                'label' : _('Сертификаты') ,
                'value' : certificates ,
                'type' : 'relation_list' ,
                'icon' : '📋' ,
                'priority' : 50 ,
                'count' : len(certificates)
            }

        # Обработка разных типов представления
        if view_type == self.CARD :
            brand_badge = self.brand.get_display_data('badge') if self.brand else None
            output_type_badge = (
                self.default_output_type.get_display_data('badge')
                if self.default_output_type else None
            )

            return {
                'title' : self.name ,
                'subtitle' : self.code or '' ,
                'description' : self.description[:100] + '...' if self.description else '' ,
                'badges' : [
                    {'text' : self.code , 'type' : 'code'} if self.code else None ,
                    brand_badge if brand_badge else None ,
                    {'text' : 'Активна' , 'type' : 'success'} if self.is_active
                    else {'text' : 'Неактивна' , 'type' : 'secondary'} ,
                    {'text' : f'{len(certificates)} серт.' , 'type' : 'info'} if certificates else None ,
                ] ,
                'details' : [
                    {'label' : 'Тип работы' , 'value' : output_type_badge.get('text' , '')}
                    if output_type_badge else None ,
                ]
            }

        elif view_type == self.LIST :
            return {
                'id' : self.id ,
                'name' : self.name ,
                'code' : self.code ,
                'brand' : self.brand.name if self.brand else '' ,
                'certificates_count' : len(certificates) ,
                'is_active' : self.is_active ,
            }

        elif view_type == self.BADGE :
            return {
                'text' : self.name ,
                'code' : self.code ,
                'type' : 'model_line' ,
                'color' : 'blue' if self.is_active else 'gray' ,
                'brand' : self.brand.get_display_data('badge') if self.brand else None ,
                'certificates_count' : len(certificates) ,
            }

        # По умолчанию DETAIL
        return {
            'title' : f'{self.name} ({self.code})' if self.code else self.name ,
            'fields' : fields ,
            'actions' : self._get_actions()
        }

    def get_full_data(self , include: Optional[List[str]] = None) -> Dict[str , Any] :
        """
        Полные данные для форм и API
        """
        if include is None :
            include = ['form' , 'metadata' , 'related' , 'certificates']

        data = {
            'id' : self.id ,
            'model' : self._get_model_name() ,
            'app' : self._get_app_label() ,
            'is_active' : self.is_active ,
            'sorting_order' : self.sorting_order ,
            'display' : self.get_display_data() ,
        }

        if 'form' in include :
            data['form'] = {
                'name' : self.name ,
                'code' : self.code ,
                'description' : self.description ,
                'model_item_code_template' : self.model_item_code_template ,
                'brand_id' : self.brand.id if self.brand else None ,
                'default_output_type_id' : self.default_output_type.id
                if self.default_output_type else None ,
                'sorting_order' : self.sorting_order ,
                'is_active' : self.is_active ,
            }

        if 'metadata' in include :
            data['metadata'] = self._get_metadata()

        if 'related' in include :
            data['related'] = {
                'brand' : self.brand.get_full_data(['form']) if self.brand else None ,
                'default_output_type' : (
                    self.default_output_type.get_full_data(['form'])
                    if self.default_output_type else None
                ) ,
            }

        if 'certificates' in include and hasattr(self , 'cert_relations') :
            cert_relations = self.cert_relations.filter(
                is_active=True ,
                cert_data__is_active=True
            ).select_related('cert_data').order_by('sorting_order')

            data['certificates'] = []
            for relation in cert_relations :
                cert = relation.cert_data
                data['certificates'].append({
                    'certificate' : cert.get_full_data(['form' , 'metadata']) ,
                    'relation' : {
                        'id' : relation.id ,
                        'sorting_order' : relation.sorting_order ,
                        'is_active' : relation.is_active ,
                    }
                })

        return data

    def ensure_all_default_options_exist(self) :
        """Создать все необходимые опции по умолчанию для электроприводов"""
        logger.info(f"ensure_all_default_options_exist для серии электроприводов: {self}")

        from .ea_options import (
            ElectricTemperatureOption ,
            ElectricIpOption ,
            ElectricExdOption ,
            ElectricBodyCoatingOption ,
            ElectricBlinkerOption ,
            ElectricWaySwitchesOption ,
            # ElectricPowerSupplyOption ,
            ElectricControlUnitInstalledOption ,
            ElectricHandWheelOption ,
            ElectricMechanicalIndicatorOption ,
            # ElectricOperatingModeOption ,
            ElectricTurnAngleOption
        )

        option_classes = [
            ElectricTemperatureOption ,
            ElectricIpOption ,
            ElectricExdOption ,
            ElectricBodyCoatingOption ,
            ElectricBlinkerOption ,
            ElectricWaySwitchesOption ,
            # ElectricPowerSupplyOption ,
            ElectricControlUnitInstalledOption ,
            ElectricHandWheelOption ,
            ElectricMechanicalIndicatorOption ,
            # ElectricOperatingModeOption ,
            ElectricTurnAngleOption
        ]

        for option_class in option_classes :
            try :
                was_created = option_class.ensure_default_exists(self)
                logger.debug(f"{option_class.__name__}: {'создана' if was_created else 'уже существует'}")
            except Exception as e :
                logger.error(f"Ошибка в {option_class.__name__}: {e}")
                import traceback
                traceback.print_exc()

    def save(self , *args , **kwargs) :
        """Сохранение с созданием опций по умолчанию для новой серии"""
        is_new = self.pk is None
        super().save(*args , **kwargs)

        if is_new :
            logger.info(f"Создание опций по умолчанию для новой серии электроприводов: {self.name}")
            self.ensure_all_default_options_exist()

    # ==================== СВОЙСТВА ДЛЯ ШАБЛОНОВ И API ====================

    @property
    def temperature_options_list(self) :
        """Список всех температурных опций"""
        return self.temperature_options.all()

    @property
    def ip_options_list(self) :
        """Список всех IP опций"""
        return self.ip_options.all()

    @property
    def exd_options_list(self) :
        """Список всех Exd опций"""
        return self.exd_options.all()

    @property
    def body_coating_options_list(self) :
        """Список всех опций покрытия корпуса"""
        return self.body_coating_options.all()

    @property
    def blinker_options_list(self) :
        """Список всех опций блинкера"""
        return self.blinker_options.all()

    # ==================== МЕТОДЫ ПОЛУЧЕНИЯ ОПЦИЙ ПО УМОЛЧАНИЮ ====================

    def get_default_temperature_option(self) :
        """Получить стандартную температурную опцию"""
        from .ea_options import ElectricTemperatureOption
        return ElectricTemperatureOption.get_or_create_default(self)

    def get_default_ip_option(self) :
        """Получить стандартную IP опцию"""
        from .ea_options import ElectricIpOption
        return ElectricIpOption.get_or_create_default(self)

    def get_default_exd_option(self) :
        """Получить стандартную Exd опцию"""
        from .ea_options import ElectricExdOption
        return ElectricExdOption.get_or_create_default(self)

    def get_default_body_coating_option(self) :
        """Получить стандартную опцию покрытия корпуса"""
        from .ea_options import ElectricBodyCoatingOption
        return ElectricBodyCoatingOption.get_or_create_default(self)

    def get_default_blinker_option(self) :
        """Получить стандартную опцию блинкера"""
        from .ea_options import ElectricBlinkerOption
        return ElectricBlinkerOption.get_or_create_default(self)

    def get_default_way_switches_option(self) :
        """Получить стандартную опцию путевых выключателей"""
        from .ea_options import ElectricWaySwitchesOption
        return ElectricWaySwitchesOption.get_or_create_default(self)

    def get_default_control_unit_option(self) :
        """Получить стандартную опцию блока управления"""
        from .ea_options import ElectricControlUnitInstalledOption
        return ElectricControlUnitInstalledOption.get_or_create_default(self)

    def get_default_turn_angle_option(self) :
        """Получить стандартную опцию угла поворота"""
        from .ea_options import ElectricTurnAngleOption
        return ElectricTurnAngleOption.get_or_create_default(self)

    def get_default_power_supply_option(self) :
        """Получить стандартную опцию питания"""
        from .ea_options import ElectricPowerSupplyOption
        return ElectricPowerSupplyOption.get_or_create_default(self)

    def get_default_operating_mode_option(self) :
        """Получить стандартную опцию режима работы"""
        from .ea_options import ElectricOperatingModeOption
        return ElectricOperatingModeOption.get_or_create_default(self)

    def get_default_mechanical_indicator_option(self) :
        """Получить стандартную опцию механического индикатора"""
        from .ea_options import ElectricMechanicalIndicatorOption
        return ElectricMechanicalIndicatorOption.get_or_create_default(self)
    def get_default_hand_wheel_option(self) :
        """Получить стандартную опцию ручного дублера"""
        from .ea_options import ElectricHandWheelOption
        return ElectricHandWheelOption.get_or_create_default(self)

    # ==================== ОТОБРАЖАЕМЫЕ СВОЙСТВА ====================

    @property
    def ip_display(self) :
        """Отображаемое имя стандартной IP опции"""
        default_ip = self.get_default_ip_option()
        if default_ip and default_ip.ip_option :
            return default_ip.ip_option.name
        return "Не указано"

    @property
    def exd_display(self) :
        """Отображаемое имя стандартной Exd опции"""
        default_exd = self.get_default_exd_option()
        if default_exd and default_exd.exd_option :
            return default_exd.exd_option.name
        return "Не указано"

    @property
    def body_coating_display(self) :
        """Отображаемое имя стандартной опции покрытия"""
        default_coating = self.get_default_body_coating_option()
        if default_coating and default_coating.body_coating_option :
            return default_coating.body_coating_option.name
        return "Не указано"

    @property
    def temperature_range_display(self) :
        """Отображаемый диапазон стандартной температуры"""
        default_temp = self.get_default_temperature_option()
        if default_temp :
            return default_temp.get_display_name()
        return "Не указано"

    @property
    def way_switches_options_list(self) :
        """Список всех опций путевых выключателей"""
        return self.way_switches_options.all()

    @property
    def power_supply_options_list(self) :
        """Список всех опций питания"""
        return self.power_supply_options.all()

    @property
    def control_unit_options_list(self) :
        """Список всех опций блока управления"""
        return self.control_unit_options.all()

    @property
    def turn_angle_options_list(self) :
        """Список всех опций угла поворота"""
        return self.turn_angle_options.all()

    @property
    def operating_mode_options_list(self) :
        """Список всех опций режима работы"""
        return self.operating_mode_options.all()

    @property
    def mechanical_indicator_options_list(self) :
        """Список всех опций механического индикатора"""
        return self.mechanical_indicator_options.all()

    @property
    def hand_wheel_options_list(self) :
        """Список всех опций ручного дулера"""
        return self.hand_wheel_options.all()

    def get_option_info(self):
        """Полная информация о всех опциях серии"""
        option_info = {
            'temperature': {
                'default': self.get_default_temperature_option().get_option_info()
                if self.get_default_temperature_option() else None,
                'options': [opt.get_option_info() for opt in self.temperature_options_list]
            },
            'ip': {
                'default': self.get_default_ip_option().get_option_info()
                if self.get_default_ip_option() else None,
                'options': [opt.get_option_info() for opt in self.ip_options_list]
            },
            'exd': {
                'default': self.get_default_exd_option().get_option_info()
                if self.get_default_exd_option() else None,
                'options': [opt.get_option_info() for opt in self.exd_options_list]
            },
            'body_coating': {
                'default': self.get_default_body_coating_option().get_option_info()
                if self.get_default_body_coating_option() else None,
                'options': [opt.get_option_info() for opt in self.body_coating_options_list]
            },
            'blinker': {
                'default': self.get_default_blinker_option().get_option_info()
                if self.get_default_blinker_option() else None,
                'options': [opt.get_option_info() for opt in self.blinker_options_list]
            },
            'way_switches': {
                'default': self.get_default_way_switches_option().get_option_info()
                if self.get_default_way_switches_option() else None,
                'options': [opt.get_option_info() for opt in self.way_switches_options_list]
            },
            'power_supply': {
                'default': self.get_default_power_supply_option().get_option_info()
                if self.get_default_power_supply_option() else None,
                'options': [opt.get_option_info() for opt in self.power_supply_options_list]
            },
            'control_unit': {
                'default': self.get_default_control_unit_option().get_option_info()
                if self.get_default_control_unit_option() else None,
                'options': [opt.get_option_info() for opt in self.control_unit_options_list]
            },
            'hand_wheel': {
                'default': self.get_default_hand_wheel_option().get_option_info()
                if self.get_default_hand_wheel_option() else None,
                'options': [opt.get_option_info() for opt in self.hand_wheel_options_list]
            },
            'turn_angle': {
                'default': self.get_default_turn_angle_option().get_option_info()
                if self.get_default_turn_angle_option() else None,
                'options': [opt.get_option_info() for opt in self.turn_angle_options_list]
            },
            'operating_mode': {
                'default': self.get_default_operating_mode_option().get_option_info()
                if self.get_default_operating_mode_option() else None,
                'options': [opt.get_option_info() for opt in self.operating_mode_options_list]
            },
            'mechanical_indicator': {
                'default': self.get_default_mechanical_indicator_option().get_option_info()
                if self.get_default_mechanical_indicator_option() else None,
                'options': [opt.get_option_info() for opt in self.mechanical_indicator_options_list]
            }
        }
        return option_info



# ==================== МОДЕЛЬ ДЛЯ СВЯЗИ СЕРТИФИКАТОВ ====================

class ElectricActuatorModelLineCertRelation(AbstractCertRelation) :
    """
    Связь сертификатов с сериями электроприводов.
    """
    model_line = models.ForeignKey(
        ElectricActuatorModelLine ,
        on_delete=models.CASCADE ,
        verbose_name=_("Серия электроприводов") ,
        related_name='cert_relations'
    )

    class Meta(AbstractCertRelation.Meta) :
        verbose_name = _("Связь сертификата с серией электроприводов")
        verbose_name_plural = _("Связи сертификатов с сериями электроприводов")
        unique_together = ['cert_data' , 'model_line']

    def get_related_object(self) :
        return self.model_line
class ModelLine(models.Model):
    name = models.CharField(max_length=20, help_text='Название серии')
    brand = \
        models.ForeignKey(Brands, blank=True, null=True,
                          related_name='model_line_brand',
                          on_delete=models.SET_NULL,
                          help_text='Бренд производителя')
    default_output_type = \
        models.ForeignKey(ActuatorGearboxOutputType, blank=True, null=True,
                          related_name='default_output_type',
                          on_delete=models.SET_NULL,
                          help_text='Тип работы серии приводов')

    default_ip = \
        models.ForeignKey(IpOption, blank=True, null=True,
                          related_name='default_ip_option',
                          on_delete=models.SET_NULL,
                          help_text='Стандартное исполнение степени защиты IP для серии')
    allowed_ip = \
        models.ManyToManyField(IpOption, blank=True, default=1,
                               related_name='ea_model_line_allowed_ip',
                               help_text='Возможные для выбора степени защиты IP для серии (можно выбрать '
                                         'несколько)')

    default_body_coating = \
        models.ForeignKey(BodyCoatingOption, blank=True, null=True,
                          related_name='default_body_coating',
                          on_delete=models.SET_NULL,
                          help_text='Стандартное исполнение покрытия корпуса для серии')
    allowed_body_coating = \
        models.ManyToManyField(BodyCoatingOption, blank=True, default=1,
                               related_name='ea_model_line_allowed_body_coating',
                               help_text='Возможные для выбора покрытия корпуса для серии (можно выбрать несколько)')

    default_exd = \
        models.ForeignKey(ExdOption, blank=True, null=True,
                          related_name='default_exd_option',
                          on_delete=models.SET_NULL,
                          help_text='Стандартное исполнение степени взрывозащиты для серии')
    allowed_exd = \
        models.ManyToManyField(ExdOption, blank=True, default=1,
                               related_name='ea_model_line_allowed_exd',
                               help_text='Возможные для выбора степени взрывозащиты для серии (можно '
                                         'выбрать несколько)')

    default_blinker = \
        models.ForeignKey(BlinkerOption, blank=True, null=True,
                          related_name='default_blinker_option',
                          on_delete=models.SET_NULL,
                          help_text='Стандартное исполнение блинкера для серии')

    default_end_switches = \
        models.ForeignKey(SwitchesParameters, blank=True, null=True,
                          related_name='default_end_switches',
                          on_delete=models.SET_NULL,
                          help_text='Стандартное исполнение путевых выключателей для серии')
    allowed_end_switches = \
        models.ManyToManyField(SwitchesParameters, blank=True, default=1,
                               related_name='ea_model_line_allowed_end_switches',
                               help_text='Возможные для выбора исполнения путевых выключателей для '
                                         'серии (можно выбрать несколько)')
    default_way_switches = \
        models.ForeignKey(SwitchesParameters, blank=True, null=True,
                          related_name='default_way_switches',
                          on_delete=models.SET_NULL,
                          help_text='Стандартное исполнение конечных выключателей для серии')
    allowed_way_switches = \
        models.ManyToManyField(SwitchesParameters, blank=True, default=1,
                               related_name='ea_model_line_allowed_way_switches',
                               help_text='Возможные для выбора исполнения конечных выключателей '
                                         'для серии (можно выбрать несколько)')
    default_torque_switches = models.ForeignKey(SwitchesParameters, blank=True, null=True,
                                                related_name='default_torque_switches',
                                                on_delete=models.SET_NULL,
                                                help_text='Стандартное исполнение ограничителей момента для серии')
    allowed_torque_switches = models.ManyToManyField(SwitchesParameters, blank=True, default=1,
                                                     related_name='ea_model_line_allowed_torque_switches',
                                                     help_text='Возможные для выбора исполнения ограничителей момента '
                                                               'для серии (можно выбрать несколько)')

    default_temperature = models.ForeignKey(EnvTempParameters, blank=True, null=True,
                                            related_name='default_temperature',
                                            on_delete=models.SET_NULL,
                                            help_text='Стандартное температурное исполнения для серии')
    allowed_temperature = \
        models.ManyToManyField(EnvTempParameters, blank=True, default=1,
                               related_name='ea_model_line_allowed_temperature',
                               help_text='Возможные для выбора температурные исполнения для серии ('
                                         'можно выбрать несколько)')

    default_control_unit_installed = \
        models.ForeignKey(ControlUnitInstalledOption, blank=True, null=True,
                          related_name='default_control_unit_installed',
                          on_delete=models.SET_NULL,
                          help_text='Стандартно установленный блок управления для серии')
    allowed_control_unit_installed = \
        models.ManyToManyField(ControlUnitInstalledOption, blank=True, default=1,
                               related_name='ea_model_line_allowed_control_unit_installed',
                               help_text='Возможные для выбора блоки управления для серии (можно выбрать несколько)')

    default_hand_wheel = \
        models.ForeignKey(HandWheelInstalledOption, blank=True, null=True,
                          related_name='default_hand_wheel',
                          on_delete=models.SET_NULL,
                          help_text='Стандартно установленный ручной дублер для серии')

    allowed_hand_wheel = \
        models.ManyToManyField(HandWheelInstalledOption, blank=True, default=1,
                               related_name='ea_model_line_allowed_hand_wheel',
                               help_text='Возможные для выбора ручные дублеры для серии (можно выбрать несколько)')

    default_mechanical_indicator = \
        models.ForeignKey(MechanicalIndicatorInstalledOption, blank=True, null=True,
                          related_name='default_mechanical_indicator',
                          on_delete=models.SET_NULL,
                          help_text='Стандартно установленный механический индикатор для серии')

    allowed_mechanical_indicator = \
        models.ManyToManyField(MechanicalIndicatorInstalledOption, blank=True, default=1,
                               related_name='ea_model_line_allowed_mechanical_indicator',
                               help_text='Возможные для выбора варианты установки механического индикатора для серии '
                                         '(можно выбрать несколько)')
    default_operating_mode = \
        models.ForeignKey(OperatingModeOption, blank=True, null=True,
                          related_name='default_operating_mode',
                          on_delete=models.SET_NULL,
                          help_text='Стандартный режим работы двигателя для серии')
    allowed_operating_mode = \
        models.ManyToManyField(OperatingModeOption, blank=True, default=1,
                               related_name='ea_model_line_allowed_operating_mode',
                               help_text='Возможные для выбора режимы работы двигателя для серии (можно выбрать '
                                         'несколько)')

    certificates = GenericRelation(CertData)

    def __str__(self):
        return self.name

