# solenoid_valves/models/dv_exd_option.py
from django.db import models
from django.utils.translation import gettext_lazy as _

from options.models import BaseM2MExdThroughOption

from .dv_model_line import DirectionalValveModelLine


class DirectionValveExdOption(BaseM2MExdThroughOption):
    """Взрывозащита, разрешённая для серии распределительных клапанов.

    Одна строка = одна КОДИРОВКА (опция выбора), внутри — M2M видов взрывозащиты
    (params.ExdOption). Аналог CableGlandExdOption у кабельных вводов.

    Кодировка уникальна в пределах серии (валидация BaseM2MExdThroughOption);
    виды Exd внутри кодировки перечислены M2M ``exd_options``.
    """

    model_line = models.ForeignKey(
        DirectionalValveModelLine,
        on_delete=models.CASCADE,
        related_name='exd_options',
        verbose_name=_("Серия распределительных клапанов"),
    )

    class Meta:
        verbose_name = _("Взрывозащита для серии распределительных клапанов")
        verbose_name_plural = _("Взрывозащита для серий распределительных клапанов")
        ordering = ['sorting_order']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'
