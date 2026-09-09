# cable_glands/models/cg_exd_option.py
from django.db import models
from django.utils.translation import gettext_lazy as _

from options.models import BaseM2MExdThroughOption

from .cg_model_line import CableGlandModelLine


class CableGlandExdOption(BaseM2MExdThroughOption):
    """Взрывозащита, разрешённая для серии кабельных вводов.

    Одна строка = одна КОДИРОВКА (опция выбора), внутри — M2M видов взрывозащиты
    (params.ExdOption). Аналог PosiExdOption у позиционеров.

    Кодировка уникальна в пределах серии (валидация BaseM2MExdThroughOption);
    виды Exd внутри кодировки перечислены M2M ``exd_options``.
    """

    model_line = models.ForeignKey(
        CableGlandModelLine, on_delete=models.CASCADE,
        related_name='exd_options',
        verbose_name=_("Серия кабельных вводов"),
    )

    class Meta:
        verbose_name = _("Взрывозащита для серии кабельных вводов")
        verbose_name_plural = _("Взрывозащита для серий кабельных вводов")
        ordering = ['sorting_order']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'
