# pneumatic_actuators/api/views_item.py
"""
REST-каталог эталонной модели PneumaticActuatorItem (2026-09-01).

Сконструированные пневмоприводы: каждая запись — артикул каталога
(сгенерированные code/name/description из шаблонов серии) + привязанная SKU.

Эндпоинты:
    GET /api/pneumatic_actuators/items/        — список (to_values_dict)
        ?model_line_id=<id>                    — фильтр по серии
        ?variety=DA|SR                         — фильтр по виду привода
    GET /api/pneumatic_actuators/items/<id>/   — карточка (to_dict)
"""

import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from pneumatic_actuators.models.pa_item import PneumaticActuatorItem

logger = logging.getLogger(__name__)


class PneumaticActuatorItemListView(APIView):
    """Список сконструированных пневмоприводов (эталонная модель)."""

    permission_classes = [AllowAny]

    def get(self, request):
        qs = PneumaticActuatorItem.objects.filter(is_active=True).order_by('sorting_order', 'code')

        model_line_id = request.query_params.get('model_line_id')
        if model_line_id:
            qs = qs.filter(model_line_id=model_line_id)

        variety = request.query_params.get('variety')
        if variety:
            qs = qs.filter(pneumatic_actuator_variety__code=variety)

        return Response([item.to_values_dict() for item in qs])


class PneumaticActuatorItemDetailView(APIView):
    """Карточка сконструированного пневмопривода (to_dict)."""

    permission_classes = [AllowAny]

    def get(self, request, pk=None):
        try:
            item = PneumaticActuatorItem.objects.get(pk=pk)
        except PneumaticActuatorItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)
        return Response(item.to_dict())
