# pneumatic_actuators/api/views_constructor.py
"""
API для конструктора пневмоприводов (PneumaticActuatorConstructor).

Эндпоинты:
    GET    /constructor/                    — список сконструированных приводов
    POST   /constructor/                    — создать новую конфигурацию
    GET    /constructor/<id>/               — детальная информация
    PUT    /constructor/<id>/               — обновить конфигурацию
    DELETE /constructor/<id>/               — удалить
    GET    /constructor/<id>/options/       — доступные опции для модели
    GET    /constructor/model-lines/        — список серий
    GET    /constructor/model-lines/<id>/items/ — модели серии
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action

from pneumatic_actuators.models import (
    PneumaticActuatorConstructor,
    PneumaticActuatorModelLine,
    PneumaticActuatorModelLineItem,
)


class ConstructorViewSet(viewsets.ModelViewSet):
    """
    CRUD для конструктора пневмоприводов.
    """
    permission_classes = [AllowAny]
    queryset = PneumaticActuatorConstructor.objects.filter(is_active=True)

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
            'selected_safety_position',
            'selected_springs_qty',
            'selected_temperature',
            'selected_ip',
            'selected_exd',
            'selected_body_coating',
            'selected_hand_wheel',
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
        return PneumaticActuatorConstructor(
            selected_model_line_id=request.data.get('selected_model_line'),
            selected_model_line_item_id=request.data.get('selected_model_line_item'),
            selected_safety_position_id=request.data.get('selected_safety_position'),
            selected_springs_qty_id=request.data.get('selected_springs_qty'),
            selected_temperature_id=request.data.get('selected_temperature'),
            selected_ip_id=request.data.get('selected_ip'),
            selected_exd_id=request.data.get('selected_exd'),
            selected_body_coating_id=request.data.get('selected_body_coating'),
            selected_hand_wheel_id=request.data.get('selected_hand_wheel'),
            sorting_order=request.data.get('sorting_order', 0),
            is_active=request.data.get('is_active', True),
        )

    def create(self, request, *args, **kwargs):
        obj = self._build_from_request(request)
        # Проверка дубликата: если конфигурация уже существует — возвращаем её
        existing_msg = obj._check_for_duplicates()
        if existing_msg:
            # Ищем существующую запись
            existing = PneumaticActuatorConstructor.objects.filter(
                selected_model_line_item=obj.selected_model_line_item,
                selected_safety_position=obj.selected_safety_position,
                selected_springs_qty=obj.selected_springs_qty,
                selected_temperature=obj.selected_temperature,
                selected_ip=obj.selected_ip,
                selected_exd=obj.selected_exd,
                selected_body_coating=obj.selected_body_coating,
                selected_hand_wheel=obj.selected_hand_wheel,
                is_active=True,
            ).first()
            if existing:
                return Response(self._serialize_detail(existing), status=status.HTTP_200_OK)
        obj.save()
        return Response(self._serialize_detail(obj), status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        for field in [
            'selected_model_line', 'selected_model_line_item',
            'selected_safety_position', 'selected_springs_qty',
            'selected_temperature', 'selected_ip', 'selected_exd',
            'selected_body_coating', 'selected_hand_wheel',
        ]:
            value = request.data.get(field)
            if value is not None:
                setattr(obj, f'{field}_id', value)
        if 'sorting_order' in request.data:
            obj.sorting_order = request.data['sorting_order']
        if 'is_active' in request.data:
            obj.is_active = request.data['is_active']
        obj.save()
        return Response(self._serialize_detail(obj))

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='options')
    def options(self, request):
        """Доступные опции для модели. ?model_line_item_id=X"""
        mli_id = request.query_params.get('model_line_item_id')
        if not mli_id:
            return Response({'error': 'model_line_item_id required'}, status=400)
        # Временный инстанс только для вызова get_available_options
        obj = PneumaticActuatorConstructor(selected_model_line_item_id=mli_id)
        return Response(obj.get_available_options())

    @action(detail=False, methods=['get'])
    def model_lines(self, request):
        """Список активных серий пневмоприводов."""
        items = PneumaticActuatorModelLine.objects.filter(is_active=True).order_by('sorting_order')
        return Response([
            {'id': ml.id, 'name': ml.name, 'code': ml.code}
            for ml in items
        ])

    @action(detail=False, methods=['get'], url_path='model-lines/(?P<ml_id>[^/.]+)/items')
    def model_line_items(self, request, ml_id=None):
        """Модели в серии. ?variety=DA|SR — фильтр по виду привода."""
        qs = PneumaticActuatorModelLineItem.objects.filter(
            model_line_id=ml_id, is_active=True
        )
        variety = request.query_params.get('variety')
        if variety:
            qs = qs.filter(pneumatic_actuator_variety__code=variety)
        qs = qs.order_by('sorting_order')
        return Response([
            {
                'id': item.id, 'name': item.name, 'code': item.code,
                'variety': item.pneumatic_actuator_variety.code if item.pneumatic_actuator_variety else None,
            }
            for item in qs
        ])

    @action(detail=False, methods=['post'])
    def preview(self, request):
        """
        Превью кода и описания без сохранения в базу.
        Принимает: selected_model_line_item, + опции (selected_safety_position, ...).
        Возвращает: {name, code, description}.
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
            'model_line': {'id': obj.selected_model_line_id, 'name': str(obj.selected_model_line)} if obj.selected_model_line else None,
            'model_line_item': {'id': obj.selected_model_line_item_id, 'name': str(obj.selected_model_line_item)} if obj.selected_model_line_item else None,
            'is_active': obj.is_active,
            'sorting_order': obj.sorting_order,
        }

    def _serialize_detail(self, obj):
        data = self._serialize(obj)
        data.update({
            'selected_safety_position': _fk_dict(obj.selected_safety_position),
            'selected_springs_qty': _fk_dict(obj.selected_springs_qty),
            'selected_temperature': _fk_dict(obj.selected_temperature),
            'selected_ip': _fk_dict(obj.selected_ip),
            'selected_exd': _fk_dict(obj.selected_exd),
            'selected_body_coating': _fk_dict(obj.selected_body_coating),
            'selected_hand_wheel': _fk_dict(obj.selected_hand_wheel),
            'work_temp_min': obj.work_temp_min,
            'work_temp_max': obj.work_temp_max,
        })
        return data


def _fk_dict(fk_obj):
    if not fk_obj:
        return None
    return {'id': fk_obj.id, 'name': str(fk_obj), 'code': getattr(fk_obj, 'code', '') or getattr(fk_obj, 'encoding', '')}
