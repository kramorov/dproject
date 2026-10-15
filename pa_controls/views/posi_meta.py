# pa_controls/views/posi_meta.py
"""
GET /api/pa-controls/positioners/meta/ — метаданные полей (label, group, unit, type).
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from pa_controls.models.positioner_item import PosiModelLineItem


class PosiMetaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        meta = PosiModelLineItem.get_field_meta()
        return Response(meta)
