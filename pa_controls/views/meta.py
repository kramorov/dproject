# pa_controls/views/meta.py
"""
GET /api/pa-controls/meta/ — метаданные полей (label, group, unit, type).
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from pa_controls.models.limit_switch import LimitSwitchBox


class LimitSwitchBoxMetaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        meta = LimitSwitchBox.get_field_meta()
        return Response(meta)
