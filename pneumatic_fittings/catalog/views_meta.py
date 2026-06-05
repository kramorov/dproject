# pneumatic_fittings/catalog/views_meta.py
"""
GET /api/pneumatic-fittings/meta/ — метаданные полей (label, group, unit, type).
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from pneumatic_fittings.models import PneumaticFitting


class PneumaticFittingsMetaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        meta = PneumaticFitting.get_field_meta()
        return Response(meta)
