# core/models/equipment_type_mixin.py
from django.db import models
from core.models.equipment_type import EquipmentType

class EquipmentTypeMixin(models.Model):
    """
    Миксин для привязки модели к типу оборудования.
    Добавляет ForeignKey на EquipmentType  и M2M на CertData..
    """
    equipment_type = models.ForeignKey(
        EquipmentType,
        on_delete=models.PROTECT,
        limit_choices_to={'is_active': True},
        verbose_name="Тип оборудования",
        help_text="К какому типу оборудования относится эта запись"
    )
    cert_docs = models.ManyToManyField(
        'cert_doc.CertData' ,
        blank=True ,
        related_name='%(class)s_related' ,
        verbose_name="Сертификаты" ,
        help_text="Сертификаты, применимые к этой серии"
    )

    class Meta:
        abstract = True
