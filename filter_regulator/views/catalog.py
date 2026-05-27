# filter_regulator/views/catalog.py
"""
API каталога фильтр-регуляторов.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import translation

from filter_regulator.models import FilterRegulator
from core.views import BaseFilterOptionsView
from filter_regulator.services.filters import (
    FILTER_REGULATOR_FILTER_DEFINITIONS,
    FILTER_REGULATOR_SEARCH_FIELDS,
    FILTER_REGULATOR_SELECT_RELATED,
    FILTER_REGULATOR_PREFETCH_FIELDS,
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


class FilterRegulatorCatalogView(APIView):
    """GET /api/filter-regulator/catalog/"""
    permission_classes = [AllowAny]

    def get(self, request):
        params = request.query_params
        lang = params.get('lang', 'ru')
        currency_code = _get_currency_code(request)

        with translation.override(lang):
            qs = FilterRegulator.objects.select_related(*FILTER_REGULATOR_SELECT_RELATED)
            qs = qs.prefetch_related(*FILTER_REGULATOR_PREFETCH_FIELDS)

            is_active = params.get('is_active', 'true')
            if is_active.lower() in ('true', '1'):
                qs = qs.filter(is_active=True)

            filters_applied = {}

            for fd in FILTER_REGULATOR_FILTER_DEFINITIONS:
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
                for field in FILTER_REGULATOR_SEARCH_FIELDS:
                    q_obj |= Q(**{f"{field}__icontains": search})
                qs = qs.filter(q_obj)
                filters_applied['search'] = search

            total = qs.count()
            limit = min(int(params.get('limit', 24)), 100)
            offset = max(int(params.get('offset', 0)), 0)
            qs_page = qs[offset:offset + limit]

            data = [obj.to_values_dict() for obj in qs_page]

            sku_codes = [
                obj.sku.code for obj in qs_page
                if hasattr(obj, 'sku') and obj.sku and obj.sku.code
            ]
            prices = get_bulk_prices(sku_codes, currency_code) if sku_codes else {}

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


class FilterRegulatorDetailView(APIView):
    """GET /api/filter-regulator/catalog/<id>/"""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        lang = request.GET.get('lang', 'ru')
        currency_code = _get_currency_code(request)

        with translation.override(lang):
            obj = get_object_or_404(
                FilterRegulator.objects
                .select_related(*FILTER_REGULATOR_SELECT_RELATED)
                .prefetch_related(*FILTER_REGULATOR_PREFETCH_FIELDS),
                pk=pk,
            )
            data = obj.to_dict()

            sku_code = obj.sku.code if hasattr(obj, 'sku') and obj.sku else None
            if sku_code:
                data['price'] = get_display_price(sku_code, currency_code)

            data['schema'] = FilterRegulator.build_schema(
                data,
                price_data=data.get('price'),
                category_name='Фильтр-регуляторы',
            )

        return Response(data)


class FilterRegulatorFilterOptionsView(BaseFilterOptionsView):
    """
    GET /api/filter-regulator/filters/ — опции для FilterSidebar на фронтенде.

    Наследует get() из BaseFilterOptionsView (core/views.py).
    """
    permission_classes = [AllowAny]
    filter_definitions = FILTER_REGULATOR_FILTER_DEFINITIONS
    model_class = FilterRegulator