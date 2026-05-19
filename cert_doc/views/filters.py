# cert_doc/views/filters.py
"""
GET /api/admin/certs/filters/ — опции фильтров (только те, для которых есть сертификаты).
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from cert_doc.models import CertData


class CertFilterOptionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        options = CertData.get_filter_options()
        return Response(options)
