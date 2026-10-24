# ea_control/api.py
"""
API ea_control: CRUD моделей для фронт-админки + пакет конфигуратора БУ.

Эндпоинты (под префиксом /api/ea-control/):

- CRUD (DRF-роутер, IsAdminUser): control-units, sections, slots,
  slot-options, matrix-entries, slot-rules, signal-forms, control-signals,
  feedback-signals, comm-protocols, feedback-devices, heater-supplies,
  location-options, capabilities, local-control-types, display-types,
  signal-power-sources, signal-powers, control-logics, signal-types;
- GET units/ — список типов БУ (id/code/name/kind/brand);
- GET meta/ — справочники для селекторов (серии, напряжения, бренды, БУ);
- GET series-units/?model_line=&power_supply= — доступные БУ серии
  (резолвер слота control_unit);
- GET package/?unit=&model_line=&power_supply=&mode=&locale= — пакет
  конфигуратора (slots.md §5).

Пакет — серверный источник истины: доступность, дефолты и правила
резолвятся на бэке (ea_control.services).
"""
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from ea_control.models import (CuCapability, CuCommProtocol, CuControlLogic,
                               CuControlSignal, CuDisplayType, CuFeedbackDevice,
                               CuFeedbackSignal, CuHeaterSupply,
                               CuLocalControlType, CuLocationOption,
                               CuMatrixEntry, CuSignalForm, CuSignalPower,
                               CuSignalPowerSource, CuSignalType, CuSlot,
                               CuSlotOption, CuSlotRule, CuUnitPowerSource,
                               ControlUnit, CuSectionNode)
from ea_control.services.cu_matrix import resolve_control_units
from ea_control.services.cu_package import build_package
from ea_control.services.cu_report import build_description


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


def _slot_option_serializer():
    """CuSlotOption + валидация «display-опция без видов отображения».

    model.clean() для M2M не надёжен (см. cu_config.py) — проверяем здесь,
    чтобы API-путь фронта не мог сохранить пустую display-опцию.
    """
    class S(serializers.ModelSerializer):
        class Meta:
            model = CuSlotOption
            fields = '__all__'

        def validate(self, attrs):
            kind = attrs.get('kind', getattr(self.instance, 'kind', None))
            if kind == 'display':
                if 'display_types' in attrs:
                    types = attrs.get('display_types') or []
                elif self.instance and self.instance.pk:
                    types = list(self.instance.display_types.all())
                else:
                    types = []
                if not types:
                    raise serializers.ValidationError(
                        {'display_types': _('Для опции отображения нужен '
                                            'хотя бы один вид отображения.')})
            return attrs

    S.__name__ = 'CuSlotOptionSerializer'
    return S


# ── CRUD-вьюсеты (регистрируются в urls.py роутером) ────────────────────────


class ControlUnitViewSet(viewsets.ModelViewSet):
    """Типы БУ + копирование (с матрицей/правилами) и удаление с очисткой."""
    queryset = ControlUnit.objects.all().order_by('brand', 'sorting_order', 'code')
    serializer_class = _serializer(ControlUnit)
    permission_classes = [IsAdminUser]
    pagination_class = _LargePagination

    @action(detail=True, methods=['post'])
    def copy(self, request, pk=None):
        """Копия БУ: скаляры + M2M + опция слота control_unit +
        профильные строки матрицы + правила, завязанные на код опции."""
        unit = get_object_or_404(ControlUnit, pk=pk)
        base = unit.code
        n = 1
        code = f'{base}-cp{n}'
        while ControlUnit.objects.filter(brand=unit.brand, code=code).exists():
            n += 1
            code = f'{base}-cp{n}'
        new = ControlUnit.objects.create(
            brand=unit.brand, code=code, name=unit.name,
            kind=unit.kind, location=unit.location,
            control_voltage=unit.control_voltage, signal_power=unit.signal_power,
            legacy_cu=unit.legacy_cu,
            name_template=unit.name_template,
            description_template=unit.description_template,
            spec_template=unit.spec_template,
            name_template_i18n=unit.name_template_i18n,
            description_template_i18n=unit.description_template_i18n,
            description=unit.description,
            sorting_order=(unit.sorting_order or 0) + 1, is_active=unit.is_active)
        # имя «(копия)» без перегенерации шаблоном (TemplateMixin.save)
        new.name = f'{unit.name} (копия)'
        new.description = unit.description
        new.save(skip_auto_generate=True)
        new.accepts.set(unit.accepts.all())
        new.emits.set(unit.emits.all())
        new.protocols.set(unit.protocols.all())
        new.capabilities.set(unit.capabilities.all())

        # опция слота control_unit для копии (коды опций глобально уникальны)
        old_opt = CuSlotOption.objects.filter(
            slot__code='control_unit', control_unit=unit).first()
        new_opt = None
        if old_opt:
            m = 1
            opt_code = f'{old_opt.code}_CP{m}'
            while CuSlotOption.objects.filter(code=opt_code).exists():
                m += 1
                opt_code = f'{old_opt.code}_CP{m}'
            new_opt = CuSlotOption.objects.create(
                code=opt_code, slot=old_opt.slot, kind='unit',
                control_unit=new, encoding=old_opt.encoding,
                ext_encoding=old_opt.ext_encoding,
                sorting_order=old_opt.sorting_order, is_active=old_opt.is_active)

        # профильные строки матрицы (control_unit → копия) + конфликты
        old_rows = list(CuMatrixEntry.objects.filter(control_unit=unit))
        id_map = {}
        for r in old_rows:
            nr = CuMatrixEntry.objects.create(
                slot=r.slot, option=r.option, brand=r.brand,
                model_line=r.model_line, body=r.body,
                model_line_item=r.model_line_item, control_unit=new,
                power_supply=r.power_supply, mode=r.mode,
                control_signal=r.control_signal, feedback_signal=r.feedback_signal,
                protocol=r.protocol, device=r.device,
                heater_supply=r.heater_supply, availability=r.availability,
                is_default=r.is_default, bundle=r.bundle,
                encoding=r.encoding, ext_encoding=r.ext_encoding,
                name=r.name, description=r.description,
                sorting_order=r.sorting_order)
            id_map[r.id] = nr
        for r in old_rows:
            for c in r.conflicts.all():
                if c.id in id_map:
                    id_map[r.id].conflicts.add(id_map[c.id])

        # правила, завязанные на код опции выбора БУ (в т.ч. списки — 'in')
        def _remap(value):
            if value == old_opt.code:
                return (new_opt.code if new_opt else None), True
            if isinstance(value, list) and old_opt.code in value:
                out = [(new_opt.code if x == old_opt.code else x)
                       for x in value]
                if new_opt is None:
                    out = [x for x in out if x is not None]
                return out, True
            return value, False

        if old_opt:
            for rule in CuSlotRule.objects.filter(
                    when_slot__code='control_unit'):
                wv, c1 = _remap(rule.when_value)
                av, c2 = _remap(rule.action_value)
                if c1 or c2:
                    CuSlotRule.objects.create(
                        when_slot=rule.when_slot, target_slot=rule.target_slot,
                        when_operator=rule.when_operator, when_value=wv,
                        action=rule.action, action_value=av,
                        priority=rule.priority, is_active=rule.is_active,
                        description=rule.description)
        return Response({'id': new.id, 'code': new.code}, status=201)

    @action(detail=True, methods=['delete'], url_path='delete-unit')
    def delete_unit(self, request, pk=None):
        """Удаление БУ: опция слота control_unit (PROTECT) снимается,
        связанные правила чистятся, профильные строки матрицы — каскадом."""
        unit = get_object_or_404(ControlUnit, pk=pk)
        opts = list(CuSlotOption.objects.filter(
            slot__code='control_unit', control_unit=unit))
        for o in opts:
            # exact-правила
            CuSlotRule.objects.filter(
                Q(when_slot__code='control_unit', when_value=o.code)
                | Q(action_value=o.code)).delete()
            # правила со списками (оператор in/not_in): убрать код из списка
            for rule in CuSlotRule.objects.filter(
                    when_slot__code='control_unit'):
                wv, av = rule.when_value, rule.action_value
                changed = False
                if isinstance(wv, list) and o.code in wv:
                    wv = [x for x in wv if x != o.code]
                    changed = True
                if isinstance(av, list) and o.code in av:
                    av = [x for x in av if x != o.code]
                    changed = True
                if changed:
                    rule.when_value = wv
                    rule.action_value = av
                    rule.save(update_fields=['when_value', 'action_value'])
            o.delete()
        unit.delete()
        return Response(status=204)
CuSectionNodeViewSet = _viewset(CuSectionNode, _serializer(CuSectionNode))
CuSlotViewSet = _viewset(CuSlot, _serializer(CuSlot))
CuSlotOptionViewSet = _viewset(CuSlotOption, _slot_option_serializer())
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
CuLocalControlTypeViewSet = _viewset(CuLocalControlType,
                                     _serializer(CuLocalControlType))
CuDisplayTypeViewSet = _viewset(CuDisplayType, _serializer(CuDisplayType))
CuUnitPowerSourceViewSet = _viewset(CuUnitPowerSource,
                                    _serializer(CuUnitPowerSource))
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
    from params.models import PowerSupplies, ThreadSize, ThreadSizeSet
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
    thread_sizes = [{'id': t.id, 'code': t.code or '', 'name': t.name or str(t.id)}
                    for t in ThreadSize.objects.filter(is_active=True)
                    .order_by('sorting_order', 'name')]
    thread_sets = [{'id': s.id, 'code': s.code or '', 'name': s.name or str(s.id)}
                   for s in ThreadSizeSet.objects.filter(is_active=True)
                   .order_by('sorting_order', 'name')]
    return Response({
        'model_lines': model_lines,
        'power_supplies': power_supplies,
        'brands': brands,
        'bodies': bodies,
        'model_line_items': model_line_items,
        'thread_sizes': thread_sizes,
        'thread_sets': thread_sets,
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
def describe_view(request):
    """Описание БУ для проверки производителем: все слоты по узлам,
    каждая опция с доступностью std/opt/na."""
    try:
        unit = ControlUnit.objects.get(pk=request.query_params['unit'])
    except (KeyError, ControlUnit.DoesNotExist):
        return Response({'error': 'unit обязателен'}, status=400)
    locale = request.query_params.get('locale', 'ru')
    return Response(build_description(unit, locale=locale))


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
