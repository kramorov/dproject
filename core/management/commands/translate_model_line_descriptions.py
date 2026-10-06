"""Заполняет en/cn переводы описаний серий (``description_i18n``).

Переводит описательные русские описания. Коды/уникальные строки (EJSM-C,
«Серия PS — Premiun segment» и т.п.) не трогает. Ключ — нормализованный
текст описания (схлопнутые пробелы), поэтому совпадает независимо от \r\n.

Идемпотентна.
"""
import re

from django.core.management.base import BaseCommand
from django.apps import apps

DESCRIPTIONS = {
    # cable_glands
    'Серия КНК - Кабельные вводы для всех типов небронированного кабеля круглого сечения.':
        ('KNK series — cable glands for all types of unarmoured round-section cable.',
         'KNK系列 — 适用于各种非铠装圆截面电缆的电缆接头。'),
    'Серия КМР- Кабельные вводы для всех типов небронированного кабеля круглого сечения, проложенного в гибком металлорукаве.':
        ('KMR series — cable glands for unarmoured round cable laid in flexible metal conduit.',
         'KMR系列 — 适用于金属软管内非铠装圆截面电缆的电缆接头。'),
    'Серия КБУ - Кабельные вводы для всех типов бронированного кабеля круглого сечения':
        ('KBU series — cable glands for all types of armoured round-section cable.',
         'KBU系列 — 适用于各种铠装圆截面电缆的电缆接头。'),
    'Серия КБУ-МР - Кабельные вводы для всех типов бронированного кабеля круглого сечения, проложенного в гибком металлорукаве':
        ('KBU-MR series — cable glands for armoured round cable laid in flexible metal conduit.',
         'KBU-MR系列 — 适用于金属软管内铠装圆截面电缆的电缆接头。'),
    # pneumatic_actuators
    'Серия приводов в общепромышленном исполнении':
        ('Actuator series for general industrial service.', '通用工业型执行器系列。'),
    'Серия приводов во взрывобезопасном и ультранизкотемпературном исполнении':
        ('Actuator series for explosion-proof and ultra-low-temperature service.',
         '防爆超低温型执行器系列。'),
    'Серия кулисных приводов с малым вращающим моментом':
        ('Linkage actuator series with low output torque.', '低扭矩连杆执行器系列。'),
    # solenoid_valves
    'Серия недорогих распределителей 3/2 и 5/2 для общепромышленного применения':
        ('Economical 3/2 and 5/2 valve series for general industrial use.',
         '通用工业用经济型3/2和5/2阀系列。'),
    'Серия взрывозащищённых клапанов 3/2, импортозамещенный технический аналог серии 327 ASCO':
        ('Explosion-proof 3/2 valve series, domestic technical equivalent of ASCO 327 series.',
         '防爆3/2阀系列，ASCO 327系列的国产技术替代品。'),
    'Серия взрывозащищенных клапанов 5/2 для низких температур окружающей среды.':
        ('Explosion-proof 5/2 valve series for low ambient temperatures.',
         '适用于低环境温度的防爆5/2阀系列。'),
    # pa_controls positioners
    'Серия TS600 позиционер поворотного типа':
        ('TS600 rotary positioner series.', 'TS600角行程定位器系列。'),
    'Серия TS900 Интеллектуальный (смарт) позиционер (Взрывозащищенный) поворотного типа':
        ('TS900 smart (intelligent) positioner, explosion-proof, rotary type.',
         'TS900智能（防爆）角行程定位器系列。'),
    # filter_regulator
    'Фильтр-регуляторы для очистки сжатого воздуха серии BPFR размера 1/4”…1”, темп. -10...+60':
        ('Filter regulators for compressed air cleaning, BPFR series, size 1/4”…1”, temp. -10…+60.',
         '压缩空气过滤调压阀BPFR系列，规格1/4”…1”，温度-10…+60。'),
    'Фильтр-регуляторы для очистки сжатого воздуха серии BPFR.LT размера 1/4”…1”, темп. -40...+60':
        ('Filter regulators for compressed air cleaning, BPFR.LT series, size 1/4”…1”, temp. -40…+60.',
         '压缩空气过滤调压阀BPFR.LT系列，规格1/4”…1”，温度-40…+60。'),
    'Фильтр-регуляторы серии BPFAR размера корпус нерж.сталь 1/4” и 1/2”, темп. -40...+80':
        ('Filter regulators, BPFAR series, stainless steel body 1/4” and 1/2”, temp. -40…+80.',
         '过滤调压阀BPFAR系列，不锈钢阀体1/4”和1/2”，温度-40…+80。'),
    # gearbox
    'Недорогие ручные дублеры для пневмоприводов':
        ('Economical manual overrides for pneumatic actuators.',
         '气动执行器用经济型手动操作机构。'),
    # valve_data (long marketing paragraphs)
    'Затворы проходят двойной контроль качества - после гидроиспытаний дополнительно испытываются воздухом Малое гидравлическое сопротивление затворов ABRA обеспечивает великолепные гидравлические характеристики. Поворотный затвор межфланцевый ABRA - это запорно-регулирующая трубопроводная арматура с минимальной практически достижимой строительной длиной. Высокое качество изготовления и проверенные материалы конструкции обеспечивают отличные эксплуатационные характеристики. Конструкция поворотного затвора ABRA обеспечивает при необходимости полную разборность.':
        ('Valves undergo double quality control — after hydrotesting they are additionally air-tested. The low hydraulic resistance of ABRA valves ensures excellent hydraulic performance. The ABRA wafer butterfly valve is a shut-off and regulating valve with the shortest practically achievable face-to-face length. High manufacturing quality and proven materials ensure excellent service performance. The ABRA butterfly valve design is fully demountable when required.',
         '蝶阀经过双重质量检验——水压试验后额外进行气密试验。ABRA蝶阀水力阻力小，水力性能优异。ABRA对夹式蝶阀为截止-调节型管路阀门，结构长度最短。高制造质量和经过验证的材料确保优异的运行性能。ABRA蝶阀结构在需要时可完全拆解。'),
    'Дисковый поворотный затвор является арматурой общего назначения, используется в различных отраслях в качестве запорного устройства. Дисковые поворотные затворы в основном применяются в системах холодного и горячего водоснабжения, а также в системах отопления, вентиляции, кондиционирования. Седловое уплотнение и диск затвора устойчивы к теплоносителям на базе гликолевых и спиртовых антифризов.':
        ('The wafer butterfly valve is a general-purpose valve used in various industries as a shut-off device. Butterfly valves are mainly used in hot and cold water supply systems as well as in heating, ventilation and air-conditioning systems. The seat seal and disc are resistant to glycol- and alcohol-based antifreeze heat transfer fluids.',
         '对夹式蝶阀为通用阀门，作为截止装置用于各行各业。蝶阀主要用于冷热水供应系统以及供暖、通风和空调系统。阀座密封和阀板耐乙二醇和醇基防冻液载热介质。'),
    'Регулирование и полное перекрытие потока химически активных жидкостей (кислот, щелочей, органических растворителей, нефтепродуктов) и других сред (в зависимости от материала проточной части), имеющих твердые включения и механические примеси до 2,0 мм, объемная концентрация которых не превышает 0,5%.':
        ('Regulation and full shut-off of chemically active liquids (acids, alkalis, organic solvents, petroleum products) and other media (depending on the flow-path material), containing solid inclusions and mechanical impurities up to 2.0 mm with a volume concentration not exceeding 0.5%.',
         '调节和完全截断含固体夹杂和机械杂质（粒径≤2.0 mm，体积浓度≤0.5%）的化学活性液体（酸、碱、有机溶剂、石油产品）及其他介质（视流道材料而定）。'),
}


def _norm(s):
    return re.sub(r'\s+', ' ', (s or '')).strip()


class Command(BaseCommand):
    help = 'Backfill en/cn translations for model line descriptions.'

    def handle(self, *args, **options):
        total = 0
        for model in apps.get_models():
            if 'description_i18n' not in {f.name for f in model._meta.fields}:
                continue
            updated = 0
            for obj in model._meta.default_manager.all():
                key = _norm(getattr(obj, 'description', ''))
                if key in DESCRIPTIONS:
                    en, cn = DESCRIPTIONS[key]
                    i18n = dict(obj.description_i18n or {})
                    i18n['en'] = en
                    i18n['cn'] = cn
                    obj.description_i18n = i18n
                    obj.save(update_fields=['description_i18n'])
                    updated += 1
            if updated:
                total += updated
                self.stdout.write(f'{model._meta.app_label}.{model._meta.object_name}: {updated}')
        self.stdout.write(self.style.SUCCESS(f'Done. Translated descriptions: {total}'))
