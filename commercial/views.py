# commercial/views.py
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from cart.models import Cart
from .services.quotation import build_cart_quotation


class CartQuotationView(APIView):
    """GET /api/commercial/quotation/<uuid:cart_id>/ — сформировать КП (.docx) по корзине."""

    permission_classes = [AllowAny]

    def get(self, request, cart_id):
        cart = get_object_or_404(Cart, id=cart_id)
        docx_bytes = build_cart_quotation(cart)

        filename = f'Quotation_{cart_id.hex[:8]}.docx'
        response = HttpResponse(
            docx_bytes,
            content_type=(
                'application/vnd.openxmlformats-officedocument'
                '.wordprocessingml.document'
            ),
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
