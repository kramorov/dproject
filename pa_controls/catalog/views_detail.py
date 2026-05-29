# pa_controls/catalog/views_detail.py
"""
GET /api/pa-controls/catalog/<id>/ — detail card.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch

from pa_controls.catalog.config import LIMIT_SWITCH_CONFIG
from pa_controls.models.sensor import SensorComponent


class LimitSwitchBoxDetailView(APIView):
    permission_classes = [AllowAny]
    config = LIMIT_SWITCH_CONFIG

    def get(self, request, pk):
        item = get_object_or_404(
            self.config.model_class.objects.select_related(
                *self.config.select_related,
                'image_gallery', 'model_line__image_gallery',
            ).prefetch_related(
                'image_gallery__items__image',
                'tech_docs',
                Prefetch(
                    'additional_sensor',
                    queryset=SensorComponent.objects.select_related(
                        'variety', 'signal_type', 'contact_form',
                        'contact_state', 'brand',
                    )
                ),
                'model_line__image_gallery__items__image',
                'model_line__tech_docs',
            ),
            pk=pk,
        )
        return Response(item.to_dict())
