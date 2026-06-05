# core/models/image_gallery_mixin.py
"""
Миксин галереи изображений через ImageGallerySet.

Добавляет FK ``image_gallery`` на ImageGallerySet + методы доступа.
Фолбэк: если у model_line_item нет своей галереи — берётся из model_line.

Заменяет старый подход с голым M2M ``images`` на MediaLibraryItem.
"""
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from storage_manager.services import file_service


class ImageGalleryMixin(models.Model):
    """
    Миксин с FK на ImageGallerySet.

    Поле:
        image_gallery — FK → ImageGallerySet (набор изображений с порядком и default)

    Свойства/методы:
        _gallery            — @cached_property: своя галерея → model_line (фолбэк)
        _get_first_image()  — dict для списков (ProductCard)
        _get_images_section() — list для детальной карточки
        _build_image_dict() — dict из MediaLibraryItem
    """

    image_gallery = models.ForeignKey(
        'media_library.ImageGallerySet',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Галерея изображений"),
        help_text=_("Набор изображений")
    )

    class Meta:
        abstract = True

    # ── cached property: своя галерея → model_line ──

    @cached_property
    def _gallery(self):
        """Галерея: своя → фолбэк на model_line. Кэшируется на инстансе."""
        g = self.image_gallery
        if not g:
            ml = getattr(self, 'model_line', None)
            if ml:
                g = getattr(ml, 'image_gallery', None)
        return g

    # ── методы для CatalogDictMixin ──

    def _get_first_image(self) -> dict | None:
        """Первое изображение — для списков (ProductCard)."""
        g = self._gallery
        if not g:
            return None
        img = g.get_default_image()
        return self._build_image_dict(img) if img else None

    def _get_images_section(self) -> list:
        """Галерея — для детальной карточки."""
        g = self._gallery
        if not g:
            return []
        return [
            self._build_image_dict(item.image)
            for item in g.get_images()
        ]

    def _build_image_dict(self, img) -> dict:
        """Собрать словарь для одного изображения.

        url         — card_800 > card_400 > оригинал (полноразмерный показ, галерея)
        preview_url — card_400 (быстрая загрузка: карточки, начальное состояние галереи)
        thumb_url   — thumb_150 > thumb_80 > card_400 (миниатюры в галерее)
        """
        url = ''
        preview = ''
        thumb = ''
        if img.media_file:
            preview = img.preview_url or ''
            # card_800 для полноразмерного показа
            card_800 = img.variants.filter(role='card', width=800).first()
            if card_800:
                url = file_service.get_file_url(card_800.file_path)
            else:
                card_400 = img.variants.filter(role='card', width=400).first()
                url = file_service.get_file_url(card_400.file_path) if card_400 else img.media_file.url
            # thumb_150 (2x) > thumb_80 > card_400 для миниатюр
            t150 = img.variants.filter(role='thumb', width=150).first()
            if t150:
                thumb = file_service.get_file_url(t150.file_path)
            else:
                t80 = img.variants.filter(role='thumb', width=80).first()
                thumb = file_service.get_file_url(t80.file_path) if t80 else (preview or url)
        return {
            'id': img.id,
            'name': getattr(img, 'name', '') or '',
            'code': getattr(img, 'code', '') or '',
            'url': url,
            'preview_url': preview,
            'thumb_url': thumb,
            'is_default': getattr(img, 'is_default', False),
        }

    # ── deprecated: старые методы для обратной совместимости ──

    def get_images(self):
        """Deprecated. Используйте self._gallery.get_images()."""
        g = self._gallery
        if not g:
            return []
        return [item.image for item in g.get_images()]

    def get_first_image(self):
        """Deprecated. Используйте self._get_first_image()."""
        return self._get_first_image()