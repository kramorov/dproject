# documents/models/__init__.py
"""
Пакет моделей приложения documents.

Экспортирует:
    AbstractDocument      — абстрактный документ (заголовок + статусная модель)
    AbstractDocumentItem  — абстрактная строка табличной части
    DocumentNumerator     — универсальный нумератор с атомарным инкрементом
"""
from .abstract_document import AbstractDocument
from .abstract_document_item import AbstractDocumentItem
from .document_numerator import DocumentNumerator

__all__ = [
    'AbstractDocument',
    'AbstractDocumentItem',
    'DocumentNumerator',
]
