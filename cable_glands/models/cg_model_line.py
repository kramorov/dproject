# cable_glands/models/cg_model_line.py

from django.db import models
from django.utils.translation import gettext_lazy as _
# from typing import List, Optional, Tuple, Any, Dict, Union

from core.models import StructuredDataMixin, ImageGalleryMixin, TechDocMixin, EquipmentTypeMixin
from core.models.cert_doc_mixin import CertDocMixin
from core.models.mixins import CopyMixin
from producers.models import Brands, Producer

from params.models import IpOption


class CableGlandModelLine(ImageGalleryMixin, TechDocMixin, CertDocMixin,
                          EquipmentTypeMixin, CopyMixin,
                          StructuredDataMixin, models.Model):
    """Серия кабельных вводов (model line) — «семейство» изделий.

    Роль в иерархии каталога:

        CableGlandModelLine (серия)                  ← эта модель
          └─ CableGlandModelLineItem («модель в серии»: корпус + крепление МР + вес)
               └─ CableGland (артикул каталога: + резьба + материал корпуса)

    На серии живут ОБЩИЕ атрибуты (наследуются всеми артикулами):
      * brand / producer — бренд и производитель;
      * equipment_type — тип оборудования (для SKU/каталога; единственный тип
        на серии, переходно nullable — ужесточить до PROTECT после заполнения);
      * ip — степени защиты IP (M2M на params.IpOption);
      * exd — виды взрывозащиты (through-строка CableGlandExdOption: кодировка + M2M ExdOption);
      * cable_type — тип кабеля (справочник CableType: понятное название +
        булевы атрибуты бронированного кабеля / металлорукава / трубопровода);
      * thread_external / thread_internal — исполнение резьбы присоединения;
      * temp_min / temp_max — диапазон рабочей температуры окружающей среды;
      * gost — соответствие ГОСТ/ТУ/стандартам; extra_params — прочие (JSON).

    Размерная геометрия и варианты резьб относятся НЕ к серии, а к корпусу
    (CableGlandBody) и «модели в серии» (CableGlandModelLineItem) — см. их
    докстринги.

    Шаблоны текста каталога (контракт TemplateMixin, template_mixin.md):
      * name_template / description_template — шаблоны названия и описания
        артикулов (CableGland);
      * model_item_code_template — шаблон автогенерации артикула (code).
    Плейсхолдеры берутся из реестра CableGland.TEMPLATE_FIELDS
    (cg_item_fields.py); в админке серии их показывает
    TemplatePlaceholdersAdminMixin.

    Миксины: ImageGalleryMixin / TechDocMixin / CertDocMixin /
    EquipmentTypeMixin (медиа, документация, сертификаты, тип оборудования),
    CopyMixin (копирование серии вместе с M2M-связями) и StructuredDataMixin.
    """
    name = models.CharField(max_length=200,
                            verbose_name=_("Название"),
                            help_text=_('Название серии кабельных вводов'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код серии кабельных вводов"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание модели корпуса КВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    name_template = models.TextField(blank=True, null=True,
                                     verbose_name=_("Шаблон названия"),
                                     help_text=_('Шаблон для текстового названия серии КВ'))
    description_template = models.TextField(blank=True, null=True,
                                            verbose_name=_("Шаблон описания"),
                                            help_text=_('Шаблон для описания КВ'))
    title_template = models.TextField(blank=True, null=True,
                                      verbose_name=_("Шаблон заголовка"),
                                      help_text=_('Шаблон короткого заголовка для карточки '
                                                  '(плейсхолдеры из реестра CableGland)'))
    spec_template = models.JSONField(default=dict, blank=True,
                                     verbose_name=_("Шаблон спецификации"),
                                     help_text=_('JSON: группы и поля спецификации; пусто — '
                                                 'используется реестр CableGland'))
    model_item_code_template = models.CharField(
        max_length=500, blank=True, null=True,
        verbose_name=_("Шаблон артикула"),
        help_text=_('Шаблон артикула'),
    )
    producer = models.ForeignKey(Producer, related_name='cg_model_line_producer', blank=True,
                                 null=True, on_delete=models.SET_NULL,
                                 help_text=_('Производитель КВ'),
                                 verbose_name=_("Производитель"))
    brand = models.ForeignKey(Brands, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("Бренд"),
                              help_text=_('Бренд (производитель) КВ'))
    # Переопределение EquipmentTypeMixin: на переходный период поле
    # необязательное (SET_NULL); после заполнения данных — ужесточить
    # до PROTECT/обязательного (эталон: PosiModelLine).
    equipment_type = models.ForeignKey(
        'core.EquipmentType',
        blank=True, null=True, on_delete=models.SET_NULL,
        limit_choices_to={'is_active': True},
        verbose_name=_("Тип оборудования"),
        help_text=_('Тип оборудования для SKU/каталога'))
    ip = models.ManyToManyField(IpOption, blank=True,
                                related_name='cable_gland_model_lines',
                                verbose_name=_("IP"),
                                help_text=_('Степени защиты IP'))
    cable_type = models.ForeignKey(
        'CableType',
        blank=True, null=True, on_delete=models.SET_NULL,
        related_name='model_lines',
        verbose_name=_("Тип кабеля"),
        help_text=_('Тип кабеля из справочника (заменяет булевы флаги бронированного/МР/трубопровода)'),
    )
    thread_external = models.BooleanField(blank=True, null=True, verbose_name=_("Наружная резьба"),
                                          help_text=_('Наружная резьба для внешнего присоединения'))
    thread_internal = models.BooleanField(blank=True, null=True, verbose_name=_("Внутренняя резьба"),
                                          help_text=_('Внутренняя резьба для внешнего присоединения'))
    temp_min = models.SmallIntegerField(blank=True, null=True, verbose_name=_("Темп.мин"),
                                        help_text=_('Минимальная температура окружающей среды'))
    temp_max = models.SmallIntegerField(blank=True, null=True, verbose_name=_("Темп.макс"),
                                        help_text=_('Максимальная температура окружающей среды'))
    gost = models.CharField(max_length=1000, blank=True, null=True, verbose_name=_("ГОСТ"),
                            help_text=_('Соответствие ГОСТ, ТУ, другим стандартам - перечень'))
    extra_params = models.JSONField(default=dict, blank=True,
                                    verbose_name=_("Параметры"),
                                    help_text=_("Дополнительные параметры серии"))

    class Meta:
        verbose_name = _("Серия кабельных вводов")
        verbose_name_plural = _("Серии кабельных вводов")
        ordering = ['sorting_order']

    def __str__(self):
        return self.code
