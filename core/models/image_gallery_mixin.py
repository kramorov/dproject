# core/models/image_gallery_mixin.py
from django.db import models


class ImageGalleryMixin(models.Model):
    """
    Mixin for models with an image gallery from the media library.

    Adds ``images`` M2M to MediaLibraryItem + access methods.

    Methods:
        get_images()            — all active images, ordered by sorting_order
        get_images_by_category  — filter by MediaCategory.code
        get_default_image()     — image with is_default=True, or first by order
        get_first_image()       — alias for get_default_image()
        get_images_count()      — count of active images
        get_images_description()— string: 'icon title; icon title'
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
    # Access methods
    # ----------------------------------------------------------------

    def get_images(self):
        """All active images, ordered by sorting_order."""
        return self.images.filter(is_active=True).order_by('sorting_order')

    def get_images_by_category(self, code: str):
        """Images of a specific category by MediaCategory.code."""
        return self.images.filter(category__code=code, is_active=True)

    def get_default_image(self):
        """Default image (with is_default flag) or first by sorting_order."""
        img = self.images.filter(
            is_active=True, is_default=True
        ).order_by('sorting_order').first()
        if not img:
            img = self.images.filter(is_active=True).order_by('sorting_order').first()
        return img

    def get_first_image(self):
        """First image for preview / cover."""
        return self.get_default_image()

    def get_images_count(self) -> int:
        """Number of active images."""
        return self.images.filter(is_active=True).count()

    def get_images_description(self) -> str:
        """String for template: 'icon title; icon title'."""
        imgs = list(self.get_images())
        if not imgs:
            return ''
        parts = []
        for img in imgs:
            icon = getattr(img.category, 'icon', ' ') if img.category else ' '
            name = img.title or (img.media_file.name if img.media_file else '-')
            parts.append(f'{icon} {name}')
        return '; '.join(parts)
