# gearbox/views/meta.py
"""
GET /api/gearbox/meta/ — метаданные полей (label, group, unit, type).

Возвращает плоский словарь field_key → {label, group, unit, type, order},
извлечённый из ``GearBox.to_dict()`` через ``CatalogDictMixin.get_field_meta()``.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from gearbox.models import GearBox


class GearboxMetaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        meta = GearBox.get_field_meta()
        return Response(meta)
