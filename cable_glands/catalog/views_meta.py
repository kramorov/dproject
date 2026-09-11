# cable_glands/catalog/views_meta.py
"""
GET /api/cable-glands/meta/ — метаданные полей (label, group, unit, type).
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from cable_glands.models import CableGland


class CableGlandMetaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        meta = CableGland.get_field_meta()
        return Response(meta)
