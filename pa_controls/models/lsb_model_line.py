# pa_controls/models/lsb_model_line.py
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import StructuredDataMixin, EquipmentTypeMixin, TechDocMixin, ImageGalleryMixin
from core.models.cert_doc_mixin import CertDocMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin
from producers.models import Producer, Brands
from options.models import BaseM2MExdThroughOption


class LimitSwitchModelLine(ImageGalleryMixin, TechDocMixin, CertDocMixin,EquipmentTypeMixin, SmartCatalogMixin,  StructuredDataMixin, models.Model):
    """
    Серия БКВ
    """

    name = models.CharField(max_length=200,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название серии БКВ'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код клапана"))

    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание серии БКВ'))
    name_template = models.TextField(blank=True, null=True,
                                     verbose_name=_("Шаблон названия"),
                                     help_text=_('Шаблон для текстового названия БКВ'))
    description_template = models.TextField(blank=True, null=True,
                                            verbose_name=_("Шаблон описания"),
                                            help_text=_('Шаблон для описания БКВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    producer = models.ForeignKey(Producer, related_name='limit_switch_model_line_producer', blank=True,
                                 null=True,
                                 on_delete=models.SET_NULL,
                                 help_text=_('Производитель БКВ'),
                                 verbose_name=_("Производитель"))
    brand = models.ForeignKey(Brands, related_name='limit_switch_model_line_brand', blank=True, null=True,
                              on_delete=models.SET_NULL,
                              help_text=_('Бренд БКВ'),
                              verbose_name=_("Бренд"))
    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Параметры"),
        help_text=_("signal_type, resistance, range и т.д.")
    )

    class Meta:
        ordering = ['sorting_order', 'code']
        verbose_name = _('Серия БКВ')
        verbose_name_plural = _('Серии БКВ')

    def __str__(self):
        return self.name

    # ── M2M-сериализаторы: id, code, name ──

    def get_images_data(self):
        """Изображения → [{id, code, name}]"""
        g = self._gallery
        if not g:
            return []
        return [
            {'id': item.image.id, 'code': item.image.code or '', 'name': item.image.name or ''}
            for item in g.get_images()
        ]

    def get_tech_docs_data(self):
        """Техдокументация → [{id, code, name}]"""
        return [
            {'id': doc.id, 'code': doc.code or '', 'name': doc.name or ''}
            for doc in self.tech_docs.all()
        ]

    def get_cert_docs_data(self):
        """Сертификаты → [{id, code, name}]"""
        return [
            {'id': cert.id, 'code': cert.code or '', 'name': cert.name or ''}
            for cert in self.cert_docs.all()
        ]


class LimitSwitchExdOption(BaseM2MExdThroughOption):
    """Взрывозащита, разрешённая для серии БКВ.

    Through-строка уровня серии ``LimitSwitchModelLine`` по схеме M2M
    (аналог ``PosiExdOption`` у позиционеров):

      * одна строка = одна КОДИРОВКА (опция выбора для артикула);
      * внутри кодировки через M2M ``exd_options`` перечислены все виды
        ``params.ExdOption``, которые её разделяют;
      * «общепром» представляется строкой с пустым M2M, «Ex» — строкой
        с непустым M2M.

    Поле ``exd_options`` наследуется из ``BaseM2MExdThroughOption`` и получает
    обратное имя ``limitswitchexdoption_exd_rows`` на ``params.ExdOption``.

    Значения копируются в ``LimitSwitchBox.exd`` при сохранении нового БКВ
    (см. ``ExdOptionsConsumerMixin._sync_exd_options_from_model_line``).
    """
    model_line = models.ForeignKey(
        LimitSwitchModelLine, on_delete=models.CASCADE,
        related_name='exd_options',
        verbose_name=_("Серия БКВ")
    )

    class Meta:
        verbose_name = _("Взрывозащита для серии БКВ")
        verbose_name_plural = _("Взрывозащита для серий БКВ")
        ordering = ['sorting_order']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'