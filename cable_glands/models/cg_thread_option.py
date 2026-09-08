# cable_glands/models/cg_thread_option.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union

from params.models import ThreadSizeThroughOption




class CableGlandThreadOption(ThreadSizeThroughOption):
    """Разрешённая резьба для корпуса кабельного ввода (через-модель).

    Связывает корпус (CableGlandBody) со справочником ThreadSize (params):
    перечень резьб (метрическая / NPT / G и т.п.), доступных для данного
    корпуса. unique_together (cable_gland_body, thread_size) — каждая резьба
    для корпуса задаётся один раз.

    Поля inherited от ThreadSizeThroughOption/BaseThroughOption: thread_size,
    encoding (кодировка опции — резерв для артикулов), is_default,
    is_active, sorting_order. Отображается inline в админке корпуса
    (CableGlandBodyAdmin); копируется вместе с корпусом
    (CableGlandBody._copy_custom_relations).
    """
    cable_gland_body = models.ForeignKey(
        'CableGlandBody',
        on_delete=models.CASCADE,
        related_name='cg_thread_body',
        verbose_name=_("Корпус кабельного ввода")
    )

    class Meta:
        verbose_name = _("Резьба модели корпуса кабельного ввода")
        verbose_name_plural = _("Типы резьбы модели корпуса кабельного ввода")
        ordering = ['sorting_order']
        unique_together = ['cable_gland_body', 'thread_size']

    def __str__(self) :
        return f"{self.thread_size.name}"

    @classmethod
    def _get_parent_field_name(cls) -> Optional[str] :
        return 'cable_gland_body'

