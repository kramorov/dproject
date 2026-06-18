# svg_converter/models.py
"""
SvgConversionSession — временная сессия конвертации в SVG.

Хранит загруженный файл, координаты области выделения и результат в SVG.
После обработки сессия может быть удалена.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class SvgConversionSession(models.Model):
    """Временная сессия: загруженный файл → SVG."""

    original_file = models.FileField(
        upload_to='svg_converter/originals/',
        verbose_name=_('Исходный файл'),
    )
    original_filename = models.CharField(
        max_length=255, blank=True,
        verbose_name=_('Имя исходного файла'),
    )

    # Размеры оригинала (заполняются при загрузке)
    original_width = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Ширина'))
    original_height = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Высота'))

    # Область выделения (в пикселях, относительно оригинала)
    region_x = models.FloatField(null=True, blank=True, verbose_name=_('X области'))
    region_y = models.FloatField(null=True, blank=True, verbose_name=_('Y области'))
    region_w = models.FloatField(null=True, blank=True, verbose_name=_('Ширина области'))
    region_h = models.FloatField(null=True, blank=True, verbose_name=_('Высота области'))

    # Параметры трассировки
    color_mode = models.CharField(
        max_length=20,
        choices=[('bw', 'Чёрно-белый'), ('color', 'Цветной')],
        default='bw',
        verbose_name=_('Режим цвета'),
    )
    threshold = models.PositiveSmallIntegerField(
        default=128,
        verbose_name=_('Порог бинаризации'),
        help_text=_('0–255, по умолчанию 128'),
    )

    # Результат
    svg_content = models.TextField(
        blank=True,
        verbose_name=_('SVG-содержимое'),
    )
    svg_file = models.FileField(
        upload_to='svg_converter/results/',
        blank=True, null=True,
        verbose_name=_('SVG-файл'),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Создана'))

    class Meta:
        verbose_name = _('Сессия SVG-конвертации')
        verbose_name_plural = _('Сессии SVG-конвертации')

    def __str__(self):
        return f'SVG session #{self.id} ({self.original_filename or "—"})'

    @property
    def is_pdf(self):
        return self.original_filename.lower().endswith('.pdf') if self.original_filename else False
