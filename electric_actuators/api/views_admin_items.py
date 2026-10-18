# electric_actuators/api/views_admin_items.py
"""
Admin API для model_line_item: детальный просмотр и редактирование.

GET  /ea/admin/items/?model_line_id=X     → список model_line_item
GET  /ea/admin/items/<id>/                → один элемент + все опции
PUT  /ea/admin/items/<id>/                → сохранить базовые поля + power_supply_options

Опции БУ (ElectricControlUnitOption) и справочник схем ControlUnitWiring
удалены в фазе 7 — БУ×напряжение теперь в AllowedControlUnitOption, схемы —
в EaWiringDiagramBinding.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from project_customers.permissions import SectionAccessPermission
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from electric_actuators.models import (
    ElectricActuatorModelLine,
    ElectricActuatorModelLineItem,
)
from electric_actuators.models.ea_model_line_item_options import (
    ElectricPowerSupplyOption,
    ElectricSafetyPositionOption,
)


class EAModelLineItemListView(APIView):
    """Список model_line_item с фильтром по model_line."""
    permission_classes = [SectionAccessPermission]
    required_section = 'configurator_ea'

    def get(self, request):
        ml_id = request.query_params.get('model_line_id')
        if not ml_id:
            return Response({'error': 'model_line_id required'}, status=400)

        try:
            ml_id = int(ml_id)
        except (ValueError, TypeError):
            return Response({'error': 'invalid model_line_id'}, status=400)

        items = ElectricActuatorModelLineItem.objects.filter(
            model_line_id=ml_id, is_active=True
        ).select_related('model_line', 'body').order_by('sorting_order')

        data = []
        for item in items:
            data.append({
                'id': item.id,
                'name': item.name,
                'code': item.code,
                'description': item.description,
                'sorting_order': item.sorting_order,
                'is_active': item.is_active,
                'model_line': {'id': item.model_line_id, 'name': item.model_line.name} if item.model_line_id else None,
                'body': {'id': item.body_id, 'name': item.body.name} if item.body_id else None,
                'time_to_open': float(item.time_to_open) if item.time_to_open else 0,
                'time_to_close': float(item.time_to_close) if item.time_to_close else 0,
                'rotation_speed': float(item.rotation_speed) if item.rotation_speed else 0,
                'torque_min': float(item.torque_min) if item.torque_min else 0,
                'torque_max': float(item.torque_max) if item.torque_max else 0,
                'torque_work': float(item.torque_work) if item.torque_work else 0,
            })
        return Response(data)


# ═══════════════════════════════════════════════════════════════
# Полный список prefetch-цепочек (используется и в GET, и при
# перезапросе после PUT)
# ═══════════════════════════════════════════════════════════════

ITEM_PREFETCH_CHAINS = [
    'model_line_item_power_supply_option__power_supply',
    'model_line_item_power_supply_option__safety_position_power_supply_option__safety_position',
]


def _get_item_with_prefetch(pk):
    """Запросить model_line_item со всеми prefetch-цепочками."""
    return ElectricActuatorModelLineItem.objects.select_related(
        'model_line', 'body'
    ).prefetch_related(
        *ITEM_PREFETCH_CHAINS
    ).get(pk=pk)


class EAModelLineItemDetailView(APIView):
    """GET/PUT одного model_line_item со всеми опциями."""
    permission_classes = [SectionAccessPermission]
    required_section = 'configurator_ea'

    def get(self, request, pk):
        try:
            item = _get_item_with_prefetch(pk)
        except ElectricActuatorModelLineItem.DoesNotExist:
            return Response({'error': 'not found'}, status=404)

        return Response(_serialize_item(item))

    @transaction.atomic
    def put(self, request, pk):
        try:
            item = ElectricActuatorModelLineItem.objects.select_related(
                'model_line', 'body'
            ).get(pk=pk)
        except ElectricActuatorModelLineItem.DoesNotExist:
            return Response({'error': 'not found'}, status=404)

        errors = []

        # Обновить базовые поля
        for field in ['name', 'code', 'description', 'sorting_order']:
            if field in request.data:
                setattr(item, field, request.data[field])
        for field in ['time_to_open', 'time_to_close', 'rotation_speed',
                      'torque_min', 'torque_max', 'torque_work']:
            if field in request.data:
                val = request.data[field]
                setattr(item, field, val if val != '' else None)
        if 'body_id' in request.data:
            item.body_id = request.data['body_id'] or None

        try:
            item.save()
        except ValidationError as e:
            errors.append({'field': 'item', 'error': str(e)})
        except IntegrityError as e:
            errors.append({'field': 'item', 'error': str(e)})

        # Сохранить power_supply_options
        if 'power_supply_options' in request.data:
            save_errors = _save_power_supply_options(item, request.data['power_supply_options'])
            errors.extend(save_errors)

        if errors:
            return Response({'ok': False, 'errors': errors}, status=400)

        # Перезапросить с полным prefetch (refresh_from_db убивает prefetch-кеш)
        try:
            item = _get_item_with_prefetch(pk)
        except ElectricActuatorModelLineItem.DoesNotExist:
            return Response({'ok': True, 'warning': 'saved but could not reload'})

        return Response(_serialize_item(item))


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _serialize_item(item):
    """Сериализовать model_line_item со всеми вложенными опциями."""
    power_supply_options = []
    for pso in item.model_line_item_power_supply_option.all():
        sp_options = []
        for sp in pso.safety_position_power_supply_option.all():
            sp_options.append({
                'id': sp.id,
                'safety_position': {
                    'id': sp.safety_position_id,
                    'name': sp.safety_position.name,
                } if sp.safety_position_id else None,
                'encoding': sp.encoding,
                'is_default': sp.is_default,
                'is_active': sp.is_active,
                'sorting_order': sp.sorting_order,
            })

        power_supply_options.append({
            'id': pso.id,
            'power_supply': {
                'id': pso.power_supply_id,
                'name': str(pso.power_supply),
                'encoding': pso.power_supply.encoding if hasattr(pso.power_supply, 'encoding') else '',
            } if pso.power_supply_id else None,
            'motor_current_rated': float(pso.motor_current_rated) if pso.motor_current_rated else 0,
            'motor_current_starting': float(pso.motor_current_starting) if pso.motor_current_starting else 0,
            'motor_power': float(pso.motor_power) if pso.motor_power else 0,
            'time_to_open': float(pso.time_to_open) if pso.time_to_open else 0,
            'time_to_close': float(pso.time_to_close) if pso.time_to_close else 0,
            'torque_min': float(pso.torque_min) if pso.torque_min else 0,
            'torque_max': float(pso.torque_max) if pso.torque_max else 0,
            'is_active': pso.is_active,
            'sorting_order': pso.sorting_order,
            'control_unit_options': [],
            'safety_position_options': sp_options,
        })

    return {
        'id': item.id,
        'name': item.name,
        'code': item.code,
        'description': item.description,
        'sorting_order': item.sorting_order,
        'is_active': item.is_active,
        'model_line': {'id': item.model_line_id, 'name': item.model_line.name} if item.model_line_id else None,
        'body': {'id': item.body_id, 'name': item.body.name} if item.body_id else None,
        'time_to_open': float(item.time_to_open) if item.time_to_open else 0,
        'time_to_close': float(item.time_to_close) if item.time_to_close else 0,
        'rotation_speed': float(item.rotation_speed) if item.rotation_speed else 0,
        'torque_min': float(item.torque_min) if item.torque_min else 0,
        'torque_max': float(item.torque_max) if item.torque_max else 0,
        'torque_work': float(item.torque_work) if item.torque_work else 0,
        'power_supply_options': power_supply_options,
    }


def _save_power_supply_options(item, options_data):
    """Сохранить power_supply_options для model_line_item.
    Возвращает список ошибок (может быть пустым)."""
    errors = []
    for opt_data in options_data:
        pso_id = opt_data.get('id')
        if pso_id:
            try:
                pso = ElectricPowerSupplyOption.objects.get(id=pso_id, model_line_item=item)
            except ElectricPowerSupplyOption.DoesNotExist:
                continue
        else:
            continue

        for field in ['motor_current_rated', 'motor_current_starting', 'motor_power',
                      'time_to_open', 'time_to_close', 'torque_min', 'torque_max', 'sorting_order']:
            if field in opt_data:
                setattr(pso, field, opt_data[field])
        try:
            pso.save(preserve_encoding=True)
        except ValidationError as e:
            errors.append({'power_supply_option_id': pso_id, 'error': str(e)})
            continue  # не сохраняем вложенные опции, если родитель не прошёл валидацию

        # Сохранить safety_position_options
        if 'safety_position_options' in opt_data:
            for sp_data in opt_data['safety_position_options']:
                sp_id = sp_data.get('id')
                if not sp_id:
                    continue
                try:
                    sp = ElectricSafetyPositionOption.objects.get(id=sp_id, power_supply_option=pso)
                except ElectricSafetyPositionOption.DoesNotExist:
                    continue

                if 'encoding' in sp_data:
                    sp.encoding = sp_data['encoding']
                if 'is_default' in sp_data:
                    sp.is_default = sp_data['is_default']
                if 'sorting_order' in sp_data:
                    sp.sorting_order = sp_data['sorting_order']
                try:
                    sp.save()
                except ValidationError as e:
                    errors.append({'safety_position_option_id': sp_id, 'error': str(e)})

    return errors
