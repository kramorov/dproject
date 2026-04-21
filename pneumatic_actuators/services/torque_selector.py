# pneumatic_actuators/services/torque_selector.py
from typing import List , Dict , Optional
from decimal import Decimal

from pneumatic_actuators.models.py_options_constants import SPRINGS_DA_DEFAULT_CODE


class TorqueSelectorService :
    """Сервис для подбора приводов по моменту"""

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
        except :
            return None

    @staticmethod
    def get_spring_data_sr(table_model , body_id: int) -> List[Dict] :
        """Получить данные для пружин (spring) для SR приводов"""
        spring_records = table_model.objects.filter(
            body_id=body_id ,
            pressure__code='spring' ,
            spring_qty__is_active=True
        ).exclude(spring_qty__code=SPRINGS_DA_DEFAULT_CODE).select_related('spring_qty').order_by(
            'spring_qty__sorting_order')

        result = []
        for record in spring_records :
            if record.bto and record.eto :
                result.append({
                    'id' : record.id ,
                    'spring_qty_id' : record.spring_qty.id ,
                    'spring_qty_code' : record.spring_qty.code ,
                    'spring_qty_name' : record.spring_qty.name ,
                    'bto' : float(record.bto) ,
                    'eto' : float(record.eto) ,
                    'min_value' : min(float(record.bto) , float(record.eto))
                })
        return result

    @staticmethod
    def get_work_pressure_data_sr(table_model , body_id: int , work_pressure_id: int) -> List[Dict] :
        """Получить данные для рабочего давления для SR приводов"""
        pressure_records = table_model.objects.filter(
            body_id=body_id ,
            pressure_id=work_pressure_id ,
            spring_qty__is_active=True
        ).exclude(spring_qty__code=SPRINGS_DA_DEFAULT_CODE).select_related('spring_qty').order_by(
            'spring_qty__sorting_order')

        result = []
        for record in pressure_records :
            if record.bto and record.eto :
                result.append({
                    'id' : record.id ,
                    'spring_qty_id' : record.spring_qty.id ,
                    'spring_qty_code' : record.spring_qty.code ,
                    'spring_qty_name' : record.spring_qty.name ,
                    'bto' : float(record.bto) ,
                    'eto' : float(record.eto) ,
                    'min_value' : min(float(record.bto) , float(record.eto))
                })
        return result

    @staticmethod
    def get_da_data(table_model , body_id: int , work_pressure_id: int) -> List[Dict] :
        """Получить данные для DA приводов (без пружин)"""
        da_records = table_model.objects.filter(
            body_id=body_id ,
            pressure_id=work_pressure_id ,
            spring_qty__code=SPRINGS_DA_DEFAULT_CODE ,
            spring_qty__is_active=True
        ).select_related('spring_qty')

        result = []
        for record in da_records :
            if record.bto :
                result.append({
                    'id' : record.id ,
                    'spring_qty_id' : record.spring_qty.id ,
                    'spring_qty_code' : record.spring_qty.code ,
                    'spring_qty_name' : record.spring_qty.name ,
                    'bto' : float(record.bto) ,
                    'rto' : float(record.rto) if record.rto else float(record.bto) ,
                    'eto' : float(record.eto) if record.eto else float(record.bto) ,
                    'value' : float(record.bto)
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
            bodies = body_model.objects.filter(id__in=body_ids , is_active=True)
        else :
            bodies = body_model.objects.filter(is_active=True)

        all_results = []

        for body in bodies :
            # Группируем записи по количеству пружин
            all_records = table_model.objects.filter(
                body_id=body.id ,
                spring_qty__is_active=True
            ).exclude(spring_qty__code=SPRINGS_DA_DEFAULT_CODE).select_related('spring_qty' , 'pressure')

            spring_qty_groups = {}
            for record in all_records :
                qty_code = record.spring_qty.code
                if qty_code not in spring_qty_groups :
                    spring_qty_groups[qty_code] = {
                        'spring_qty_id' : record.spring_qty.id ,
                        'spring_qty_code' : qty_code ,
                        'spring_qty_name' : record.spring_qty.name ,
                        'spring_record' : None ,
                        'pressure_record' : None
                    }

                if record.pressure and record.pressure.code == 'spring' :
                    spring_qty_groups[qty_code]['spring_record'] = {
                        'bto' : float(record.bto) if record.bto else None ,
                        'eto' : float(record.eto) if record.eto else None
                    }
                elif record.pressure_id == work_pressure_id :
                    spring_qty_groups[qty_code]['pressure_record'] = {
                        'bto' : float(record.bto) if record.bto else None ,
                        'eto' : float(record.eto) if record.eto else None
                    }

            suitable_combinations = []
            for qty_code , group in spring_qty_groups.items() :
                spring = group['spring_record']
                pressure = group['pressure_record']

                if spring is None or pressure is None :
                    continue
                if not spring.get('bto') or not spring.get('eto') or not pressure.get('bto') or not pressure.get(
                        'eto') :
                    continue

                score_data = self.calculate_score_sr(spring , pressure , torque_with_sf)
                if score_data['is_valid'] :
                    suitable_combinations.append({
                        'spring_qty_id' : group['spring_qty_id'] ,
                        'spring_qty_code' : qty_code ,
                        'spring_qty_name' : group['spring_qty_name'] ,
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
                all_results.append({
                    'body_id' : body.id ,
                    'body_code' : body.code ,
                    'body_name' : body.name ,
                    'type' : 'SR' ,
                    'combinations' : suitable_combinations ,
                    'best_combination' : suitable_combinations[0] ,
                    'total_combinations' : len(suitable_combinations)
                })

        all_results.sort(key=lambda x : x['best_combination']['score'])
        return all_results[:max_bodies]

    def find_suitable_da_actuators(self , table_model , body_model , pressure_model ,
                                   torque_with_sf: float , work_pressure_id: int ,
                                   body_ids: Optional[List[int]] = None ,
                                   max_bodies: int = 3) -> List[Dict] :
        """Найти подходящие DA приводы"""

        work_pressure = self.get_pressure_by_id(pressure_model , work_pressure_id)
        if not work_pressure :
            return []

        if body_ids :
            bodies = body_model.objects.filter(id__in=body_ids , is_active=True)
        else :
            bodies = body_model.objects.filter(is_active=True)

        all_results = []

        for body in bodies :
            da_records = self.get_da_data(table_model , body.id , work_pressure_id)

            suitable = []
            for da in da_records :
                score_data = self.calculate_score_da(da , torque_with_sf)
                if score_data['is_valid'] :
                    suitable.append({
                        'bto' : da['bto'] ,
                        'margin' : score_data['margin'] ,
                        'score' : score_data['total_score']
                    })

            if suitable :
                suitable.sort(key=lambda x : x['score'])
                all_results.append({
                    'body_id' : body.id ,
                    'body_code' : body.code ,
                    'body_name' : body.name ,
                    'type' : 'DA' ,
                    'best_combination' : suitable[0] ,
                    'total_combinations' : len(suitable)
                })

        all_results.sort(key=lambda x : x['best_combination']['score'])
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