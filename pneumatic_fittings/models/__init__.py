# pneumatic_fittings/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from typing import Dict , List
from core.models.mixins import StructuredDataMixin, TemplateMixin, CopyMixin, LocalizedDictFieldsMixin, LocalizedModelLineMixin
from core.models.config_hash import ConfigHashMixin
from core.models.catalog_serializer import CatalogSerializerMixin
from core.models import ImageGalleryMixin, TechDocMixin, EquipmentTypeMixin
from core.models.cert_doc_mixin import CertDocMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin , FilterDefinition , FilterType , DataSourceType
from materials.models import MaterialGeneral
from params.models import ThreadSize , ThreadInnerOuter , ThreadTypes
from producers.models import Brands , Producer
from sku.models import SKUMixin
from pneumatic_fittings.models.pf_item_fields import PF_ITEM_TEMPLATE_FIELDS


class FittingShape(StructuredDataMixin , LocalizedDictFieldsMixin) :
    name = models.CharField(max_length=100 , verbose_name=_("Название формы"))
    code = models.SlugField(max_length=50 , unique=True , verbose_name=_("Код"))
    description = models.TextField(blank=True , verbose_name=_("Краткое описание"))
    help_text_content = models.TextField(blank=True , verbose_name=_("Особенности применения"))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        verbose_name = "Форма фитинга"
        verbose_name_plural = "Формы фитингов"

    def __str__(self) :
        return self.name


class FittingFixationMethod(StructuredDataMixin , LocalizedDictFieldsMixin) :
    name = models.CharField(max_length=100 , verbose_name=_("Название способа"))
    code = models.SlugField(max_length=50 , unique=True , verbose_name=_("Код"))
    description = models.TextField(blank=True , verbose_name=_("Описание"))
    help_text_content = models.TextField(blank=True , verbose_name=_("Описание для подсказок"))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        verbose_name = "Способ фиксации фитинга"
        verbose_name_plural = "Способы фиксации фитингов"

    def __str__(self) :
        return self.name


class AbstractPneumaticFittingModelLine(LocalizedModelLineMixin, ImageGalleryMixin, TechDocMixin,
                                        CertDocMixin,
                                        EquipmentTypeMixin,
                                        StructuredDataMixin, CopyMixin, models.Model):
    """Общая база серий фитингов/глушителей/заглушек.

    Видозависимые поля (форма/способ фиксации, поворотность) — в конкретных
    сериях (PneumaticFittingModelLine / PneumaticSilencerModelLine / PneumaticPlugModelLine).
    """

    class Meta:
        abstract = True

    name = models.CharField(max_length=100 ,
                            verbose_name=_("Название") ,
                            help_text=_('Текстовое название серии'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код серии"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание серии'))
    name_template = models.CharField(max_length=300 ,
                                     verbose_name=_("Шаблон названия") ,
                                     help_text=_('Шаблон для текстового названия'))
    description_template = models.TextField(blank=True , verbose_name=_("Шаблон описания") ,
                                            help_text=_('Шаблон для описания'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    producer = models.ForeignKey(Producer , related_name='%(class)s_producer' , blank=True ,
                                 null=True ,
                                 on_delete=models.SET_NULL ,
                                 help_text=_('Производитель') ,
                                 verbose_name=_("Производитель"))
    brand = models.ForeignKey(Brands , related_name='%(class)s_brand' , blank=True , null=True ,
                              on_delete=models.SET_NULL ,
                              help_text=_('Бренд') ,
                              verbose_name=_("Бренд"))

    def __str__(self) :
        return self.name


class PneumaticFittingModelLine(AbstractPneumaticFittingModelLine):
    """Серия пневматических фитингов (резьба-трубка).

    Серия = конкретное сочетание «форма + способ фиксации» (прямой цанговый и т.п.),
    поэтому форма и способ задаются здесь, а позиции их наследуют.
    """

    shape = models.ForeignKey(FittingShape , related_name='pneumatic_fitting_model_lines' ,
                              blank=True , null=True ,
                              on_delete=models.SET_NULL ,
                              help_text=_('Форма фитинга') ,
                              verbose_name=_("Форма"))
    fixation_method = models.ForeignKey(FittingFixationMethod , related_name='pneumatic_fitting_model_lines_fixation' ,
                                        blank=True , null=True ,
                                        on_delete=models.SET_NULL ,
                                        help_text=_('Способ фиксации фитинга') ,
                                        verbose_name=_("Способ фиксации"))
    is_swivel = models.BooleanField(default=False ,
                                    verbose_name=_("Поворотный") ,
                                    help_text=_('Поворотное исполнение серии фитингов'))

    class Meta :
        ordering = ['brand' , 'code']
        verbose_name = _('Серия пневматических фитингов')
        verbose_name_plural = _('Серии пневматических фитингов')


class PneumaticSilencerModelLine(AbstractPneumaticFittingModelLine):
    """Серия глушителей пневматических."""

    class Meta :
        ordering = ['brand' , 'code']
        verbose_name = _('Серия глушителей пневматических')
        verbose_name_plural = _('Серии глушителей пневматических')


class PneumaticPlugModelLine(AbstractPneumaticFittingModelLine):
    """Серия заглушек пневматических."""

    class Meta :
        ordering = ['brand' , 'code']
        verbose_name = _('Серия заглушек пневматических')
        verbose_name_plural = _('Серии заглушек пневматических')


class AbstractPneumaticFitting(CatalogSerializerMixin, SmartCatalogMixin,
                               ImageGalleryMixin, TechDocMixin,
                               SKUMixin, EquipmentTypeMixin, ConfigHashMixin,
                               StructuredDataMixin, TemplateMixin, CopyMixin, models.Model):
    """Общая база позиций фитингов/глушителей/заглушек.

    ``model_line`` и видозависимые поля задаются в конкретных моделях.
    """

    TEMPLATE_FIELDS = PF_ITEM_TEMPLATE_FIELDS

    class Meta:
        abstract = True

    name = models.CharField(max_length=300 ,
                            verbose_name=_("Название") ,
                            help_text=_('Текстовое название позиции'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код позиции"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание позиции'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    body_material = models.ForeignKey(MaterialGeneral , related_name='%(class)s_body_material' , blank=True ,
                                      null=True ,
                                      on_delete=models.SET_NULL ,
                                      help_text=_('Корпус') ,
                                      verbose_name=_('Тип материала корпуса'))
    thread = models.ForeignKey(ThreadSize , on_delete=models.SET_NULL , null=True , blank=True ,
                               related_name='%(class)s_thread' ,
                               verbose_name=_("Резьба") ,
                               help_text=_('Резьба'))
    thread_inner_outer = models.ForeignKey(ThreadInnerOuter , on_delete=models.SET_NULL , null=True , blank=True ,
                                           related_name='%(class)s_thread_in_out' ,
                                           verbose_name=_("Резьба наружная или внутренняя") ,
                                           help_text=_('Резьба наружная или внутренняя'))

    pressure_min = models.DecimalField(decimal_places=2 , max_digits=6 ,
                                       null=True , blank=True ,
                                       help_text=_('Минимальное рабочее давление, бар') ,
                                       verbose_name=_('P раб.мин, бар'))
    pressure_max = models.DecimalField(decimal_places=2 , max_digits=6 ,
                                       null=True , blank=True ,
                                       help_text=_('Максимальное рабочее давление, бар') ,
                                       verbose_name=_('P раб.макс, бар'))
    temp_min = models.SmallIntegerField(blank=True , null=True , verbose_name=_("Темп.мин") ,
                                        help_text=_('Минимальная температура окружающей среды'))
    temp_max = models.SmallIntegerField(blank=True , null=True , verbose_name=_("Темп.макс") ,
                                        help_text=_('Максимальная температура окружающей среды'))

    # ── SKUMixin ──

    def get_equipment_type_for_sku(self):
        """Тип оборудования для SKU — берётся из model_line."""
        return self.model_line.equipment_type if self.model_line else None

    def get_brand_for_sku(self):
        """Бренд для SKU — берётся из model_line."""
        return self.model_line.brand if self.model_line else None

    def save(self, *args, **kwargs):
        """Сохраняет модель и синхронизирует номенклатуру (SKU)."""
        self.config_hash = self.compute_config_hash()
        self._check_config_hash_unique()
        super().save(*args, **kwargs)
        self.sync_sku()

    def clean(self):
        """Вид артикула должен совпадать с видом серии (вид = свойство серии)."""
        super().clean()
        if self.model_line_id and self.equipment_type_id:
            ml_eq = self.model_line.equipment_type if self.model_line else None
            if ml_eq is not None and ml_eq.pk != self.equipment_type_id:
                raise ValidationError({
                    'equipment_type': _(
                        'Тип оборудования артикула (%(item)s) не совпадает с типом серии (%(line)s). '
                        'Вид определяется серией — исправьте серию или тип артикула.'
                    ) % {'item': self.equipment_type.code, 'line': ml_eq.code},
                })

    @property
    def temperature_range_display(self) :
        """Отображаемый диапазон рабочих температур"""
        if self.temp_min is not None and self.temp_max is not None :
            return f'{self.temp_min}..{self.temp_max}'
        return ''

    @property
    def pressure_range_display(self) :
        """Отображаемый диапазон рабочих давлений"""
        if self.pressure_min is not None and self.pressure_max is not None :
            return f'{self.pressure_min}..{self.pressure_max}'
        operating_pressure = getattr(self, 'operating_pressure', None)
        if operating_pressure is not None :
            return str(operating_pressure)
        return ''

    def swivel_display(self, locale=None) :
        """Текстовое обозначение поворотности для шаблонов (локализованное)."""
        if self.model_line is None :
            return ''
        is_swivel = getattr(self.model_line, 'is_swivel', False)
        if is_swivel :
            word = {'ru': 'поворотный', 'en': 'swivel', 'cn': '可旋转'}
        else :
            word = {'ru': 'неповоротный', 'en': 'fixed', 'cn': '不可旋转'}
        return word.get(locale or 'ru', word['ru'])

    def _get_name_template_source(self) :
        return self.model_line.name_template if self.model_line else None

    def _get_description_template_source(self) :
        return self.model_line.description_template if self.model_line else None

    @classmethod
    def get_filtered_threads(cls, thread_type_id: int = None) -> List[Dict]:
        """Получить резьбы с опциональной фильтрацией по типу резьбы."""
        queryset = ThreadSize.objects.filter(is_active=True)
        if thread_type_id:
            queryset = queryset.filter(thread_type_id=thread_type_id)
        queryset = queryset.order_by('thread_type', 'sorting_order')
        return [{'id': t.id, 'name': t.name, 'code': t.code or ''} for t in queryset]

    def __str__(self) :
        return self.name


# Общие фильтры (бренд/серия/корпус/резьба/температура) для трёх видов.
_COMMON_FILTER_DEFINITIONS = [
        FilterDefinition(
            param_name='brand_id' ,
            model_field='model_line__brand' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Бренд' ,
            order=1
        ) ,
        FilterDefinition(
            param_name='model_line_id' ,
            model_field='model_line' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Серия' ,
            order=2
        ) ,
        FilterDefinition(
            param_name='body_material_id' ,
            model_field='body_material' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Материал корпуса' ,
            order=3
        ) ,
        FilterDefinition(
            param_name='thread_type_id' ,
            model_field='thread' ,
            is_parent_filter=True ,
            filter_type=FilterType.THREAD_COMPATIBLE ,
            data_source_type=DataSourceType.GLOBAL_MODEL ,
            source_model=ThreadTypes ,
            label='Тип резьбы' ,
            order=4
        ) ,
        FilterDefinition(
            param_name='thread_id' ,
            model_field='thread' ,
            filter_type=FilterType.THREAD_COMPATIBLE ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Резьба' ,
            order=5
        ) ,
        FilterDefinition(
            param_name='thread_inner_outer_id' ,
            model_field='thread_inner_outer' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.FOREIGN_KEY ,
            label='Тип резьбы (нар/внут)' ,
            order=6
        ) ,
        FilterDefinition(
            param_name='temp_min' ,
            model_field='temp_min' ,
            filter_type=FilterType.TEMP_MIN ,
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='Мин. температура (≤)' ,
            order=7
        ) ,
    ]


class PneumaticFitting(AbstractPneumaticFitting):
    """Пневматический фитинг (резьба-трубка, вид 'fitting-thread-pipe')."""

    NAME_FIELD_KEYS = (
        'code', 'brand_name', 'equipment_type', 'temperature_range',
        'shape', 'fixation_method', 'swivel', 'pressure_range',
        'pipe_diameter', 'thread', 'thread_inner_outer',
        'body_material', 'pipe_material', 'pressure_min', 'pressure_max',
        'temp_min', 'temp_max',
    )

    VARS_FIELD_KEYS = (
        'code', 'name', 'model_line_name', 'brand_name',
        'shape', 'fixation_method',
        'thread', 'thread_inner_outer', 'body_material', 'temperature_range',
        'swivel', 'pipe_diameter', 'pipe_material', 'pressure_range',
        'pressure_min', 'pressure_max', 'temp_min', 'temp_max',
    )

    config_hash_fields = (
        'model_line', 'body_material', 'pipe_material',
        'pipe_diameter', 'thread', 'thread_inner_outer',
    )

    model_line = models.ForeignKey(PneumaticFittingModelLine , related_name='pneumaticfitting_items' ,
                                   blank=True , null=True ,
                                   on_delete=models.SET_NULL ,
                                   help_text=_('Серия') ,
                                   verbose_name=_("Серия"))
    pipe_material = models.ForeignKey(MaterialGeneral , related_name='pneumatic_fitting_pipe_material' , blank=True ,
                                      null=True ,
                                      on_delete=models.SET_NULL ,
                                      help_text=_('Трубка') ,
                                      verbose_name=_('Тип материала трубки'))
    pipe_diameter = models.IntegerField(blank=True , null=True ,
                                        help_text=_('Диаметр') ,
                                        verbose_name=_('Диаметр трубки, мм'))

    class Meta :
        ordering = ['pipe_diameter' , 'thread']
        verbose_name = _('Пневматический фитинг')
        verbose_name_plural = _('Пневматические фитинги')

    FILTER_DEFINITIONS = _COMMON_FILTER_DEFINITIONS + [
        FilterDefinition(
            param_name='shape_id' ,
            model_field='model_line__shape' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Форма фитинга' ,
            order=8
        ) ,
        FilterDefinition(
            param_name='fixation_method_id' ,
            model_field='model_line__fixation_method' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Способ фиксации' ,
            order=9
        ) ,
        FilterDefinition(
            param_name='pipe_material_id' ,
            model_field='pipe_material' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Материал трубки' ,
            order=10
        ) ,
        FilterDefinition(
            param_name='pipe_diameter' ,
            model_field='pipe_diameter' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='Диаметр трубки' ,
            order=11
        ) ,
        FilterDefinition(
            param_name='swivel' ,
            model_field='model_line__is_swivel' ,
            filter_type=FilterType.BOOLEAN ,
            data_source_type=DataSourceType.CHOICES ,
            choices=[('true', 'Поворотный'), ('false', 'Неповоротный')] ,
            label='Поворотность' ,
            order=12
        ) ,
    ]

    SEARCH_FIELDS = ['code']
    SELECT_RELATED_FIELDS = [
        'model_line__brand' , 'model_line' , 'model_line__shape' , 'model_line__fixation_method' ,
        'body_material' , 'pipe_material' , 'thread' , 'thread_inner_outer'
    ]


class PneumaticSilencer(AbstractPneumaticFitting):
    """Глушитель пневматический (вид 'fitting-silencer')."""

    NAME_FIELD_KEYS = (
        'code', 'brand_name', 'equipment_type', 'temperature_range',
        'thread', 'thread_inner_outer', 'pressure_range',
        'flow_rate', 'noise_level', 'operating_pressure',
        'body_material', 'pressure_min', 'pressure_max',
        'temp_min', 'temp_max',
    )

    VARS_FIELD_KEYS = (
        'code', 'name', 'model_line_name', 'brand_name',
        'thread', 'thread_inner_outer', 'body_material', 'temperature_range',
        'pressure_range', 'flow_rate', 'noise_level', 'operating_pressure',
        'pressure_min', 'pressure_max', 'temp_min', 'temp_max',
    )

    config_hash_fields = (
        'model_line', 'body_material', 'thread', 'thread_inner_outer',
        'flow_rate', 'noise_level', 'operating_pressure',
    )

    model_line = models.ForeignKey(PneumaticSilencerModelLine , related_name='pneumaticsilencer_items' ,
                                   blank=True , null=True ,
                                   on_delete=models.SET_NULL ,
                                   help_text=_('Серия') ,
                                   verbose_name=_("Серия"))
    flow_rate = models.DecimalField(
        max_digits=10 , decimal_places=2 , blank=True , null=True ,
        verbose_name=_("Пропускная способность") ,
        help_text=_('Пропускная способность глушителя (Норм.л/мин)')
    )
    noise_level = models.DecimalField(
        max_digits=5 , decimal_places=1 , blank=True , null=True ,
        verbose_name=_("Уровень шума") ,
        help_text=_('Уровень шума глушителя (дБ)')
    )
    operating_pressure = models.DecimalField(
        max_digits=8 , decimal_places=2 , blank=True , null=True ,
        verbose_name=_("Рабочее давление") ,
        help_text=_('Максимальное рабочее давление (бар)')
    )

    class Meta :
        ordering = ['thread']
        verbose_name = _('Глушитель пневматический')
        verbose_name_plural = _('Глушители пневматические')

    FILTER_DEFINITIONS = _COMMON_FILTER_DEFINITIONS

    SEARCH_FIELDS = ['code']
    SELECT_RELATED_FIELDS = [
        'model_line__brand' , 'model_line' ,
        'body_material' , 'thread' , 'thread_inner_outer'
    ]


class PneumaticPlug(AbstractPneumaticFitting):
    """Заглушка пневматическая (вид 'fitting-plug')."""

    NAME_FIELD_KEYS = (
        'code', 'brand_name', 'equipment_type', 'temperature_range',
        'thread', 'thread_inner_outer', 'pressure_range',
        'body_material', 'pressure_min', 'pressure_max',
        'temp_min', 'temp_max',
    )

    VARS_FIELD_KEYS = (
        'code', 'name', 'model_line_name', 'brand_name',
        'thread', 'thread_inner_outer', 'body_material', 'temperature_range',
        'pressure_range', 'pressure_min', 'pressure_max', 'temp_min', 'temp_max',
    )

    config_hash_fields = (
        'model_line', 'body_material', 'thread', 'thread_inner_outer',
    )

    model_line = models.ForeignKey(PneumaticPlugModelLine , related_name='pneumaticplug_items' ,
                                   blank=True , null=True ,
                                   on_delete=models.SET_NULL ,
                                   help_text=_('Серия') ,
                                   verbose_name=_("Серия"))

    class Meta :
        ordering = ['thread']
        verbose_name = _('Заглушка пневматическая')
        verbose_name_plural = _('Заглушки пневматические')

    FILTER_DEFINITIONS = _COMMON_FILTER_DEFINITIONS

    SEARCH_FIELDS = ['code']
    SELECT_RELATED_FIELDS = [
        'model_line__brand' , 'model_line' ,
        'body_material' , 'thread' , 'thread_inner_outer'
    ]
