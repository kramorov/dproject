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

    model_line = models.ForeignKey('GearBoxModelLine' , related_name='gear_box_model_line' ,
                                   blank=True ,
                                   null=True ,
                                   on_delete=models.SET_NULL ,
                                   help_text=_('Серия модели редуктора') ,
                                   verbose_name=_("Серия"))

    body = models.ForeignKey(
        'GearBoxBody',
        on_delete=models.SET_NULL,
        null=True,
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
        null=True,
        verbose_name=_("Механизм отключения"),
        help_text=_("Механизм отключения дублера")
    )
    locking_mechanism = models.ForeignKey(
        LockingMechanism,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Механизм блокировки"),
        help_text=_("Механизм блокировки дублера/переключателя")
    )
    is_declutchable = models.BooleanField(
        default=True,
        verbose_name=_("Выключаемый (Declutchable)"),
        help_text=_("Можно ли физически отсоединить штурвал от привода")
    )
    ip = models.ForeignKey(IpOption, on_delete=models.SET_NULL, null=True,
                           related_name='gearbox_ip',
                           help_text=_('Степень защиты IP'),
                           verbose_name=_("IP")
                           )
    # Интерлок (лучше вынести в отдельную модель)
    interlock = models.ForeignKey('GearBoxInterlock', on_delete=models.SET_NULL, null=True, blank=True,related_name='gearbox_interlock',
                           help_text=_('Модель интерлока'),
                           verbose_name=_("Модель интерлока")
                           )
    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict , blank=True ,
        verbose_name=_("Параметры") ,
        help_text=_("signal_type, resistance, range и т.д.")
    )
    class Meta:
        verbose_name = _("Редуктор")
        verbose_name_plural = _("Редукторы")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.name}"

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
            '{flow_rate}': 'flow_rate',
            '{filter_variety}': 'model_line__filter_variety',
            '{pressure_min}': 'model_line__pressure_min',
            '{pressure_max}': 'model_line__pressure_max',
            '{pressure_inlet_max}': 'model_line__pressure_inlet_max',
            '{wall_mounting_included}': 'wall_mounting_included_display',
            '{body_material}': 'model_line__body_material',
            '{bowl_material}': 'model_line__bowl_material',
            '{bowl_material_text}': 'model_line__bowl_material_text',
            '{protection_material}': 'model_line__protection_material',
            '{body_material_specified}': 'body_material_specified',
            '{filter_element_material}': 'filter_element_material',
            '{filtration_rating}': 'filtration_rating',
            '{work_temp_min}': 'model_line__work_temp_min',
            '{work_temp_max}': 'model_line__work_temp_max',
            '{weight}': 'body__weight',
            '{thread}': 'body__thread',
            '{gauge_port_size}': 'body__gauge_port_size',
            '{drain_port_size}': 'body__drain_port_size',
            '{drain_variety}' : 'drain_variety' ,
            '{gauge_quantity}': 'gauge_quantity_display',
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


