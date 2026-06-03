# core/climate_views.py
"""
API для каскадного фильтра климатического исполнения (ГОСТ 15150-69).

GET  /api/core/climate/structure/  — зоны, размещения, все условия с температурами
POST /api/core/climate/parse/     — парсинг «УХЛ4» → {zone_id, placement_id, min_temp, max_temp, designation}
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from params.models import ClimaticZoneClassifier, ClimaticEquipmentPlacementClassifier, ClimaticConditions
from core.models.climate_parser import ClimateStringParser


class ClimateStructureView(APIView):
    """GET /api/core/climate/structure/ — зоны, размещения, все ClimaticConditions."""
    permission_classes = [AllowAny]

    def get(self, request):
        # Климатические зоны (У, ХЛ, УХЛ, Т, ТВ...) — лежат в ClimaticEquipmentPlacementClassifier
        zones = list(
            ClimaticEquipmentPlacementClassifier.objects
            .filter(is_active=True)
            .order_by('sorting_order')
            .values('id', 'code', 'name', 'description')
        )

        # Категории размещения (1–5) — лежат в ClimaticZoneClassifier
        placements = list(
            ClimaticZoneClassifier.objects
            .filter(is_active=True)
            .order_by('sorting_order')
            .values('id', 'code', 'name', 'description')
        )

        # Все комбинации зона+размещение с температурами
        conditions = list(
            ClimaticConditions.objects
            .filter(is_active=True)
            .select_related('climaticZone', 'climaticPlacement')
            .order_by('sorting_order')
            .values(
                'id', 'code', 'name',
                'climaticZone_id', 'climaticPlacement_id',
                'min_temp_work', 'max_temp_work',
                'min_temp_extremal', 'max_temp_extremal',
            )
        )

        return Response({
            'zones': zones,
            'placements': placements,
            'conditions': conditions,
        })


class ClimateParseView(APIView):
    """POST /api/core/climate/parse/ — «УХЛ4» → zone_id, placement_id, температуры."""
    permission_classes = [AllowAny]

    def post(self, request):
        raw = request.data.get('climate_string', '').strip()
        if not raw:
            return Response({'error': 'Пустая строка'}, status=400)

        parsed = ClimateStringParser.parse(raw)
        if not parsed:
            return Response({'error': f'Не удалось распознать строку: «{raw}». '
                                      f'Ожидается формат: зона ГОСТ + цифра размещения, например «УХЛ4», «У2», «ТВ3».'},
                            status=400)

        result = {}

        # Ищем зону по коду
        zone = None
        if parsed.zone_code:
            zone = ClimaticEquipmentPlacementClassifier.objects.filter(
                code=parsed.zone_code, is_active=True
            ).first()
            if zone:
                result['zone_id'] = zone.id
                result['zone_code'] = zone.code
                result['zone_name'] = zone.name

        # Ищем размещение по коду
        placement = None
        if parsed.placement_code:
            placement = ClimaticZoneClassifier.objects.filter(
                code=parsed.placement_code, is_active=True
            ).first()
            if placement:
                result['placement_id'] = placement.id
                result['placement_code'] = placement.code
                result['placement_name'] = placement.name

        # Ищем ClimaticConditions для этой комбинации
        cc = None
        if zone and placement:
            cc = ClimaticConditions.objects.filter(
                climaticPlacement_id=zone.id,   # Внимание: поля перепутаны в БД!
                climaticZone_id=placement.id,   # climaticPlacement → зона, climaticZone → размещение
                is_active=True,
            ).first()

        if cc:
            result['condition_id'] = cc.id
            result['min_temp_work'] = cc.min_temp_work
            result['max_temp_work'] = cc.max_temp_work
            result['min_temp_extremal'] = cc.min_temp_extremal
            result['max_temp_extremal'] = cc.max_temp_extremal
        elif zone and placement:
            return Response({
                'error': f'Комбинация «{zone.name}{placement.code}» не найдена в базе ClimaticConditions.',
                **result,
            }, status=404)

        result['designation'] = raw  # исходная строка

        return Response(result)
