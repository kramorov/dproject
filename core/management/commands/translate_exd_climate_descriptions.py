"""Заполняет en/cn переводы описаний (description) справочников взрывозащиты
и климатического исполнения.

Эти справочники отличаются от остальных: поле ``name`` у них — аббревиатура/код
(«Ex db», «IIA», «T1», «У», «1»), поэтому НЕ переводится; переводимо только
``description`` (через ``description_i18n``).

Идемпотентна: повторный запуск просто перезаписывает en/cn (ru синхронизируется
миксином LocalizedDictFieldsMixin при save).
"""
from django.core.management.base import BaseCommand
from django.apps import apps

TRANSLATIONS = {
    'params.ExplosionProtectionMethod': {
        'd': ('Prevents explosion transmission to the outside. If a flash occurs inside the enclosure, the enclosure withstands the pressure and cools the escaping gases to a safe temperature.',
              '防止爆炸向外传播。若壳体内发生闪燃，外壳承受压力并将喷出的气体冷却至安全温度。'),
        'i': ('The most reliable method. Based on limiting electrical energy (voltage, current) so that a spark or wire heating cannot ignite an explosive mixture in principle.',
              '最可靠的方法。基于限制电能（电压、电流），使火花或导线发热原则上无法点燃爆炸性混合物。'),
        'e': ('Prevents arcs, sparks, and hazardous temperatures. Achieved by using high-quality insulating materials and reliable contacts.',
              '防止产生电弧、火花或危险温度。通过使用优质绝缘材料和可靠触点实现。'),
        'm': ('Parts capable of igniting the mixture are fully encapsulated in epoxy resin or another polymer. Gas or dust physically cannot reach the potential spark source.',
              '能引燃混合物的部件用环氧树脂或其他聚合物完全灌封。气体或粉尘在物理上无法接触潜在火花源。'),
        'p': ('The enclosure is kept at a pressure of clean air or inert gas above atmospheric. This pushes the explosive mixture out and prevents it from entering.',
              '壳体内保持高于大气压的清洁空气或惰性气体压力，将爆炸性混合物挤出并阻止其进入。'),
        'q': ('The equipment enclosure is completely filled with fine-grained sand. The sand quenches the arc and cools the flame if a fault occurs inside the device.',
              '设备外壳完全填充细粒石英砂。发生内部故障时，砂子熄灭电弧并冷却火焰。'),
        'o': ('Electrical parts are immersed in a layer of mineral oil or another non-flammable liquid, fully isolating potential sparks from contact with the atmosphere.',
              '电气部件浸入矿物油或其他不燃液体层中，使潜在火花与大气完全隔离。'),
        't': ('Based on a highly sealed enclosure (IP6X). Dust cannot enter, and the outer surface temperature is strictly limited to prevent a dust layer from smouldering.',
              '基于外壳的高度密封性（IP6X）。粉尘无法进入，且外表面温度受到严格限制，以防粉尘层阴燃。'),
        'n': ('A simplified protection for Zone 2, where the risk of an accident is minimal. Includes intrinsically safe and non-sparking components rated only for normal operation.',
              '用于2区的简化防护，事故风险最小。包括仅适用于正常工况的本安和非火花组件。'),
        's': ('Used for equipment that cannot be classified by standard methods but whose safety is confirmed by special laboratory tests.',
              '适用于无法按标准方法分类、但安全性经实验室特殊测试确认的设备。'),
    },
    'params.ExplosionProtectionType': {
        'db': ('Flameproof enclosure — equipment withstands internal explosion pressure. Intended for Zone 1 (protection level Gb).',
               '隔爆外壳——设备能承受内部爆炸压力。适用于1区（防护等级Gb）。'),
        'ia': ('Intrinsically safe circuit — very high degree of protection.',
               '本安电路——防护等级很高。'),
        'ib': ('Intrinsically safe circuit — high degree of protection.',
               '本安电路——高防护等级。'),
        'nA': ('Non-sparking equipment for Zone 2. Obsolete, replaced by Ex ec.',
               '用于2区的非火花设备。已过时，由Ex ec替代。'),
        'tc': ('Dust enclosure protection for zone 22 (dust only under fault conditions).',
               '用于22区的粉尘外壳防护（仅在故障时有粉尘）。'),
        'tb': ('Dust enclosure protection — high degree.',
               '粉尘外壳防护——高防护等级。'),
        'ta': ('Dust enclosure protection for zone 20 (dust continuously present).',
               '用于20区的粉尘外壳防护（粉尘持续存在）。'),
        'ec': ('Increased safety (Zone 2). Non-sparking equipment. Replaced the old nA.',
               '增安型（2区）。非火花设备。取代旧的nA。'),
        'eb': ('Increased safety (Zone 1). Prevents sparking and overheating.',
               '增安型（1区）。防止火花和过热。'),
        'ic': ('Intrinsically safe circuit (Zone 2). Safe under normal operation.',
               '本安电路（2区）。正常运行下安全。'),
        'ma': ('Encapsulation (Zone 0). Maximum protection by potting.',
               '浇封型（0区）。通过灌封实现最大防护。'),
        'mb': ('Encapsulation (Zone 1). Components potted in polymer.',
               '浇封型（1区）。部件用聚合物灌封。'),
        'pxb': ('Pressurized enclosure (Zone 1). Inert gas inside.',
                '正压外壳（1区）。内部为惰性气体。'),
        'da': ('Flameproof enclosure (Zone 0). Typically for gas analyzer sensors.',
               '隔爆外壳（0区）。通常用于气体分析仪传感器。'),
        'q': ('Powder (quartz) filling (Zone 1). Enclosure filled with fine-grained sand.',
              '充砂型（1区）。外壳填充细粒砂。'),
        'o': ('Oil immersion (Zone 1). Electrical parts immersed in oil.',
              '充油型（1区）。电气部件浸入油中。'),
        'pzc': ('Pressurized protection (Zone 22). Prevents dust from entering the enclosure.',
                '正压防护（22区）。防止粉尘进入外壳。'),
        'nR': ('nR = restricted breathing.',
               'nR = 限制呼吸。'),
    },
    'params.HazardousGroup': {
        'IIA': ('Propane, methane, ammonia. The least hazardous gas group.',
                '丙烷、甲烷、氨。危险性最低的气体组。'),
        'IIB': ('Ethylene, coke oven gas, dimethyl ether. A gas group of medium hazard.',
                '乙烯、焦炉煤气、二甲醚。中等危险性的气体组。'),
        'IIC': ('Hydrogen, acetylene, carbon disulphide. The most hazardous gas group.',
                '氢气、乙炔、二硫化碳。危险性最高的气体组。'),
        'IIIA': ('Flammable volatile particles (flour, grain, sugar, starch).',
                 '易燃挥发性颗粒（面粉、谷物、糖、淀粉）。'),
        'IIIB': ('Non-conductive dust (wood, coal, plastic, peat).',
                 '非导电粉尘（木材、煤、塑料、泥炭）。'),
        'IIIC': ('Conductive dust (metal, graphite, coke, carbon).',
                 '导电粉尘（金属、石墨、焦炭、碳）。'),
    },
    'params.TemperatureClass': {
        'T1': ('Maximum surface temperature 450°C. Suitable for gases with ignition temperature above 450°C (hydrogen, methane, propane). The least stringent class.',
               '最高表面温度450°C。适用于点燃温度高于450°C的气体（氢气、甲烷、丙烷）。最不严格的等级。'),
        'T2': ('Maximum surface temperature 300°C. For gases with ignition temperature above 300°C (ethylene, butane, ethanol).',
               '最高表面温度300°C。适用于点燃温度高于300°C的气体（乙烯、丁烷、乙醇）。'),
        'T3': ('Maximum surface temperature 200°C. For gases with ignition temperature above 200°C (petrol, diesel fuel).',
               '最高表面温度200°C。适用于点燃温度高于200°C的气体（汽油、柴油）。'),
        'T4': ('Maximum surface temperature 135°C. For gases with ignition temperature above 135°C (carbon disulphide, diethyl ether). The most common class for general industrial equipment.',
               '最高表面温度135°C。适用于点燃温度高于135°C的气体（二硫化碳、乙醚）。通用工业设备最常用的等级。'),
        'T5': ('Maximum surface temperature 100°C. For gases with ignition temperature above 100°C. Increased heat-dissipation requirements.',
               '最高表面温度100°C。适用于点燃温度高于100°C的气体。对散热有更高要求。'),
        'T6': ('Maximum surface temperature 85°C. For gases with the lowest ignition temperature (carbon disulphide). The most stringent class.',
               '最高表面温度85°C。适用于点燃温度最低的气体（二硫化碳）。最严格的等级。'),
        'T85': ('Maximum surface temperature 85°C for dust explosion protection.',
                '用于粉尘防爆的最高表面温度85°C。'),
        'T95': ('Maximum surface temperature 95°C for dust explosion protection.',
                '用于粉尘防爆的最高表面温度95°C。'),
        'T100': ('Maximum surface temperature 100°C for dust explosion protection.',
                 '用于粉尘防爆的最高表面温度100°C。'),
    },
    'params.ClimaticZoneCategory': {
        'u': ('У — temperate climate', 'У — 温带气候'),
        'hl': ('ХЛ — cold climate', 'ХЛ — 寒冷气候'),
        'uhl': ('УХЛ — temperate and cold climate', 'УХЛ — 温带和寒冷气候'),
        't': ('Т — tropical climate', 'Т — 热带气候'),
        'tv': ('ТВ — tropical humid climate', 'ТВ — 热带湿润气候'),
        'ts': ('ТС — tropical dry climate', 'ТС — 热带干燥气候'),
        'ut': ('УТ — temperate and tropical climate', 'УТ — 温带和热带气候'),
        'm': ('М — marine climate', 'М — 海洋性气候'),
        'tm': ('ТМ — tropical marine climate', 'ТМ — 热带海洋性气候'),
        'om': ('ОМ — tropical and moderately cold marine climate', 'ОМ — 热带和温寒海洋性气候'),
        'o': ('О — general-purpose climatic version', 'О — 通用气候型'),
        'v': ('В — all-climate version', 'В — 全气候型'),
    },
    'params.ClimaticPlacementCategory': {
        '1': ('1 — for outdoor operation', '1 — 用于露天使用'),
        '2': ('2 — for operation under a canopy', '2 — 用于遮棚下使用'),
        '3': ('3 — for operation indoors without artificially controlled climate', '3 — 用于无人工气候调节的封闭场所'),
        '4': ('4 — for operation indoors with artificially controlled climate', '4 — 用于有人工气候调节的封闭场所'),
        '5': ('5 — for operation in sealed conditions', '5 — 用于密封环境'),
    },
}

# name тоже переводится по общему правилу: код «Ex d» сохраняется, переводится
# только пояснение в скобках.
NAME_TRANSLATIONS = {
    'params.ExplosionProtectionMethod': {
        'd': ('Ex d (Flameproof enclosure)', 'Ex d (隔爆外壳)'),
        'i': ('Ex i (Intrinsically safe electrical circuit)', 'Ex i (本安电路)'),
        'e': ('Ex e (Increased safety type «e»)', 'Ex e (增安型「e」)'),
        'm': ('Ex m (Encapsulation)', 'Ex m (浇封型)'),
        'p': ('Ex p (Pressurization)', 'Ex p (正压型)'),
        'q': ('Ex q (Powder (quartz) filling)', 'Ex q (充砂型)'),
        'o': ('Ex o (Oil immersion)', 'Ex o (充油型)'),
        't': ('Ex t (Dust enclosure protection)', 'Ex t (粉尘外壳防护)'),
        'n': ('Ex n (Type of protection «n»)', 'Ex n (防护类型「n」)'),
        's': ('Ex s (Special type of protection)', 'Ex s (特殊防爆类型)'),
    },
}


class Command(BaseCommand):
    help = 'Backfill en/cn translations for Exd/Climate reference names and descriptions.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перезаписать существующие переводы из словаря (затирает ручные правки).')

    def handle(self, *args, **options):
        force = options['force']
        total = 0
        for label, trans in TRANSLATIONS.items():
            total += self._apply_translations(label, trans, 'description_i18n', force)
        for label, trans in NAME_TRANSLATIONS.items():
            total += self._apply_translations(label, trans, 'name_i18n', force)
        self.stdout.write(self.style.SUCCESS(f'Done. Translated rows: {total}'))

    def _apply_translations(self, label, trans, field, force=False):
        app_label, model_name = label.split('.', 1)
        Model = apps.get_model(app_label, model_name)
        updated = 0
        for obj in Model._meta.default_manager.all():
            code = getattr(obj, 'code', None)
            if code is None or code not in trans:
                continue
            en, cn = trans[code]
            i18n = dict(getattr(obj, field, None) or {})
            changed = False
            for locale, value in (('en', en), ('cn', cn)):
                if force or locale not in i18n:
                    i18n[locale] = value
                    changed = True
            if changed:
                setattr(obj, field, i18n)
                obj.save(update_fields=[field])
                updated += 1
        if updated:
            self.stdout.write(f'{label} ({field}): {updated}')
        return updated
