# cable_glands/models/cg_body_material_option.py
from django.db import models
from django.utils.translation import gettext_lazy as _

from options.models import BaseThroughOption

from .cg_dicts import CableGlandBodyMaterial
from .cg_model_line import CableGlandModelLine


class CableGlandBodyMaterialOption(BaseThroughOption):
    """Материал корпуса, разрешённый для серии кабельных вводов.

    Through-модель уровня серии: model_line + body_material + encoding/is_default.
    Аналог PosiBodyConnectionOption / PosiLeverOption у позиционеров.

    encoding — код опции для подстановки в артикул; уникален в связке
    «серия + материал + кодировка» (unique_together).
    """

    model_line = models.ForeignKey(
        CableGlandModelLine, on_delete=models.CASCADE,
        related_name='body_material_options',
        verbose_name=_("Серия кабельных вводов"),
    )
    body_material = models.ForeignKey(
        CableGlandBodyMaterial, on_delete=models.CASCADE,
        verbose_name=_("Материал корпуса"),
    )

    class Meta:
        verbose_name = _("Материал корпуса для серии кабельных вводов")
        verbose_name_plural = _("Материалы корпуса для серий кабельных вводов")
        ordering = ['sorting_order']
        unique_together = ['model_line', 'body_material', 'encoding']

    @classmethod
    def _get_parent_field_name(cls):
        return 'model_line'

    def __str__(self):
        return f"{self.body_material} ({self.encoding})"
