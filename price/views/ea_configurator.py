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
from rest_framework.permissions import AllowAny

import pandas as pd
import numpy as np
from io import BytesIO
from django.http import HttpResponse

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
        print(f'[EaConfiguratorOptions] GET power_supply_id={ps_id!r} (type={type(ps_id).__name__})')
        if not ps_id:
            return Response({'error': 'power_supply_id required'}, status=400)

        try:
            ps = ElectricPowerSupplyOption.objects.get(id=ps_id)
        except ElectricPowerSupplyOption.DoesNotExist:
            print(f'[EaConfiguratorOptions] power_supply not found for id={ps_id!r}')
            return Response({'error': 'power_supply not found'}, status=404)

        # Все модели серии, у которых есть это напряжение (по справочнику PowerSupplies)
        ml_id = ps.model_line_item.model_line_id
        model_items = ElectricActuatorModelLineItem.objects.filter(
            model_line_id=ml_id,
            model_line_item_power_supply_option__power_supply_id=ps.power_supply_id,
            is_active=True,
        ).select_related('model_line', 'body').order_by('sorting_order').distinct()

        # Pre-fetch through-models for this series + voltage (for dependent options)
        all_ps = ElectricPowerSupplyOption.objects.filter(
            model_line_item__model_line_id=ml_id,
            power_supply_id=ps.power_supply_id,
            is_active=True,
        ).select_related('model_line_item')
        ps_by_mli = {p.model_line_item_id: p for p in all_ps}

        result = {
            'power_supply': {'id': ps.id, 'name': str(ps), 'encoding': ps.encoding},
            'model_items': [],
        }

        for item in model_items:
            item_ps = ps_by_mli.get(item.id)
            if not item_ps:
                continue
            temp = ElectricActuatorConstructor(
                selected_model_line_item=item,
                selected_power_supply=item_ps,
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
                'model_line_code': item.model_line.code,
                'torque_min': float(item.torque_min) if item.torque_min else None,
                'torque_max': float(item.torque_max) if item.torque_max else None,
                'rotation_speed': float(item.rotation_speed) if item.rotation_speed else None,
                'option_groups': option_groups,
            })

        return Response(result)


class EaConfiguratorDocumentView(APIView):
    """CRUD для документов конфигуратора."""
    permission_classes = [AllowAny]

    def get(self, request, doc_id=None):
        if doc_id:
            url_name = request.resolver_match.url_name if request.resolver_match else ''
            if 'export' in url_name:
                return self._export(request, doc_id)
            if 'print' in url_name:
                return self._print_doc(request, doc_id)
            return self._get_detail(doc_id)
        return self._list(request)

    def _list(self, request):
        qs = EAPriceDocument.objects.filter(is_active=True).exclude(status=EAPriceDocument.Status.DELETED).order_by('-document_date').select_related('price_variety', 'currency', 'power_supply', 'model_line')
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
            doc = EAPriceDocument.objects.select_related('model_line', 'price_variety', 'currency', 'power_supply').get(id=doc_id)
        except EAPriceDocument.DoesNotExist:
            return Response({'error': 'not found'}, status=404)

        rows = EAPriceConstructor.objects.filter(document=doc).select_related('model_line_item').order_by('model_line_item', 'option_field', 'option_id')

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
            'model_line': {'id': doc.model_line_id, 'name': doc.model_line.name, 'code': doc.model_line.code} if doc.model_line else None,
            'power_supply': {'id': doc.power_supply_id, 'name': str(doc.power_supply)},
            'rows': list(by_model.values()),
        })

    def post(self, request, doc_id=None):
        """POST /create/ → создать, /documents/{id}/post/ → провести, /documents/{id}/unpost/ → отменить, /import/ → импорт."""
        if doc_id is None:
            return self._create(request)
        url_name = request.resolver_match.url_name if request.resolver_match else ''
        if 'unpost' in url_name:
            return self._unpost(request, doc_id)
        if 'import' in url_name:
            return self._import(request, doc_id)
        return self._conduct(request, doc_id)

    def _create(self, request):
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

        if rows_data:
            self._create_rows(doc, rows_data, currency_id, price_variety_id)
        elif doc.model_line_id:
            # Auto-generate base rows for all models in this series+voltage
            model_items = ElectricActuatorModelLineItem.objects.filter(
                model_line_id=doc.model_line_id,
                model_line_item_power_supply_option__power_supply_id=ps.power_supply_id,
                is_active=True,
            ).distinct()
            for item in model_items:
                EAPriceConstructor.objects.create(
                    document=doc, model_line_item=item, power_supply=ps,
                    option_field='base', option_id=None, surcharge=0,
                    currency_id=currency_id, price_variety_id=price_variety_id,
                    is_active=False,
                )
        return Response({'id': doc.id, 'name': doc.name}, status=201)

    def _conduct(self, request, doc_id):
        """Провести документ. Если уже проведён — отмена + пересоздание строк."""
        try:
            doc = EAPriceDocument.objects.get(id=doc_id)
        except EAPriceDocument.DoesNotExist:
            return Response({'error': 'not found'}, status=404)

        rows_data = request.data.get('rows')

        # Если уже проведён — отменить, пересоздать строки
        if doc.status == EAPriceDocument.Status.POSTED:
            doc.unpost()
            if rows_data:
                EAPriceConstructor.objects.filter(document=doc).delete()
                self._create_rows(doc, rows_data, request.data.get('currency_id'), request.data.get('price_variety_id'))

        # Если черновик и есть новые данные — пересоздать строки
        elif rows_data and doc.status == EAPriceDocument.Status.DRAFT:
            EAPriceConstructor.objects.filter(document=doc).delete()
            self._create_rows(doc, rows_data, request.data.get('currency_id'), request.data.get('price_variety_id'))

        doc.post()
        return Response({'ok': True, 'status': doc.status, 'status_label': doc.get_status_display()})

    def _unpost(self, request, doc_id):
        """Отменить проведение документа."""
        try:
            doc = EAPriceDocument.objects.get(id=doc_id)
        except EAPriceDocument.DoesNotExist:
            return Response({'error': 'not found'}, status=404)

        if doc.status != EAPriceDocument.Status.POSTED:
            return Response({'error': 'Документ не проведён'}, status=400)

        doc.unpost()
        return Response({'ok': True, 'status': doc.status, 'status_label': doc.get_status_display()})

    def _create_rows(self, doc, rows_data, currency_id, price_variety_id):
        """Создать строки EAPriceConstructor для документа."""
        ps = doc.power_supply
        for row in rows_data:
            mli_id = row.get('model_line_item_id')
            base_price = row.get('base_price', 0)
            if not mli_id:
                continue
            EAPriceConstructor.objects.create(
                document=doc, model_line_item_id=mli_id, power_supply=ps,
                option_field='base', option_id=None, surcharge=base_price,
                currency_id=currency_id, price_variety_id=price_variety_id,
                is_active=False,
            )
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
                    document=doc, model_line_item_id=mli_id, power_supply=ps,
                    option_field=opt_field, option_id=opt_id_int, surcharge=price,
                    currency_id=currency_id, price_variety_id=price_variety_id,
                    is_active=False,
                )

    def _get_option_columns(self, doc):
        """Get all option column definitions + per-model availability.
        Returns {columns: [{key, label}], availability: {mli_id: set(key)}}"""
        if not doc.power_supply:
            return {'columns': [], 'availability': {}}
        ps = doc.power_supply
        model_items = ElectricActuatorModelLineItem.objects.filter(
            model_line_id=doc.model_line_id,
            model_line_item_power_supply_option__power_supply_id=ps.power_supply_id,
            is_active=True,
        ).distinct()
        cols = []
        seen = set()
        availability = {}
        for item in model_items:
            item_ps = ElectricPowerSupplyOption.objects.filter(
                model_line_item=item, power_supply_id=ps.power_supply_id, is_active=True
            ).first()
            if not item_ps:
                continue
            temp = ElectricActuatorConstructor(selected_model_line_item=item, selected_power_supply=item_ps)
            options = temp.get_available_options()
            item_keys = set()
            for key, items_list in options.items():
                if key == 'power_supply_options':
                    continue
                field = key.replace('_options', '')
                for opt in items_list:
                    if opt.get('is_default'):
                        continue
                    k = f"{field}_{opt['option_id']}"
                    item_keys.add(k)
                    if k not in seen:
                        seen.add(k)
                        cols.append({
                            'key': k,
                            'label': opt.get('encoding') or k,
                        })
            availability[item.id] = item_keys
        return {'columns': cols, 'availability': availability}

    def _build_matrix_df(self, doc):
        """Build pandas DataFrame from document rows + through-model option columns.
        NaN = unavailable option, 0 = available but not set, value = set."""
        col_data = self._get_option_columns(doc)
        col_defs = col_data['columns']
        availability = col_data['availability']

        base_rows = list(EAPriceConstructor.objects.filter(
            document=doc, option_field='base'
        ).select_related('model_line_item__model_line').order_by('model_line_item'))

        if not base_rows:
            return pd.DataFrame()

        ps_enc = doc.power_supply.encoding if doc.power_supply else ''

        # Build rows with NaN for all option columns
        rows = []
        for base in base_rows:
            mli = base.model_line_item
            label = f"{mli.model_line.code}{mli.code}.{ps_enc}"
            row = {'Модель': label, 'Базовая цена': float(base.surcharge)}
            for c in col_defs:
                row[c['label']] = np.nan
            rows.append(row)

        df = pd.DataFrame(rows)

        # Index DB options by model_line_item
        db_opts = EAPriceConstructor.objects.filter(document=doc).exclude(option_field='base')
        opt_by_mli = {}
        for opt in db_opts:
            opt_by_mli.setdefault(opt.model_line_item_id, {})[f"{opt.option_field}_{opt.option_id}"] = float(opt.surcharge)

        # Fill: available → 0 if not in DB, value if in DB; unavailable stays NaN
        for idx, base in enumerate(base_rows):
            mli_id = base.model_line_item_id
            avail = availability.get(mli_id, set())
            for c in col_defs:
                if c['key'] in avail:
                    df.at[idx, c['label']] = opt_by_mli.get(mli_id, {}).get(c['key'], 0.0)

        return df

    def _export(self, request, doc_id):
        """GET /documents/{id}/export/ — скачать матрицу как Excel (Pandas)."""
        try:
            doc = EAPriceDocument.objects.select_related('power_supply').get(id=doc_id)
        except EAPriceDocument.DoesNotExist:
            return Response({'error': 'not found'}, status=404)

        df = self._build_matrix_df(doc)
        if df.empty:
            return Response({'error': 'no rows'}, status=404)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=(doc.name or 'EA_Configurator')[:31], index=False, na_rep='—')
            ws = writer.sheets[(doc.name or 'EA_Configurator')[:31]]
            from openpyxl.styles import Font, PatternFill
            hf = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
            hfont = Font(bold=True)
            for col in range(1, len(df.columns) + 1):
                c = ws.cell(row=1, column=col)
                c.fill = hf
                c.font = hfont

        output.seek(0)
        safe_name = doc.name.replace(' ', '_').replace('/', '-')[:50] if doc.name else 'ea_config'
        resp = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = f'attachment; filename="ea_config_{doc_id}_{safe_name}.xlsx"'
        return resp

    def _print_doc(self, request, doc_id):
        """GET /documents/{id}/print/ — HTML для печати (Pandas)."""
        try:
            doc = EAPriceDocument.objects.select_related('model_line', 'price_variety', 'currency', 'power_supply').get(id=doc_id)
        except EAPriceDocument.DoesNotExist:
            return Response({'error': 'not found'}, status=404)

        df = self._build_matrix_df(doc)
        table_html = df.to_html(index=False, na_rep='—', classes='mtx', border=0) if not df.empty else '<p>Нет данных</p>'

        html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><title>{doc.name}</title>
<style>body{{font-family:Arial;margin:20px;font-size:12px}}
h2{{margin:0 0 4px}}table.mtx{{border-collapse:collapse;width:100%;margin-top:10px}}
.mtx th,.mtx td{{border:1px solid #999;padding:4px 6px;text-align:left}}
.mtx th{{background:#d9e2f3}}.mtx td{{text-align:right}}</style></head><body>
<h2>{doc.name}</h2>
<p>Дата: {doc.document_date} | Тип цены: {doc.price_variety.name if doc.price_variety else '—'} | Валюта: {doc.currency.code if doc.currency else '—'}</p>
<p>Серия: {doc.model_line.name if doc.model_line else '—'} | Напряжение: {doc.power_supply}</p>
{table_html}</body></html>'''
        return Response({'html': html})

    def _import(self, request, doc_id):
        """POST /documents/{id}/import/ — загрузить Excel, вернуть данные матрицы (Pandas)."""
        try:
            doc = EAPriceDocument.objects.get(id=doc_id)
        except EAPriceDocument.DoesNotExist:
            return Response({'error': 'not found'}, status=404)

        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'error': 'No file'}, status=400)

        df = pd.read_excel(uploaded)
        cols = list(df.columns[2:]) if len(df.columns) > 2 else []
        rows_data = df.where(pd.notna(df), None).to_dict('records')
        return Response({'rows': rows_data, 'headers': cols})

    def delete(self, request, doc_id=None):
        """Мягкое удаление (mark_deleted)."""
        if not doc_id:
            return Response({'error': 'id required'}, status=400)
        try:
            doc = EAPriceDocument.objects.get(id=doc_id)
            doc.mark_deleted()
            return Response({'ok': True, 'status': doc.status})
        except EAPriceDocument.DoesNotExist:
            return Response({'error': 'not found'}, status=404)