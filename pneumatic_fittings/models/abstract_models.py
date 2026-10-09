# pneumatic_fittings/abstract_models.py

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
from pneumatic_fittings.models.pf_item_fields import PF_ITEM_TEMPLATE_FIELDS
from producers.models import Brands , Producer
from sku.models import SKUMixin



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
    body_material = models.ForeignKey(MaterialGeneral, related_name='%(class)s_body_material', blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Корпус'),
                                      verbose_name=_('Тип материала корпуса'))

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

    def __str__(self) :
        return self.name


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

    weight = models.DecimalField(decimal_places=3, max_digits=6,
                                       null=True, blank=True,
                                       help_text=_('Вес, кг'),
                                       verbose_name=_('Вес, кг'))
    width_across_flats = models.SmallIntegerField(blank=True , null=True , verbose_name=_("Ключ, мм") ,
                                        help_text=_('Размер гайки под ключ, мм'))
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

    # ── Рабочее давление / температура (наследуются из серии) ──

    @property
    def pressure_min(self):
        """Эффективное минимальное давление — из серии."""
        ml = self.model_line
        return ml.pressure_min if ml else None

    @property
    def pressure_max_effective(self):
        """Эффективное максимальное давление (глушители — с override)."""
        return self._effective_pressure_max()

    @property
    def temp_min(self):
        """Эффективная минимальная температура — из серии."""
        ml = self.model_line
        return ml.temp_min if ml else None

    @property
    def temp_max(self):
        """Эффективная максимальная температура — из серии."""
        ml = self.model_line
        return ml.temp_max if ml else None

    def _effective_pressure_max(self):
        """Максимальное давление позиции: по умолчанию — из серии.

        Глушители переопределяют: при заданном override (не 0/null) берётся
        фактическое значение позиции, иначе — значение серии.
        """
        ml = self.model_line
        return ml.pressure_max if ml else None

    @property
    def temperature_range_display(self) :
        """Отображаемый диапазон рабочих температур"""
        if self.temp_min is not None and self.temp_max is not None :
            return f'{self.temp_min}..{self.temp_max}'
        return ''

    @property
    def pressure_range_display(self) :
        """Отображаемый диапазон рабочих давлений"""
        if self.pressure_min is not None and self.pressure_max_effective is not None :
            return f'{self.pressure_min}..{self.pressure_max_effective}'
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

