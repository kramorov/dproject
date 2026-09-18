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
from project_customers.permissions import SectionAccessPermission
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
    permission_classes = [SectionAccessPermission]
    required_section = 'configurator_pa'
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

    def _materialize_item(self, obj):
        """
        Записать конфигурацию конструктора в эталонную PneumaticActuatorItem + SKU.

        Constructor — только форма: результат записи — item каталога
        (автогенерация code/name/description из шаблонов серии) и SKU,
        созданный из него через SKUMixin.sync_sku().

        Returns:
            (item, sku) или (None, None) при ошибке/отсутствии модели.
        """
        import logging
        logger = logging.getLogger(__name__)

        from pneumatic_actuators.services.sku_service import get_or_create_sku
        from pneumatic_actuators.models.pa_item import PneumaticActuatorItem

        if not obj.selected_model_line_item_id:
            return None, None

        options = {
            'springs_qty': obj.selected_springs_qty_id,
            'temperature': obj.selected_temperature_id,
            'safety_position': obj.selected_safety_position_id,
            'ip': obj.selected_ip_id,
            'exd': obj.selected_exd_id,
            'body_coating': obj.selected_body_coating_id,
            'hand_wheel': obj.selected_hand_wheel_id,
        }
        try:
            sku = get_or_create_sku(obj.selected_model_line_item, options)
        except Exception as e:
            logger.error(f"Материализация item не удалась: {e}")
            return None, None

        item = None
        if sku and sku.source_content_type_id and sku.source_object_id:
            item = PneumaticActuatorItem.objects.filter(pk=sku.source_object_id).first()
        return item, sku

    def _attach_item_sku(self, data, obj):
        """Добавить в ответ item (to_dict) и sku (кратко)."""
        item, sku = self._materialize_item(obj)
        data['item'] = item.to_dict() if item else None
        if sku:
            data['sku'] = {
                'id': sku.id, 'code': sku.code, 'name': sku.name,
                'description': sku.description,
            }
        else:
            data['sku'] = None
        return data

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
                data = self._serialize_detail(existing)
                data = self._attach_item_sku(data, existing)
                return Response(data, status=status.HTTP_200_OK)
        obj.save()
        data = self._serialize_detail(obj)
        data = self._attach_item_sku(data, obj)
        return Response(data, status=status.HTTP_201_CREATED)

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
        data = self._serialize_detail(obj)
        data = self._attach_item_sku(data, obj)
        return Response(data)

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
        Превью: возвращает to_dict() model_line_item + динамический код/описание.
        """
        obj = self._build_from_request(request)
        obj._ensure_valid_options()
        if obj.selected_temperature:
            obj.work_temp_min = obj.selected_temperature.work_temp_min
            obj.work_temp_max = obj.selected_temperature.work_temp_max

        mli = obj.selected_model_line_item
        if not mli:
            return Response({'error': 'model_line_item required'}, status=400)

        # Базовая структура из to_dict()
        data = mli.to_dict()

        # Переопределяем title/code/description динамическим кодом
        data['title'] = obj.generated_model_item_code
        data['code'] = obj.generated_model_item_code
        data['description'] = obj._generate_short_description()
        # Подменяем статичное описание в секции на динамическое
        for s in data.get('sections', []):
            if s.get('key') == 'description':
                s['data'] = data['description']
        data['tech_description'] = obj._generate_tech_description()  # HTML для кнопки «Просмотр» в legacy-конструкторе

        # === Перестраиваем specs из spec_template (серия → EquipmentType) ===
        spec_vars = obj.get_spec_vars()
        spec_data = mli._get_spec_sections(vars=spec_vars)

        data['sections'] = [s for s in data.get('sections', []) if s['key'] != 'specs']
        data['sections'].insert(1, {
            'key': 'specs', 'title': 'Характеристики', 'type': 'specs', 'order': 1,
            'data': spec_data,
        })

        return Response(data)

    @action(detail=False, methods=['post'], url_path='create-sku')
    def create_sku(self, request):
        """
        Создать SKU для конфигурации пневмопривода (ленивое создание).
        Принимает: model_line_item_id + options.
        """
        from pneumatic_actuators.services.sku_service import get_or_create_sku
        from pneumatic_actuators.models import PneumaticActuatorModelLineItem

        mli_id = request.data.get('model_line_item_id')
        options = request.data.get('options', {})
        if not mli_id:
            return Response({'error': 'model_line_item_id required'}, status=400)

        try:
            mli = PneumaticActuatorModelLineItem.objects.get(id=mli_id)
        except PneumaticActuatorModelLineItem.DoesNotExist:
            return Response({'error': 'Model line item not found'}, status=404)

        # Разрешаем реальные объекты опций по ID
        resolved_options = {}
        for key, value in options.items():
            if value is None:
                continue
            resolved_options[key] = value

        try:
            sku = get_or_create_sku(mli, resolved_options)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

        return Response({
            'id': sku.id, 'code': sku.code, 'name': sku.name, 'description': sku.description,
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
