"""Заполняет en/cn для вопросов узлов графа подбора и описаний датчиков БКВ.

1) QuestionGraph.graph_json — узлы: ``description_i18n`` / ``title_i18n`` /
   ``question_i18n`` / ``name_i18n`` (общий паттерн ``<field>_i18n``) и
   ``params[].title_i18n``.
2) LimitSwitchSensorVariety.description_i18n — hint-описания опций выбора.

Идемпотентна: перезаписывает en/cn, «ru» остаётся исходным значением поля.
"""
import copy

from django.core.management.base import BaseCommand
from django.apps import apps

# RU-строка → (en, cn). Используется и для вопросов узлов, и для подписей параметров.
TEXT_TRANSLATIONS = {
    'Ветвление по типу датчика': ('Branching by sensor type', '按传感器类型分支'),
    'Выберите тип датчика БКВ': ('Select the LSB sensor type', '选择限位开关盒传感器类型'),
    'Количество точек, тип сигнала, форма контактов, материал корпуса, IP, взрывозащита': (
        'Number of points, signal type, contact form, body material, IP, explosion protection',
        '触点数量、信号类型、触点形式、壳体材料、IP、防爆',
    ),
    'Температура эксплуатации': ('Operating temperature', '工作温度'),
    'IP': ('IP', 'IP'),
    'Взрывозащита': ('Explosion protection', '防爆'),
    'Количество точек': ('Number of points', '触点数量'),
    'Материал корпуса': ('Body material', '壳体材料'),
    'Температура мин': ('Temperature min', '最低温度'),
    'Тип датчика': ('Sensor type', '传感器类型'),
    'Тип сигнала': ('Signal type', '信号类型'),
    'Форма контактов': ('Contact form', '触点形式'),
}

VARIETY_DESCRIPTIONS = {
    'MECH': (
        'Mechanical limit switch. Actuated by physical pressure on a lever or plunger. Contacts open/close mechanically. Specifications: switching current up to 5 A, voltage up to 250 V AC. Advantages: reliability, low cost, high load capacity. Disadvantages: contact wear, limited life (up to 10 million operations).',
        '机械式限位开关。通过物理按压杠杆或顶杆触发。触点机械式通断。规格：开关电流至 5 A，电压至 250 V AC。优点：可靠、成本低、负载能力强。缺点：触点磨损、寿命有限（至 1000 万次动作）。',
    ),
    'IND': (
        'Inductive proximity sensor. Detects approaching metal objects without physical contact. Operating principle: high-frequency electromagnetic field, oscillation amplitude changes when metal appears. Specifications: sensing range 2–15 mm, switching frequency up to 1000 Hz, IP67. Advantages: non-contact, durable, high switching frequency.',
        '电感式接近传感器。无需物理接触即可检测金属物体的接近。工作原理：高频电磁场，金属出现时振荡幅度改变。规格：检测距离 2–15 mm，开关频率至 1000 Hz，防护等级 IP67。优点：非接触、耐用、开关频率高。',
    ),
    'REED': (
        'Reed sensor (magnetically operated contact). Actuated when a magnet approaches. Two ferromagnetic contacts in a sealed bulb with inert gas. Specifications: switching current up to 0.5 A, voltage up to 200 V DC, life up to 10^9 operations. Advantages: simple, low cost, no power required, full galvanic isolation.',
        '干簧管传感器（磁控触点）。磁铁靠近时动作。惰性气体密封玻璃管内两个铁磁触点。规格：开关电流至 0.5 A，电压至 200 V DC，寿命至 10^9 次动作。优点：简单、成本低、无需供电、完全电气隔离。',
    ),
    'MAG': (
        'Magnetic sensor based on the Hall effect. Responds to a magnetic field. Has an electronic amplification circuit. Specifications: PNP/NPN output, switching frequency up to 10 kHz, IP67. Advantages: fast response, vibration resistance.',
        '基于霍尔效应的磁传感器。响应磁场。带电子放大电路。规格：PNP/NPN 输出，开关频率至 10 kHz，IP67。优点：响应快、抗振动。',
    ),
    'PNEUM': (
        'Pneumatic limit switch. Actuated by air pressure. Used in hazardous areas (Ex) where electricity is prohibited. Specifications: actuation pressure 0.5–8 bar, port G1/8 or G1/4. Advantages: complete explosion safety, operation in aggressive media.',
        '气动限位开关。由气压触发。用于禁止用电的防爆区域 (Ex)。规格：动作压力 0.5–8 bar，接口 G1/8 或 G1/4。优点：完全防爆、可在腐蚀性环境中工作。',
    ),
    'CAP': (
        'Capacitive proximity sensor. Responds to the approach of any object (metal, plastic, liquid, bulk materials). Operating principle: change in capacitor capacitance. Specifications: sensing range up to 20 mm. Advantages: versatility, operation through dielectric walls.',
        '电容式接近传感器。响应任何物体（金属、塑料、液体、散料）的接近。工作原理：电容变化。规格：检测距离至 20 mm。优点：通用性强、可穿过介质壁工作。',
    ),
    'OPT': (
        'Optical sensor. Uses a light beam (often IR) to detect objects. Types: through-beam, diffuse reflection, retro-reflective. Advantages: long range (up to 30 m), works with any materials. Disadvantages: sensitivity to optical contamination.',
        '光电传感器。利用光束（通常为红外）检测物体。类型：对射、漫反射、回归反射。优点：检测距离远（至 30 m）、可用于任何材料。缺点：对光学污染敏感。',
    ),
    'TRANS': (
        'Provides a 4–20 mA feedback signal, usually combined with limit position sensors.',
        '输出 4–20 mA 反馈信号，通常与极限位置传感器配套使用。',
    ),
    'POTE': (
        'Analog, resistive (potentiometric divider) 0–1 kΩ.',
        '模拟量、电阻式（电位分压器）0–1 kΩ。',
    ),
}


class Command(BaseCommand):
    help = 'Backfill en/cn for wizard node questions and sensor variety descriptions.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перезаписать существующие переводы (затирает ручные правки).')

    def handle(self, *args, **options):
        force = options['force']
        total = 0

        # 1. Узлы графа → *_i18n
        Graph = apps.get_model('core', 'QuestionGraph')
        updated = 0
        for graph in Graph.objects.all():
            gj = copy.deepcopy(graph.graph_json or {})
            nodes = gj.get('nodes') or {}
            changed = False
            for node in nodes.values():
                if not isinstance(node, dict):
                    continue
                for field in ('question', 'description', 'title', 'name'):
                    val = node.get(field)
                    if val and (force or not node.get(field + '_i18n')):
                        en, cn = TEXT_TRANSLATIONS.get(val, (None, None))
                        if en:
                            node[field + '_i18n'] = {'ru': val, 'en': en, 'cn': cn}
                            changed = True
                for p in node.get('params') or []:
                    if not isinstance(p, dict):
                        continue
                    val = p.get('title')
                    if val and (force or not p.get('title_i18n')):
                        en, cn = TEXT_TRANSLATIONS.get(val, (None, None))
                        if en:
                            p['title_i18n'] = {'ru': val, 'en': en, 'cn': cn}
                            changed = True
            if changed:
                graph.graph_json = gj
                graph.save(update_fields=['graph_json'])
                updated += 1
        if updated:
            total += updated
            self.stdout.write(f'QuestionGraph: {updated}')

        # 2. Описания разновидностей датчиков → description_i18n
        Variety = apps.get_model('pa_controls', 'LimitSwitchSensorVariety')
        updated = 0
        for v in Variety.objects.all():
            if v.code not in VARIETY_DESCRIPTIONS or not v.description:
                continue
            en, cn = VARIETY_DESCRIPTIONS[v.code]
            i18n = dict(v.description_i18n or {})
            changed = False
            for locale, value in (('en', en), ('cn', cn)):
                if force or locale not in i18n:
                    i18n[locale] = value
                    changed = True
            if changed:
                v.description_i18n = i18n
                v.save(update_fields=['description_i18n'])
                updated += 1
        if updated:
            total += updated
            self.stdout.write(f'LimitSwitchSensorVariety: {updated}')

        self.stdout.write(self.style.SUCCESS(f'Done. Translated rows: {total}'))
