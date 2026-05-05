#gearbox/models/gearbox.py
from typing import Dict

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import CopyMixin, TemplateMixin
from params.models import LockingMechanism, IpOption


class GearBox(CopyMixin,TemplateMixin,  models.Model):
    """Модель редуктора (каталог)"""
    name = models.TextField(blank=True ,
                            verbose_name=_("Название") ,
                            help_text=_('Текстовое название модели редуктора'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код модели редуктора"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание модели редуктора'))

    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    model_line = models.ForeignKey('gearbox.GearBoxModelLine' , related_name='gear_box_model_line' ,
                                   blank=True ,
                                   null=True ,
                                   on_delete=models.SET_NULL ,
                                   help_text=_('Серия модели редуктора') ,
                                   verbose_name=_("Серия"))

    body = models.ForeignKey(
        'gearbox.GearBoxBody',
        on_delete=models.SET_NULL,
        blank=True , null=True ,
        verbose_name=_("Корпус редуктора"),
        help_text=_("Корпус редуктора с писанием свойств")
    )
    body_material_text = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name=_("Материал корпуса")
    )

    work_temp_min = models.IntegerField(
        null=True, blank=True, default=-40,
        help_text=_('Минимальная рабочая температура, °С'),
        verbose_name=_('Т раб.мин, °С')
    )
    work_temp_max = models.IntegerField(
        null=True, blank=True, default=120,
        help_text=_('Максимальная рабочая температура, °С'),
        verbose_name=_('Т раб.макс, °С'))

    override_mechanism = models.ForeignKey(
        'OverrideMechanism',
        on_delete=models.SET_NULL,
        blank=True , null=True ,
        verbose_name=_("Механизм отключения"),
        help_text=_("Механизм отключения дублера")
    )
    locking_mechanism = models.ForeignKey(
        LockingMechanism,
        on_delete=models.SET_NULL,
        blank=True , null=True ,
        verbose_name=_("Механизм блокировки"),
        help_text=_("Механизм блокировки дублера/переключателя")
    )
    DECLUTCHABLE_CHOICES = (
        ('yes' , _('расцепляемый')) ,
        ('no' , _('не расцепляемый')) ,
    )

    is_declutchable = models.CharField(
        max_length=3 ,
        choices=DECLUTCHABLE_CHOICES ,
        default='yes' ,
        verbose_name=_("Расцепляемый (Declutchable)") ,
        help_text=_("Можно ли физически отсоединить штурвал от привода")
    )
    ip = models.ForeignKey(IpOption, on_delete=models.SET_NULL, blank=True , null=True ,
                           related_name='gearbox_ip',
                           help_text=_('Степень защиты IP'),
                           verbose_name=_("IP")
                           )
    # Интерлок (лучше вынести в отдельную модель)
    interlock = models.ForeignKey('gearbox.GearBoxInterlock', on_delete=models.SET_NULL, null=True, blank=True,related_name='gearbox_interlock',
                           help_text=_('Модель интерлока'),
                           verbose_name=_("Модель интерлока")
                           )
    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict , blank=True , null=True ,
        verbose_name=_("Параметры") ,
        help_text=_("signal_type, resistance, range и т.д.")
    )
    class Meta:
        verbose_name = _("Редуктор")
        verbose_name_plural = _("Редукторы")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.name}"

    @property
    def is_declutchable_display(self) :
        return dict(self.DECLUTCHABLE_CHOICES).get(self.is_declutchable , '')
    def copy(self):
        """ Переоределяем - вызываем функцию из миксина CopyMixin и передаем параметры
        Создает копию с суффиксом 'Копия' и сбросом sorting_order и is_active """
        copied_obj = super().copy(suffix=" Копия", reset_fields=['sorting_order', 'is_active'])
        # Если нужно скопировать и корпус (создать новый корпус)
        # if self.body:
        #     copied_obj.body = self.body.copy()
        #     copied_obj.body.save()
        return copied_obj

    def _get_data_dict(self) -> Dict[str, str]:
        """Получить словарь соответствий плейсхолдеров и атрибутов для замены"""
        return {
            '{model_code}': 'code',
            '{brand}': 'model_line__brand',
            '{gearbox_output_variety}': 'model_line__gearbox_output_variety',
            '{gearbox_variety}' : 'model_line__gearbox_variety' ,
            '{turn_angle}': 'model_line__turn_angle' ,
            '{turn_tuning_limit}': 'model_line__turn_tuning_limit' ,
            '{weight}' : 'body__weight' ,
            '{mechanical_advantage}' : 'body__mechanical_advantage' ,
            '{max_stem_diameter_bottom}' : 'body__max_stem_diameter_bottom',
            '{stem_height_bottom}' : 'body__stem_height_bottom' ,
            '{stem_size_bottom}' : 'body__stem_size_bottom' ,
            '{stem_shape_bottom}' : 'body__stem_shape_bottom' ,
            '{mounting_plate_bottom_list_text}' : 'body__mounting_plate_bottom_list_text' ,
            '{stem_height_top}' : 'body__stem_height_top' ,
            '{stem_size_top}' : 'body__stem_size_top' ,
            '{stem_shape_top}' : 'body__stem_shape_top' ,
            '{mounting_plate_top_list_text}' : 'body__mounting_plate_top_list_text' ,
            '{handwheel_diameter}' : 'body__handwheel_diameter' ,
            '{handwheel_force_nominal}' : 'body__handwheel_force_nominal' ,
            '{max_output_torque}' : 'body__max_output_torque' ,
            '{max_input_torque}' : 'body__max_input_torque' ,
            '{efficiency}': 'body__efficiency',
            '{amplification_factor}': 'body__amplification_factor',
            '{reduction_ratio_text}': 'body__reduction_ratio_text',
            '{transmission_variety}': 'body__transmission_variety',
            '{interlock}': 'interlock',
            '{ip}': 'ip',
            '{locking_mechanism}': 'locking_mechanism',
            '{is_declutchable}': 'is_declutchable_display',
            '{override_mechanism}': 'override_mechanism',
            '{body_material_text}': 'body_material_text',
            '{work_temp_min}': 'work_temp_min',
            '{work_temp_max}': 'work_temp_max',
        }
    def _get_name_template_source(self):
        """Переоределяем в модели функцию из миксина CopyMixin: вернуть шаблон названия или None."""
        return self.model_line.name_template or None

    def _get_description_template_source(self):
        """Переоределяем в модели функцию из миксина CopyMixin: вернуть шаблон описания или None."""
        return self.model_line.description_template or None

    def _get_default_name_template(self) -> str:
        default_description_template = ("{model_code} {filter_variety} {brand}; Расход {flow_rate} л/мин; {drain_variety}; Т.окр. {work_temp_min}..{work_temp_max} °С, Рег.давления {pressure_min}..{pressure_max} бар; Порты: {thread}; фильтрация {filtration_rating} мкм;")
        return default_description_template

    def _get_default_description_template(self) -> str:
        default_description_template = ("{model_code} {filter_variety} {brand}; Расход {flow_rate} л/мин; {drain_variety}; Т.окр. {work_temp_min}..{work_temp_max} °С, Материал корпуса: {body_material}, Материал стакана: {bowl_material_text}, Кожух: {protection_material} Порты: {thread}; слив: {drain_port_size}; {gauge_quantity}; фильтрация {filtration_rating} мкм; Диапазон регулировки давления {pressure_min}..{pressure_max} бар; Макс. входное давление {pressure_inlet_max} бар; вес {weight}кг. Настенное крепление: {wall_mounting_included}")
        return default_description_template


