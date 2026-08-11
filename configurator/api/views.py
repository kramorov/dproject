"""
configurator/api/views.py

API endpoints для Configurator.

Сборки:
    POST   /api/configurator/assemblies/           — создать
    GET    /api/configurator/assemblies/{id}/       — получить
    PATCH  /api/configurator/assemblies/{id}/       — обновить
    POST   /api/configurator/assemblies/{id}/expand/  — развернуть CG
    GET    /api/configurator/assemblies/{id}/bom/   — MBOM/EBOM

Компоненты:
    GET    /api/configurator/components/{id}/       — состояние
    PATCH  /api/configurator/components/{id}/       — own_requirements
    POST   /api/configurator/components/{id}/filter/  — подбор
    POST   /api/configurator/components/{id}/select/  — выбрать

Схема:
    GET    /api/configurator/equipment-types/{id}/filter-schema/
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.shortcuts import get_object_or_404

from ai_assistant.models import CompositionGroup
from core.models import EquipmentType
from configurator.models import (
    AssemblyRequirements,
    ComponentRequirement,
)
from configurator.services.expander import expand_composition_group
from configurator.services.resolver import (
    resolve_effective_requirements,
    resolve_all_components,
)
from configurator.services.filter_engine import filter_by_requirements, select_product
from configurator.services.cascade import cascade_after_select
from configurator.api.serializers import (
    AssemblyRequirementsSerializer,
    AssemblyRequirementsCreateSerializer,
    ComponentRequirementSerializer,
    ComponentRequirementUpdateSerializer,
)


# ═══════════════════════════════════════════════════════════════════
# AssemblyRequirements
# ═══════════════════════════════════════════════════════════════════


class AssemblyListView(APIView):
    """POST /api/configurator/assemblies/ — создать сборку."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AssemblyRequirementsCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            cg = CompositionGroup.objects.get(id=data['composition_group_id'], is_active=True)
        except CompositionGroup.DoesNotExist:
            return Response(
                {'error': f'CompositionGroup id={data["composition_group_id"]} not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        assembly = AssemblyRequirements.objects.create(
            composition_group=cg,
            name=data.get('name', ''),
            global_requirements=data.get('global_requirements', {}),
            status='draft',
        )

        # Разворачиваем CompositionGroup → дерево ComponentRequirement
        expand_composition_group(assembly)

        # Применяем global_requirements
        if assembly.global_requirements:
            resolve_all_components(assembly)

        assembly.status = 'in_progress'
        assembly.save(update_fields=['status'])

        result = AssemblyRequirementsSerializer(assembly).data
        return Response(result, status=status.HTTP_201_CREATED)


class AssemblyDetailView(APIView):
    """GET/PATCH /api/configurator/assemblies/{id}/"""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        assembly = get_object_or_404(AssemblyRequirements, pk=pk)
        return Response(AssemblyRequirementsSerializer(assembly).data)

    def patch(self, request, pk):
        assembly = get_object_or_404(AssemblyRequirements, pk=pk)
        allowed = {'name', 'global_requirements', 'status'}
        for key in allowed:
            if key in request.data:
                setattr(assembly, key, request.data[key])
        assembly.save()

        # Если изменились global_requirements — пересчитываем все компоненты
        if 'global_requirements' in request.data:
            resolve_all_components(assembly)

        return Response(AssemblyRequirementsSerializer(assembly).data)


class AssemblyExpandView(APIView):
    """POST /api/configurator/assemblies/{id}/expand/ — переразвернуть CG."""

    permission_classes = [AllowAny]

    def post(self, request, pk):
        assembly = get_object_or_404(AssemblyRequirements, pk=pk)
        expand_composition_group(assembly)

        if assembly.global_requirements:
            resolve_all_components(assembly)

        return Response(AssemblyRequirementsSerializer(assembly).data)


class AssemblyBomView(APIView):
    """GET /api/configurator/assemblies/{id}/bom/ — MBOM/EBOM."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        assembly = get_object_or_404(AssemblyRequirements, pk=pk)

        components = assembly.components.filter(
            status='selected',
        ).select_related('equipment_type').order_by('path')

        bom = []
        for cr in components:
            bom.append({
                'component_id': cr.id,
                'equipment_type': cr.equipment_type.code if cr.equipment_type else None,
                'equipment_name': cr.equipment_type.name if cr.equipment_type else None,
                'path': cr.path,
                'product_type': cr.selected_product_type,
                'product_id': cr.selected_product_id,
                'product_name': cr.selected_product_specs.get('name', '') if cr.selected_product_specs else '',
                'product_code': cr.selected_product_specs.get('code', '') if cr.selected_product_specs else '',
            })

        return Response({
            'assembly_id': assembly.id,
            'assembly_name': assembly.name,
            'composition_group': assembly.composition_group.code if assembly.composition_group else None,
            'bom': bom,
            'total_selected': len(bom),
        })


# ═══════════════════════════════════════════════════════════════════
# ComponentRequirement
# ═══════════════════════════════════════════════════════════════════


class ComponentDetailView(APIView):
    """GET /api/configurator/components/{id}/ — состояние компонента."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        cr = get_object_or_404(ComponentRequirement, pk=pk)
        return Response(ComponentRequirementSerializer(cr).data)


class ComponentRequirementsView(APIView):
    """PATCH /api/configurator/components/{id}/requirements/ — own_requirements."""

    permission_classes = [AllowAny]

    def patch(self, request, pk):
        cr = get_object_or_404(ComponentRequirement, pk=pk)

        serializer = ComponentRequirementUpdateSerializer(cr, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        # Пересчитываем effective_requirements
        resolve_effective_requirements(cr)

        if cr.own_requirements:
            cr.status = 'requirements_filled'
            cr.save(update_fields=['status'])

        return Response(ComponentRequirementSerializer(cr).data)


class ComponentFilterView(APIView):
    """POST /api/configurator/components/{id}/filter/ — запустить подбор."""

    permission_classes = [AllowAny]

    def post(self, request, pk):
        cr = get_object_or_404(ComponentRequirement, pk=pk)

        if not cr.effective_requirements:
            return Response(
                {'error': 'No effective_requirements. Fill own_requirements first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = filter_by_requirements(cr)
        return Response(result)


class ComponentSelectView(APIView):
    """POST /api/configurator/components/{id}/select/ — выбрать продукт."""

    permission_classes = [AllowAny]

    def post(self, request, pk):
        cr = get_object_or_404(ComponentRequirement, pk=pk)

        product_id = request.data.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        specs = select_product(cr, int(product_id))
        if not specs:
            return Response(
                {'error': f'Product id={product_id} not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Каскад: DerivationRule + FittingPattern
        cascade_result = cascade_after_select(cr)

        return Response({
            'component_id': cr.id,
            'selected_product': specs,
            'cascade': cascade_result,
        })


# ═══════════════════════════════════════════════════════════════════
# Filter Schema
# ═══════════════════════════════════════════════════════════════════


class FilterSchemaView(APIView):
    """
    GET /api/configurator/equipment-types/{id}/filter-schema/

    Возвращает схему формы требований для equipment_type
    на основе FilterDefinition продукт-модели.

    Ответ: {fields: [{param_name, label, field_type, options, ...}], defaults: {...}}
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        et = get_object_or_404(EquipmentType, pk=pk, is_active=True)

        from configurator.services.registry import get_product_model_class

        try:
            model_class = get_product_model_class(et)
        except KeyError:
            return Response(
                {'error': f'No product model registered for equipment_type "{et.code}"'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ── Спец-путь для пневмопривода: поля из PA selector ──
        if et.code == 'pneumatic-actuator':
            pa_fields = _get_pa_filter_schema(model_class)
            return Response({
                'equipment_type': et.code,
                'equipment_type_name': et.name,
                'fields': pa_fields,
            })

        # ── EquipmentTypeParameter из БД ──
        from configurator.models import EquipmentTypeParameter as ETP

        params = ETP.objects.filter(
            equipment_type=et,
            is_active=True,
        ).select_related('parameter_rule').order_by('sorting_order', 'param_name')

        if not params.exists():
            return Response({'fields': [], 'defaults': {}})

        fields = []
        for p in params:
            options = p.get_options()
            fields.append({
                'param_name': p.param_name,
                'model_field': p.field_path or p.param_name,
                'label': p.label or p.param_name,
                'filter_type': p.filter_type or p.field_type or 'choice',
                'data_source_type': p.data_source_type,
                'parameter_rule_code': p.parameter_rule.code if p.parameter_rule else None,
                'is_required': p.is_required,
                'options': options,
            })

        return Response({
            'equipment_type': et.code,
            'equipment_type_name': et.name,
            'fields': fields,
        })


# ── PA filter schema helper ──

def _get_pa_filter_schema(model_class) -> list[dict]:
    """
    Возвращает поля формы требований для пневмопривода.

    Использует get_actuator_options() из PA selector для получения
    всех доступных опций (varieties, safety_positions, ip, exd, etc.).
    """
    from pneumatic_actuators.actuator_selector_handler import get_actuator_options

    try:
        options = get_actuator_options()
    except Exception:
        return []

    fields = []

    # Серия моделей (загружаем отдельно — get_actuator_options не возвращает)
    try:
        from pneumatic_actuators.models import PneumaticActuatorModelLine
        model_lines = [
            {'id': ml.id, 'name': ml.name, 'code': ml.code or ''}
            for ml in PneumaticActuatorModelLine.objects.filter(is_active=True).order_by('sorting_order', 'name')
        ]
    except Exception:
        model_lines = []
    fields.append({
        'param_name': 'model_line_id',
        'model_field': 'model_line_id',
        'label': 'Серия моделей',
        'filter_type': 'choice',
        'parameter_rule_code': None,
        'options': model_lines,
    })

    # Давление в пневмосистеме (только для PA)
    try:
        from params.models import PneumaticAirSupplyPressure
        pressures = [
            {'id': p.id, 'name': p.name, 'code': p.code or ''}
            for p in PneumaticAirSupplyPressure.objects.filter(is_active=True).order_by('sorting_order', 'name')
        ]
    except Exception:
        pressures = []
    fields.append({
        'param_name': 'air_pressure_id',
        'model_field': 'air_pressure_id',
        'label': 'Давление в пневмосистеме',
        'filter_type': 'choice',
        'parameter_rule_code': None,
        'options': pressures,
    })

    # Вид привода (DA/SR)
    fields.append({
        'param_name': 'actuator_variety_id',
        'model_field': 'actuator_variety_id',
        'label': 'Вид привода',
        'filter_type': 'choice',
        'parameter_rule_code': None,
        'options': options.get('actuator_varieties', []),
    })

    # Положение безопасности (для SR)
    fields.append({
        'param_name': 'safety_position_id',
        'model_field': 'safety_position_id',
        'label': 'Положение безопасности',
        'filter_type': 'choice',
        'parameter_rule_code': None,
        'options': options.get('safety_positions', []),
    })

    # Покрытие корпуса
    fields.append({
        'param_name': 'coating_id',
        'model_field': 'coating_id',
        'label': 'Покрытие корпуса',
        'filter_type': 'choice',
        'parameter_rule_code': None,
        'options': options.get('coating_options', []),
    })

    # Ручной дублёр
    fields.append({
        'param_name': 'hand_wheel_id',
        'model_field': 'hand_wheel_id',
        'label': 'Ручной дублёр',
        'filter_type': 'choice',
        'parameter_rule_code': None,
        'options': options.get('hand_wheel_options', []),
    })

    # IP
    fields.append({
        'param_name': 'ip_id',
        'model_field': 'ip',
        'label': 'IP защита',
        'filter_type': 'ip_rank',
        'parameter_rule_code': 'ip',
        'options': options.get('ip_options', []),
    })

    # Exd (наследуется из global)
    fields.append({
        'param_name': 'exd',
        'model_field': 'exd',
        'label': 'Взрывозащита (из глобальных)',
        'filter_type': 'exd_compatible',
        'parameter_rule_code': 'exd',
        'options': options.get('exd_options', []),
    })

    # Температура (наследуется из global)
    fields.append({
        'param_name': 'temp_min',
        'model_field': 'temp_min',
        'label': 'Мин. температура (из глобальных)',
        'filter_type': 'temp_min',
        'parameter_rule_code': 'temperature_min',
        'options': options.get('temperature_options', []),
    })
    fields.append({
        'param_name': 'temp_max',
        'model_field': 'temp_max',
        'label': 'Макс. температура (из глобальных)',
        'filter_type': 'temp_max',
        'parameter_rule_code': 'temperature_max',
        'options': options.get('temperature_options', []),
    })

    return fields
