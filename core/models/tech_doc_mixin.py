# core/models/tech_doc_mixin.py
from django.db import models


class TechDocMixin(models.Model):
    """
    Mixin for models with набором технических документов (РЭ, технички) from the media library.
    Adds M2M to MediaLibraryItem + access methods.
    """

    tech_docs = models.ManyToManyField(
        'media_library.MediaLibraryItem',
        blank=True,
        related_name='+',
        verbose_name="Тех.документы",
        help_text="Технические документы"
    )

    class Meta:
        abstract = True

    # ----------------------------------------------------------------
    # Access methods
    # ----------------------------------------------------------------

    def get_tech_docs(self):
        """All active images, ordered by sorting_order."""
        return self.tech_docs.filter(is_active=True).order_by('sorting_order')

    def get_tech_docs_by_category(self, code: str):
        """Images of a specific category by MediaCategory.code."""
        return self.tech_docs.filter(category__code=code, is_active=True)

    def get_tech_docs_description(self) -> str:
        """String for template: 'icon title; icon title'."""
        tech_docs_list = list(self.get_tech_docs())
        if not tech_docs_list:
            return ''
        parts = []
        for doc in tech_docs_list:
            icon = getattr(doc.category, 'icon', ' ') if doc.category else ' '
            name = doc.title or (doc.media_file.name if doc.media_file else '-')
            parts.append(f'{icon} {name}')
        return '; '.join(parts)
