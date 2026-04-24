# pneumatic_actuators/services/pneumatic_calculator.py
import math


class PneumaticCalculator:
    """
    Класс для физического расчета времени работы и расхода воздуха пневмопривода.

    МЕТОДОЛОГИЯ РАСЧЕТА:
    1. Зависимость времени от силы: Время хода (t) обратно пропорционально квадратному
       корню из ускоряющей силы (F). t_new = t_base * sqrt(F_base / F_new).
    2. Разделение сил: Вычисляется сопротивление пружин как разница времени между DA и SR.
    3. Учет арматуры: Момент срыва (Нм) конвертируется в эквивалентное падение давления.
    4. Расход воздуха: Считается по закону Бойля-Мариотта. Объем сжатого воздуха
       пересчитывается в "нормальные литры" (при атм. давлении) по формуле:
       V_norm = V_cyl * (P_bar + 1).
    5. Kv (коэффициент пропускной способности): Расход воды (м³/ч) при перепаде 1 бар.
       Для воздуха используется пересчет через плотность и критическое отношение давлений.
    """

    @classmethod
    def calculate_air_consumption(cls, pressure_bar, volume_liters, is_da):
        """
        Рассчитать расход воздуха для заданных параметров

        Args:
            pressure_bar: давление в барах (избыточное)
            volume_liters: объем цилиндра в литрах
            is_da: True для DA (двустороннего действия), False для SR (пружинный возврат)

        Returns:
            float: расход воздуха в нормальных литрах за цикл
        """
        # Абсолютное давление (бар)
        p_abs = pressure_bar + 1.013

        if is_da:
            # DA: воздух расходуется на оба хода (две полости)
            return round(2 * volume_liters * p_abs, 2)
        else:
            # SR: пружинный возврат - воздух только на открытие
            return round(volume_liters * p_abs, 2)

    @classmethod
    def calculate_air_consumption_per_minute(cls, air_per_cycle, cycles_per_hour):
        """
        Рассчитать расход воздуха в минуту

        Args:
            air_per_cycle: расход воздуха за цикл (нормальные литры)
            cycles_per_hour: количество циклов в час

        Returns:
            float: расход воздуха в нормальных литрах в минуту
        """
        return round(air_per_cycle * (cycles_per_hour / 60), 2)

    @classmethod
    def calculate_kv_from_air_flow(cls, flow_nl_min, pressure_bar, delta_p_bar=0.1):
        """
        Рассчитать Kv (коэффициент пропускной способности) по расходу воздуха

        Стандартная формула для газов:
        Kv = Qn / (514 * sqrt(delta_p * P2 * ρn/ρ))

        Упрощенная формула для воздуха при нормальных условиях:
        Kv = (Qn / 514) * sqrt(ρn / (delta_p * P2))

        где:
        - Qn - расход, нм³/ч
        - delta_p - перепад давления, бар
        - P2 - абсолютное давление на выходе, бар
        - ρn - плотность воздуха при н.у. (1.293 кг/м³)
        - ρ - плотность газа (для воздуха 1.293)

        Args:
            flow_nl_min: расход воздуха, нормальные литры в минуту
            pressure_bar: абсолютное давление на входе, бар
            delta_p_bar: перепад давления на клапане, бар (обычно 0.1-0.2)

        Returns:
            float: коэффициент Kv (м³/ч)
        """
        # Переводим расход из л/мин в нм³/ч
        flow_nm3_h = flow_nl_min * 0.06  # (л/мин → м³/ч)

        # Абсолютное давление на выходе (бар)
        p2_abs = pressure_bar + 1.013 - delta_p_bar

        # Плотность воздуха при н.у. (кг/м³)
        rho_n = 1.293

        # Проверяем критическое отношение давлений
        pressure_ratio = p2_abs / (pressure_bar + 1.013)

        if pressure_ratio < 0.528:
            # Критический режим (сверхзвуковой поток)
            # Формула для критического режима
            kv = flow_nm3_h / (257 * (pressure_bar + 1.013))
        else:
            # Докритический режим
            # Kv = Qn / (514 * sqrt(delta_p * P2))
            try:
                kv = flow_nm3_h / (514 * math.sqrt(delta_p_bar * p2_abs))
            except (ValueError, ZeroDivisionError):
                kv = 0.0

        # Корректировка для малых расходов (эмпирическая)
        if kv < 0.01 and flow_nm3_h > 0:
            # Минимальный Kv для малых расходов
            kv = max(kv, flow_nm3_h / 1000)

        return round(kv, 3)

    @classmethod
    def calculate_valve_recommendation(cls, air_per_cycle, pressure_bar, cycles_per_hour=60, safety_factor=1.8):
        """
        Рассчитать рекомендации по подбору распределителя
        """
        # Расход в минуту
        air_per_minute = air_per_cycle * (cycles_per_hour / 60)

        # Рекомендуемый расход с запасом
        recommended_flow = air_per_minute * safety_factor

        # Расчет Kv (используем перепад 0.1 бар как стандартный)
        kv = cls.calculate_kv_from_air_flow(recommended_flow, pressure_bar, delta_p_bar=0.1)

        # Эмпирическая корректировка для реальных распределителей
        # Опытные данные: для расхода 25 л/мин при 6 бар нужен Kv ~0.3-0.5
        if kv < 0.05 and recommended_flow > 10:
            kv = recommended_flow / 100  # Простая эмпирическая формула

        # Рекомендации по типу распределителя по Kv
        if kv <= 0.2:
            valve_type = "Миниатюрный"
            valve_size = "G1/8"
            kv_range = "0.1-0.2"
        elif kv <= 0.5:
            valve_type = "Малый"
            valve_size = "G1/8 или G1/4"
            kv_range = "0.2-0.5"
        elif kv <= 1.2:
            valve_type = "Средний"
            valve_size = "G3/8"
            kv_range = "0.5-1.2"
        elif kv <= 2.5:
            valve_type = "Крупный"
            valve_size = "G1/2"
            kv_range = "1.2-2.5"
        elif kv <= 5.0:
            valve_type = "Большой"
            valve_size = "G3/4"
            kv_range = "2.5-5.0"
        else:
            valve_type = "Промышленный"
            valve_size = "G1 и более"
            kv_range = ">5.0"

        return {
            'air_consumption_cycle_nl': round(air_per_cycle, 2),
            'air_consumption_minute_nl': round(air_per_minute, 2),
            'recommended_flow_nl_min': round(recommended_flow, 2),
            'calculated_kv': round(kv, 3),
            'recommended_valve_type': valve_type,
            'recommended_valve_size': valve_size,
            'recommended_kv_range': kv_range,
            'safety_factor': safety_factor,
            'cycles_per_hour': cycles_per_hour,
            'pressure_bar': pressure_bar,
        }

    @classmethod
    def calculate_actuator_data(cls,
                                mechanism_type,
                                is_target_sr,
                                target_pressure_bar,
                                target_springs_qty,
                                base_p_sr,
                                base_t_open_sr,
                                base_t_close_sr,
                                base_springs_qty,
                                base_p_da,
                                base_t_open_da,
                                piston_diameter,
                                volume_liters,
                                valve_torque_nm=0):

        # Конвертируем Decimal в float если нужно
        piston_diameter = float(piston_diameter) if piston_diameter else 50.0
        volume_liters = float(volume_liters) if volume_liters else 0.5
        target_pressure_bar = float(target_pressure_bar)
        target_springs_qty = float(target_springs_qty)
        base_p_sr = float(base_p_sr)
        base_t_open_sr = float(base_t_open_sr)
        base_t_close_sr = float(base_t_close_sr)
        base_springs_qty = float(base_springs_qty)
        base_p_da = float(base_p_da)
        base_t_open_da = float(base_t_open_da)
        valve_torque_nm = float(valve_torque_nm)

        # --- 1. ГЕОМЕТРИЯ И ЭКВИВАЛЕНТЫ СИЛ ---
        area_m2 = (math.pi * (piston_diameter / 1000) ** 2) / 4
        # Оценка плеча силы для перевода Нм в Бар
        if area_m2 > 0:
            stroke_m = (volume_liters / 1000) / area_m2
            r_gear_m = stroke_m / (math.pi / 2)
        else:
            r_gear_m = 0.01

        if not base_t_open_da or base_t_open_da == 0:
            base_t_open_da = base_t_open_sr / 1.6 if base_t_open_sr > 0 else 1.0
            base_p_da = base_p_sr

        # Сопротивление пружин (в барах)
        if base_springs_qty > 0 and base_t_open_sr > 0:
            p_springs_total_base = base_p_sr * (1 - (base_t_open_da ** 2 / base_t_open_sr ** 2))
            p_per_spring = p_springs_total_base / base_springs_qty
            current_p_springs_loss = target_springs_qty * p_per_spring
        else:
            p_springs_total_base = 0
            p_per_spring = 0
            current_p_springs_loss = 0

        # Сопротивление арматуры (в барах)
        if valve_torque_nm > 0 and r_gear_m > 0 and area_m2 > 0:
            p_valve_loss = (valve_torque_nm / r_gear_m) / area_m2 / 100000
        else:
            p_valve_loss = 0

        # --- 2. РАСЧЕТ ВРЕМЕНИ (ДИНАМИКА) ---
        mech_factor = 0.92 if mechanism_type == 'scotch_yoke' else 1.0

        # Открытие
        if not is_target_sr:  # DA
            net_p_target = target_pressure_bar - p_valve_loss
            if net_p_target <= 0.1:
                time_open = 999.0
            else:
                if base_p_da > 0:
                    time_open = base_t_open_da * math.sqrt(base_p_da / net_p_target)
                else:
                    time_open = 999.0
        else:  # SR
            net_p_base = max(base_p_sr - p_springs_total_base, 0.1)
            net_p_target = target_pressure_bar - current_p_springs_loss - p_valve_loss
            if net_p_target <= 0.1:
                time_open = 999.0
            else:
                if net_p_base > 0:
                    time_open = base_t_open_sr * math.sqrt(net_p_base / net_p_target) * mech_factor
                else:
                    time_open = 999.0

        # Закрытие
        if not is_target_sr:  # DA
            time_close = time_open * 1.05
        else:  # SR
            if p_springs_total_base > 0:
                spring_force_ratio = (current_p_springs_loss - p_valve_loss) / p_springs_total_base
                if spring_force_ratio <= 0.05:
                    time_close = 999.0
                else:
                    time_close = base_t_close_sr * math.sqrt(1 / spring_force_ratio)
            else:
                time_close = base_t_close_sr

        # Ограничение по пропускной способности каналов
        flow_limit = volume_liters * 0.12
        final_open = max(time_open, flow_limit)
        final_close = max(time_close, flow_limit)

        # --- 3. РАСЧЕТ РАСХОДА ВОЗДУХА (НОРМАЛЬНЫЕ ЛИТРЫ) ---
        air_per_cycle = cls.calculate_air_consumption(
            pressure_bar=target_pressure_bar,
            volume_liters=volume_liters,
            is_da=not is_target_sr
        )

        return {
            'time_open_sec': round(final_open, 2),
            'time_close_sec': round(final_close, 2),
            'air_consumption_norm_liters': air_per_cycle,
            'p_loss_springs_bar': round(current_p_springs_loss, 2),
            'p_loss_valve_bar': round(p_valve_loss, 2),
            'can_operate': net_p_target > 0.5 if 'net_p_target' in locals() else False
        }