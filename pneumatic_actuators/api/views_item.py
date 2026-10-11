# pneumatic_actuators/api/views_item.py
"""
REST-каталог эталонной модели PneumaticActuatorCatalogItem (2026-09-01).

Сконструированные пневмоприводы: каждая запись — артикул каталога
(сгенерированные code/name/description из шаблонов серии) + привязанная SKU.

Эндпоинты:
    GET /api/pneumatic_actuators/items/        — список (пагинированный контракт
        {data, total, limit, offset, filters_applied, ...}, совместимый с useCatalog)
        ?model_line_id=<id>                    — фильтр по серии
        ?variety=DA|SR                         — фильтр по виду привода (legacy)
        ?search=<текст>                        — поиск по code/name/description
        ?actuator_variety_id=<id>              — тип привода (sidebar, exact)
        ?torque_nm=<число>                     — момент не менее (gte)
        ?limit=N&offset=M                      — пагинация
    GET /api/pneumatic_actuators/filters/      — опции фильтров (FilterSidebar),
        ?model_line_id=<id> — скоуп опций до карточек серии
    GET /api/pneumatic_actuators/items/<id>/   — карточка (to_dict)
"""

import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from core.utils.localization import locale_from_accept_language, pick_i18n
from pneumatic_actuators.models.pa_item import PneumaticActuatorCatalogItem

logger = logging.getLogger(__name__)


class PneumaticActuatorCatalogItemListView(APIView):
    """Список сконструированных пневмоприводов (эталонная модель).

    Возвращает пагинированный контракт {data, total, ...} — как у остальных
    каталогов (pneumatic-fittings/gearbox/…), совместимый с useCatalog.
    """

    permission_classes = [AllowAny]

    SELECT_RELATED = (
        'model_line', 'body', 'pneumatic_actuator_variety', 'sku',
        'selected_safety_position', 'selected_springs_qty', 'selected_temperature',
        'selected_ip', 'selected_exd', 'selected_body_coating', 'selected_body_color',
        'selected_manual_override', 'manual_override_option', 'source_model_line_item',
        'equipment_type',
    )

    def get(self, request):
        locale = locale_from_accept_language(request.headers.get('Accept-Language'))
        params = request.query_params

        qs = PneumaticActuatorCatalogItem.objects.filter(is_active=True)\
            .select_related(*self.SELECT_RELATED).order_by('sorting_order', 'code')

        # ── Скоуп по серии (невалидный id → игнорируем, а не 500) ──
        model_line_id = params.get('model_line_id')
        if model_line_id:
            try:
                model_line_id = int(model_line_id)
            except (TypeError, ValueError):
                model_line_id = None
            if model_line_id:
                qs = qs.filter(model_line_id=model_line_id)

        # ── Legacy-фильтр по виду привода (DA/SR) ──
        variety = params.get('variety')
        if variety:
            qs = qs.filter(pneumatic_actuator_variety__code=variety)

        # ── Пользовательский фильтр torque_nm (по таблице моментов корпуса) ──
        torque_nm = params.get('torque_nm')
        if torque_nm:
            qs = PneumaticActuatorCatalogItem._apply_torque_min(qs, torque_nm)

        try:
            result = PneumaticActuatorCatalogItem.apply_filters_and_split(
                params,
                filter_definitions=[
                    fd for fd in PneumaticActuatorCatalogItem.FILTER_DEFINITIONS
                    if fd.param_name != 'torque_nm'
                ],
                base_queryset=qs,
                locale=locale,
            )
        except (TypeError, ValueError):
            # Некорректные query-параметры (limit/offset/идентификаторы) → пустая страница
            try:
                limit = min(int(params.get('limit', 24)), 200)
            except (TypeError, ValueError):
                limit = 24
            result = {
                'data': [], 'total': 0, 'filters_applied': {},
                'limit': limit, 'offset': 0,
            }
        if torque_nm:
            result.setdefault('filters_applied', {})['torque_nm'] = torque_nm
        return Response(result)


class PneumaticActuatorFilterOptionsView(APIView):
    """Опции фильтров каталога ПП (для FilterSidebar / EngineerFilterBar).

    Сериализует PneumaticActuatorCatalogItem.FILTER_DEFINITIONS;
    ?model_line_id=<id> — скоуп опций до карточек серии.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        locale = locale_from_accept_language(request.headers.get('Accept-Language'))
        model_line_id = request.query_params.get('model_line_id')

        # Неактивные карточки в каталоге не существуют — опции только по активным
        base_qs = PneumaticActuatorCatalogItem.objects.filter(is_active=True)
        if model_line_id:
            try:
                model_line_id = int(model_line_id)
            except (TypeError, ValueError):
                model_line_id = None
            if model_line_id:
                base_qs = base_qs.filter(model_line_id=model_line_id)

        result = {}
        for fd in PneumaticActuatorCatalogItem.FILTER_DEFINITIONS:
            entry = {
                'label': pick_i18n(fd.label_i18n, locale, fallback=fd.label),
                'order': fd.order,
                'filter_type': fd.filter_type.value,
                'options': [],
                'default_value': fd.default_value,
                'group': fd.group,
                'visible_when': fd.visible_when,
            }
            try:
                entry['options'] = fd.get_options(
                    PneumaticActuatorCatalogItem, queryset=base_qs, locale=locale
                )
            except Exception as e:
                logger.warning(
                    'pa filter options error for %s: %s', fd.param_name, e
                )
                entry['error'] = str(e)
            result[fd.param_name] = entry

        return Response({'filters': result, 'show_compatible': False})


class PneumaticActuatorCatalogItemDetailView(APIView):
    """Карточка сконструированного пневмопривода (to_dict)."""

    permission_classes = [AllowAny]

    def get(self, request, pk=None):
        locale = locale_from_accept_language(request.headers.get('Accept-Language'))
        try:
            item = PneumaticActuatorCatalogItem.objects.select_related(
                *PneumaticActuatorCatalogItemListView.SELECT_RELATED
            ).get(pk=pk)
        except PneumaticActuatorCatalogItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)
        return Response(item.to_dict(locale=locale))
