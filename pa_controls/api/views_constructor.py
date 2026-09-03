# pa_controls/api/views_constructor.py
"""
API для конструктора позиционеров (PositionerConstructor).

Паттерн — electric_actuators/api/views_constructor.py и
pneumatic_actuators/api/views_constructor.py.

Эндпоинты:
    GET    /constructor/                    — список сохранённых конфигураций
    POST   /constructor/                    — создать конфигурацию (+ item/SKU)
    GET    /constructor/<id>/               — детальная информация
    PUT    /constructor/<id>/               — обновить конфигурацию (+ item/SKU)
    DELETE /constructor/<id>/               — удалить (жёстко)
    GET    /constructor/acting-types/       — типы действия (линейный/ротационный)
    GET    /constructor/model-lines/        — серии (?acting_type= для фильтра)
    GET    /constructor/options/            — опции серии (?model_line=)
    POST   /constructor/preview/            — превью артикула/описания без сохранения
"""
import logging

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from project_customers.permissions import SectionAccessPermission
from pa_controls.models import PosiModelLine, PosiModelLineItem, PositionerConstructor
from pa_controls.models.posi_options import ActingType
from pa_controls.services.posi_sku_service import materialize

logger = logging.getLogger(__name__)


class PosiConstructorViewSet(viewsets.ModelViewSet):
    """CRUD + каскадные справочники конструктора позиционеров."""
    permission_classes = [SectionAccessPermission]
    required_section = 'configurator_pa'
    queryset = PositionerConstructor.objects.filter(is_active=True)

    # ── queryset / list / retrieve ──

    def get_queryset(self):
        qs = super().get_queryset()
        model_line_id = self.request.query_params.get('model_line_id')
        acting_type_id = self.request.query_params.get('acting_type_id')
        if model_line_id:
            qs = qs.filter(selected_model_line_id=model_line_id)
        if acting_type_id:
            qs = qs.filter(selected_model_line__acting_type_id=acting_type_id)
        return qs.select_related(
            'selected_model_line',
            'selected_model_line__acting_type',
            'selected_model_line__brand',
            'selected_body_connection',
            'selected_lever',
            'selected_temperature',
            'selected_signal_profile',
            'selected_signal_profile_option',
            'selected_smart_capability_set',
            'selected_alarm',
            'selected_exd_row',
            'selected_exd',
        )

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        return Response([self._serialize(obj) for obj in qs])

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        data = self._serialize_detail(obj)
        return Response(data)

    # ── сборка из запроса ──

    def _build_from_request(self, request):
        """Инстанс формы из данных запроса (без сохранения)."""
        return PositionerConstructor(
            selected_model_line_id=request.data.get('selected_model_line'),
            selected_body_connection_id=request.data.get('selected_body_connection'),
            selected_lever_id=request.data.get('selected_lever'),
            selected_temperature_id=request.data.get('selected_temperature'),
            selected_signal_profile_option_id=request.data.get('selected_signal_profile_option'),
            selected_alarm_id=request.data.get('selected_alarm'),
            selected_exd_row_id=request.data.get('selected_exd_row'),
            selected_exd_id=request.data.get('selected_exd'),
        )

    def _prepare(self, obj):
        """Дефолты + синк производных полей + name/code/description (без сохранения)."""
        obj._ensure_valid_options()
        obj._sync_derived_fields()
        item = obj.build_preview_item()
        if item:
            obj.name = item.name or ''
            obj.code = item.code or None
            obj.description = item.description or ''
        return obj

    # ── create / update / destroy ──

    def create(self, request, *args, **kwargs):
        obj = self._build_from_request(request)
        if not obj.selected_model_line_id:
            return Response({'error': 'selected_model_line required'}, status=400)
        try:
            self._prepare(obj)
        except ObjectDoesNotExist:
            return Response({'error': 'Серия или опция не найдена'}, status=404)

        # Дедупликация форм: тот же набор опций → возвращаем существующую
        existing = self._find_duplicate(obj)
        if existing:
            item, sku = self._materialize(existing)
            data = self._serialize_detail(existing)
            self._attach_item_sku(data, item, sku)
            return Response(data, status=status.HTTP_200_OK)

        try:
            item, sku = materialize(obj)
        except ValidationError as e:
            return Response(_validation_error_payload(e), status=400)

        obj.save()
        data = self._serialize_detail(obj)
        self._attach_item_sku(data, item, sku)
        return Response(data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        for field, model_field in [
            ('selected_model_line', 'selected_model_line'),
            ('selected_body_connection', 'selected_body_connection'),
            ('selected_lever', 'selected_lever'),
            ('selected_temperature', 'selected_temperature'),
            ('selected_signal_profile_option', 'selected_signal_profile_option'),
            ('selected_alarm', 'selected_alarm'),
            ('selected_exd_row', 'selected_exd_row'),
            ('selected_exd', 'selected_exd'),
        ]:
            if field in request.data:
                setattr(obj, f'{model_field}_id', request.data[field])
        if 'sorting_order' in request.data:
            obj.sorting_order = request.data['sorting_order']
        if 'is_active' in request.data:
            obj.is_active = request.data['is_active']

        try:
            self._prepare(obj)
        except ObjectDoesNotExist:
            return Response({'error': 'Серия или опция не найдена'}, status=404)

        try:
            item, sku = materialize(obj)
        except ValidationError as e:
            return Response(_validation_error_payload(e), status=400)

        obj.save()
        data = self._serialize_detail(obj)
        self._attach_item_sku(data, item, sku)
        return Response(data)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── справочники каскада ──

    @action(detail=False, methods=['get'], url_path='acting-types')
    def acting_types(self, request):
        """Типы действия позиционера (шаг 0 конструктора)."""
        items = ActingType.objects.filter(is_active=True).order_by('sorting_order', 'code')
        return Response([
            {'id': at.id, 'code': at.code, 'name': at.name}
            for at in items
        ])

    @action(detail=False, methods=['get'], url_path='model-lines')
    def model_lines(self, request):
        """Активные серии позиционеров. ?acting_type=<id> — фильтр по типу действия."""
        qs = PosiModelLine.objects.filter(is_active=True).order_by('sorting_order', 'code')
        acting_type_id = request.query_params.get('acting_type')
        if acting_type_id:
            try:
                acting_type_id = int(acting_type_id)
            except (ValueError, TypeError):
                return Response({'error': 'acting_type must be an id'}, status=400)
            qs = qs.filter(acting_type_id=acting_type_id)
        return Response([
            {
                'id': ml.id,
                'name': ml.name,
                'code': ml.code,
                'acting_type': {'id': ml.acting_type.id, 'code': ml.acting_type.code,
                                'name': ml.acting_type.name} if ml.acting_type else None,
                'brand': ml.brand.name if ml.brand else '',
            }
            for ml in qs.select_related('acting_type', 'brand')
        ])

    @action(detail=False, methods=['get'], url_path='options')
    def options(self, request):
        """Доступные опции серии. ?model_line=<id>"""
        ml_id = request.query_params.get('model_line')
        if not ml_id:
            return Response({'error': 'model_line required'}, status=400)
        try:
            ml_id = int(ml_id)
        except (ValueError, TypeError):
            return Response({'error': 'model_line must be an id'}, status=400)
        obj = PositionerConstructor(selected_model_line_id=ml_id)
        try:
            return Response(obj.get_available_options())
        except ObjectDoesNotExist:
            return Response({'error': 'Серия позиционеров не найдена'}, status=404)

    @action(detail=False, methods=['post'], url_path='preview')
    def preview(self, request):
        """Превью артикула/названия/описания и карточки без сохранения."""
        obj = self._build_from_request(request)
        if not obj.selected_model_line_id:
            return Response({'error': 'selected_model_line required'}, status=400)
        try:
            self._prepare(obj)
        except ObjectDoesNotExist:
            return Response({'error': 'Серия или опция не найдена'}, status=404)

        item = obj.build_preview_item()
        if not item:
            return Response({'error': 'Не удалось собрать конфигурацию'}, status=400)

        data = item.to_dict()
        # Описание в карточке — сгенерированное, а не сохранённое
        for section in data.get('sections', []):
            if section.get('key') == 'description':
                section['data'] = item.description or ''
        data['code'] = item.code or ''
        data['name'] = item.name or ''
        data['description'] = item.description or ''
        data['tech_description'] = obj._generate_tech_description()
        data['warnings'] = [
            {'field': c['field'], 'message': c['message']}
            for c in item.get_ex_only_conflicts()
        ]

        # Если такой item уже существует — показываем его id/SKU
        existing = PosiModelLineItem.objects.filter(code=item.code).first()
        data['item_id'] = existing.id if existing else None
        data['sku'] = None
        if existing:
            sku = getattr(existing, 'sku', None)
            if sku:
                data['sku'] = {'id': sku.id, 'code': sku.code, 'name': sku.name}
        return Response(data)

    # ── материализация и сериализация ──

    def _materialize(self, obj):
        """Materialize формы в PosiModelLineItem + SKU (ошибки → логируем)."""
        try:
            return materialize(obj)
        except ValidationError as e:
            logger.warning(f"Материализация конфигурации {obj.pk} не удалась: {e}")
            return None, None
        except Exception:
            logger.exception('Материализация конфигурации не удалась')
            return None, None

    def _attach_item_sku(self, data, item, sku):
        """Добавить в ответ item (to_dict) и SKU (кратко)."""
        data['item'] = item.to_dict() if item else None
        data['sku'] = {'id': sku.id, 'code': sku.code, 'name': sku.name,
                       'description': sku.description} if sku else None
        return data

    def _serialize(self, obj):
        return {
            'id': obj.id,
            'name': obj.name,
            'code': obj.code,
            'description': obj.description,
            'model_line': _fk_dict(obj.selected_model_line) if obj.selected_model_line_id else None,
            'acting_type': _fk_dict(obj.selected_model_line.acting_type)
                           if obj.selected_model_line_id and obj.selected_model_line.acting_type else None,
            'is_active': obj.is_active,
            'is_unique': obj.is_unique,
            'sorting_order': obj.sorting_order,
        }

    def _serialize_detail(self, obj):
        data = self._serialize(obj)
        data.update({
            'selected_body_connection': _fk_dict(obj.selected_body_connection),
            'selected_lever': _fk_dict(obj.selected_lever),
            'selected_temperature': _temperature_dict(obj.selected_temperature),
            'selected_signal_profile_option': _signal_profile_option_dict(obj.selected_signal_profile_option),
            'selected_signal_profile': _fk_dict(obj.selected_signal_profile),
            'selected_smart_capability_set': _fk_dict(obj.selected_smart_capability_set),
            'selected_alarm': _fk_dict(obj.selected_alarm),
            'selected_exd_row': _exd_row_dict(obj.selected_exd_row),
            'selected_exd': _fk_dict(obj.selected_exd),
            'work_temp_min': obj.work_temp_min,
            'work_temp_max': obj.work_temp_max,
        })
        return data

    def _find_duplicate(self, obj):
        """Существующая форма с тем же набором опций (фильтры как _check_for_duplicates)."""
        filters = {}
        for field_name in obj.get_option_fields():
            value = getattr(obj, field_name)
            if value:
                filters[field_name] = value
            else:
                filters[f'{field_name}__isnull'] = True
        for extra in ('selected_signal_profile', 'selected_smart_capability_set', 'selected_exd'):
            value = getattr(obj, extra)
            if value:
                filters[extra] = value
            else:
                filters[f'{extra}__isnull'] = True
        if obj.selected_model_line:
            filters['selected_model_line'] = obj.selected_model_line
        else:
            filters['selected_model_line__isnull'] = True
        # ВАЖНО: не self.get_queryset() — query-параметры запроса не должны
        # сужать поиск дубликата (is_active-фильтр тоже не применяем)
        return PositionerConstructor.objects.filter(**filters).first()


# ── helpers ──

def _fk_dict(fk_obj):
    if not fk_obj:
        return None
    return {
        'id': fk_obj.id,
        'name': str(fk_obj),
        'code': getattr(fk_obj, 'code', '') or '',
    }


def _temperature_dict(temp_row):
    if not temp_row:
        return None
    return {
        'id': temp_row.id,
        'name': f"{temp_row.work_temp_min}...{temp_row.work_temp_max} °С",
        'encoding': temp_row.encoding or '',
        'work_temp_min': temp_row.work_temp_min,
        'work_temp_max': temp_row.work_temp_max,
    }


def _signal_profile_option_dict(row):
    if not row:
        return None
    return {
        'id': row.id,
        'encoding': row.encoding or '',
        'signal_profile': _fk_dict(row.signal_profile),
        'smart_capability_set': _fk_dict(row.smart_capability_set),
        'is_default': row.is_default,
    }


def _exd_row_dict(row):
    if not row:
        return None
    return {
        'id': row.id,
        'encoding': row.encoding or '',
        'is_default': row.is_default,
        'variants': [
            {'id': v.id, 'name': v.name, 'code': v.code}
            for v in row.exd_options.all()
        ],
    }


def _validation_error_payload(e: ValidationError) -> dict:
    """Сериализация django ValidationError в JSON-ответ 400."""
    if hasattr(e, 'message_dict'):
        return {'error': str(e), 'errors': {k: v[0] for k, v in e.message_dict.items()}}
    return {'error': str(e)}
