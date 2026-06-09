# documents/views/document_journal.py
"""
BaseDocumentJournalView — базовый журнал документов.

GET  — отфильтрованный список документов с пагинацией.
POST — создать новый документ.

Использует FilterDefinition из DocumentJournalConfig для фильтрации.
Формат ответа совместим с useCatalog.js на фронте.

Подкласс должен задать:
    journal_config = DocumentJournalConfig(...)

Опционально переопределить:
    get_queryset()       — базовый queryset
    apply_filters()      — кастомная фильтрация
    serialize_item()     — сериализация одного документа
    get_create_fields()  — поля для создания документа
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils.timezone import now

from documents.catalog.config import DocumentJournalConfig


class BaseDocumentJournalView(APIView):
    """
    Журнал документов.

    GET:
        ?status=draft&date_from=2026-01-01&date_to=2026-12-31&search=...
        &limit=50&offset=0

    POST:
        {name: "...", ...}  →  создаёт документ со статусом DRAFT
    """

    permission_classes = [AllowAny]
    journal_config: DocumentJournalConfig = None

    # ── GET ──

    def get_queryset(self):
        """Базовый queryset. Подкласс может переопределить."""
        config = self.journal_config
        qs = config.document_model.objects.filter(is_active=True).exclude(
            status='deleted'
        )
        if config.select_related:
            qs = qs.select_related(*config.select_related)
        if config.prefetch_fields:
            qs = qs.prefetch_related(*config.prefetch_fields)
        return qs

    def apply_filters(self, qs, params):
        """
        Применить фильтры к queryset на основе FilterDefinition.

        Обходит self.journal_config.filter_definitions и для каждой строит
        Q-условие через _build_filter_condition().
        """
        from django.db.models import Q
        from core.models.filter_definition import FilterType

        for fd in self.journal_config.filter_definitions:
            value = params.get(fd.param_name, '').strip()
            if not value:
                continue

            condition = self._build_filter_condition(fd, value)
            if condition:
                qs = qs.filter(condition)

        # Поиск по нескольким полям (если есть search_fields и не обработан FilterDefinition)
        search = params.get('search', '').strip()
        if search and self.journal_config.search_fields:
            search_q = Q()
            for field in self.journal_config.search_fields:
                search_q |= Q(**{f'{field}__icontains': search})
            qs = qs.filter(search_q)

        return qs

    def _build_filter_condition(self, fd, value):
        """Построить Q-условие для одного FilterDefinition."""
        from django.db.models import Q
        from core.models.filter_definition import FilterType

        ft = fd.filter_type
        field = fd.model_field

        if ft == FilterType.EXACT or ft == FilterType.CHOICE:
            return Q(**{field: value})
        elif ft == FilterType.CONTAINS:
            return Q(**{f'{field}__icontains': value})
        elif ft == FilterType.MIN:
            return Q(**{f'{field}__gte': value})
        elif ft == FilterType.MAX:
            return Q(**{f'{field}__lte': value})
        elif ft == FilterType.BOOLEAN:
            is_true = value.lower() in ('true', '1', 'yes')
            return Q(**{field: is_true})

        return None

    def serialize_item(self, doc):
        """
        Сериализовать один документ для списка.

        По умолчанию вызывает doc.get_compact_data().
        Подкласс может переопределить для дополнительных полей.
        """
        return doc.get_compact_data()

    def get(self, request):
        """Список документов с фильтрацией и пагинацией."""
        config = self.journal_config
        if not config:
            return Response({'error': 'journal_config not set'}, status=500)

        qs = self.get_queryset()
        qs = self.apply_filters(qs, request.query_params)

        total = qs.count()

        # Пагинация
        try:
            limit = int(request.query_params.get('limit', 50))
            offset = int(request.query_params.get('offset', 0))
        except (TypeError, ValueError):
            limit = 50
            offset = 0

        qs = qs[offset:offset + limit]

        data = [self.serialize_item(doc) for doc in qs]

        return Response({
            'total': total,
            'count': len(data),
            'data': data,
        })

    # ── POST ──

    def get_create_fields(self, data):
        """
        Извлечь поля для создания документа из request.data.

        Возвращает словарь kwargs для document_model.objects.create().
        Подкласс ДОЛЖЕН переопределить.
        """
        raise NotImplementedError('Подкласс должен реализовать get_create_fields()')

    def post(self, request):
        """Создать новый документ (черновик)."""
        config = self.journal_config
        if not config:
            return Response({'error': 'journal_config not set'}, status=500)

        try:
            fields = self.get_create_fields(request.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        if not fields.get('name', '').strip():
            return Response({'error': 'name is required'}, status=400)

        doc = config.document_model.objects.create(**fields)

        return Response(
            self.serialize_item(doc),
            status=status.HTTP_201_CREATED,
        )

    # ── Фильтры (для FilterSidebar) ──

    def get_filter_options(self, request):
        """Опции фильтров для сайдбара."""
        config = self.journal_config
        if not config:
            return Response({'error': 'journal_config not set'}, status=500)
        return Response(config.get_filter_options())
