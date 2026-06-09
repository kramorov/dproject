# documents/views/document_detail.py
"""
BaseDocumentDetailView — базовые операции с документом.

GET    — карточка документа со строками
PUT    — редактировать реквизиты / перевести статус
DELETE — удалить документ
POST   — register / unregister / print / export / import (по action в URL)

Подкласс должен задать:
    document_model = ...

Опционально переопределить:
    _get_doc()            — свой способ получения (select_related/prefetch)
    serialize_detail()    — полная сериализация
    serialize_items()     — сериализация строк
    get_editable_fields() — какие поля можно менять в PUT
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.http import HttpResponse


class BaseDocumentDetailView(APIView):
    """
    Детальная работа с документом.

    URL pattern:
        GET    /<pk>/
        PUT    /<pk>/
        DELETE /<pk>/
        POST   /<pk>/register/      — провести
        POST   /<pk>/unregister/    — отменить проведение
        POST   /<pk>/print/         — печатная форма (HTML)
        POST   /<pk>/export/word/   — скачать Word
        POST   /<pk>/export/excel/  — скачать Excel
        POST   /<pk>/export/pdf/    — скачать PDF
        POST   /<pk>/import/        — загрузить данные из файла
    """

    permission_classes = [AllowAny]
    document_model = None

    # ── Получение документа ──

    def _get_doc(self, pk):
        """
        Получить документ по первичному ключу.

        Подкласс может переопределить для select_related/prefetch_related.
        """
        if not self.document_model:
            raise ValueError('document_model не задан')
        try:
            return self.document_model.objects.get(pk=pk)
        except self.document_model.DoesNotExist:
            return None

    # ── GET ──

    def serialize_detail(self, doc):
        """
        Полная сериализация документа со строками.

        Подкласс должен переопределить, включив строки через
        doc.get_items_related_name().
        """
        data = doc.get_compact_data()
        items_related = doc.get_items_related_name()
        items_qs = getattr(doc, items_related).filter(is_active=True)
        data['items'] = [self.serialize_item(item) for item in items_qs]
        return data

    def serialize_item(self, item):
        """Сериализовать одну строку. Подкласс переопределяет."""
        return {
            'id': item.id,
            'sorting_order': item.sorting_order,
            'comment': item.comment,
            'is_active': item.is_active,
        }

    def get(self, request, pk):
        doc = self._get_doc(pk)
        if not doc:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.serialize_detail(doc))

    # ── PUT ──

    def get_editable_fields(self):
        """
        Список полей, разрешённых к редактированию в PUT.

        Подкласс переопределяет. Возвращает список имён полей.
        """
        return ['name', 'description', 'document_date']

    def put(self, request, pk):
        """
        Редактировать реквизиты и/или изменить статус.

        - Статус: только по графу переходов.
        - Реквизиты: только когда текущий статус DRAFT
          (или при переходе DRAFT→ON_APPROVAL — можно одновременно).
        - Если статус меняется и реквизиты редактируются —
          оба изменения применяются атомарно в одном save.
        """
        doc = self._get_doc(pk)
        if not doc:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        has_status_change = 'status' in data
        has_field_changes = any(f in data for f in self.get_editable_fields())

        # Валидация: реквизиты можно менять только если сейчас DRAFT
        if has_field_changes and doc.status != doc.Status.DRAFT:
            return Response({
                'error': f'Редактирование реквизитов запрещено. Текущий статус: {doc.get_status_display()}',
            }, status=status.HTTP_400_BAD_REQUEST)

        # Изменение статуса
        modified = False
        if has_status_change:
            new_status = data['status']
            if new_status != doc.status:
                if not doc.can_transition_to(new_status):
                    return Response({
                        'error': f'Переход {doc.status} → {new_status} запрещён',
                    }, status=status.HTTP_400_BAD_REQUEST)
                doc.status = new_status
                modified = True

        # Редактирование реквизитов
        for field in self.get_editable_fields():
            if field in data:
                setattr(doc, field, data[field])
                modified = True

        if modified:
            doc.save()
        return Response({
            'success': True,
            'status': doc.status,
            'status_label': doc.get_status_display(),
        })

    # ── DELETE ──

    def delete(self, request, pk):
        """
        Пометить документ на удаление (soft delete).

        Проведённый документ сначала отменяет проведение,
        затем переходит в статус DELETED.
        Физическое удаление из БД — отдельным механизмом.
        """
        doc = self._get_doc(pk)
        if not doc:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if doc.is_deleted:
            return Response(
                {'error': 'Документ уже помечен на удаление'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            doc.mark_deleted()
            return Response({
                'success': True,
                'status': doc.status,
                'status_label': doc.get_status_display(),
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ── POST: register / unregister / print / export / import ──

    def post(self, request, pk):
        """
        Маршрутизация всех POST-действий с документом.

        Действие определяется по сегментам URL:
            .../<pk>/register/       → register_changes()
            .../<pk>/unregister/     → unregister_changes()
            .../<pk>/print/          → печатная форма (HTML)
            .../<pk>/export/<fmt>/   → скачать Word/Excel/PDF
            .../<pk>/import/         → загрузить данные из файла
        """
        doc = self._get_doc(pk)
        if not doc:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        # Разбираем путь: .../<pk>/action/sub_action/
        parts = request.path.rstrip('/').split('/')
        action = parts[-1] if len(parts) >= 1 else ''
        sub_action = parts[-2] if len(parts) >= 2 else ''

        if not action:
            return Response(
                {'error': 'Действие не указано в URL'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action == 'register':
            if doc.is_posted:
                return Response(
                    {'error': 'Документ уже проведён'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                doc.register_changes()
                doc.refresh_from_db()
                if doc.status != doc.Status.POSTED:
                    raise RuntimeError(
                        f'{doc.__class__.__name__}.register_changes() '
                        f'не установил status=POSTED (текущий: {doc.status})'
                    )
                return Response({
                    'success': True,
                    'status': doc.status,
                    'status_label': doc.get_status_display(),
                })
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif action == 'unregister':
            if not doc.is_posted:
                return Response(
                    {'error': 'Документ не был проведён'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                doc.unregister_changes()
                doc.refresh_from_db()
                if doc.status != doc.Status.DRAFT:
                    raise RuntimeError(
                        f'{doc.__class__.__name__}.unregister_changes() '
                        f'не установил status=DRAFT (текущий: {doc.status})'
                    )
                return Response({
                    'success': True,
                    'status': doc.status,
                    'status_label': doc.get_status_display(),
                })
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif action == 'print':
            return self._handle_print(doc)

        elif sub_action == 'export':
            return self._handle_export(doc, action)

        elif action == 'import':
            return self._handle_import(doc, request)

        return Response(
            {'error': f'Unknown action: {action}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── Печать ──

    def _handle_print(self, doc):
        """
        Вернуть HTML печатной формы.

        Вызывает doc.get_print_html().
        Фронтенд открывает HTML в новом окне или модалке.
        """
        try:
            html = doc.get_print_html()
            return HttpResponse(html, content_type='text/html; charset=utf-8')
        except NotImplementedError:
            return Response(
                {'error': 'Печатная форма не реализована для этого типа документа'},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ── Экспорт ──

    # Маппинг форматов на методы документа
    EXPORT_FORMATS = {
        'word':  {
            'method': 'export_word',
            'content_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'ext': 'docx',
        },
        'excel': {
            'method': 'export_excel',
            'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'ext': 'xlsx',
        },
        'pdf':   {
            'method': 'export_pdf',
            'content_type': 'application/pdf',
            'ext': 'pdf',
        },
    }

    def _handle_export(self, doc, fmt):
        """
        Экспорт документа в заданном формате.

        Вызывает doc.export_word() / export_excel() / export_pdf()
        и возвращает файл для скачивания.
        """
        export_config = self.EXPORT_FORMATS.get(fmt)
        if not export_config:
            return Response(
                {'error': f'Неизвестный формат экспорта: {fmt}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            method = getattr(doc, export_config['method'], None)
            if not callable(method):
                return Response(
                    {'error': f'export_{fmt}() не реализован (не является методом)'},
                    status=status.HTTP_501_NOT_IMPLEMENTED,
                )
            file_bytes = method()
        except NotImplementedError:
            return Response(
                {'error': f'Экспорт в {fmt.upper()} не реализован для этого типа документа'},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not isinstance(file_bytes, (bytes, bytearray)):
            return Response(
                {'error': f'export_{fmt}() должен вернуть bytes'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        safe_name = (doc.name or 'document').replace(' ', '_').replace('/', '-')[:50]
        filename = f'{safe_name}.{export_config["ext"]}'

        from urllib.parse import quote
        response = HttpResponse(file_bytes, content_type=export_config['content_type'])
        response['Content-Disposition'] = (
            f"attachment; filename=\"{quote(filename)}\"; "
            f"filename*=UTF-8''{quote(filename)}"
        )
        return response

    # ── Импорт ──

    def _handle_import(self, doc, request):
        """
        Импорт данных из загруженного файла.

        Ожидает файл в request.FILES['file'].
        Только для документов в статусе DRAFT.
        """
        if doc.status != doc.Status.DRAFT:
            return Response(
                {'error': f'Импорт запрещён. Текущий статус: {doc.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = doc.import_from_file(uploaded)
            return Response({
                'success': True,
                'created': result.get('created', 0),
                'updated': result.get('updated', 0),
                'errors': result.get('errors', []),
            })
        except NotImplementedError:
            return Response(
                {'error': 'Импорт не реализован для этого типа документа'},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
