"""Переводит SensorComponent.extra_params из плоского формата в локализованный.

Было (плоский, ключи-машины + RU-подписи/значения):
    {"voltage_nominal": {"name": "Номинальное напряжение", "value": "8.2V DC"}, ...}

Стало (стандарт локализации — локаль как внешний ключ):
    {"ru": {"voltage_nominal": {"name": "Номинальное напряжение", "value": "8.2V DC"}, ...},
     "en": {"voltage_nominal": {"name": "Rated voltage", "value": "8.2 V DC"}, ...},
     "cn": {"voltage_nominal": {"name": "额定电压", "value": "8.2 V DC"}, ...}}

Идемпотентна: уже локализованные записи (с ключом «ru») не трогает.
"""
from django.core.management.base import BaseCommand
from django.apps import apps

from core.utils.localization import localize_service_word

# Машинный ключ параметра → (en, cn) подпись.
NAME_TRANSLATIONS = {
    'voltage_nominal': ('Rated voltage', '额定电压'),
    'current_on': ('Operating current (ON)', '动作电流（接通）'),
    'current_off': ('Operating current (OFF)', '动作电流（断开）'),
    'frequency': ('Switching frequency', '开关频率'),
    'frequency_hz': ('Switching frequency', '开关频率'),
    'hysteresis': ('Hysteresis', '迟滞'),
    'slot_width_mm': ('Slot width', '槽宽'),
    'immersion_depth_mm': ('Immersion depth', '浸入深度'),
    'material': ('Body material', '壳体材料'),
    'sil_level': ('Safety class', '安全等级'),
    'sensing_range': ('Sensing range', '感应距离'),
    'voltage_range': ('Rated voltage range', '额定电压范围'),
    'current_nominal': ('Rated operating current', '额定工作电流'),
    'ex_protection_notes': ('Explosion protection notes', '防爆说明'),
    'mds_range': ('Operating MDS', '动作安匝 (MDS)'),
    'contact_resistance': ('Contact resistance', '接触电阻'),
    'insulation_resistance': ('Insulation resistance', '绝缘电阻'),
    'response_time': ('Response time', '响应时间'),
    'response_time_ms': ('Response time', '响应时间'),
    'short_circuit_protection': ('Short-circuit protection', '短路保护'),
    'reverse_polarity_protection': ('Reverse polarity protection', '反极性保护'),
    'protection_class': ('Protection class (electric shock)', '防触电保护等级'),
    'contact_structure': ('Contact group', '触点组'),
    'output_logic': ('Output logic', '输出逻辑'),
    'inrush_current': ('Maximum inrush current', '最大浪涌电流'),
    'mechanical_life': ('Mechanical life', '机械寿命'),
    'electrical_life': ('Electrical life', '电气寿命'),
    'connection_type': ('Connection type', '连接方式'),
    'min_load': ('Minimum load', '最小负载'),
    'type': ('Sensor type', '传感器类型'),
    'switching_frequency': ('Switching frequency', '开关频率'),
    'voltage_type': ('Voltage type', '电压类型'),
    'no_load_current': ('No-load current (Io)', '空载电流 (Io)'),
    'voltage_drop': ('Voltage drop (Ud)', '压降 (Ud)'),
    'off_state_current': ('Leakage current (Ir)', '漏电流 (Ir)'),
    'breakdown_voltage': ('Breakdown voltage', '击穿电压'),
    'resource_cycles': ('MTBF', '平均无故障时间'),
    'analog_0_1k_res': ('Sensor nominal resistance', '传感器额定电阻'),
    'mtf_d': ('Reliability MTTFd', '可靠性 MTTFd'),
    'operating_mode': ('Operating mode', '工作模式'),
    'analog_4_20_res': ('Load resistance', '负载电阻'),
    'potentiometer_res': ('Potentiometer resistance', '电位计电阻'),
    'signal_type': ('Signal characteristic', '信号特性'),
    'capacity_pf': ('Capacitance', '电容'),
    'special_features': ('Special features', '特性'),
}

# RU-значение → (en, cn). Для значений, не попавших в словарь, применяется
# localize_service_word (единицы/служебные слова).
VALUE_TRANSLATIONS = {
    '0 ... 0.5 мА (типично 0.1 мкА при 25°C)': ('0 … 0.5 mA (typ. 0.1 µA at 25 °C)', '0 … 0.5 mA（典型值 25 °C 时 0.1 µA）'),
    '0-1000 Ом': ('0–1000 Ω', '0–1000 Ω'),
    '0-500 Ом': ('0–500 Ω', '0–500 Ω'),
    '0...1000 Гц': ('0…1000 Hz', '0…1000 Hz'),
    '0...3000 Гц': ('0…3000 Hz', '0…3000 Hz'),
    '0.01…0.1 мм': ('0.01…0.1 mm', '0.01…0.1 mm'),
    '0.025 - 0.045 мм': ('0.025–0.045 mm', '0.025–0.045 mm'),
    '0.025...10 млн. циклов (зависит от нагрузки)': ('0.025…10 million cycles (depending on load)', '0.025…10 百万次循环（取决于负载）'),
    '0.75 мс (размыкание 0.3 мс)': ('0.75 ms (opening 0.3 ms)', '0.75 ms（断开 0.3 ms）'),
    '0.8 пФ': ('0.8 pF', '0.8 pF'),
    '10 мм': ('10 mm', '10 mm'),
    '100 Гц': ('100 Hz', '100 Hz'),
    '100 мА': ('100 mA', '100 mA'),
    '1287 лет': ('1287 years', '1287 年'),
    '160 мА при 5 В пост.': ('160 mA at 5 V DC', '5 V DC 时 160 mA'),
    '2 мм': ('2 mm', '2 mm'),
    '20…60 А': ('20…60 A', '20…60 A'),
    '24 В пост.': ('24 V DC', '24 V DC'),
    '24 В пост. (раб. диапазон 8.5-34 В)': ('24 V DC (operating range 8.5–34 V)', '24 V DC（工作范围 8.5–34 V）'),
    '3.5 мм': ('3.5 mm', '3.5 mm'),
    '36 А': ('36 A', '36 A'),
    '5...30 В пост. тока': ('5…30 V DC', '5…30 V DC'),
    '5...7 мм (ном. 6 мм)': ('5…7 mm (nom. 6 mm)', '5…7 mm（额定 6 mm）'),
    '8.2V DC': ('8.2 V DC', '8.2 V DC'),
    '<50 мОм': ('<50 mΩ', '<50 mΩ'),
    '>1 000 000 циклов': ('>1,000,000 cycles', '>1,000,000 次循环'),
    '>1.8 mA': ('>1.8 mA', '>1.8 mA'),
    '>50 000 циклов': ('>50,000 cycles', '>50,000 次循环'),
    'DPDT (две независимые линии управления)': ('DPDT (two independent control lines)', 'DPDT（两条独立控制线路）'),
    'NAMUR с защитной функцией (SN)': ('NAMUR with protective function (SN)', '带保护功能的 NAMUR (SN)'),
    'SIL 3': ('SIL 3', 'SIL 3'),
    'Быстросъемная клемма': ('Quick-connect terminal', '快插端子'),
    'Высокотемпературное исполнение (HT2), защитная функция': ('High-temperature version (HT2), protective function', '高温型 (HT2)，保护功能'),
    'Класс 1': ('Class 1', '1 级'),
    'Линейная, 4-20 мА': ('Linear, 4–20 mA', '线性，4–20 mA'),
    'Линейная, пропорциональная степени открытия арматуры (0–100%)': ('Linear, proportional to valve opening (0–100%)', '线性，与阀门开度成正比（0–100%）'),
    'Магнитоуправляемый герметизированный (геркон)': ('Magnetically operated sealed (reed)', '磁控密封（干簧管）'),
    'Нет (внешнее измерительное питание)': ('No (external measurement supply)', '无（外部测量电源）'),
    'Нет (требуется внешнее питание токовой петли)': ('No (external loop power required)', '无（需要外部回路电源）'),
    'Определяется внешним источником питания': ('Determined by external power supply', '由外部电源决定'),
    'ПВ 100%': ('Duty cycle 100%', '负载持续率 100%'),
    'Параметры Ui/Ii соответствуют защите уровня ia (Зона 0)': ('Ui/Ii parameters comply with ia protection level (Zone 0)', 'Ui/Ii 参数符合 ia 防护等级（0区）'),
    'Полибутилентерефталат (ПБТ)': ('Polybutylene terephthalate (PBT)', '聚对苯二甲酸丁二醇酯 (PBT)'),
    'Постоянный ток (DC)': ('Direct current (DC)', '直流 (DC)'),
    'Проверена': ('Verified', '已验证'),
    'Тактовая (pulsing)': ('Pulsing', '脉冲'),
    'Термопластичный пластик': ('Thermoplastic', '热塑性塑料'),
    'до 100 Гц': ('up to 100 Hz', '至 100 Hz'),
    'макс. 15 мОм': ('max. 15 mΩ', '最大 15 mΩ'),
    'не более 0.1 Ом': ('not more than 0.1 Ω', '不超过 0.1 Ω'),
    'не более 0.3 Ом (макс. 100 мОм)': ('not more than 0.3 Ω (max. 100 mΩ)', '不超过 0.3 Ω（最大 100 mΩ）'),
    'не более 0.75 мс': ('not more than 0.75 ms', '不超过 0.75 ms'),
    'не более 10%': ('not more than 10%', '不超过 10%'),
    'не менее 10^9 Ом': ('not less than 10^9 Ω', '不低于 10^9 Ω'),
    'не менее 450 В пост.': ('not less than 450 V DC', '不低于 450 V DC'),
    '≤ 15 мА': ('≤ 15 mA', '≤ 15 mA'),
    '≤ 3 В': ('≤ 3 V', '≤ 3 V'),
    '≤1.5 mA': ('≤1.5 mA', '≤1.5 mA'),
}


class Command(BaseCommand):
    help = 'Migrate SensorComponent.extra_params to localized {ru/en/cn} format.'

    def handle(self, *args, **options):
        Sensor = apps.get_model('pa_controls', 'SensorComponent')
        updated = 0
        for obj in Sensor.objects.all():
            raw = obj.extra_params or {}
            if not isinstance(raw, dict) or isinstance(raw.get('ru'), dict):
                continue  # уже локализовано или пусто

            ru = dict(raw)
            en = {}
            cn = {}
            for key, item in raw.items():
                if not isinstance(item, dict):
                    en[key] = item
                    cn[key] = item
                    continue
                ru_name = item.get('name', key)
                ru_value = item.get('value', '')
                en_name, cn_name = NAME_TRANSLATIONS.get(key, (ru_name, ru_name))
                en_value, cn_value = VALUE_TRANSLATIONS.get(
                    ru_value,
                    (localize_service_word(str(ru_value), 'en'), localize_service_word(str(ru_value), 'cn')),
                )
                en[key] = {'name': en_name, 'value': en_value}
                cn[key] = {'name': cn_name, 'value': cn_value}

            obj.extra_params = {'ru': ru, 'en': en, 'cn': cn}
            obj.save(update_fields=['extra_params'])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f'Migrated sensors: {updated}'))
