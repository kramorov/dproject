# pneumatic_actuators/services/pointwise_selector.py
"""Поточечный (4/6-точечный) подбор привода.

Требование арматуры — кривая по точкам набора характеристик:
    требуемое[точка] = база × коэффициент × запас.

Возможности привода:
    - воздух — точки открытия BTO/RTO/ETO при рабочем давлении (для SR это нетто);
    - пружина — точки закрытия BTC/RTC/ETC (строка давления 'spring').

Сравнение выполняется по позициям хода (start/mid/end), спаривание open↔close
по позиции: BTO↔ETC, RTO↔RTC, ETO↔BTC.

Правила:
    DA      — воздух должен покрыть max(требование открытия, требование закрытия)
              в каждой позиции (привод симметричный);
    SR НЗ   — воздух ≥ требование открытия по позициям; пружина ≥ требование
              закрытия по позициям;
    SR НО   — воздух ≥ требование закрытия; пружина ≥ требование открытия.
"""
from collections import defaultdict
from typing import Dict, List, Optional

from pneumatic_actuators.models.py_options_constants import (
    SPRINGS_DA_DEFAULT_CODE, SAFETY_POSITION_NC_DEFAULT_CODE,
    SAFETY_POSITION_NO_DEFAULT_CODE,
)
from pneumatic_actuators.services.torque_selector import (
    SPRING_POINT_CODES, AIR_POINT_CODES,
)

# Позиции хода: код точки открытия/закрытия на каждой позиции.
OPEN_BY_POSITION = {'start': 'bto', 'mid': 'rto', 'end': 'eto'}
CLOSE_BY_POSITION = {'start': 'etc', 'mid': 'rtc', 'end': 'btc'}
POSITIONS = ('start', 'mid', 'end')


class PointwiseSelector:
    """Подбор приводов по кривой требуемого момента (4/6 точек)."""

    @staticmethod
    def compute_required_curve(base_torque: float, safety_factor: float,
                               factors: Dict[str, float]) -> Dict[str, float]:
        """Требуемая кривая: {code: значение} = база × запас × коэффициент."""
        return {code: base_torque * safety_factor * factor
                for code, factor in factors.items() if factor}

    @staticmethod
    def _demand_by_position(required: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Разложить требование по позициям: {pos: {direction: value}}."""
        out = defaultdict(dict)
        for pos in POSITIONS:
            oc = OPEN_BY_POSITION[pos]
            cc = CLOSE_BY_POSITION[pos]
            if oc in required:
                out[pos]['open'] = required[oc]
            if cc in required:
                out[pos]['close'] = required[cc]
        return out

    @staticmethod
    def _actuator_curves(table_model, body_ids, work_pressure_id):
        """Кривые приводов: body_id → {'air': {pos: v}, 'spring': {pos: v},
        'spring_qty': code} для каждого spring_qty."""
        rows = table_model.objects.filter(
            body_id__in=body_ids,
            spring_qty__is_active=True,
            point__code__in=AIR_POINT_CODES + SPRING_POINT_CODES,
        ).select_related('spring_qty', 'pressure', 'point')

        # body → spring_qty_code → {'air': {pos: v}, 'spring': {pos: v}}
        curves = defaultdict(lambda: defaultdict(lambda: {'air': {}, 'spring': {}}))
        for r in rows:
            code = r.point.code
            grp = curves[r.body_id][r.spring_qty.code]
            if r.pressure.code == 'spring':
                if code == 'btc':
                    grp['spring']['end'] = float(r.value)
                elif code == 'rtc' and r.value:
                    grp['spring']['mid'] = float(r.value)
                elif code == 'etc':
                    grp['spring']['start'] = float(r.value)
            elif r.pressure_id == work_pressure_id:
                if code == 'bto':
                    grp['air']['start'] = float(r.value)
                elif code == 'rto' and r.value:
                    grp['air']['mid'] = float(r.value)
                elif code == 'eto':
                    grp['air']['end'] = float(r.value)
                # Линейные: значения пружины лежат в строках рабочего давления
                # (нет отдельной строки 'spring'); у ротационных в этих строках
                # только точки открытия, ветки не срабатывают.
                elif code == 'btc':
                    grp['spring']['end'] = float(r.value)
                elif code == 'rtc' and r.value:
                    grp['spring']['mid'] = float(r.value)
                elif code == 'etc':
                    grp['spring']['start'] = float(r.value)
        # Средняя точка 0 (реечные, данные без середины) → консервативно
        # принимаем min(start, end): линейное изменение момента между концами.
        for by_sq in curves.values():
            for grp in by_sq.values():
                for curve in ('air', 'spring'):
                    if 'mid' not in grp[curve]:
                        if 'start' in grp[curve] and 'end' in grp[curve]:
                            grp[curve]['mid'] = min(grp[curve]['start'], grp[curve]['end'])
        return curves

    @classmethod
    def select(cls, table_model, body_model, required: Dict[str, float],
               actuator_variety: str, safety_position: str,
               work_pressure_id: int, body_ids: Optional[List[int]] = None,
               max_bodies: int = 10) -> List[Dict]:
        """Подобрать тела по кривой требования.

        Returns: список тел с полями body_id/body_code/type/spring_qty/
        margins (по позициям), critical_position, margin (минимальный).
        """
        demand = cls._demand_by_position(required)
        positions_used = [p for p in POSITIONS if demand[p]]

        if body_ids:
            bodies = list(body_model.objects.filter(id__in=body_ids, is_active=True))
        else:
            bodies = list(body_model.objects.filter(is_active=True))

        curves = cls._actuator_curves(table_model, [b.id for b in bodies], work_pressure_id)

        is_da = actuator_variety == SPRINGS_DA_DEFAULT_CODE
        is_nc = safety_position == SAFETY_POSITION_NC_DEFAULT_CODE

        results = []
        for body in bodies:
            for sq_code, grp in curves.get(body.id, {}).items():
                if is_da and sq_code != SPRINGS_DA_DEFAULT_CODE:
                    continue
                if not is_da and sq_code == SPRINGS_DA_DEFAULT_CODE:
                    continue

                air = grp['air']
                spring = grp['spring']

                margins = {}
                valid = True
                for pos in positions_used:
                    d = demand[pos]
                    checks = []
                    if is_da:
                        cap = air.get(pos)
                        req = max(d.get('open', 0.0), d.get('close', 0.0))
                        checks.append({'side': 'air', 'capability': cap, 'demand': req,
                                       'margin': (cap - req) if cap is not None else None})
                        if cap is None or cap < req:
                            valid = False
                            margins[pos] = {'margin': None, 'details': checks}
                            break
                    else:
                        # НЗ: воздух против open, пружина против close; НО — наоборот.
                        air_key, spring_key = ('open', 'close') if is_nc else ('close', 'open')
                        if air_key in d:
                            cap = air.get(pos)
                            req = d[air_key]
                            checks.append({'side': 'air', 'capability': cap, 'demand': req,
                                           'margin': (cap - req) if cap is not None else None})
                            if cap is None or cap < req:
                                valid = False
                                margins[pos] = {'margin': None, 'details': checks}
                                break
                        if spring_key in d:
                            cap = spring.get(pos)
                            req = d[spring_key]
                            checks.append({'side': 'spring', 'capability': cap, 'demand': req,
                                           'margin': (cap - req) if cap is not None else None})
                            if cap is None or cap < req:
                                valid = False
                                margins[pos] = {'margin': None, 'details': checks}
                                break
                    if valid or pos not in margins:
                        margins[pos] = {
                            'margin': min((c['margin'] for c in checks if c['margin'] is not None), default=None),
                            'details': checks,
                        }

                if not valid:
                    continue

                min_margin = min((m['margin'] for m in margins.values() if m.get('margin') is not None),
                                 default=None)
                if min_margin is None:
                    continue
                critical = min(margins.items(), key=lambda kv: kv[1].get('margin', 1e18))[0]

                results.append({
                    'body_id': body.id,
                    'body_code': body.code,
                    'body_name': body.name,
                    'type': 'DA' if is_da else 'SR',
                    'spring_qty_code': sq_code,
                    'margins': margins,
                    'critical_position': critical,
                    'margin': min_margin,
                })

        results.sort(key=lambda r: r['margin'])
        return results[:max_bodies]
