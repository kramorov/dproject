# core/models/image_gallery_mixin.py
from django.db import models


class ImageGalleryMixin(models.Model):
    """
    Миксин для моделей, у которых есть галерея изображений из медиабиблиотеки.
    Добавляет M2M на MediaLibraryItem + методы доступа.

    Использование:
        class PneumaticActuatorModelLine(ImageGalleryMixin, ...):
            ...
    """

    images = models.ManyToManyField(
        'media_library.MediaLibraryItem',
        blank=True,
        related_name='+',
        verbose_name="Изображения",
        help_text="Изображения из медиабиблиотеки"
    )

    class Meta:
        abstract = True

    # ----------------------------------------------------------------
    # Методы доступа
    # ----------------------------------------------------------------

    def get_images(self):
        """Все активные изображения."""
        return self.images.filter(is_active=True)

    def get_images_by_category(self, code: str):
        """
        Изображения определённой категории.
        code — код MediaCategory: 'PHOTO', 'DRAWING', 'SCHEMA', ...
        """
        return self.images.filter(category__code=code, is_active=True)

    def get_first_image(self):
        """Первое изображение — для превью / обложки."""
        return self.images.filter(is_active=True).first()

    def get_images_count(self) -> int:
        """Количество активных изображений."""
        return self.images.filter(is_active=True).count()

    def get_images_description(self) -> str:
        """
        Строка для шаблона описания:
        '🖼️ photo_001.jpg; 📐 scheme_v1.pdf'

        Если изображений нет — пустая строка.
        """
        imgs = list(self.get_images())
        if not imgs:
            return ''

        parts = []
        for img in imgs:
            icon = getattr(img.category, 'icon', '📎') if img.category else '📎'
            name = img.title or (img.media_file.name if img.media_file else '—')
            parts.append(f'{icon} {name}')

        return '; '.join(parts)
