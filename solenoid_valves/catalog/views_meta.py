# solenoid_valves/catalog/views_meta.py
"""
GET /api/solenoid-valves/meta/ — метаданные полей (label, group, unit, type).
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from solenoid_valves.models import DirectionValve


class SolenoidValvesMetaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        meta = DirectionValve.get_field_meta()
        return Response(meta)
