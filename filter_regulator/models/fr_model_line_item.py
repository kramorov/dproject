# filter_regulator/models/fr_model_line_item.py

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import ImageGalleryMixin, TechDocMixin
from core.models.mixins import CopyMixin, TemplateMixin
from core.models.catalog_serializer import CatalogSerializerMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin, FilterDefinition, FilterType, DataSourceType
from filter_regulator.models import FilterRegulatorBody
from filter_regulator.models.fr_model_line import FilterRegulatorModelLine
from filter_regulator.models.fr_options import FilterRegulatorVariety, DrainVariety
from filter_regulator.models.fr_item_fields import FR_ITEM_TEMPLATE_FIELDS
from sku.models import SKUMixin


class FilterRegulator(
    CatalogSerializerMixin,
    CopyMixin,
    ImageGalleryMixin,
    TechDocMixin,
    SmartCatalogMixin,
    TemplateMixin,
    SKUMixin,
    models.Model,
):
    """Модель фильтр-регулятора (каталог)"""

    # ── Реестр полей (единый источник правды) — fr_item_fields.py ──
    TEMPLATE_FIELDS = FR_ITEM_TEMPLATE_FIELDS

    # Составы словарей (по ключам реестра).
    NAME_FIELD_KEYS = (
        'code', 'brand_name', 'flow_rate', 'filter_variety',
        'pressure_min', 'pressure_max', 'pressure_inlet_max',
        'wall_mounting_included', 'body_material', 'bowl_material',
        'protection_material', 'filter_element_material', 'filtration_rating',
        'work_temp_min', 'work_temp_max', 'weight', 'thread',
        'gauge_port_size', 'drain_port_size', 'drain_variety', 'gauge_quantity',
    )

    VARS_FIELD_KEYS = (
        'code', 'name', 'model_line_name', 'brand_name', 'filter_variety',
        'body_material', 'bowl_material', 'protection_material', 'ip',
        'work_temp', 'pressure_range', 'pressure_inlet_max', 'weight',
        'thread', 'gauge_port_size', 'drain_port_size', 'filtration_rating',
        'flow_rate', 'filter_element_material', 'wall_mounting_included',
        'has_shut_off_valve',
    )

    # SPEC_FIELD_KEYS закомментирован: спецификация задаётся spec_template.
    # SPEC_FIELD_KEYS = (
    #     'model_line_name', 'brand_name', 'filter_variety', 'body_material',
    #     'bowl_material', 'protection_material', 'ip', 'filtration_rating',
    #     'flow_rate', 'filter_element_material',
    #     'pressure_range', 'pressure_inlet_max',
    #     'weight', 'thread', 'gauge_port_size', 'drain_port_size',
    #     'wall_mounting_included', 'has_shut_off_valve',
    #     'work_temp',
    # )

    # SPEC_GROUP_TITLES закомментирован: названия групп задаются в spec_template (JSON).
    # SPEC_GROUP_TITLES = {
    #     'general': 'Основные',
    #     'pressure': 'Давление',
    #     'body_specs': 'Корпус',
    #     'conditions': 'Условия эксплуатации',
    # }

    name = models.TextField(blank=True,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название модели фильтр-регулятора'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код модели фильтр-регулятора"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание модели фильтр-регулятора'))

    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    GAUGE_CHOICES = [
        (0, _('Без манометра')),
        (1, _('1 манометр в комплекте')),
        (2, _('2 манометра в комплекте')),
    ]
    gauge_quantity = models.IntegerField(
        choices=GAUGE_CHOICES,
        default=1,
        verbose_name=_("Комплектация манометром")
    )

    model_line = models.ForeignKey(FilterRegulatorModelLine, related_name='filter_model_line',
                                   blank=True,
                                   null=True,
                                   on_delete=models.SET_NULL,
                                   help_text=_('Серия модели фильтр-регулятора'),
                                   verbose_name=_("Серия"))

    body = models.ForeignKey(FilterRegulatorBody, related_name='filter_body',
                             blank=True,
                             null=True,
                             on_delete=models.SET_NULL,
                             help_text=_('Корпус фильтр-регулятора'),
                             verbose_name=_("Корпус"))

    ip = models.ForeignKey('params.IpOption', related_name='filter_regulator_ip',
                           blank=True, null=True,
                           on_delete=models.SET_NULL,
                           verbose_name=_("Степень защиты IP"))

    body_material = models.ForeignKey('materials.MaterialGeneral',
                                      related_name='filter_regulator_body_material',
                                      blank=True, null=True,
                                      on_delete=models.SET_NULL,
                                      verbose_name=_('Материал корпуса'))

    work_temp_min = models.IntegerField(
        null=True, blank=True, default=-40,
        help_text=_('Минимальная рабочая температура, °С'),
        verbose_name=_('Т раб.мин, °С')
    )
    work_temp_max = models.IntegerField(
        null=True, blank=True, default=120,
        help_text=_('Максимальная рабочая температура, °С'),
        verbose_name=_('Т раб.макс, °С'))

    filtration_rating = models.DecimalField(
        max_digits=5, decimal_places=1,
        null=True, blank=True,
        verbose_name=_("Тонкость фильтрации (мкм)")
    )
    MATERIAL_CHOICES = [
        ('bronze', 'Спеченная бронза'),
        ('plastic', 'Пористый полимер'),
        ('ss', 'Нержавеющая сетка'),
    ]
    filter_element_material = models.CharField(max_length=20, choices=MATERIAL_CHOICES,
                                               verbose_name=_("Материал фильтрующего элемента"))

    flow_rate = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name=_("Макс. расход (л/мин)")
    )
    WALL_MOUNTING_CHOICES = [
        ('no', 'Нет'),
        ('yes', 'В комплекте'),
    ]
    wall_mounting_included = models.CharField(max_length=20, choices=WALL_MOUNTING_CHOICES, default='yes',
                                              verbose_name=_("Настенное крепление в комплекте"))
    has_shut_off_valve = models.BooleanField(default=False, verbose_name=_("Отсечной клапан в комплекте"))

    drain_variety = models.ForeignKey(DrainVariety, related_name='filter_drain_variety',
                                      blank=True, null=True,
                                      on_delete=models.SET_NULL,
                                      verbose_name=_("Слив"))

    extra_params = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Параметры"),
        help_text=_("signal_type, resistance, range и т.д.")
    )

    class Meta:
        verbose_name = _("Фильтр-регулятор")
        verbose_name_plural = _("Фильтр-регуляторы")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.name} ({self.code})"

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

    def copy(self):
        return super().copy(suffix=" Копия", reset_fields=[])

    @property
    def gauge_quantity_display(self):
        return self.get_gauge_quantity_display()

    @property
    def wall_mounting_included_display(self):
        return self.get_wall_mounting_included_display()

    @property
    def filter_element_material_display(self):
        """Отображаемое значение материала фильтрующего элемента."""
        return self.get_filter_element_material_display() if self.filter_element_material else ''

    @property
    def has_shut_off_valve_display(self):
        """Отображаемое значение наличия отсечного клапана."""
        return 'Да' if self.has_shut_off_valve else 'Нет'

    @property
    def work_temp_display(self):
        """Диапазон рабочей температуры для отображения."""
        if self.work_temp_min is None:
            return ''
        return f'{self.work_temp_min}...+{self.work_temp_max} °С'

    @property
    def pressure_range_display(self):
        """Диапазон регулировки выходного давления (из серии)."""
        ml = self.model_line
        if ml and ml.pressure_min is not None:
            return f'{ml.pressure_min}...{ml.pressure_max}'
        return ''

    # ── TemplateMixin helpers ──

    def _get_name_template_source(self):
        return self.model_line.name_template or None

    def _get_description_template_source(self):
        return self.model_line.description_template or None

    def _get_default_name_template(self) -> str:
        return (
            "{model_code} {filter_variety} {brand}; "
            "Расход {flow_rate} л/мин; {drain_variety}; "
            "Т.окр. {work_temp_min}..{work_temp_max} °С, "
            "Рег.давления {pressure_min}..{pressure_max} бар; "
            "Порты: {thread}; фильтрация {filtration_rating} мкм;"
        )

    def _get_default_description_template(self) -> str:
        return (
            "{model_code} {filter_variety} {brand}; "
            "Расход {flow_rate} л/мин; {drain_variety}; "
            "Т.окр. {work_temp_min}..{work_temp_max} °С, "
            "Материал корпуса: {body_material}, "
            "Материал стакана: {bowl_material}, "
            "Кожух: {protection_material} "
            "Порты: {thread}; слив: {drain_port_size}; "
            "{gauge_quantity}; фильтрация {filtration_rating} мкм; "
            "Диапазон регулировки давления {pressure_min}..{pressure_max} бар; "
            "Макс. входное давление {pressure_inlet_max} бар; "
            "вес {weight}кг. "
            "Настенное крепление: {wall_mounting_included}"
        )

    def _get_model_line_summary(self) -> dict:
        if not self.model_line:
            return None
        ml = self.model_line
        return {
            'id': ml.id,
            'name': ml.name,
            'code': getattr(ml, 'code', '') or '',
            'description': ml.description or '',
            'filter_variety': ml.filter_variety.name if ml.filter_variety else None,
            'brand': {
                'id': ml.brand.id,
                'name': ml.brand.name,
            } if ml.brand else None,
        }