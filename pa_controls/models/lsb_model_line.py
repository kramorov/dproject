# pa_controls/models/lsb_model_line.py
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import StructuredDataMixin, EquipmentTypeMixin, TechDocMixin, ImageGalleryMixin
from core.models.cert_doc_mixin import CertDocMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin
from producers.models import Producer, Brands


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
        return [
            {'id': img.id, 'code': img.code or '', 'name': img.name or ''}
            for img in self.images.all()
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