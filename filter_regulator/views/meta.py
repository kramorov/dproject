# filter_regulator/views/meta.py
from rest_framework.views import APIView
from rest_framework.response import Response
from filter_regulator.models import FilterRegulator


class FilterRegulatorMetaView(APIView):
    """GET /api/filter-regulator/meta/"""
    permission_classes = []

    def get(self, request):
        meta = FilterRegulator.get_field_meta()
        return Response(meta)
