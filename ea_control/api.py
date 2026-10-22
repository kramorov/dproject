# ea_control/api.py
"""
API ea_control: CRUD моделей для фронт-админки + пакет конфигуратора БУ.

Эндпоинты (под префиксом /api/ea-control/):

- CRUD (DRF-роутер, IsAdminUser): control-units, sections, slots,
  slot-options, matrix-entries, slot-rules, signal-forms, control-signals,
  feedback-signals, comm-protocols, feedback-devices, heater-supplies,
  location-options, capabilities, signal-power-sources, signal-powers,
  control-logics, signal-types;
- GET units/ — список типов БУ (id/code/name/kind/brand);
- GET meta/ — справочники для селекторов (серии, напряжения, бренды, БУ);
- GET series-units/?model_line=&power_supply= — доступные БУ серии
  (резолвер слота control_unit);
- GET package/?unit=&model_line=&power_supply=&mode=&locale= — пакет
  конфигуратора (slots.md §5).

Пакет — серверный источник истины: доступность, дефолты и правила
резолвятся на бэке (ea_control.services).
"""
from rest_framework import serializers, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from ea_control.models import (CuCapability, CuCommProtocol, CuControlLogic,
                               CuControlSignal, CuFeedbackDevice,
                               CuFeedbackSignal, CuHeaterSupply, CuLocationOption,
                               CuMatrixEntry, CuSignalForm, CuSignalPower,
                               CuSignalPowerSource, CuSignalType, CuSlot,
                               CuSlotOption, CuSlotRule, ControlUnit,
                               CuSectionNode)
from ea_control.services.cu_matrix import resolve_control_units
from ea_control.services.cu_package import build_package


class _LargePagination(PageNumberPagination):
    """Админ-таблицы: без жёсткого лимита страницы по умолчанию."""
    page_size = 1000


def _serializer(model_cls):
    """ModelSerializer «все поля» для модели (фронт-админка)."""
    class S(serializers.ModelSerializer):
        class Meta:
            model = model_cls
            fields = '__all__'
    S.__name__ = f'{model_cls.__name__}Serializer'
    return S


def _viewset(model_cls, serializer_cls):
    """ModelViewSet с IsAdminUser и крупной страницей."""
    class V(viewsets.ModelViewSet):
        queryset = model_cls.objects.all()
        serializer_class = serializer_cls
        permission_classes = [IsAdminUser]
        pagination_class = _LargePagination
    V.__name__ = f'{model_cls.__name__}ViewSet'
    return V


# ── CRUD-вьюсеты (регистрируются в urls.py роутером) ────────────────────────

ControlUnitViewSet = _viewset(ControlUnit, _serializer(ControlUnit))
CuSectionNodeViewSet = _viewset(CuSectionNode, _serializer(CuSectionNode))
CuSlotViewSet = _viewset(CuSlot, _serializer(CuSlot))
CuSlotOptionViewSet = _viewset(CuSlotOption, _serializer(CuSlotOption))
CuMatrixEntryViewSet = _viewset(CuMatrixEntry, _serializer(CuMatrixEntry))
CuSlotRuleViewSet = _viewset(CuSlotRule, _serializer(CuSlotRule))
CuSignalFormViewSet = _viewset(CuSignalForm, _serializer(CuSignalForm))
CuControlSignalViewSet = _viewset(CuControlSignal, _serializer(CuControlSignal))
CuFeedbackSignalViewSet = _viewset(CuFeedbackSignal, _serializer(CuFeedbackSignal))
CuCommProtocolViewSet = _viewset(CuCommProtocol, _serializer(CuCommProtocol))
CuFeedbackDeviceViewSet = _viewset(CuFeedbackDevice, _serializer(CuFeedbackDevice))
CuHeaterSupplyViewSet = _viewset(CuHeaterSupply, _serializer(CuHeaterSupply))
CuLocationOptionViewSet = _viewset(CuLocationOption, _serializer(CuLocationOption))
CuCapabilityViewSet = _viewset(CuCapability, _serializer(CuCapability))
CuSignalPowerSourceViewSet = _viewset(CuSignalPowerSource,
                                      _serializer(CuSignalPowerSource))
CuSignalPowerViewSet = _viewset(CuSignalPower, _serializer(CuSignalPower))
CuControlLogicViewSet = _viewset(CuControlLogic, _serializer(CuControlLogic))
CuSignalTypeViewSet = _viewset(CuSignalType, _serializer(CuSignalType))


# ── Особые эндпоинты ────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def units_view(request):
    """Список типов БУ (для селекторов админки и конфигуратора)."""
    units = []
    for u in ControlUnit.objects.select_related('brand').order_by(
            'brand__name', 'sorting_order', 'code'):
        units.append({
            'id': u.id,
            'code': u.code,
            'name': u.name,
            'kind': u.kind,
            'brand_name': u.brand.name if u.brand_id else '',
        })
    return Response(units)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def meta_view(request):
    """Справочники для селекторов конфигуратора и админки."""
    from electric_actuators.models import (ElectricActuatorBody,
                                           ElectricActuatorModelLine,
                                           ElectricActuatorModelLineItem)
    from params.models import PowerSupplies
    from producers.models import Brands

    model_lines = [{'id': m.id, 'code': m.code, 'name': m.name}
                   for m in ElectricActuatorModelLine.objects.order_by('code')]
    power_supplies = [{'id': p.id, 'code': p.code, 'name': p.name}
                      for p in PowerSupplies.objects.order_by('sorting_order', 'name')]
    brands = [{'id': b.id, 'name': b.name, 'code': getattr(b, 'code', '')}
              for b in Brands.objects.order_by('name')]
    bodies = [{'id': b.id, 'code': getattr(b, 'code', ''), 'name': str(b)}
              for b in ElectricActuatorBody.objects.order_by('id')]
    model_line_items = [{'id': i.id, 'code': getattr(i, 'code', ''), 'name': str(i)}
                        for i in ElectricActuatorModelLineItem.objects.order_by('id')[:500]]
    return Response({
        'model_lines': model_lines,
        'power_supplies': power_supplies,
        'brands': brands,
        'bodies': bodies,
        'model_line_items': model_line_items,
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def series_units_view(request):
    """Доступные типы БУ для серии/напряжения (слот control_unit)."""
    from electric_actuators.models import ElectricActuatorModelLine
    from params.models import PowerSupplies

    try:
        model_line = ElectricActuatorModelLine.objects.get(
            pk=request.query_params['model_line'])
    except (KeyError, ElectricActuatorModelLine.DoesNotExist):
        return Response({'error': 'model_line обязателен'}, status=400)
    power_supply = None
    ps_id = request.query_params.get('power_supply')
    if ps_id:
        try:
            power_supply = PowerSupplies.objects.get(pk=ps_id)
        except PowerSupplies.DoesNotExist:
            return Response({'error': 'power_supply не найден'}, status=400)
    locale = request.query_params.get('locale', 'ru')
    return Response(resolve_control_units(model_line, power_supply=power_supply,
                                          locale=locale))


@api_view(['GET'])
@permission_classes([IsAdminUser])
def package_view(request):
    """Пакет конфигуратора БУ (slots.md §5)."""
    from electric_actuators.models import ElectricActuatorModelLine
    from params.models import PowerSupplies

    try:
        unit = ControlUnit.objects.get(pk=request.query_params['unit'])
    except (KeyError, ControlUnit.DoesNotExist):
        return Response({'error': 'unit обязателен'}, status=400)
    model_line = None
    if request.query_params.get('model_line'):
        try:
            model_line = ElectricActuatorModelLine.objects.get(
                pk=request.query_params['model_line'])
        except ElectricActuatorModelLine.DoesNotExist:
            return Response({'error': 'model_line не найден'}, status=400)
    power_supply = None
    if request.query_params.get('power_supply'):
        try:
            power_supply = PowerSupplies.objects.get(
                pk=request.query_params['power_supply'])
        except PowerSupplies.DoesNotExist:
            return Response({'error': 'power_supply не найден'}, status=400)
    mode = request.query_params.get('mode', 'both')
    locale = request.query_params.get('locale', 'ru')
    return Response(build_package(unit, model_line=model_line,
                                  power_supply=power_supply, mode=mode,
                                  locale=locale))
