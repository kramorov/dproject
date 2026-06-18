# electric_actuators/api/views_admin_items.py
"""
Admin API для model_line_item: детальный просмотр и редактирование.

GET  /ea/admin/items/?model_line_id=X     → список model_line_item
GET  /ea/admin/items/<id>/                → один элемент + все опции
PUT  /ea/admin/items/<id>/                → сохранить базовые поля + power_supply_options
GET  /ea/admin/wirings/                   → справочник ControlUnitWiring
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from electric_actuators.models import (
    ElectricActuatorModelLine,
    ElectricActuatorModelLineItem,
)
from electric_actuators.models.ea_model_line_item_options import (
    ElectricPowerSupplyOption,
    ElectricControlUnitOption,
    ElectricSafetyPositionOption,
)
from electric_actuators.models.ea_control_unit_wiring import ControlUnitWiring
from params.models import PowerSupplies


class EAWiringRefsView(APIView):
    """Справочные данные для формы ControlUnitWiring."""
    permission_classes = [AllowAny]

    def get(self, request):
        from params.models import ControlUnitInstalledOption, ControlUnitSignalProfile
        from media_library.models import MediaLibraryItem

        cu = list(ControlUnitInstalledOption.objects.filter(is_active=True).values('id', 'name').order_by('name'))
        ps = list(PowerSupplies.objects.filter(is_active=True).values('id', 'name').order_by('name'))
        sp = list(ControlUnitSignalProfile.objects.filter(is_active=True).values('id', 'name').order_by('name'))
        img = list(MediaLibraryItem.objects.filter(
            category__code='SCHEMA', is_active=True
        ).values('id', 'name', 'code').order_by('name'))

        return Response({
            'control_units': [{'id': x['id'], 'name': x['name']} for x in cu],
            'power_supplies': [{'id': x['id'], 'name': x['name']} for x in ps],
            'signal_profiles': [{'id': x['id'], 'name': x['name']} for x in sp],
            'schema_images': [{'id': x['id'], 'name': x['name'], 'code': x['code']} for x in img],
        })


class EAModelLineItemListView(APIView):
    """Список model_line_item с фильтром по model_line."""
    permission_classes = [AllowAny]

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
    'model_line_item_power_supply_option__ea_model_line_item_options_power_supply_options__control_unit',
    'model_line_item_power_supply_option__ea_model_line_item_options_power_supply_options__control_unit_wiring__signal_profile',
    'model_line_item_power_supply_option__ea_model_line_item_options_power_supply_options__control_unit_wiring__wiring_diagram',
    'model_line_item_power_supply_option__ea_model_line_item_options_power_supply_options__default_turn_counter',
    'model_line_item_power_supply_option__ea_model_line_item_options_power_supply_options__allowed_turn_counters',
    'model_line_item_power_supply_option__ea_model_line_item_options_power_supply_options__power_supply_option__model_line_item__model_line',
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
    permission_classes = [AllowAny]

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


class EAAdminWiringsView(APIView):
    """Справочник ControlUnitWiring."""
    permission_classes = [AllowAny]

    def get(self, request, pk=None):
        # Детальный запрос: одна запись по pk
        if pk is not None:
            try:
                w = ControlUnitWiring.objects.select_related(
                    'control_unit', 'power_supply', 'signal_profile', 'wiring_diagram'
                ).get(pk=pk)
            except ControlUnitWiring.DoesNotExist:
                return Response({'error': 'not found'}, status=404)
            return Response(_serialize_wiring(w))

        # Список
        qs = ControlUnitWiring.objects.filter(is_active=True).select_related(
            'control_unit', 'power_supply', 'signal_profile', 'wiring_diagram'
        ).order_by('sorting_order', 'code')

        data = []
        for w in qs:
            data.append({
                'id': w.id,
                'code': w.code,
                'name': w.name,
                'description': w.description,
                'control_unit': {'id': w.control_unit_id, 'name': w.control_unit.name} if w.control_unit_id else None,
                'power_supply': {'id': w.power_supply_id, 'name': str(w.power_supply)} if w.power_supply_id else None,
                'signal_profile': {'id': w.signal_profile_id, 'name': w.signal_profile.name} if w.signal_profile_id else None,
                'wiring_diagram': _serialize_wiring_diagram(w),
                'cached_json': w.cached_json,
            })
        return Response(data)

    @transaction.atomic
    def post(self, request, pk=None):
        """Создать новую запись (без pk) или копию существующей (с pk)."""
        # Копирование: POST /wirings/<pk>/ (с pk в URL)
        if pk is not None:
            try:
                w = ControlUnitWiring.objects.get(pk=pk)
            except ControlUnitWiring.DoesNotExist:
                return Response({'error': 'not found'}, status=404)
            try:
                copied = w.copy(suffix=' (копия)')
            except Exception as e:
                return Response({'error': str(e)}, status=400)
            # Перезапросить с select_related, чтобы _serialize_wiring не делал N+1
            copied = ControlUnitWiring.objects.select_related(
                'control_unit', 'power_supply', 'signal_profile', 'wiring_diagram'
            ).get(pk=copied.pk)
            return Response(_serialize_wiring(copied), status=201)

        # Создание: POST /wirings/
        try:
            w = ControlUnitWiring(
                code=request.data.get('code', ''),
                name=request.data.get('name', ''),
                description=request.data.get('description', ''),
                is_active=request.data.get('is_active', True),
                sorting_order=request.data.get('sorting_order', 0),
            )
            for fk_field in ['control_unit_id', 'power_supply_id',
                             'signal_profile_id', 'wiring_diagram_id']:
                if fk_field in request.data:
                    setattr(w, fk_field, request.data[fk_field] or None)
            w.full_clean()
            w.save()
        except ValidationError as e:
            return Response({'ok': False, 'errors': str(e)}, status=400)
        except IntegrityError as e:
            return Response({'ok': False, 'errors': str(e)}, status=400)

        w = ControlUnitWiring.objects.select_related(
            'control_unit', 'power_supply', 'signal_profile', 'wiring_diagram'
        ).get(pk=w.pk)
        return Response(_serialize_wiring(w), status=201)

    @transaction.atomic
    def put(self, request, pk=None):
        """Обновить запись ControlUnitWiring."""
        if pk is None:
            return Response({'error': 'id required'}, status=400)
        try:
            w = ControlUnitWiring.objects.get(pk=pk)
        except ControlUnitWiring.DoesNotExist:
            return Response({'error': 'not found'}, status=404)

        for field in ['code', 'name', 'description', 'is_active', 'sorting_order']:
            if field in request.data:
                setattr(w, field, request.data[field])
        for fk_field in ['control_unit_id', 'power_supply_id',
                         'signal_profile_id', 'wiring_diagram_id']:
            if fk_field in request.data:
                setattr(w, fk_field, request.data[fk_field] or None)
        try:
            w.full_clean()
            w.save()
        except ValidationError as e:
            return Response({'ok': False, 'errors': str(e)}, status=400)
        except IntegrityError as e:
            return Response({'ok': False, 'errors': str(e)}, status=400)

        try:
            w = ControlUnitWiring.objects.select_related(
                'control_unit', 'power_supply', 'signal_profile', 'wiring_diagram'
            ).get(pk=w.pk)
        except ControlUnitWiring.DoesNotExist:
            return Response({'ok': True, 'warning': 'updated but could not reload'})

        return Response(_serialize_wiring(w))

    @transaction.atomic
    def delete(self, request, pk=None):
        """Удалить запись ControlUnitWiring."""
        if pk is None:
            return Response({'error': 'id required'}, status=400)
        try:
            w = ControlUnitWiring.objects.get(pk=pk)
        except ControlUnitWiring.DoesNotExist:
            return Response({'error': 'not found'}, status=404)

        # Проверить, не используется ли в ElectricControlUnitOption
        used = ElectricControlUnitOption.objects.filter(
            control_unit_wiring_id=pk
        ).exists()
        if used:
            return Response({'error': 'Нельзя удалить: схема используется в опциях БУ'}, status=409)
        w.delete()
        return Response({'ok': True})

# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _serialize_item(item):
    """Сериализовать model_line_item со всеми вложенными опциями."""
    power_supply_options = []
    for pso in item.model_line_item_power_supply_option.all():
        cu_options = []
        for cu in pso.ea_model_line_item_options_power_supply_options.all():
            cu_data = {
                'id': cu.id,
                'control_unit': {'id': cu.control_unit_id, 'name': cu.control_unit.name} if cu.control_unit_id else None,
                'control_unit_wiring': {
                    'id': cu.control_unit_wiring_id,
                    'code': cu.control_unit_wiring.code,
                    'name': cu.control_unit_wiring.name,
                    'signal_profile': {
                        'id': cu.control_unit_wiring.signal_profile_id,
                        'name': cu.control_unit_wiring.signal_profile.name,
                    } if (cu.control_unit_wiring_id and cu.control_unit_wiring.signal_profile_id) else None,
                    'wiring_diagram': _serialize_wiring_diagram(cu.control_unit_wiring) if cu.control_unit_wiring_id else None,
                } if cu.control_unit_wiring_id else None,
                'encoding': cu.resolved_encoding if hasattr(cu, 'resolved_encoding') else cu.encoding,
                'is_default': cu.is_default,
                'is_active': cu.is_active,
                'sorting_order': cu.sorting_order,
                'default_turn_counter': {
                    'id': cu.default_turn_counter_id,
                    'name': cu.default_turn_counter.name,
                } if cu.default_turn_counter_id else None,
                'allowed_turn_counters': [
                    {'id': tc.id, 'name': tc.name}
                    for tc in cu.allowed_turn_counters.all()
                ],
            }
            cu_options.append(cu_data)

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
            'control_unit_options': cu_options,
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


def _serialize_wiring(w):
    """Сериализовать одну запись ControlUnitWiring."""
    return {
        'id': w.id,
        'code': w.code,
        'name': w.name,
        'description': w.description,
        'is_active': w.is_active,
        'sorting_order': w.sorting_order,
        'control_unit': {'id': w.control_unit_id, 'name': w.control_unit.name} if w.control_unit_id else None,
        'power_supply': {'id': w.power_supply_id, 'name': str(w.power_supply)} if w.power_supply_id else None,
        'signal_profile': {'id': w.signal_profile_id, 'name': w.signal_profile.name} if w.signal_profile_id else None,
        'wiring_diagram': _serialize_wiring_diagram(w),
        'cached_json': w.cached_json,
    }


def _serialize_wiring_diagram(obj):
    """Сериализовать изображение схемы из ControlUnitWiring или MediaLibraryItem."""
    if not obj or not obj.wiring_diagram_id:
        return None
    img = obj.wiring_diagram
    return {
        'id': img.id,
        'name': img.name,
        'code': img.code,
        'preview_url': getattr(img, 'preview_url', None),
        'serve_url': img.get_serve_url() if hasattr(img, 'get_serve_url') else None,
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

        # Сохранить control_unit_options
        if 'control_unit_options' in opt_data:
            for cu_data in opt_data['control_unit_options']:
                cu_id = cu_data.get('id')
                if not cu_id:
                    continue
                try:
                    cu = ElectricControlUnitOption.objects.get(id=cu_id, power_supply_option=pso)
                except ElectricControlUnitOption.DoesNotExist:
                    continue

                if 'control_unit_wiring_id' in cu_data:
                    cu.control_unit_wiring_id = cu_data['control_unit_wiring_id'] or None
                if 'is_default' in cu_data:
                    cu.is_default = cu_data['is_default']
                if 'sorting_order' in cu_data:
                    cu.sorting_order = cu_data['sorting_order']
                try:
                    cu.save()
                except ValidationError as e:
                    errors.append({'control_unit_option_id': cu_id, 'error': str(e)})

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