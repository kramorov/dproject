# gearbox/models/gearbox.py
from typing import Dict, List, Any

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import ImageGalleryMixin, TechDocMixin
from core.models.mixins import CopyMixin, TemplateMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin, DataSourceType, FilterType, FilterDefinition
from materials.models import MaterialGeneral
from params.models import LockingMechanism, IpOption, MountingPlateTypes
from sku.models import SKUMixin


class GearBox(SmartCatalogMixin, CopyMixin, TemplateMixin, ImageGalleryMixin, TechDocMixin, SKUMixin, models.Model):
    """
    Модель редуктора (каталог).

    Наследует:
    - ``SmartCatalogMixin`` — фильтрация и поиск в каталоге
    - ``CopyMixin`` — копирование через админку
    - ``TemplateMixin`` — генерация названия/описания по шаблону из model_line
    - ``ImageGalleryMixin`` — галерея изображений (поле ``images``)
    - ``TechDocMixin`` — техническая документация (поле ``tech_docs``)
    - ``SKUMixin`` — привязка к номенклатуре (поле ``sku``, автосинхронизация)

    Если у конкретного редуктора нет своих изображений, страница каталога
    подхватывает их из ``GearBoxModelLine.images``.
    """
    name = models.TextField(blank=True,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название модели редуктора'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код модели редуктора"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание модели редуктора'))

    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    model_line = models.ForeignKey('gearbox.GearBoxModelLine', related_name='gear_box_model_line',
                                   blank=True,
                                   null=True,
                                   on_delete=models.SET_NULL,
                                   help_text=_('Серия модели редуктора'),
                                   verbose_name=_("Серия"))

    body = models.ForeignKey(
        'gearbox.GearBoxBody',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_("Корпус редуктора"),
        help_text=_("Корпус редуктора с писанием свойств")
    )
    # Материал корпуса - для фильтров
    body_material = models.ForeignKey(MaterialGeneral, related_name='gearbox_body_material',
                                      blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Корпус'),
                                      verbose_name=_('Тип материала корпуса'))

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
        blank=True, null=True,
        verbose_name=_("Механизм отключения"),
        help_text=_("Механизм отключения дублера")
    )
    locking_mechanism = models.ForeignKey(
        LockingMechanism,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_("Механизм блокировки"),
        help_text=_("Механизм блокировки дублера/переключателя")
    )
    DECLUTCHABLE_CHOICES = (
        ('yes', _('расцепляемый')),
        ('no', _('не расцепляемый')),
    )

    is_declutchable = models.CharField(
        max_length=3,
        choices=DECLUTCHABLE_CHOICES,
        default='yes',
        verbose_name=_("Расцепляемый (Declutchable)"),
        help_text=_("Можно ли физически отсоединить штурвал от привода")
    )
    ip = models.ForeignKey(IpOption, on_delete=models.SET_NULL, blank=True, null=True,
                           related_name='gearbox_ip',
                           help_text=_('Степень защиты IP'),
                           verbose_name=_("IP")
                           )
    # Интерлок
    interlock = models.ForeignKey('gearbox.GearBoxInterlock', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='gearbox_interlock',
                                  help_text=_('Модель интерлока'),
                                  verbose_name=_("Модель интерлока")
                                  )
    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict, blank=True, null=True,
        verbose_name=_("Параметры"),
        help_text=_("signal_type, resistance, range и т.д.")
    )

    class Meta:
        verbose_name = _("Редуктор")
        verbose_name_plural = _("Редукторы")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.name}"

    # ── SKUMixin ──

    def get_equipment_type_for_sku(self):
        """Тип оборудования для SKU — берётся из model_line."""
        return self.model_line.equipment_type

    def get_brand_for_sku(self):
        """Бренд для SKU — берётся из model_line."""
        return self.model_line.brand

    def save(self, *args, **kwargs):
        """
        Сохраняет модель и синхронизирует номенклатуру (SKU).

        Вызывает ``sync_sku()`` после сохранения — создаёт новую SKU
        или «подхватывает» существующую по коду, обогащая её полями модели.
        """
        super().save(*args, **kwargs)
        self.sync_sku()

    @property
    def is_declutchable_display(self):
        return dict(self.DECLUTCHABLE_CHOICES).get(self.is_declutchable, '')

    def copy(self):
        """
        Создаёт копию редуктора.

        Переопределяет ``CopyMixin.copy()``: добавляет суффикс « Копия»
        к названию и сбрасывает ``sorting_order`` и ``is_active``.
        Корпус (body) при копировании расшаривается (не клонируется).
        """
        copied_obj = super().copy(suffix=" Копия", reset_fields=['sorting_order', 'is_active'])
        return copied_obj

    def _get_data_dict(self) -> Dict[str, str]:
        """
        Словарь плейсхолдер → путь к атрибуту для шаблонов названия/описания.

        Используется ``TemplateMixin`` для подстановки значений в шаблоны
        ``name_template`` и ``description_template`` из model_line.

        Ключи — плейсхолдеры вида ``{model_code}``, значения — dotted-пути
        к атрибутам модели (поддерживает ``__`` для связанных полей).
        """
        return {
            '{model_code}': 'code',
            '{brand}': 'model_line__brand',
            '{gearbox_output_variety}': 'model_line__gearbox_output_variety',
            '{gearbox_variety}': 'model_line__gearbox_variety',
            '{turn_angle}': 'model_line__turn_angle',
            '{turn_tuning_limit}': 'model_line__turn_tuning_limit',
            '{weight}': 'body__weight',
            '{mechanical_advantage}': 'body__mechanical_advantage',
            '{max_stem_diameter_bottom}': 'body__max_stem_diameter_bottom',
            '{stem_height_bottom}': 'body__stem_height_bottom',
            '{stem_size_bottom}': 'body__stem_size_bottom',
            '{stem_shape_bottom}': 'body__stem_shape_bottom',
            '{mounting_plate_bottom_list_text}': 'body__mounting_plate_bottom_list_text',
            '{stem_height_top}': 'body__stem_height_top',
            '{stem_size_top}': 'body__stem_size_top',
            '{stem_shape_top}': 'body__stem_shape_top',
            '{mounting_plate_top_list_text}': 'body__mounting_plate_top_list_text',
            '{handwheel_diameter}': 'body__handwheel_diameter',
            '{handwheel_force_nominal}': 'body__handwheel_force_nominal',
            '{max_output_torque}': 'body__max_output_torque',
            '{max_input_torque}': 'body__max_input_torque',
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
        """
        Шаблон названия из model_line.

        Переопределяет ``TemplateMixin._get_name_template_source()``.
        Если шаблон не задан — возвращает None (используется стандартное название).
        """
        return self.model_line.name_template or None

    def _get_description_template_source(self):
        """
        Шаблон описания из model_line.

        Переопределяет ``TemplateMixin._get_description_template_source()``.
        Если шаблон не задан — возвращает None (используется стандартное описание).
        """
        return self.model_line.description_template or None

    def _get_default_name_template(self) -> str:
        """
        Дефолтный шаблон названия (заглушка — для редукторов не используется).

        В реальности название редуктора задаётся шаблоном из model_line,
        этот метод — fallback из TemplateMixin.
        """
        return "{model_code} {brand} {gearbox_variety}"

    def _get_default_description_template(self) -> str:
        """
        Дефолтный шаблон описания (заглушка — для редукторов не используется).

        В реальности описание редуктора задаётся шаблоном из model_line,
        этот метод — fallback из TemplateMixin.
        """
        return "{model_code} {brand} {gearbox_variety} {gearbox_output_variety}"

    # FILTER_DEFINITIONS, M2M_FILTER_CONFIG, SEARCH_FIELDS
    # перенесены в gearbox/services/filters.py

    def to_dict(self) -> Dict[str, Any]:
        """
        Сериализация редуктора в словарь для API (SmartCatalogMixin).

        Возвращает полную структуру: базовые поля, model_line, ip, корпус
        (через ``GearBoxBody.api_dict()``), изображения, extra_params.
        Используется ``SmartCatalogMixin.filter_by_params()`` для выдачи
        каталога с фильтрами.
        """
        return {
            # Базовые поля
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'sorting_order': self.sorting_order,
            'is_active': self.is_active,

            # Прямые связи
            'model_line': {
                'id': self.model_line.id,
                'name': self.model_line.name,
                'code': getattr(self.model_line, 'code', '')
            } if self.model_line else None,

            'override_mechanism': {
                'id': self.override_mechanism.id,
                'name': self.override_mechanism.name,
            } if self.override_mechanism else None,

            'locking_mechanism': {
                'id': self.locking_mechanism.id,
                'name': self.locking_mechanism.name,
            } if self.locking_mechanism else None,

            'ip': {
                'id': self.ip.id,
                'name': self.ip.name,
                'code': getattr(self.ip, 'code', '')
            } if self.ip else None,

            'work_temp_min': self.work_temp_min,
            'work_temp_max': self.work_temp_max,
            'is_declutchable': self.is_declutchable,
            'is_declutchable_display': self.is_declutchable_display,

            # Изображения
            'images': [
                {
                    'id': img.id,
                    'title': img.title,
                    'url': img.media_file.url if img.media_file else '',
                    'preview_url': img.preview_file.url if img.preview_file else '',
                    'is_default': img.is_default,
                    'sorting_order': img.sorting_order,
                }
                for img in self.get_images()
            ],

            # Дополнительные параметры
            'extra_params': self.extra_params or {},

            # Корпус - используем метод api_dict() модели корпуса
            'body': self.body.api_dict() if self.body else None,

            # Материал корпуса (текстовое поле из GearBox, а не из корпуса)
            'body_material_text': self.body_material_text,
        }
