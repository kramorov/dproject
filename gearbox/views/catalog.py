# gearbox/views/catalog.py
"""
API каталога редукторов.

GET  /api/gearbox/catalog/       — список с фильтрами, поиском и ценами в валюте клиента
GET  /api/gearbox/catalog/<id>/  — детальная модель со schema.org и ценой
GET  /api/gearbox/filters/       — опции фильтров

Цены вшиты в ответ сервером — фронт не делает второй запрос.
Валюта конвертируется на лету через ExchangeRate в валюту из CustomerSettings.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import translation

from gearbox.models import GearBox
from core.views import BaseFilterOptionsView
from gearbox.services.filters import (
    GEARBOX_FILTER_DEFINITIONS,
    GEARBOX_SEARCH_FIELDS,
    GEARBOX_SELECT_RELATED,
    GEARBOX_PREFETCH_FIELDS,
)
from price.services.currency_converter import get_bulk_prices, get_display_price
from project_customers.utils import get_current_customer_user


def _get_currency_code(request):
    """Извлечь код валюты из настроек клиента или дефолт RUB."""
    try:
        user = get_current_customer_user(request)
        if user and hasattr(user, 'customer'):
            settings = getattr(user.customer, 'settings', None)
            if settings and settings.default_currency:
                return settings.default_currency.code
    except Exception:
        pass
    return 'RUB'


class GearboxCatalogView(APIView):
    """
    GET /api/gearbox/catalog/

    Параметры:
        search              — поиск по code, name, description
        ip_id               — IP (с ранжированием: >= выбранного)
        work_temp_min       — температура от, °С
        work_temp_max       — температура до, °С
        min_work_torque     — рабочий момент не менее, Нм
        body_material_id    — материал корпуса (только используемые)
        brand_id            — бренд (только используемые)
        mounting_plate_top_id — монтажная площадка (только используемые)
        is_active           — только активные (по умолчанию true)
        limit / offset      — пагинация
        lang                — язык (ru, en, zh)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        params = request.query_params
        lang = params.get('lang', 'ru')
        currency_code = _get_currency_code(request)

        with translation.override(lang):
            qs = GearBox.objects.select_related(*GEARBOX_SELECT_RELATED)
            qs = qs.prefetch_related(*GEARBOX_PREFETCH_FIELDS)

            is_active = params.get('is_active', 'true')
            if is_active.lower() in ('true', '1'):
                qs = qs.filter(is_active=True)

            filters_applied = {}

            for fd in GEARBOX_FILTER_DEFINITIONS:
                value = params.get(fd.param_name)
                if value is None or value == '' or value == 'all':
                    continue
                lookup, converted = fd.build_filter_lookup(value)
                if lookup and converted is not None:
                    qs = qs.filter(**{lookup: converted})
                    filters_applied[fd.param_name] = value

            search = params.get('search', '').strip()
            if search:
                q_obj = Q()
                for field in GEARBOX_SEARCH_FIELDS:
                    q_obj |= Q(**{f"{field}__icontains": search})
                qs = qs.filter(q_obj)
                filters_applied['search'] = search

            total = qs.count()
            limit = min(int(params.get('limit', 24)), 100)
            offset = max(int(params.get('offset', 0)), 0)
            qs_page = qs[offset:offset + limit]

            data = [obj.to_values_dict() for obj in qs_page]

            # ── Цены: один bulk-запрос + конвертация ──
            sku_codes = [
                obj.sku.code for obj in qs_page
                if hasattr(obj, 'sku') and obj.sku and obj.sku.code
            ]
            prices = get_bulk_prices(sku_codes, currency_code) if sku_codes else {}

            # Вшиваем цену в каждый item
            for item in data:
                sku = item.get('sku') or {}
                item['price'] = prices.get(sku.get('code'))

        return Response({
            'total': total,
            'count': len(data),
            'limit': limit,
            'offset': offset,
            'filters_applied': filters_applied,
            'currency': currency_code,
            'data': data,
        })


class GearboxDetailView(APIView):
    """
    GET /api/gearbox/catalog/<id>/

    Полная информация о редукторе + Schema.org Product + цена.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        lang = request.GET.get('lang', 'ru')
        currency_code = _get_currency_code(request)

        with translation.override(lang):
            obj = get_object_or_404(
                GearBox.objects
                .select_related(*GEARBOX_SELECT_RELATED)
                .prefetch_related(*GEARBOX_PREFETCH_FIELDS),
                pk=pk,
            )
            data = obj.to_dict()

            # Цена
            sku_code = obj.sku.code if hasattr(obj, 'sku') and obj.sku else None
            if sku_code:
                data['price'] = get_display_price(sku_code, currency_code)

            # Schema.org Product (с ценой)
            data['schema'] = GearBox.build_schema(
                data,
                price_data=data.get('price'),
                category_name='Редукторы',
            )

        return Response(data)


class GearboxFilterOptionsView(BaseFilterOptionsView):
    """
    GET /api/gearbox/filters/ — опции для FilterSidebar на фронтенде.

    Наследует get() из BaseFilterOptionsView (core/views.py).
    """
    permission_classes = [AllowAny]
    filter_definitions = GEARBOX_FILTER_DEFINITIONS
    model_class = GearBox