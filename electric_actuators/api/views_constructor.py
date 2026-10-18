# electric_actuators/api/views_constructor.py
"""
API для конструктора электроприводов (ElectricActuatorConstructor).

Эндпоинты:
    GET    /constructor/                    — список сконструированных приводов
    POST   /constructor/                    — создать новую конфигурацию
    GET    /constructor/<id>/               — детальная информация
    PUT    /constructor/<id>/               — обновить конфигурацию
    DELETE /constructor/<id>/               — удалить
    GET    /constructor/<id>/options/       — доступные опции для модели
    POST   /constructor/preview/            — превью кода/описания без сохранения
    GET    /constructor/model-lines/        — список серий
    GET    /constructor/model-lines/<id>/items/ — модели серии
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from project_customers.permissions import SectionAccessPermission
from rest_framework.decorators import action

from electric_actuators.models import (
    ElectricActuatorConstructor,
    ElectricActuatorModelLine,
    ElectricActuatorModelLineItem,
)


class ConstructorViewSet(viewsets.ModelViewSet):
    """
    CRUD для конструктора электроприводов.
    """
    permission_classes = [SectionAccessPermission]
    required_section = 'configurator_ea'
    queryset = ElectricActuatorConstructor.objects.filter(is_active=True)

    def get_queryset(self):
        qs = super().get_queryset()
        model_line_id = self.request.query_params.get('model_line_id')
        model_line_item_id = self.request.query_params.get('model_line_item_id')
        if model_line_id:
            qs = qs.filter(selected_model_line_id=model_line_id)
        if model_line_item_id:
            qs = qs.filter(selected_model_line_item_id=model_line_item_id)
        return qs.select_related(
            'selected_model_line',
            'selected_model_line_item',
            'selected_power_supply',
            'selected_safety_position',
            'selected_control_unit_option',
            'selected_temperature',
            'selected_ip',
            'selected_exd',
            'selected_body_coating',
            'selected_body_color_option',
            'selected_hand_wheel',
            'selected_turn_angle_option',
            'selected_cable_glands_holes',
        )

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = []
        for obj in qs:
            data.append(self._serialize(obj))
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        return Response(self._serialize_detail(obj))

    def _build_from_request(self, request):
        """Создать инстанс из данных запроса (без сохранения)."""
        return ElectricActuatorConstructor(
            selected_model_line_id=request.data.get('selected_model_line'),
            selected_model_line_item_id=request.data.get('selected_model_line_item'),
            selected_power_supply_id=request.data.get('selected_power_supply'),
            selected_safety_position_id=request.data.get('selected_safety_position'),
            selected_control_unit_option_id=request.data.get('selected_control_unit_option'),
            selected_access_device_option_id=request.data.get('selected_access_device_option'),
            selected_temperature_id=request.data.get('selected_temperature'),
            selected_ip_id=request.data.get('selected_ip'),
            selected_exd_id=request.data.get('selected_exd'),
            selected_body_coating_id=request.data.get('selected_body_coating'),
            selected_body_color_option_id=request.data.get('selected_body_color_option'),
            selected_hand_wheel_id=request.data.get('selected_hand_wheel'),
            selected_turn_angle_option_id=request.data.get('selected_turn_angle_option'),
            selected_cable_glands_holes_id=request.data.get('selected_cable_glands_holes'),
            actual_mounting_plate_id=request.data.get('actual_mounting_plate'),
            actual_stem_shape_id=request.data.get('actual_stem_shape'),
            actual_stem_size_id=request.data.get('actual_stem_size'),
            actual_cable_glands_holes_id=request.data.get('actual_cable_glands_holes'),
            sorting_order=request.data.get('sorting_order', 0),
            is_active=request.data.get('is_active', True),
        )

    def create(self, request, *args, **kwargs):
        obj = self._build_from_request(request)
        # Проверка дубликата: если конфигурация уже существует — возвращаем её
        existing_msg = obj._check_for_duplicates()
        if existing_msg:
            # Дубликат: сигнальные опции применяем к найденной конфигурации
            existing = ElectricActuatorConstructor.objects.filter(
                selected_model_line_item=obj.selected_model_line_item,
                selected_power_supply=obj.selected_power_supply,
                selected_safety_position=obj.selected_safety_position,
                selected_control_unit_option=obj.selected_control_unit_option,
                selected_temperature=obj.selected_temperature,
                selected_ip=obj.selected_ip,
                selected_exd=obj.selected_exd,
                selected_body_coating=obj.selected_body_coating,
                selected_body_color_option=obj.selected_body_color_option,
                selected_hand_wheel=obj.selected_hand_wheel,
                selected_turn_angle_option=obj.selected_turn_angle_option,
                selected_cable_glands_holes=obj.selected_cable_glands_holes,
                is_active=True,
            ).first()
            if existing:
                if 'selected_matrix_rows' in request.data:
                    self._set_matrix_rows(existing, request.data)
                return Response(self._serialize_detail(existing), status=status.HTTP_200_OK)
        obj.save()
        if 'selected_matrix_rows' in request.data:
            self._set_matrix_rows(obj, request.data)
        return Response(self._serialize_detail(obj), status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        for field in [
            'selected_model_line', 'selected_model_line_item',
            'selected_power_supply', 'selected_safety_position',
            'selected_control_unit_option', 'selected_access_device_option',
            'selected_temperature',
            'selected_ip', 'selected_exd', 'selected_body_coating',
            'selected_body_color_option', 'selected_hand_wheel',
            'selected_turn_angle_option', 'selected_cable_glands_holes',
            'actual_mounting_plate', 'actual_stem_shape', 'actual_stem_size',
            'actual_cable_glands_holes',
        ]:
            value = request.data.get(field)
            if value is not None:
                setattr(obj, f'{field}_id', value)
        if 'sorting_order' in request.data:
            obj.sorting_order = request.data['sorting_order']
        if 'is_active' in request.data:
            obj.is_active = request.data['is_active']
        if 'selected_matrix_rows' in request.data:
            self._set_matrix_rows(obj, request.data)
        obj.save()
        return Response(self._serialize_detail(obj))

    @staticmethod
    def _parse_matrix_row_ids(data):
        """Список id строк матрицы из запроса (валидные числа)."""
        return [int(x) for x in data if str(x).isdigit()]

    def _valid_matrix_row_ids(self, obj):
        """Валидные id строк сигнального профиля для конфигурации.
        None — проверить нельзя (не хватает модели/БУ/напряжения)."""
        if not (obj.selected_model_line_item_id
                and obj.selected_control_unit_option_id
                and obj.selected_power_supply_id):
            return None
        try:
            from electric_actuators.services.ea_configurator_data import (
                configurator_signal_data)
            sig = configurator_signal_data(
                obj.selected_model_line_item,
                obj.selected_control_unit_option,
                obj.selected_power_supply.power_supply,
                'on_off')
            return {row['id'] for slot in sig['slots'] for row in slot['rows']}
        except Exception:  # noqa: BLE001
            return None

    def _set_matrix_rows(self, obj, data):
        from electric_actuators.models import EaSignalMatrixEntry
        ids = self._parse_matrix_row_ids(data.get('selected_matrix_rows') or [])
        valid = self._valid_matrix_row_ids(obj)
        if valid is not None:
            ids = [i for i in ids if i in valid]
        obj.selected_matrix_rows.set(
            EaSignalMatrixEntry.objects.filter(pk__in=ids))

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='options')
    def options(self, request):
        """Доступные опции для модели.
        ?model_line_item_id=X&power_supply_id=Y&control_unit_id=Z"""
        from core.utils.localization import locale_from_accept_language
        locale = locale_from_accept_language(
            request.headers.get('Accept-Language'))
        mli_id = request.query_params.get('model_line_item_id')
        if not mli_id:
            return Response({'error': 'model_line_item_id required'}, status=400)
        # Временный инстанс: опции зависят от model_line_item + power_supply
        kwargs = {'selected_model_line_item_id': mli_id}
        ps_id = request.query_params.get('power_supply_id')
        if ps_id:
            kwargs['selected_power_supply_id'] = ps_id
        cu_id = request.query_params.get('control_unit_id')
        if cu_id:
            kwargs['selected_control_unit_option_id'] = cu_id
        obj = ElectricActuatorConstructor(**kwargs)
        return Response(obj.get_available_options(locale=locale))

    @action(detail=False, methods=['get'], url_path='power-supplies')
    def power_supplies(self, request):
        """Уникальные напряжения для всей серии. ?model_line_id=X"""
        ml_id = request.query_params.get('model_line_id')
        if not ml_id:
            return Response({'error': 'model_line_id required'}, status=400)

        from electric_actuators.models import ElectricPowerSupplyOption
        ps_options = ElectricPowerSupplyOption.objects.filter(
            model_line_item__model_line_id=ml_id,
            is_active=True
        ).select_related('power_supply').order_by('power_supply__sorting_order')

        seen = set()
        result = []
        for opt in ps_options:
            if opt.power_supply_id not in seen:
                seen.add(opt.power_supply_id)
                result.append({
                    'id': opt.id, 'option_id': opt.id,
                    'encoding': opt.power_supply.encoding or opt.encoding,
                    'name': str(opt.power_supply),
                    'description': opt.power_supply.description or '',
                    'power_supply_id': opt.power_supply_id,
                })
        return Response(result)

    @action(detail=False, methods=['get'])
    def model_lines(self, request):
        """Список активных серий электроприводов."""
        items = ElectricActuatorModelLine.objects.filter(is_active=True).order_by('sorting_order')
        return Response([
            {'id': ml.id, 'name': ml.name, 'code': ml.code}
            for ml in items
        ])

    @action(detail=False, methods=['get'], url_path='model-lines/(?P<ml_id>[^/.]+)/items')
    def model_line_items(self, request, ml_id=None):
        """Модели в серии."""
        qs = ElectricActuatorModelLineItem.objects.filter(
            model_line_id=ml_id, is_active=True
        ).order_by('sorting_order')
        return Response([
            {
                'id': item.id, 'name': item.name, 'code': item.code,
            }
            for item in qs
        ])

    @action(detail=False, methods=['post'])
    def preview(self, request):
        """
        Превью кода и описания без сохранения в базу.
        Принимает: selected_model_line_item, + опции.
        Возвращает: {name, code, description, tech_description}.
        """
        obj = self._build_from_request(request)
        # Генерация без сохранения
        obj._ensure_valid_options()
        if obj.selected_temperature:
            obj.work_temp_min = obj.selected_temperature.work_temp_min
            obj.work_temp_max = obj.selected_temperature.work_temp_max
        return Response({
            'name': obj.generated_model_item_code,
            'code': obj.generated_model_item_code,
            'description': obj._generate_short_description(),
            'tech_description': obj._generate_tech_description(),
        })

    # --- serialization helpers ---

    def _serialize(self, obj):
        return {
            'id': obj.id,
            'name': obj.name,
            'code': obj.code,
            'description': obj.description,
            'model_line': _fk_dict(obj.selected_model_line),
            'model_line_item': _fk_dict(obj.selected_model_line_item),
            'is_active': obj.is_active,
            'sorting_order': obj.sorting_order,
        }

    def _serialize_detail(self, obj):
        data = self._serialize(obj)
        data.update({
            'selected_power_supply': _fk_dict(obj.selected_power_supply),
            'selected_safety_position': _fk_dict(obj.selected_safety_position),
            'selected_control_unit_option': _fk_dict(obj.selected_control_unit_option),
            'selected_access_device_option': _fk_dict(obj.selected_access_device_option),
            'selected_temperature': _fk_dict(obj.selected_temperature),
            'selected_ip': _fk_dict(obj.selected_ip),
            'selected_exd': _fk_dict(obj.selected_exd),
            'selected_body_coating': _fk_dict(obj.selected_body_coating),
            'selected_body_color_option': _fk_dict(obj.selected_body_color_option),
            'selected_hand_wheel': _fk_dict(obj.selected_hand_wheel),
            'selected_turn_angle_option': _fk_dict(obj.selected_turn_angle_option),
            'selected_cable_glands_holes': _fk_dict(obj.selected_cable_glands_holes),
            'selected_matrix_rows': list(obj.selected_matrix_rows.values_list(
                'pk', flat=True)) if obj.pk else [],
            'actual_mounting_plate': _fk_dict(obj.actual_mounting_plate),
            'actual_stem_shape': _fk_dict(obj.actual_stem_shape),
            'actual_stem_size': _fk_dict(obj.actual_stem_size),
            'actual_cable_glands_holes': _fk_dict(obj.actual_cable_glands_holes),
            'work_temp_min': obj.work_temp_min,
            'work_temp_max': obj.work_temp_max,
        })
        return data


def _fk_dict(fk_obj):
    if not fk_obj:
        return None
    return {'id': fk_obj.id, 'name': str(fk_obj), 'code': getattr(fk_obj, 'code', '') or getattr(fk_obj, 'encoding', '')}
