# pneumatic_actuators/api/views_constructor.py
"""
API для конструктора пневмоприводов.

Запись конфигурации идёт напрямую в эталонную ``PneumaticActuatorCatalogItem``
(хэш-дедупликация + SKU через ``get_or_create_sku``), а НЕ в legacy-модель
``PneumaticActuatorConstructor``. ``PneumaticActuatorConstructor`` остаётся
только как временный хелпер чтения опций/превью (без записи).

Эндпоинты:
    POST   /constructor/                      — материализовать конфигурацию (item + SKU)
    GET    /constructor/options/              — доступные опции для модели
    GET    /constructor/model-lines/          — список серий
    GET    /constructor/model-lines/<id>/items/ — модели серии
    POST   /constructor/preview/              — превью (несохранённая карточка)
    POST   /constructor/create-sku/           — ленивое создание SKU
"""

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from project_customers.permissions import SectionAccessPermission
from rest_framework.decorators import action
from core.utils.localization import (locale_from_accept_language, localized_name,
                                     pick_i18n)

from pneumatic_actuators.models import (
    PneumaticActuatorConstructor,
    PneumaticActuatorModelLine,
    PneumaticActuatorModelLineItem,
)
from pneumatic_actuators.models.pa_item import PneumaticActuatorCatalogItem
from pneumatic_actuators.services.sku_service import get_or_create_sku, materialize_configuration


class ConstructorViewSet(viewsets.GenericViewSet):
    """Материализация конфигураций пневмопривода в PneumaticActuatorCatalogItem.

    Только запись (create) и справочники/превью. Списка «сохранённых
    конфигураций», деталки, обновления и удаления нет — карточки каталога
    не редактируются и не удаляются через конфигуратор.
    """

    permission_classes = [SectionAccessPermission]
    required_section = 'configurator_pa'

    # Ключ опции (get_or_create_sku) → поле формы фронтенда.
    _OPTION_FIELD_BY_KEY = {
        'safety_position': 'selected_safety_position',
        'springs_qty': 'selected_springs_qty',
        'temperature': 'selected_temperature',
        'ip': 'selected_ip',
        'exd': 'selected_exd',
        'body_coating': 'selected_body_coating',
        'body_color': 'selected_body_color',
        'manual_override': 'selected_manual_override',
    }

    # ── Запись ──

    def _options_from_request(self, request):
        """Ключи опций get_or_create_sku → значения из тела запроса."""
        return {
            key: request.data.get(field)
            for key, field in self._OPTION_FIELD_BY_KEY.items()
        }

    def _materialize(self, mli_id, options):
        """Материализовать конфигурацию в карточку + SKU (хэш-дедуп)."""
        mli = get_object_or_404(PneumaticActuatorModelLineItem, pk=mli_id)
        sku, created = materialize_configuration(mli, options)
        item = None
        if sku and sku.source_content_type_id and sku.source_object_id:
            item = PneumaticActuatorCatalogItem.objects.filter(
                pk=sku.source_object_id,
            ).select_related('sku').first()
        return item, sku, created

    def create(self, request, *args, **kwargs):
        mli_id = request.data.get('selected_model_line_item')
        if not mli_id:
            return Response({'error': 'selected_model_line_item required'}, status=400)
        options = self._options_from_request(request)
        try:
            item, sku, created = self._materialize(mli_id, options)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
        if item is None:
            return Response({'error': 'Не удалось материализовать карточку'}, status=500)
        data = self._serialize_item_detail(item, sku=sku)
        data['created'] = bool(created)
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    # ── Сериализация ──

    def _serialize_item(self, item):
        return {
            'id': item.id,
            'name': item.name or item.code or '',
            'code': item.code or '',
            'description': item.description or '',
            'model_line': (
                {'id': item.model_line_id, 'name': str(item.model_line)}
                if item.model_line else None
            ),
            'model_line_item': (
                {'id': item.source_model_line_item_id, 'name': str(item.source_model_line_item)}
                if item.source_model_line_item else None
            ),
            'is_active': item.is_active,
            'sorting_order': item.sorting_order,
        }

    def _serialize_item_detail(self, item, sku=None):
        data = self._serialize_item(item)
        data.update({
            'selected_safety_position': _fk_dict(item.selected_safety_position),
            'selected_springs_qty': _fk_dict(item.selected_springs_qty),
            'selected_temperature': _fk_dict(item.selected_temperature),
            'selected_ip': _fk_dict(item.selected_ip),
            'selected_exd': _fk_dict(item.selected_exd),
            'selected_body_coating': _fk_dict(item.selected_body_coating),
            'selected_body_color': _fk_dict(item.selected_body_color),
            'selected_manual_override': _fk_dict(item.selected_manual_override),
            'work_temp_min': (
                item.selected_temperature.work_temp_min if item.selected_temperature else None
            ),
            'work_temp_max': (
                item.selected_temperature.work_temp_max if item.selected_temperature else None
            ),
        })
        try:
            data['item'] = item.to_dict()
        except Exception:
            data['item'] = None
        sku = sku or getattr(item, 'sku', None)
        if sku:
            data['sku'] = {
                'id': sku.id, 'code': sku.code, 'name': sku.name,
                'description': sku.description,
            }
        else:
            data['sku'] = None
        return data

    # ── Хелперы чтения (без записи в legacy-модели) ──

    def _build_from_request(self, request):
        """Временный PneumaticActuatorConstructor (только чтение опций/превью)."""
        return PneumaticActuatorConstructor(
            selected_model_line_id=request.data.get('selected_model_line'),
            selected_model_line_item_id=request.data.get('selected_model_line_item'),
            selected_safety_position_id=request.data.get('selected_safety_position'),
            selected_springs_qty_id=request.data.get('selected_springs_qty'),
            selected_temperature_id=request.data.get('selected_temperature'),
            selected_ip_id=request.data.get('selected_ip'),
            selected_exd_id=request.data.get('selected_exd'),
            selected_body_coating_id=request.data.get('selected_body_coating'),
            selected_body_color_id=request.data.get('selected_body_color'),
            selected_manual_override_id=request.data.get('selected_manual_override'),
            sorting_order=request.data.get('sorting_order', 0),
            is_active=request.data.get('is_active', True),
        )

    @action(detail=False, methods=['get'], url_path='options')
    def options(self, request):
        """Доступные опции для модели. ?model_line_item_id=X"""
        mli_id = request.query_params.get('model_line_item_id')
        if not mli_id:
            return Response({'error': 'model_line_item_id required'}, status=400)
        obj = PneumaticActuatorConstructor(selected_model_line_item_id=mli_id)
        locale = locale_from_accept_language(request.headers.get('Accept-Language'))
        return Response(obj.get_available_options(locale=locale))

    @action(detail=False, methods=['get'], url_path='varieties')
    def varieties(self, request):
        """Виды привода DA/SR из справочника (локализованы)."""
        from pneumatic_actuators.models import PneumaticActuatorVariety
        locale = locale_from_accept_language(request.headers.get('Accept-Language'))
        return Response(PneumaticActuatorVariety.get_for_select(
            active_only=True, locale=locale))

    @action(detail=False, methods=['get'])
    def model_lines(self, request):
        """Список активных серий пневмоприводов (с изображением и описанием)."""
        items = PneumaticActuatorModelLine.objects.filter(is_active=True).select_related(
            'pneumatic_actuator_construction_variety'
        )
        construction_variety_id = request.query_params.get('construction_variety_id')
        if construction_variety_id:
            try:
                items = items.filter(pneumatic_actuator_construction_variety_id=int(construction_variety_id))
            except (TypeError, ValueError):
                pass
        items = items.order_by('sorting_order')
        locale = locale_from_accept_language(request.headers.get('Accept-Language'))
        result = []
        for ml in items:
            image = None
            try:
                imgs = ml._get_images_section()
                if imgs:
                    image = imgs[0].get('preview_url') or imgs[0].get('url')
            except Exception:
                image = None
            result.append({
                'id': ml.id, 'name': ml.name, 'code': ml.code,
                'description': pick_i18n(
                    getattr(ml, 'description_i18n', None), locale, fallback=ml.description or ''
                ),
                'image': image,
                'construction_variety_id': ml.pneumatic_actuator_construction_variety_id,
                'construction_variety_code': ml.pneumatic_actuator_construction_variety.code if ml.pneumatic_actuator_construction_variety else None,
                'construction_name': localized_name(ml.pneumatic_actuator_construction_variety, locale) if ml.pneumatic_actuator_construction_variety else None,
            })
        return Response(result)

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
        """Превью: несохранённая PneumaticActuatorCatalogItem (to_dict)."""
        obj = self._build_from_request(request)
        obj._ensure_valid_options()
        if obj.selected_temperature:
            obj.work_temp_min = obj.selected_temperature.work_temp_min
            obj.work_temp_max = obj.selected_temperature.work_temp_max

        mli = obj.selected_model_line_item
        if not mli:
            return Response({'error': 'model_line_item required'}, status=400)

        locale = locale_from_accept_language(request.headers.get('Accept-Language'))
        item = PneumaticActuatorCatalogItem.from_constructor(obj)
        item.code = item.generated_model_item_code or None
        item.name = item.generate_name() or item.code or ''
        item.description = item.generate_description() or ''

        data = item.to_dict(locale=locale)
        data['tech_description'] = item.render_spec_html(locale=locale)
        return Response(data)

    @action(detail=False, methods=['post'], url_path='create-sku')
    def create_sku(self, request):
        """Создать SKU для конфигурации пневмопривода (ленивое создание)."""
        mli_id = request.data.get('model_line_item_id')
        options = request.data.get('options', {})
        if not mli_id:
            return Response({'error': 'model_line_item_id required'}, status=400)

        try:
            mli = PneumaticActuatorModelLineItem.objects.get(id=mli_id)
        except PneumaticActuatorModelLineItem.DoesNotExist:
            return Response({'error': 'Model line item not found'}, status=404)

        resolved_options = {k: v for k, v in options.items() if v is not None}

        try:
            sku = get_or_create_sku(mli, resolved_options)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

        return Response({
            'id': sku.id, 'code': sku.code, 'name': sku.name, 'description': sku.description,
        })


def _fk_dict(fk_obj):
    if not fk_obj:
        return None
    return {'id': fk_obj.id, 'name': str(fk_obj), 'code': getattr(fk_obj, 'code', '') or getattr(fk_obj, 'encoding', '')}
