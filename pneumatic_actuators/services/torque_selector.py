# pneumatic_actuators/services/torque_selector.py
from typing import List , Dict , Optional

from django.db.models import Q

from pneumatic_actuators.models.py_options_constants import SPRINGS_DA_DEFAULT_CODE

# Маппинг кода точки → поле отображения (пружина хранится под BTC/RTC/ETC,
# в логике подбора используется старый вид BTO/RTO/ETO ориентации открытия).
POINT_TO_DISPLAY_FIELD = {
    'bto': 'bto', 'rto': 'rto', 'eto': 'eto',
    'btc': 'eto', 'rtc': 'rto', 'etc': 'bto',
}

# Точки, из которых собирается пружинная строка (давление 'spring').
SPRING_POINT_CODES = ('btc', 'rtc', 'etc')
# Точки воздушной строки.
AIR_POINT_CODES = ('bto', 'rto', 'eto')


class TorqueSelectorService :
    """Сервис для подбора приводов по моменту (старый однозначный подбор)."""

    @staticmethod
    def get_pressure_by_id(pressure_model , pressure_id: int) -> Optional[Dict] :
        """Получить информацию о давлении по ID"""
        try :
            pressure = pressure_model.objects.get(id=pressure_id)
            return {
                'id' : pressure.id ,
                'code' : pressure.code ,
                'name' : pressure.name ,
                'value' : float(pressure.code) if pressure.code.replace('.' , '').isdigit() else None
            }
        except Exception :
            return None

    @staticmethod
    def _pivot_groups(records) -> Dict:
        """Сгруппировать строки точек по spring_qty → {spring: {bto,eto}, pressure: {bto,eto}}."""
        out = {}
        for r in records :
            field = POINT_TO_DISPLAY_FIELD.get(r.point.code)
            if field is None :
                continue
            code = r.spring_qty.code
            grp = out.setdefault(code, {'spring': {}, 'pressure': {}})
            if r.pressure.code == 'spring' :
                grp['spring'][field] = float(r.value)
            else :
                grp['pressure'][field] = float(r.value)
        return out

    @staticmethod
    def get_spring_data_sr(table_model , body_id: int) -> List[Dict] :
        """Получить данные для пружин (spring) для SR приводов"""
        spring_records = table_model.objects.filter(
            body_id=body_id ,
            pressure__code='spring' ,
            spring_qty__is_active=True,
            point__code__in=SPRING_POINT_CODES,
        ).exclude(spring_qty__code=SPRINGS_DA_DEFAULT_CODE).select_related('spring_qty', 'point')

        result = []
        for code , grp in TorqueSelectorService._pivot_groups(spring_records).items() :
            vals = grp['spring']
            if vals.get('bto') is not None and vals.get('eto') is not None :
                spring_qty = next(r.spring_qty for r in spring_records if r.spring_qty.code == code)
                result.append({
                    'id' : spring_qty.id ,
                    'spring_qty_id' : spring_qty.id ,
                    'spring_qty_code' : code ,
                    'spring_qty_name' : spring_qty.name ,
                    'bto' : vals['bto'] ,
                    'eto' : vals['eto'] ,
                    'min_value' : min(vals['bto'] , vals['eto'])
                })
        result.sort(key=lambda x : x['spring_qty_code'])
        return result

    @staticmethod
    def get_work_pressure_data_sr(table_model , body_id: int , work_pressure_id: int) -> List[Dict] :
        """Получить данные для рабочего давления для SR приводов"""
        pressure_records = table_model.objects.filter(
            body_id=body_id ,
            pressure_id=work_pressure_id ,
            spring_qty__is_active=True,
            point__code__in=AIR_POINT_CODES,
        ).exclude(spring_qty__code=SPRINGS_DA_DEFAULT_CODE).select_related('spring_qty', 'point')

        result = []
        for code , grp in TorqueSelectorService._pivot_groups(pressure_records).items() :
            vals = grp['pressure']
            if vals.get('bto') is not None and vals.get('eto') is not None :
                spring_qty = next(r.spring_qty for r in pressure_records if r.spring_qty.code == code)
                result.append({
                    'id' : spring_qty.id ,
                    'spring_qty_id' : spring_qty.id ,
                    'spring_qty_code' : code ,
                    'spring_qty_name' : spring_qty.name ,
                    'bto' : vals['bto'] ,
                    'eto' : vals['eto'] ,
                    'min_value' : min(vals['bto'] , vals['eto'])
                })
        result.sort(key=lambda x : x['spring_qty_code'])
        return result

    @staticmethod
    def get_da_data(table_model , body_id: int , work_pressure_id: int) -> List[Dict] :
        """Получить данные для DA приводов (без пружин)"""
        da_records = table_model.objects.filter(
            body_id=body_id ,
            pressure_id=work_pressure_id ,
            spring_qty__code=SPRINGS_DA_DEFAULT_CODE ,
            spring_qty__is_active=True,
            point__code='bto',
        ).select_related('spring_qty')

        result = []
        for record in da_records :
            if record.value is not None :
                result.append({
                    'id' : record.id ,
                    'spring_qty_id' : record.spring_qty.id ,
                    'spring_qty_code' : record.spring_qty.code ,
                    'spring_qty_name' : record.spring_qty.name ,
                    'bto' : float(record.value) ,
                    'rto' : float(record.value) ,
                    'eto' : float(record.value) ,
                    'value' : float(record.value)
                })
        return result

    @staticmethod
    def calculate_score_sr(spring: Dict , pressure: Dict , torque_with_sf: float) -> Dict :
        """Рассчитывает рейтинг для SR привода"""
        spring_min = min(spring['bto'] , spring['eto'])
        spring_max = max(spring['bto'] , spring['eto'])
        spring_center = (spring['bto'] + spring['eto']) / 2

        pressure_min = min(pressure['bto'] , pressure['eto'])
        pressure_max = max(pressure['bto'] , pressure['eto'])
        pressure_center = (pressure['bto'] + pressure['eto']) / 2

        if torque_with_sf >= spring_min :
            return {'total_score' : 999 , 'is_valid' : False}

        if torque_with_sf >= pressure_min :
            return {'total_score' : 999 , 'is_valid' : False}

        spring_deviation = abs(torque_with_sf - spring_center)
        pressure_deviation = abs(torque_with_sf - pressure_center)
        total_score = spring_deviation + pressure_deviation

        return {
            'total_score' : total_score ,
            'is_valid' : True ,
            'spring_deviation' : spring_deviation ,
            'pressure_deviation' : pressure_deviation ,
            'spring_center' : spring_center ,
            'pressure_center' : pressure_center ,
            'spring_margin' : spring_min - torque_with_sf ,
            'pressure_margin' : pressure_min - torque_with_sf ,
            'spring_min' : spring_min ,
            'spring_max' : spring_max ,
            'pressure_min' : pressure_min ,
            'pressure_max' : pressure_max
        }

    @staticmethod
    def calculate_score_da(da_record: Dict , torque_with_sf: float) -> Dict :
        """Рассчитывает рейтинг для DA привода"""
        bto_value = da_record['value']

        if torque_with_sf >= bto_value :
            return {'total_score' : 999 , 'is_valid' : False}

        deviation = bto_value - torque_with_sf

        return {
            'total_score' : deviation ,
            'is_valid' : True ,
            'bto_value' : bto_value ,
            'margin' : deviation
        }

    def find_suitable_sr_actuators(self , table_model , body_model , pressure_model ,
                                   torque_with_sf: float , work_pressure_id: int ,
                                   body_ids: Optional[List[int]] = None ,
                                   max_bodies: int = 3) -> List[Dict] :
        """Найти подходящие SR приводы"""

        work_pressure = self.get_pressure_by_id(pressure_model , work_pressure_id)
        if not work_pressure :
            return []

        if body_ids :
            bodies = list(body_model.objects.filter(id__in=body_ids , is_active=True))
        else :
            bodies = list(body_model.objects.filter(is_active=True))

        if not bodies :
            return []

        # Один запрос на все тела (убирает N+1).
        from collections import defaultdict
        records_by_body = defaultdict(list)
        # Только строки выбранного рабочего давления + строки пружины ('spring').
        # Раньше загружались строки всех давлений, и в _pivot_groups() кривая
        # «pressure» перезаписывалась последней строкой (максимальное давление),
        # поэтому выбор давления в пневмосистеме игнорировался.
        all_records = table_model.objects.filter(
            body_id__in=[b.id for b in bodies] ,
            spring_qty__is_active=True,
            point__code__in=SPRING_POINT_CODES + AIR_POINT_CODES,
        ).filter(
            Q(pressure_id=work_pressure_id) | Q(pressure__code='spring')
        ).exclude(spring_qty__code=SPRINGS_DA_DEFAULT_CODE).select_related('spring_qty' , 'pressure' , 'point')
        for record in all_records :
            records_by_body[record.body_id].append(record)

        all_results = []

        for body in bodies :
            groups = self._pivot_groups(records_by_body.get(body.id , []))

            suitable_combinations = []
            for qty_code , group in groups.items() :
                spring = group['spring']
                pressure = group['pressure']

                if not spring.get('bto') or not spring.get('eto') or not pressure.get('bto') or not pressure.get('eto') :
                    continue

                score_data = self.calculate_score_sr(spring , pressure , torque_with_sf) # type: ignore
                if score_data['is_valid'] :
                    qty = next((r.spring_qty for r in records_by_body.get(body.id, []) if r.spring_qty.code == qty_code), None)
                    suitable_combinations.append({
                        'spring_qty_id' : qty.id if qty else None ,
                        'spring_qty_code' : qty_code ,
                        'spring_qty_name' : qty.name if qty else qty_code ,
                        'spring_bto' : spring['bto'] ,
                        'spring_eto' : spring['eto'] ,
                        'spring_min' : score_data['spring_min'] ,
                        'spring_margin' : score_data['spring_margin'] ,
                        'pressure_bto' : pressure['bto'] ,
                        'pressure_eto' : pressure['eto'] ,
                        'pressure_min' : score_data['pressure_min'] ,
                        'pressure_margin' : score_data['pressure_margin'] ,
                        'score' : score_data['total_score']
                    })

            if suitable_combinations :
                suitable_combinations.sort(key=lambda x : x['score'])
                best = suitable_combinations[0]
                all_results.append({
                    'body_id' : body.id ,
                    'body_code' : body.code ,
                    'body_name' : body.name ,
                    'type' : 'SR' ,
                    'score' : best['score'] ,
                    'spring_margin' : best['spring_margin'] ,
                    'combinations' : suitable_combinations ,
                    'best_combination' : best ,
                    'total_combinations' : len(suitable_combinations)
                })

        all_results.sort(key=lambda x : x['best_combination']['score'])
        return all_results[:max_bodies]

    def find_suitable_da_actuators(self, table_model, body_model, pressure_model,
                                   torque_with_sf: float, work_pressure_id: int,
                                   body_ids: Optional[List[int]] = None,
                                   max_bodies: int = 3) -> List[Dict]:
        """Найти подходящие DA приводы"""

        work_pressure = self.get_pressure_by_id(pressure_model, work_pressure_id)
        if not work_pressure:
            return []

        if body_ids:
            bodies = list(body_model.objects.filter(id__in=body_ids, is_active=True))
        else:
            bodies = list(body_model.objects.filter(is_active=True))

        if not bodies:
            return []

        from collections import defaultdict
        records = table_model.objects.filter(
            body_id__in=[b.id for b in bodies],
            pressure_id=work_pressure_id,
            spring_qty__code=SPRINGS_DA_DEFAULT_CODE,
            spring_qty__is_active=True,
            point__code='bto',
        ).select_related('spring_qty')

        by_body = defaultdict(list)
        for record in records:
            if record.value is not None:
                by_body[record.body_id].append({
                    'id': record.id,
                    'spring_qty_id': record.spring_qty.id,
                    'spring_qty_code': record.spring_qty.code,
                    'spring_qty_name': record.spring_qty.name,
                    'bto': float(record.value),
                    'rto': float(record.value),
                    'eto': float(record.value),
                    'value': float(record.value),
                })

        all_results = []
        for body in bodies:
            da_records = by_body.get(body.id, [])

            suitable = []
            for da in da_records:
                score_data = self.calculate_score_da(da, torque_with_sf)
                if score_data['is_valid']:
                    suitable.append({
                        'bto': da['bto'],
                        'margin': score_data['margin'],
                        'score': score_data['total_score']
                    })

            if suitable:
                suitable.sort(key=lambda x: x['score'])
                best = suitable[0]
                all_results.append({
                    'body_id': body.id,
                    'body_code': body.code,
                    'body_name': body.name,
                    'type': 'DA',
                    'score': best['score'],
                    'spring_margin': best['margin'],
                    'best_combination': best,
                    'total_combinations': len(suitable)
                })

        all_results.sort(key=lambda x: x['best_combination']['score'])
        return all_results[:max_bodies]

    def build_result_structure(self , results: List[Dict] , max_bodies: int = 3) -> List[Dict] :
        """Формирует структуру для отображения в браузере"""
        output = []

        for res in results[:max_bodies] :
            best = res['best_combination']

            if res['type'] == 'SR' :
                item = {
                    'body_id' : res['body_id'] ,
                    'body_code' : res['body_code'] ,
                    'body_name' : res['body_name'] ,
                    'type' : 'SR' ,
                    'score' : best['score'] ,
                    'spring_margin' : best['spring_margin'] ,
                    'model_line_items' : [{
                        'body_id' : res['body_id'] ,
                        'body_code' : res['body_code'] ,
                        'actuator_variety' : 'SR' ,
                        'spring_qty_id' : best.get('spring_qty_id') ,
                        'spring_qty_code' : best['spring_qty_code'] ,
                        'spring_qty_name' : best['spring_qty_name'] ,
                        'score' : best['score'] ,
                        'spring_bto' : best['spring_bto'] ,
                        'spring_eto' : best['spring_eto'] ,
                        'spring_min' : best['spring_min'] ,
                        'pressure_bto' : best['pressure_bto'] ,
                        'pressure_eto' : best['pressure_eto'] ,
                        'pressure_min' : best['pressure_min'] ,
                        'spring_margin' : best['spring_margin'] ,
                        'pressure_margin' : best['pressure_margin']
                    }]
                }
            else :
                item = {
                    'body_id' : res['body_id'] ,
                    'body_code' : res['body_code'] ,
                    'body_name' : res['body_name'] ,
                    'type' : 'DA' ,
                    'score' : best['score'] ,
                    'spring_margin' : best['margin'] ,
                    'model_line_items' : [{
                        'body_id' : res['body_id'] ,
                        'body_code' : res['body_code'] ,
                        'actuator_variety' : 'DA' ,
                        'spring_qty_id' : None ,
                        'spring_qty_code' : 'DA' ,
                        'spring_qty_name' : 'Без пружин' ,
                        'score' : best['score'] ,
                        'spring_bto' : best['bto'] ,
                        'spring_eto' : best['bto'] ,
                        'spring_min' : best['bto'] ,
                        'pressure_bto' : best['bto'] ,
                        'pressure_eto' : best['bto'] ,
                        'pressure_min' : best['bto'] ,
                        'spring_margin' : best['margin'] ,
                        'pressure_margin' : best['margin']
                    }]
                }

            output.append(item)

        return output
