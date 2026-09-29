# core/spec_doc_views.py
"""Скачивание спецификации каталога в .docx.

GET /api/core/catalog/spec-docx/<app_label>/<model_name>/<pk>/
Возвращает готовый .docx (attachment) для любого каталогового артикула.
"""

import io
import re

from django.apps import apps
from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.models.catalog_serializer import CatalogSerializerMixin
from core.models.spec_docx import render_spec_docx_bytes


# Общие связи всех каталоговых моделей (ImageGalleryMixin / TechDocMixin / model_line).
_SPEC_DOC_SELECT_RELATED = ('model_line', 'image_gallery', 'model_line__image_gallery')
_SPEC_DOC_PREFETCH = (
    'image_gallery__items__image',
    'model_line__image_gallery__items__image',
    'tech_docs',
    'model_line__tech_docs',
)


class SpecDocxDownloadView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, app_label, model_name, pk):
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            model = None
        if model is None or not issubclass(model, CatalogSerializerMixin):
            raise Http404('Неизвестная модель каталога')

        item = get_object_or_404(self._get_queryset(model), pk=pk)

        base_url = settings.SITE_BASE_URL or request.build_absolute_uri('/')
        data = render_spec_docx_bytes(item, base_url=base_url)

        code = getattr(item, 'code', None) or str(pk)
        safe_code = re.sub(r'[\\/*?:"<>|]', '-', str(code))
        filename = 'Спец-я %s.docx' % safe_code

        return FileResponse(
            io.BytesIO(data),
            as_attachment=True,
            filename=filename,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        )

    @staticmethod
    def _get_queryset(model):
        """Базовый queryset с prefetch общих связей (галерея/техдоки).

        Модель-специфичные resolver-поля (например, ``signal_profile`` у БКВ)
        дадут ещё пару лишних запросов — допустимо для редкого скачивания.
        """
        qs = model.objects.all()
        try:
            qs = qs.select_related(*_SPEC_DOC_SELECT_RELATED)
        except Exception:
            pass
        try:
            qs = qs.prefetch_related(*_SPEC_DOC_PREFETCH)
        except Exception:
            pass
        return qs


@api_view(['POST'])
@permission_classes([AllowAny])
def rebuild_spec_template(request):
    """POST /api/core/catalog/spec-docx/rebuild-template/

    Принудительно пересоздаёт .docx-шаблон спецификации (build_spec_template).
    """
    from core.models.spec_docx import build_spec_template, DEFAULT_TEMPLATE_PATH
    try:
        build_spec_template(DEFAULT_TEMPLATE_PATH)
        return Response({'ok': True, 'path': DEFAULT_TEMPLATE_PATH})
    except Exception as e:
        return Response({'ok': False, 'error': str(e)}, status=500)
