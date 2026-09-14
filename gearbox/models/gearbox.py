# gearbox/models/gearbox.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import ImageGalleryMixin, TechDocMixin
from core.models.mixins import CopyMixin, TemplateMixin
from core.models.catalog_serializer import CatalogSerializerMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin, DataSourceType, FilterType, FilterDefinition
from gearbox.models.gb_item_fields import GB_ITEM_TEMPLATE_FIELDS
from materials.models import MaterialGeneral
from params.models import LockingMechanism, IpOption, MountingPlateTypes
from sku.models import SKUMixin


class GearBox(CatalogSerializerMixin, SmartCatalogMixin, CopyMixin, TemplateMixin, ImageGalleryMixin, TechDocMixin, SKUMixin, models.Model):
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

    # ── Реестр полей (единый источник правды) — gb_item_fields.py ──
    TEMPLATE_FIELDS = GB_ITEM_TEMPLATE_FIELDS

    # Составы словарей (по ключам реестра).
    NAME_FIELD_KEYS = (
        'code', 'brand_name', 'body_material', 'ip', 'override_mechanism',
        'locking_mechanism', 'is_declutchable', 'transmission_variety',
        'reduction_ratio', 'max_output_torque', 'max_input_torque', 'weight',
        'handwheel_diameter', 'handwheel_force_nominal', 'interlock',
        'work_temp_min', 'work_temp_max', 'gearbox_output_variety',
        'gearbox_variety', 'turn_angle', 'turn_tuning_limit',
        'mechanical_advantage', 'max_stem_diameter_bottom', 'stem_height_bottom',
        'stem_size_bottom', 'stem_shape_bottom', 'mounting_plate_bottom_list_text',
        'stem_height_top', 'stem_size_top', 'stem_shape_top',
        'mounting_plate_top_list_text', 'efficiency', 'amplification_factor',
    )

    VARS_FIELD_KEYS = (
        'code', 'name', 'model_line_name', 'brand_name', 'body_material',
        'reduction_ratio', 'max_output_torque', 'max_input_torque', 'weight',
        'ip', 'work_temp_min', 'work_temp_max', 'is_declutchable',
        'override_mechanism', 'locking_mechanism', 'transmission_variety',
        'handwheel_diameter', 'handwheel_force_nominal', 'interlock', 'work_temp',
    )

    # SPEC_FIELD_KEYS закомментирован: спецификация задаётся spec_template.
    # SPEC_FIELD_KEYS = (
    #     'model_line_name', 'brand_name', 'body_material', 'ip',
    #     'override_mechanism', 'locking_mechanism', 'is_declutchable',
    #     'transmission_variety', 'reduction_ratio', 'max_output_torque',
    #     'max_input_torque', 'weight', 'handwheel_diameter', 'work_temp',
    # )

    # SPEC_GROUP_TITLES закомментирован: названия групп задаются в spec_template (JSON).
    # SPEC_GROUP_TITLES = {
    #     'general': 'Основные',
    #     'body': 'Корпус',
    #     'conditions': 'Условия эксплуатации',
    # }

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

    @property
    def work_temp_display(self):
        """Диапазон рабочей температуры для отображения."""
        if self.work_temp_min is None:
            return ''
        return f'{self.work_temp_min}...+{self.work_temp_max} °С'

    def copy(self):
        """
        Создаёт копию редуктора.

        Переопределяет ``CopyMixin.copy()``: добавляет суффикс « Копия»
        к названию и сбрасывает ``sorting_order`` и ``is_active``.
        Корпус (body) при копировании расшаривается (не клонируется).
        """
        copied_obj = super().copy(suffix=" Копия", reset_fields=['sorting_order', 'is_active'])
        return copied_obj

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

    def _get_model_line_summary(self) -> dict:
        """Краткая сводка model_line."""
        if not self.model_line:
            return None
        return {
            'id': self.model_line.id,
            'name': self.model_line.name,
            'code': getattr(self.model_line, 'code', '') or '',
            'description': self.model_line.description or '',
            'gearbox_variety': self.model_line.gearbox_variety.name if self.model_line.gearbox_variety else None,
            'gearbox_output_variety': self.model_line.gearbox_output_variety.name if self.model_line.gearbox_output_variety else None,
            'brand': {
                'id': self.model_line.brand.id,
                'name': self.model_line.brand.name,
            } if self.model_line.brand else None,
        }
