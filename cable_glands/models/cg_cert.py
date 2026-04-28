# cable_glands/models/cg_cert.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union

from cable_glands.models import CableGlandModelLine
from cert_doc.models import AbstractCertRelation
from core.models import StructuredDataMixin
from producers.models import Producer, Brands

from params.models import ThreadSize , IpOption , ThreadSizeThroughOption
from params.exd_models import ExdOption


class CableGlandModelLineCertRelation(AbstractCertRelation) :
    """
    Связь сертификатов с сериями пневмоприводов.
    """
    model_line = models.ForeignKey(
        CableGlandModelLine ,  # Замените на реальный путь к модели Project
        on_delete=models.CASCADE ,
        verbose_name=_("Серия кабельных вводов") ,
        related_name='cert_data_cg_model_line'
    )

    class Meta(AbstractCertRelation.Meta) :
        verbose_name = _("Связь сертификата с серией кабельных вводов")
        verbose_name_plural = _("Связи сертификатов с сериями кабельных вводов")
        unique_together = ['cert_data' , 'model_line']

    def get_related_object(self) :
        return self.model_line