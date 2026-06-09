# documents/views/__init__.py
from .document_journal import BaseDocumentJournalView
from .document_detail import BaseDocumentDetailView

__all__ = [
    'BaseDocumentJournalView',
    'BaseDocumentDetailView',
]
