# cable_glands/api/views_constructor.py
"""API конструктора кабельных вводов (CableGlandConstructor).

Паттерн — pa_controls/api/views_constructor.py (позиционеры).

Эндпоинты:
    GET    /constructor/                    — список сохранённых конфигураций
    POST   /constructor/                    — создать конфигурацию (+ CableGland/SKU)
    GET    /constructor/<id>/               — детальная информация
    PUT    /constructor/<id>/               — обновить конфигурацию
    DELETE /constructor/<id>/               — удалить
    GET    /constructor/model-lines/        — серии
    GET    /constructor/model-lines/<ml>/items/ — модели серии
    GET    /constructor/options/            — опции (?model_line=&model_line_item=)
    POST   /constructor/preview/            — превью артикула/описания без сохранения
"""

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from project_customers.permissions import SectionAccessPermission
from cable_glands.models import (
    CableGland,
    CableGlandConstructor,
    CableGlandModelLine,
    CableGlandModelLineItem,
)


class CableGlandConstructorViewSet(viewsets.ModelViewSet):
    """CRUD + каскадные справочники конструктора кабельных вводов."""
    permission_classes = [SectionAccessPermission]
    required_section = 'configurator_cg'
    queryset = CableGlandConstructor.objects.filter(is_active=True)

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
            'selected_model_line_item__body',
            'selected_thread_option',
            'selected_thread_option__thread_size',
            'selected_body_material_option',
            'selected_body_material_option__body_material',
            'selected_exd_option',
        )

    def list(self, request, *args, **kwargs):
        return Response([self._serialize(obj) for obj in self.get_queryset()])

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        return Response(self._serialize_detail(obj))

    # ── сборка из запроса ──

    def _build_from_request(self, request):
        return CableGlandConstructor(
            selected_model_line_id=request.data.get('selected_model_line'),
            selected_model_line_item_id=request.data.get('selected_model_line_item'),
            selected_thread_option_id=request.data.get('selected_thread_option'),
            selected_body_material_option_id=request.data.get('selected_body_material_option'),
            selected_exd_option_id=request.data.get('selected_exd_option'),
        )

    def _prepare(self, obj):
        """Валидация + name/code/description (без сохранения)."""
        obj._ensure_valid_options()
        preview = obj.build_preview_item()
        if preview:
            obj.name = preview.name or ''
            obj.code = preview.code or None
            obj.description = preview.description or ''
        return obj

    # ── create / update / destroy ──

    def create(self, request, *args, **kwargs):
        obj = self._build_from_request(request)
        if not obj.selected_model_line_item_id:
            return Response({'error': 'selected_model_line_item required'}, status=400)
        try:
            self._prepare(obj)
        except ObjectDoesNotExist:
            return Response({'error': 'Модель или опция не найдена'}, status=404)

        existing = self._find_duplicate(obj)
        if existing:
            item, sku = existing.materialize()
            data = self._serialize_detail(existing)
            self._attach_item_sku(data, item, sku)
            return Response(data, status=status.HTTP_200_OK)

        try:
            item, sku = obj.materialize()
        except ValidationError as e:
            return Response(_validation_error_payload(e), status=400)

        obj.save()
        data = self._serialize_detail(obj)
        self._attach_item_sku(data, item, sku)
        return Response(data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        for field in ('selected_model_line', 'selected_model_line_item',
                      'selected_thread_option', 'selected_body_material_option',
                      'selected_exd_option'):
            if field in request.data:
                setattr(obj, f'{field}_id', request.data[field])
        if 'sorting_order' in request.data:
            obj.sorting_order = request.data['sorting_order']
        if 'is_active' in request.data:
            obj.is_active = request.data['is_active']

        try:
            self._prepare(obj)
        except ObjectDoesNotExist:
            return Response({'error': 'Модель или опция не найдена'}, status=404)

        try:
            item, sku = obj.materialize()
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

    @action(detail=False, methods=['get'], url_path='model-lines')
    def model_lines(self, request):
        qs = CableGlandModelLine.objects.filter(is_active=True).order_by('sorting_order', 'code')
        return Response([
            {
                'id': ml.id,
                'name': ml.name,
                'code': ml.code,
                'brand': ml.brand.name if ml.brand else '',
            }
            for ml in qs.select_related('brand')
        ])

    @action(detail=False, methods=['get'], url_path=r'model-lines/(?P<ml_id>[^/.]+)/items')
    def model_line_items(self, request, ml_id=None):
        qs = CableGlandModelLineItem.objects.filter(
            model_line_id=ml_id, is_active=True
        ).order_by('sorting_order', 'code').select_related('body')
        return Response([
            {
                'id': item.id,
                'name': item.name,
                'code': item.code,
                'body': {'id': item.body.id, 'name': str(item.body), 'code': item.body.code}
                if item.body_id else None,
            }
            for item in qs
        ])

    @action(detail=False, methods=['get'], url_path='options')
    def options(self, request):
        """Доступные опции для выбранной серии и модели."""
        ml_id = request.query_params.get('model_line')
        mli_id = request.query_params.get('model_line_item')
        obj = CableGlandConstructor()
        if mli_id:
            try:
                obj.selected_model_line_item = CableGlandModelLineItem.objects.get(pk=mli_id)
            except ObjectDoesNotExist:
                return Response({'error': 'Модель не найдена'}, status=404)
        elif ml_id:
            try:
                obj.selected_model_line = CableGlandModelLine.objects.get(pk=ml_id)
            except ObjectDoesNotExist:
                return Response({'error': 'Серия не найдена'}, status=404)
        else:
            return Response({'error': 'model_line or model_line_item required'}, status=400)
        return Response(obj.get_available_options())

    @action(detail=False, methods=['post'], url_path='preview')
    def preview(self, request):
        """Превью артикула/названия/описания без сохранения."""
        obj = self._build_from_request(request)
        if not obj.selected_model_line_item_id:
            return Response({'error': 'selected_model_line_item required'}, status=400)
        try:
            self._prepare(obj)
        except ValidationError as e:
            return Response(_validation_error_payload(e), status=400)
        except ObjectDoesNotExist:
            return Response({'error': 'Модель или опция не найдена'}, status=404)
        return Response({
            'name': obj.name,
            'code': obj.code,
            'description': obj.description,
        })

    # ── дедупликация / сериализация ──

    def _find_duplicate(self, obj):
        filters = {}
        for field in ('selected_model_line', 'selected_model_line_item',
                      'selected_thread_option', 'selected_body_material_option',
                      'selected_exd_option'):
            value = getattr(obj, field)
            if value:
                filters[field] = value
            else:
                filters[f'{field}__isnull'] = True
        return CableGlandConstructor.objects.filter(**filters).first()

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
            'selected_thread_option': _thread_option_dict(obj.selected_thread_option),
            'selected_body_material_option': _body_material_option_dict(obj.selected_body_material_option),
            'selected_exd_option': _exd_option_dict(obj.selected_exd_option),
        })
        return data

    def _attach_item_sku(self, data, item, sku):
        data['article'] = {
            'id': item.id if item else None,
            'code': item.code if item else None,
            'name': item.name if item else None,
        }
        data['sku'] = {'id': sku.id, 'code': sku.code} if sku else None


# ── helpers ──

def _fk_dict(fk_obj):
    if not fk_obj:
        return None
    return {'id': fk_obj.id, 'name': str(fk_obj), 'code': getattr(fk_obj, 'code', '') or ''}


def _thread_option_dict(row):
    if not row:
        return None
    return {
        'id': row.id,
        'encoding': row.encoding or '',
        'thread_size': _fk_dict(row.thread_size),
        'is_default': row.is_default,
    }


def _body_material_option_dict(row):
    if not row:
        return None
    return {
        'id': row.id,
        'encoding': row.encoding or '',
        'body_material': _fk_dict(row.body_material),
        'is_default': row.is_default,
    }


def _exd_option_dict(row):
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
    if hasattr(e, 'message_dict'):
        return {'error': str(e), 'errors': {k: v[0] for k, v in e.message_dict.items()}}
    return {'error': str(e)}
