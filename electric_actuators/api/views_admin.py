# electric_actuators/api/views_admin.py
"""
Admin API: bulk power supply option matrix for EA model lines.

GET  /electric_actuators/admin/power-supply-matrix/?model_line_id=X
     → matrix: rows=models, columns=voltages × {I ном, I пуск, P, t откр, t закр, M мин, M макс}

POST /electric_actuators/admin/power-supply-matrix/
     → save matrix. Rule: if all seven fields are 0 or empty → delete through-record.

GET  /electric_actuators/admin/power-supply-matrix/export/?model_line_id=X
     → download Excel file

POST /electric_actuators/admin/power-supply-matrix/import/
     → upload Excel, parse, save
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.http import HttpResponse
from io import BytesIO

from electric_actuators.models import (
    ElectricActuatorModelLine,
    ElectricActuatorModelLineItem,
)
from electric_actuators.models.ea_model_line_item_options import ElectricPowerSupplyOption
from params.models import PowerSupplies


# Все поля ElectricPowerSupplyOption, которые редактируются в матрице
MATRIX_FIELDS = [
    'current_rated',      # motor_current_rated
    'current_starting',   # motor_current_starting
    'motor_power',        # motor_power
    'time_to_open',
    'time_to_close',
    'torque_min',
    'torque_max',
]

FIELD_LABELS = {
    'current_rated': 'I ном, А',
    'current_starting': 'I пуск, А',
    'motor_power': 'P, кВт',
    'time_to_open': 't откр, с',
    'time_to_close': 't закр, с',
    'torque_min': 'M мин, Нм',
    'torque_max': 'M макс, Нм',
}

DB_FIELD_MAP = {
    'current_rated': 'motor_current_rated',
    'current_starting': 'motor_current_starting',
}


# ═══════════════════════════════════════════════════════════════════════════
# Shared queries
# ═══════════════════════════════════════════════════════════════════════════

def _get_matrix_data(ml_id: int):
    """Return (model_line, models, power_supplies, record_index)."""
    ml = ElectricActuatorModelLine.objects.get(id=ml_id, is_active=True)

    models = ElectricActuatorModelLineItem.objects.filter(
        model_line=ml, is_active=True
    ).order_by('sorting_order')

    through_records = ElectricPowerSupplyOption.objects.filter(
        model_line_item__model_line=ml
    ).select_related('power_supply', 'model_line_item')

    ps_ids = sorted(set(r.power_supply_id for r in through_records))
    power_supplies = PowerSupplies.objects.filter(
        id__in=ps_ids
    ).order_by('sorting_order', 'name')

    record_index = {}
    for r in through_records:
        record_index[(r.model_line_item_id, r.power_supply_id)] = r

    return ml, models, power_supplies, record_index


def _get_valid_mli_ids(ml_id: int):
    """Return set of valid model_line_item IDs for this series."""
    return set(
        ElectricActuatorModelLineItem.objects.filter(
            model_line_id=ml_id, is_active=True
        ).values_list('id', flat=True)
    )


# ═══════════════════════════════════════════════════════════════════════════
# Views
# ═══════════════════════════════════════════════════════════════════════════

class EAPowerSupplyMatrixView(APIView):
    """Bulk edit power supply options for all models in a series."""
    permission_classes = [AllowAny]

    def get(self, request):
        ml_id = request.query_params.get('model_line_id')
        if not ml_id:
            return Response({'error': 'model_line_id required'}, status=400)

        try:
            ml, models, power_supplies, record_index = _get_matrix_data(int(ml_id))
        except ElectricActuatorModelLine.DoesNotExist:
            return Response({'error': 'model line not found'}, status=404)
        except (ValueError, TypeError):
            return Response({'error': 'invalid model_line_id'}, status=400)

        model_items = []
        for mli in models:
            voltages = []
            for ps in power_supplies:
                rec = record_index.get((mli.id, ps.id))
                entry = {
                    'power_supply_id': ps.id,
                    'power_supply_name': str(ps.name),
                    'through_id': rec.id if rec else None,
                    'is_active': rec.is_active if rec else False,
                }
                for f in MATRIX_FIELDS:
                    db_field = DB_FIELD_MAP.get(f, f)
                    entry[f] = float(getattr(rec, db_field, 0) or 0) if rec else 0.0
                voltages.append(entry)
            model_items.append({
                'id': mli.id,
                'name': mli.name,
                'code': mli.code,
                'voltages': voltages,
            })

        return Response({
            'model_line': {'id': ml.id, 'name': ml.name},
            'power_supplies': [{'id': ps.id, 'name': str(ps.name)} for ps in power_supplies],
            'models': model_items,
            'fields': MATRIX_FIELDS,
            'field_labels': FIELD_LABELS,
        })

    @transaction.atomic
    def post(self, request):
        ml_id = request.data.get('model_line_id')
        rows = request.data.get('rows', [])

        if not ml_id:
            return Response({'error': 'model_line_id required'}, status=400)

        created, updated, deleted = _save_rows(ml_id, rows)

        return Response({
            'ok': True,
            'created': created,
            'updated': updated,
            'deleted': deleted,
        })


class EAPowerSupplyMatrixExportView(APIView):
    """Export matrix as Excel file."""
    permission_classes = [AllowAny]

    def get(self, request):
        import pandas as pd  # lazy — не ломает URLs при отсутствии pandas

        ml_id = request.query_params.get('model_line_id')
        if not ml_id:
            return Response({'error': 'model_line_id required'}, status=400)

        try:
            ml, models, power_supplies, record_index = _get_matrix_data(int(ml_id))
        except ElectricActuatorModelLine.DoesNotExist:
            return Response({'error': 'model line not found'}, status=404)
        except (ValueError, TypeError):
            return Response({'error': 'invalid model_line_id'}, status=400)

        rows = []
        for mli in models:
            row = {'Модель': mli.name}
            for ps in power_supplies:
                rec = record_index.get((mli.id, ps.id))
                for f in MATRIX_FIELDS:
                    col = f'{ps.name} / {FIELD_LABELS[f]}'
                    db_field = DB_FIELD_MAP.get(f, f)
                    row[col] = float(getattr(rec, db_field, 0) or 0) if rec else ''
            rows.append(row)

        df = pd.DataFrame(rows)
        df = df.set_index('Модель')

        output = BytesIO()
        SHEET_NAME = 'Опции напряжения'
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=SHEET_NAME)
            ws = writer.sheets[SHEET_NAME]
            ws.column_dimensions['A'].width = 22
            for i in range(2, len(df.columns) + 2):
                ws.column_dimensions[_col_letter(i)].width = 16

        output.seek(0)
        filename = f'ea_power_supply_{ml.name}.xlsx'
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class EAPowerSupplyMatrixImportView(APIView):
    """Import matrix from uploaded Excel file."""
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        import pandas as pd  # lazy

        ml_id = request.data.get('model_line_id')
        file = request.FILES.get('file')

        if not ml_id:
            return Response({'error': 'model_line_id required'}, status=400)
        if not file:
            return Response({'error': 'file required'}, status=400)

        try:
            df = pd.read_excel(file, sheet_name='Опции напряжения', index_col=0)
        except ValueError:
            # Fallback: if sheet name doesn't match, try first sheet
            file.seek(0)
            df = pd.read_excel(file, sheet_name=0, index_col=0)
        except Exception as e:
            return Response({'error': f'Cannot read Excel: {e}'}, status=400)

        # Resolve all PowerSupplies by name (not just existing through-records)
        power_supplies = {
            str(ps.name): ps for ps in PowerSupplies.objects.all()
        }

        # Build mli name → id map for this series
        mli_map = {
            mli.name: mli.id
            for mli in ElectricActuatorModelLineItem.objects.filter(
                model_line_id=ml_id, is_active=True
            )
        }

        # Parse columns: "{ps_name} / {field_label}" → (ps_name, field)
        col_map = {}
        rev_labels = {v: k for k, v in FIELD_LABELS.items()}
        for col in df.columns:
            if ' / ' in col:
                parts = col.split(' / ', 1)
                ps_name = parts[0].strip()
                label = parts[1].strip()
                field = rev_labels.get(label)
                if ps_name in power_supplies and field:
                    col_map[col] = (ps_name, field)

        # Build rows from DataFrame
        rows = []
        for mli_name, row_data in df.iterrows():
            mli_name = str(mli_name).strip()
            mli_id = mli_map.get(mli_name)
            if not mli_id:
                continue
            for col, (ps_name, field) in col_map.items():
                val = row_data.get(col)
                if pd.isna(val):
                    val = 0
                ps_id = power_supplies[ps_name].id
                rows.append({
                    'model_line_item_id': mli_id,
                    'power_supply_id': ps_id,
                    field: float(val) if val else 0,
                })

        # Merge rows: same (mli_id, ps_id) → one dict with all fields
        merged = {}
        for r in rows:
            key = (r['model_line_item_id'], r['power_supply_id'])
            if key not in merged:
                merged[key] = {'model_line_item_id': key[0], 'power_supply_id': key[1]}
            for f in MATRIX_FIELDS:
                if f in r:
                    merged[key][f] = r[f]

        created, updated, deleted = _save_rows(ml_id, list(merged.values()))

        return Response({
            'ok': True,
            'created': created,
            'updated': updated,
            'deleted': deleted,
            'rows_processed': len(merged),
        })


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _save_rows(ml_id, rows):
    """Save rows to DB. Returns (created, updated, deleted)."""
    valid_mli_ids = _get_valid_mli_ids(ml_id)

    # Pre-fetch power supplies for encoding
    all_ps_ids = set(r.get('power_supply_id') for r in rows if r.get('power_supply_id'))
    ps_encodings = {
        ps.id: ps.encoding
        for ps in PowerSupplies.objects.filter(id__in=all_ps_ids)
    }

    created = 0
    updated = 0
    deleted = 0

    for row in rows:
        mli_id = row.get('model_line_item_id')
        ps_id = row.get('power_supply_id')

        if not mli_id or not ps_id:
            continue
        if mli_id not in valid_mli_ids:
            continue  # skip foreign model_line_items

        defaults = {}
        for f in MATRIX_FIELDS:
            val = _to_decimal(row.get(f))
            defaults[DB_FIELD_MAP.get(f, f)] = val

        # If all fields are None → delete
        if not any(defaults.values()):
            qs = ElectricPowerSupplyOption.objects.filter(
                model_line_item_id=mli_id, power_supply_id=ps_id,
            )
            if qs.exists():
                deleted += qs.count()
                qs.delete()
            continue

        defaults['is_active'] = True
        defaults['encoding'] = ps_encodings.get(ps_id, '')

        obj, is_new = ElectricPowerSupplyOption.objects.update_or_create(
            model_line_item_id=mli_id,
            power_supply_id=ps_id,
            defaults=defaults,
        )
        if is_new:
            created += 1
        else:
            updated += 1

    return created, updated, deleted


def _to_decimal(val):
    """Convert value to Decimal, return None if empty/zero."""
    if val is None or val == '':
        return None
    from decimal import Decimal, InvalidOperation
    try:
        d = Decimal(str(val))
        return d if d != 0 else None
    except (InvalidOperation, ValueError):
        return None


def _col_letter(n):
    """1 → 'A', 2 → 'B', ..., 27 → 'AA'."""
    s = ''
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s
