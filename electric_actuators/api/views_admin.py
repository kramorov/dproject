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
from electric_actuators.models.ea_model_line_item_options import (
    ElectricPowerSupplyOption,
    ElectricControlUnitOption,
    ElectricSafetyPositionOption,
)
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

        # If all fields are None/zero → deactivate (не удаляем — CASCADE убьёт ControlUnit и SafetyPosition)
        if not any(defaults.values()):
            updated_count = ElectricPowerSupplyOption.objects.filter(
                model_line_item_id=mli_id, power_supply_id=ps_id,
            ).update(is_active=False,
                      motor_current_rated=0, motor_current_starting=0,
                      motor_power=0, time_to_open=0, time_to_close=0,
                      torque_min=0, torque_max=0)
            deleted += updated_count
            continue

        defaults['is_active'] = True

        # update_or_create падает при дубликатах (нет unique_together) — чистим дубли
        existing = ElectricPowerSupplyOption.objects.filter(
            model_line_item_id=mli_id,
            power_supply_id=ps_id,
        ).order_by('id')
        count = existing.count()
        if count > 1:
            # Оставляем первую запись, остальные удаляем
            first = existing.first()
            dupes = existing.exclude(id=first.id)
            dupes.delete()
            deleted += count - 1
        if count >= 1:
            first = existing.first()
            for k, v in defaults.items():
                setattr(first, k, v)
            first.save()
            updated += 1
        else:
            defaults['encoding'] = ps_encodings.get(ps_id, '')
            ElectricPowerSupplyOption.objects.create(
                model_line_item_id=mli_id,
                power_supply_id=ps_id,
                **defaults,
            )
            created += 1

    return created, updated, deleted


def _to_decimal(val):
    """Convert value to Decimal, return None for empty, Decimal('0') for zero."""
    if val is None or val == '':
        return None
    from decimal import Decimal, InvalidOperation
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError):
        return None


def _col_letter(n):
    """1 → 'A', 2 → 'B', ..., 27 → 'AA'."""
    s = ''
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


# ═══════════════════════════════════════════════════════════════════════════
# Copy Control Unit / Safety Position options
# ═══════════════════════════════════════════════════════════════════════════

class EACopyControlUnitsView(APIView):
    """GET: список моделей с опциями. POST: копировать опции от модели к модели."""
    permission_classes = [AllowAny]

    def get(self, request):
        """Список model_line_items с их ControlUnit и SafetyPosition + палитра всех опций."""
        ml_id = request.query_params.get('model_line_id')
        ps_id = request.query_params.get('power_supply_id')
        if not ml_id or not ps_id:
            return Response({'error': 'model_line_id and power_supply_id required'}, status=400)

        models = list(ElectricActuatorModelLineItem.objects.filter(
            model_line_id=ml_id, is_active=True
        ).order_by('sorting_order'))
        mli_ids = [m.id for m in models]

        # Один запрос: все PS-записи для нужного напряжения
        ps_records = {
            r.model_line_item_id: r
            for r in ElectricPowerSupplyOption.objects.filter(
                model_line_item_id__in=mli_ids, power_supply_id=ps_id, is_active=True
            )
        }
        ps_ids_with_rec = [r.id for r in ps_records.values()]

        # Один запрос: все CU
        all_cu_records = list(ElectricControlUnitOption.objects.filter(
            power_supply_option_id__in=ps_ids_with_rec, is_active=True
        ).select_related('control_unit'))
        # Один запрос: все SP
        all_sp_records = list(ElectricSafetyPositionOption.objects.filter(
            power_supply_option_id__in=ps_ids_with_rec, is_active=True
        ).select_related('safety_position'))

        # Группируем CU/SP по ps_id
        cu_by_ps = {}
        for cu in all_cu_records:
            cu_by_ps.setdefault(cu.power_supply_option_id, []).append(cu)
        sp_by_ps = {}
        for sp in all_sp_records:
            sp_by_ps.setdefault(sp.power_supply_option_id, []).append(sp)

        # Палитра
        all_cu, all_sp = {}, {}
        result = []
        for mli in models:
            ps_rec = ps_records.get(mli.id)
            cu_set, sp_set = {}, {}
            if ps_rec:
                for cu in cu_by_ps.get(ps_rec.id, []):
                    all_cu[cu.control_unit_id] = {
                        'id': cu.control_unit_id, 'name': cu.control_unit.name, 'encoding': cu.encoding,
                    }
                    cu_set[cu.control_unit_id] = {
                        'id': cu.id, 'encoding': cu.encoding, 'is_default': cu.is_default,
                    }
                for sp in sp_by_ps.get(ps_rec.id, []):
                    all_sp[sp.safety_position_id] = {
                        'id': sp.safety_position_id, 'name': sp.safety_position.name, 'encoding': sp.encoding,
                    }
                    sp_set[sp.safety_position_id] = {
                        'id': sp.id, 'encoding': sp.encoding, 'is_default': sp.is_default,
                    }
            result.append({
                'id': mli.id, 'name': mli.name,
                'has_power_supply': ps_rec is not None,
                'cu': cu_set, 'sp': sp_set,
            })

        # Добавляем все возможные опции из справочников (даже те, которых нет ни у одной модели)
        from params.models import ControlUnitInstalledOption, SafetyPositionOption
        existing_cu_ids = set(all_cu.keys())
        for opt in ControlUnitInstalledOption.objects.filter(is_active=True):
            if opt.id not in existing_cu_ids:
                all_cu[opt.id] = {
                    'id': opt.id, 'name': opt.name,
                    'encoding': opt.code or opt.symbolic_code or str(opt.id),
                }
        existing_sp_ids = set(all_sp.keys())
        for opt in SafetyPositionOption.objects.filter(is_active=True):
            if opt.id not in existing_sp_ids:
                all_sp[opt.id] = {
                    'id': opt.id, 'name': opt.name,
                    'encoding': opt.code or opt.symbolic_code or str(opt.id),
                }

        return Response({
            'models': result,
            'palette': {
                'control_units': sorted(all_cu.values(), key=lambda x: x['name']),
                'safety_positions': sorted(all_sp.values(), key=lambda x: x['name']),
            },
        })

    @transaction.atomic
    def post(self, request):
        """Копировать ControlUnit + SafetyPosition от source_mli_id к target_mli_ids."""
        source_id = request.data.get('source_mli_id')
        target_ids = request.data.get('target_mli_ids', [])
        ps_id = request.data.get('power_supply_id')

        if not source_id or not target_ids or not ps_id:
            return Response({'error': 'source_mli_id, target_mli_ids, power_supply_id required'}, status=400)

        # Найти source power_supply_option
        source_ps = ElectricPowerSupplyOption.objects.filter(
            model_line_item_id=source_id, power_supply_id=ps_id, is_active=True
        ).first()
        if not source_ps:
            return Response({'error': 'Source model has no active power supply option for this voltage'}, status=400)

        source_cus = list(ElectricControlUnitOption.objects.filter(power_supply_option=source_ps))
        source_sps = list(ElectricSafetyPositionOption.objects.filter(power_supply_option=source_ps))

        created_cu = 0
        created_sp = 0
        skipped = 0

        for tid in target_ids:
            if tid == source_id:
                continue
            target_ps = ElectricPowerSupplyOption.objects.filter(
                model_line_item_id=tid, power_supply_id=ps_id, is_active=True
            ).first()
            if not target_ps:
                skipped += 1
                continue

            # Удалить старые опции целевой модели
            ElectricControlUnitOption.objects.filter(power_supply_option=target_ps).delete()
            ElectricSafetyPositionOption.objects.filter(power_supply_option=target_ps).delete()

            # Скопировать
            for cu in source_cus:
                ElectricControlUnitOption.objects.create(
                    power_supply_option=target_ps,
                    control_unit=cu.control_unit,
                    encoding=cu.encoding,
                    is_default=cu.is_default,
                    sorting_order=cu.sorting_order,
                    is_active=True,
                )
                created_cu += 1
            for sp in source_sps:
                ElectricSafetyPositionOption.objects.create(
                    power_supply_option=target_ps,
                    safety_position=sp.safety_position,
                    encoding=sp.encoding,
                    is_default=sp.is_default,
                    sorting_order=sp.sorting_order,
                    is_active=True,
                )
                created_sp += 1

        return Response({
            'ok': True,
            'created_control_units': created_cu,
            'created_safety_positions': created_sp,
            'skipped_no_power_supply': skipped,
        })

    @transaction.atomic
    def patch(self, request):
        """Обновить CU/SP для одной модели (источник)."""
        mli_id = request.data.get('model_line_item_id')
        ps_id = request.data.get('power_supply_id')
        cus = request.data.get('control_units', [])
        sps = request.data.get('safety_positions', [])

        if not mli_id or not ps_id:
            return Response({'error': 'model_line_item_id and power_supply_id required'}, status=400)

        ps_rec = ElectricPowerSupplyOption.objects.filter(
            model_line_item_id=mli_id, power_supply_id=ps_id, is_active=True
        ).first()
        if not ps_rec:
            return Response({'error': 'No active power supply option for this model+voltage'}, status=400)

        # Validate FK existence
        cu_ids = [cu.get('control_unit_id') for cu in cus if cu.get('control_unit_id')]
        sp_ids = [sp.get('safety_position_id') for sp in sps if sp.get('safety_position_id')]
        from params.models import ControlUnitInstalledOption, SafetyPositionOption
        valid_cu = set(ControlUnitInstalledOption.objects.filter(id__in=cu_ids).values_list('id', flat=True))
        valid_sp = set(SafetyPositionOption.objects.filter(id__in=sp_ids).values_list('id', flat=True))
        invalid_cu = [i for i in cu_ids if i not in valid_cu]
        invalid_sp = [i for i in sp_ids if i not in valid_sp]
        if invalid_cu or invalid_sp:
            return Response({
                'error': 'Invalid option IDs',
                'invalid_control_units': invalid_cu,
                'invalid_safety_positions': invalid_sp,
            }, status=400)

        # Replace CU
        ElectricControlUnitOption.objects.filter(power_supply_option=ps_rec).delete()
        for i, cu in enumerate(cus):
            ElectricControlUnitOption.objects.create(
                power_supply_option=ps_rec,
                control_unit_id=cu.get('control_unit_id'),
                encoding=cu.get('encoding', ''),
                is_default=cu.get('is_default', False),
                sorting_order=i,
                is_active=True,
            )
        # Replace SP
        ElectricSafetyPositionOption.objects.filter(power_supply_option=ps_rec).delete()
        for i, sp in enumerate(sps):
            ElectricSafetyPositionOption.objects.create(
                power_supply_option=ps_rec,
                safety_position_id=sp.get('safety_position_id'),
                encoding=sp.get('encoding', ''),
                is_default=sp.get('is_default', False),
                sorting_order=i,
                is_active=True,
            )

        return Response({
            'ok': True,
            'control_units': len(cus),
            'safety_positions': len(sps),
        })
