# price/views/ea_configurator.py
"""
API для конфигуратора цен электроприводов.

GET  /admin/prices/ea-configurator/options/?power_supply_id=X
     → доступные model_line_item + опции (encoding из through-моделей)
POST /admin/prices/ea-configurator/create/
     → создать документ + строки
GET  /admin/prices/ea-configurator/documents/
     → список документов конфигуратора
GET  /admin/prices/ea-configurator/documents/{id}/
     → документ со строками (матрица)
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from price.models import EAPriceDocument, EAPriceConstructor
from electric_actuators.models import (
    ElectricActuatorModelLineItem,
    ElectricPowerSupplyOption,
    ElectricActuatorConstructor,
)


class EaPowerSuppliesView(APIView):
    """Список всех доступных напряжений питания."""

    def get(self, request):
        supplies = ElectricPowerSupplyOption.objects.filter(is_active=True).select_related('power_supply')
        data = [{
            'id': ps.id,
            'name': str(ps),
            'encoding': ps.encoding,
        } for ps in supplies]
        return Response(data)


class EaConfiguratorOptionsView(APIView):
    """Доступные модели и опции для выбранного напряжения."""

    def get(self, request):
        ps_id = request.query_params.get('power_supply_id')
        if not ps_id:
            return Response({'error': 'power_supply_id required'}, status=400)

        try:
            ps = ElectricPowerSupplyOption.objects.get(id=ps_id)
        except ElectricPowerSupplyOption.DoesNotExist:
            return Response({'error': 'power_supply not found'}, status=404)

        # Модели, доступные для этого напряжения
        model_items = ElectricActuatorModelLineItem.objects.filter(
            model_line_item_power_supply_option=ps,
            is_active=True,
        ).select_related('model_line', 'body').order_by('sorting_order')

        result = {
            'power_supply': {'id': ps.id, 'name': str(ps), 'encoding': ps.encoding},
            'model_items': [],
        }

        for item in model_items:
            # Временный конструктор для get_available_options
            temp = ElectricActuatorConstructor(
                selected_model_line_item=item,
                selected_power_supply=ps,
            )
            options = temp.get_available_options()

            # Преобразуем: для каждой группы опций берём encoding + name
            option_groups = []
            for key, items_list in options.items():
                if key == 'power_supply_options':
                    continue
                group = {
                    'field': key.replace('_options', ''),
                    'label': key,
                    'items': items_list,  # [{id, option_id, encoding, name, is_default}, ...]
                }
                option_groups.append(group)

            result['model_items'].append({
                'id': item.id,
                'name': item.name,
                'code': item.code,
                'torque_min': float(item.torque_min) if item.torque_min else None,
                'torque_max': float(item.torque_max) if item.torque_max else None,
                'rotation_speed': float(item.rotation_speed) if item.rotation_speed else None,
                'option_groups': option_groups,
            })

        return Response(result)


class EaConfiguratorDocumentView(APIView):
    """CRUD для документов конфигуратора."""

    def get(self, request, doc_id=None):
        if doc_id:
            return self._get_detail(doc_id)
        return self._list(request)

    def _list(self, request):
        qs = EAPriceDocument.objects.filter(is_active=True).order_by('-document_date').select_related('price_variety', 'currency', 'power_supply', 'model_line')
        data = [{
            'id': d.id,
            'name': d.name,
            'document_date': str(d.document_date),
            'price_variety': {'id': d.price_variety_id, 'name': d.price_variety.name} if d.price_variety else None,
            'currency': {'id': d.currency_id, 'code': d.currency.code} if d.currency else None,
            'status': d.status,
            'status_label': d.get_status_display(),
            'power_supply': {'id': d.power_supply_id, 'name': str(d.power_supply)},
            'model_line': {'id': d.model_line_id, 'name': str(d.model_line)} if d.model_line else None,
            'rows_count': d.rows.count(),
        } for d in qs]
        return Response(data)

    def _get_detail(self, doc_id):
        try:
            doc = EAPriceDocument.objects.get(id=doc_id)
        except EAPriceDocument.DoesNotExist:
            return Response({'error': 'not found'}, status=404)

        rows = EAPriceConstructor.objects.filter(document=doc).order_by('model_line_item', 'option_field', 'option_id')

        # Группируем строки по model_line_item
        by_model = {}
        for row in rows:
            mli_id = row.model_line_item_id
            if mli_id not in by_model:
                by_model[mli_id] = {
                    'model_line_item': {
                        'id': mli_id,
                        'name': row.model_line_item.name,
                        'code': row.model_line_item.code,
                    },
                    'base_price': None,
                    'options': {},
                }
            if row.option_field == 'base':
                by_model[mli_id]['base_price'] = float(row.surcharge)
            else:
                by_model[mli_id]['options'][f"{row.option_field}_{row.option_id}"] = float(row.surcharge)

        return Response({
            'id': doc.id,
            'name': doc.name,
            'document_date': str(doc.document_date),
            'price_variety': {'id': doc.price_variety_id, 'name': doc.price_variety.name} if doc.price_variety else None,
            'currency': {'id': doc.currency_id, 'code': doc.currency.code} if doc.currency else None,
            'status': doc.status,
            'status_label': doc.get_status_display(),
            'power_supply': {'id': doc.power_supply_id, 'name': str(doc.power_supply)},
            'rows': list(by_model.values()),
        })

    def post(self, request):
        """Создать документ + строки из матрицы."""
        name = request.data.get('name', 'Конфигуратор цен')
        price_variety_id = request.data.get('price_variety_id')
        currency_id = request.data.get('currency_id')
        ps_id = request.data.get('power_supply_id')
        rows_data = request.data.get('rows', [])

        if not ps_id:
            return Response({'error': 'power_supply_id required'}, status=400)

        try:
            ps = ElectricPowerSupplyOption.objects.get(id=ps_id)
        except ElectricPowerSupplyOption.DoesNotExist:
            return Response({'error': 'power_supply not found'}, status=404)

        doc = EAPriceDocument.objects.create(
            name=name,
            price_variety_id=price_variety_id,
            currency_id=currency_id,
            model_line_id=request.data.get('model_line_id'),
            power_supply=ps,
            status=EAPriceDocument.Status.DRAFT,
        )

        created = 0
        for row in rows_data:
            mli_id = row.get('model_line_item_id')
            base_price = row.get('base_price', 0)
            if not mli_id:
                continue

            # Базовая цена
            EAPriceConstructor.objects.create(
                document=doc,
                model_line_item_id=mli_id,
                power_supply=ps,
                option_field='base',
                option_id=None,
                surcharge=base_price,
                currency_id=currency_id,
                price_variety_id=price_variety_id,
                is_active=False,
            )
            created += 1

            # Опции
            for key, price in row.get('options', {}).items():
                if not price:
                    continue
                parts = key.rsplit('_', 1)
                if len(parts) != 2:
                    continue
                opt_field, opt_id = parts[0], parts[1]
                try:
                    opt_id_int = int(opt_id)
                except ValueError:
                    continue

                EAPriceConstructor.objects.create(
                    document=doc,
                    model_line_item_id=mli_id,
                    power_supply=ps,
                    option_field=opt_field,
                    option_id=opt_id_int,
                    surcharge=price,
                    currency_id=currency_id,
                    price_variety_id=price_variety_id,
                    is_active=False,
                )
                created += 1

        return Response({'id': doc.id, 'name': doc.name, 'rows_created': created}, status=201)

    def delete(self, request, doc_id=None):
        if not doc_id:
            return Response({'error': 'id required'}, status=400)
        try:
            doc = EAPriceDocument.objects.get(id=doc_id)
            doc.delete()
            return Response({'ok': True})
        except EAPriceDocument.DoesNotExist:
            return Response({'error': 'not found'}, status=404)