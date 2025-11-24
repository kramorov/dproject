# valve_data/models/dimensions/dimension_table_drawing_item.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from media_library.models import MediaLibraryItem
# from valve_dimension_table import ValveDimensionTable



class DimensionTableDrawingItem(models.Model):
    """Промежуточная модель для связи таблицы ВГХ с чертежами и указанием допустимых DN"""

    dimension_table = models.ForeignKey(
        # ValveDimensionTable,
        'valve_data.ValveDimensionTable',  # ← строковая ссылка вместо импорта
        on_delete=models.CASCADE,
        related_name='drawing_relations',
        verbose_name=_("Таблица ВГХ")
    )

    drawing = models.ForeignKey(
        MediaLibraryItem,
        on_delete=models.CASCADE,
        related_name='dimension_table_relations',
        verbose_name=_("Чертеж")
    )

    # Допустимые DN для этого чертежа в контексте таблицы ВГХ
    allowed_dn = models.ManyToManyField(
        'params.DnVariety',
        blank=True,
        related_name='dimension_table_drawings_allowed_dn',
        verbose_name=_("Применимые DN"),
        help_text=_("DN, для которых применим этот чертеж.")
    )

    # Порядок отображения чертежа
    display_order = models.IntegerField(
        default=0,
        verbose_name=_("Порядок отображения"),
        help_text=_("Порядок отображения чертежа в списке")
    )

    # Описание/комментарий для этой конкретной связи
    description = models.TextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Описание чертежа в контексте этой таблицы ВГХ")
    )

    class Meta:
        verbose_name = _("Связь таблицы ВГХ с чертежом")
        verbose_name_plural = _("Связи таблиц ВГХ с чертежами")
        ordering = ['display_order']
        unique_together = ['dimension_table', 'drawing']

    def __str__(self):
        return f"{self.dimension_table.name} - {self.drawing.title}"

    @classmethod
    def get_drawings_for_dn_list(cls, dimension_table, dn_list):
        """
        Получить изображения для списка DN

        Args:
            dimension_table: Экземпляр ValveDimensionTable
            dn_list: Список кодов DN (например ['50', '80', '100'])

        Returns:
            list: Структурированный список изображений, отсортированный по display_order
        """
        drawings = cls.objects.filter(
            dimension_table=dimension_table,
            allowed_dn__code__in=dn_list
        ).select_related('drawing').prefetch_related('allowed_dn').order_by('display_order').distinct()

        structured_drawings = []
        for drawing_item in drawings:
            drawing_data = {
                'id': drawing_item.id,
                'drawing_id': drawing_item.drawing.id,
                'title': drawing_item.drawing.title,
                'description': drawing_item.description or drawing_item.drawing.description,
                'media_file': drawing_item.drawing.media_file.url if drawing_item.drawing.media_file else None,
                'preview_file': drawing_item.drawing.preview_file.url if drawing_item.drawing.preview_file else None,
                'mime_type': drawing_item.drawing.mime_type,
                'display_order': drawing_item.display_order,
                'allowed_dns': [dn.code for dn in drawing_item.allowed_dn.all()],
                'is_image': drawing_item.drawing.mime_type.startswith(
                    'image/') if drawing_item.drawing.mime_type else False
            }
            structured_drawings.append(drawing_data)

        return structured_drawings