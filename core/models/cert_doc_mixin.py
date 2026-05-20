# core/models/cert_doc_mixin.py
from django.db import models


class CertDocMixin(models.Model):
    """
    Mixin for models для связи с сущностью Сертификат.
    Adds M2M to MediaLibraryItem + access methods.
    """

    cert_docs = models.ManyToManyField(
        'cert_doc.CertData',
        blank=True,
        related_name='+',
        verbose_name="Сертификаты",
        help_text="Сертификаты"
    )

    class Meta:
        abstract = True

    # ----------------------------------------------------------------
    # Access methods
    # ----------------------------------------------------------------

    def get_cert_docs(self):
        """All active images, ordered by sorting_order."""
        return self.cert_docs.filter(is_active=True).order_by('sorting_order')

