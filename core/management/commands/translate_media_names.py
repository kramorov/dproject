"""Заполняет en/cn переводы названий медиабиблиотеки и сертификатов.

Названия — свободный текст («Изображение БКВ ЯМАЛ-S 01», «Техничка Кабельные
вводы НОРДЭКС серия ВН», «ТР ТС 012 Блоки концевых выключателей…»). Коды и
фирменные названия (БКВ, НОРДЭКС, ЯМАЛ, ТР ТС 012, RPA…) не переводятся.

Перевод — по фразам (описательные слова), идемпотентен: перезаписывает en/cn,
«ru» синхронизируется миксином LocalizedNameFieldsMixin при save.
"""
from django.core.management.base import BaseCommand
from django.apps import apps

# (ru-фраза, en, cn) — порядок важен: более длинные фразы раньше.
PHRASES = [
    ('Техничка на БКВ', 'Tech doc for LSB', '限位开关盒 技术文档'),
    ('РЭ на БКВ', 'Operation manual for LSB', '限位开关盒 操作手册'),
    ('Техническая листовка на серию соленоидных клапанов', 'Technical leaflet for solenoid valve series', '电磁阀系列 技术单页'),
    ('Техническая листовка на серию БКВ', 'Technical leaflet for LSB series', '限位开关盒系列 技术单页'),
    ('Техническая листовка на БКВ', 'Technical leaflet for LSB', '限位开关盒 技术单页'),
    ('Техническая листовка ручные дублеры серии', 'Technical leaflet, manual overrides series', '手动超越器系列 技术单页'),
    ('РЭ ручной дублер', 'Operation manual, manual override', '操作手册, 手动超越器'),
    ('Руководство по эксплуатации', 'Operation manual', '操作手册'),
    ('РЭ', 'Operation manual', '操作手册'),
    ('ручного дублера', 'manual override', '手动超越器'),
    ('ручные дублеры', 'manual overrides', '手动超越器'),
    ('дублеры', 'overrides', '超越器'),
    ('редукторы', 'gearboxes', '减速器'),
    ('на блоки концевых выключателей', 'for limit switch boxes', '用于限位开关盒'),
    ('Блок концевых выключателей', 'Limit switch box', '限位开关盒'),
    ('Блоки концевых выключателей', 'Limit switch boxes', '限位开关盒'),
    ('Кабельные вводы', 'Cable glands', '电缆接头'),
    ('Кабельный ввод', 'Cable gland', '电缆接头'),
    ('монтажная площадка', 'mounting pad', '安装平台'),
    ('ручной редуктор', 'manual gearbox', '手动减速器'),
    ('с ручным редуктором', 'with manual gearbox', '带手动减速器'),
    ('на пневмоприводы', 'for pneumatic actuators', '用于气动执行器'),
    ('пневмоприводы', 'pneumatic actuators', '气动执行器'),
    ('пневмопривод', 'pneumatic actuator', '气动执行器'),
    ('Привод пневматический', 'Pneumatic actuator', '气动执行器'),
    ('Позиционеры', 'Positioners', '定位器'),
    ('Изображение', 'Image', '图片'),
    ('Техничка', 'Tech doc', '技术文档'),
    ('Техническая листовка', 'Technical leaflet', '技术单页'),
    ('Инструкция', 'Manual', '说明书'),
    ('Сертификат', 'Certificate', '证书'),
    (' серт ', ' cert. ', ' 证书 '),
    ('Декларация соответствия', 'Declaration of conformity', '符合性声明'),
    ('ДС', 'DoC', '符合性声明'),
    ('Отказное письмо', 'Waiver letter', '拒绝函'),
    ('Фильтр-регулятор', 'Filter regulator', '过滤器调压阀'),
    ('фильтр-регуляторы', 'filter regulators', '过滤器调压阀'),
    ('Фитинги', 'Fittings', '接头'),
    ('фитинг', 'fitting', '接头'),
    ('глушитель', 'silencer', '消声器'),
    ('заглушка', 'plug', '堵头'),
    ('Габаритный чертеж', 'Dimensional drawing', '外形图'),
    ('Чертеж', 'Drawing', '图纸'),
    ('пневмопозиционера', 'pneumatic positioner', '气动定位器'),
    ('с купольным визуальным индикатором', 'with dome visual indicator', '带拱顶视窗指示器'),
    ('с трансмиттером+БКВ', 'with transmitter+LSB', '带变送器+限位开关盒'),
    ('c трансмиттером', 'with transmitter', '带变送器'),
    ('с трансмиттером', 'with transmitter', '带变送器'),
    ('c креплением для БКВ', 'with LSB mounting', '带限位开关盒安装'),
    ('скобой для БКВ', 'bracket for LSB', '限位开关盒支架'),
    ('с пускателями', 'with starters', '带启动器'),
    ('(ротационный)', '(rotary)', '（旋转）'),
    ('(линейный)', '(linear)', '（直行程）'),
    ('(потенциометр)', '(potentiometer)', '（电位器）'),
    ('(присоединение Namur)', '(Namur connection)', '（Namur 连接）'),
    ('(трубное присоединение)', '(pipe connection)', '（管式连接）'),
    ('(копия)', '(copy)', '（副本）'),
    ('(опция', '(option', '（选件'),
    ('на серии соленоидных клапанов', 'for solenoid valve series', '用于电磁阀系列'),
    ('соленоидного клапана', 'solenoid valve', '电磁阀'),
    ('на серию БКВ', 'for LSB series', '用于限位开关盒系列'),
    ('бистабильный', 'bistable', '双稳态'),
    ('зеленый', 'green', '绿色'),
    ('откр_закр', 'open_close', '开_关'),
    ('откр-закр', 'open-close', '开-关'),
    ('упр.сигнал', 'ctrl. signal', '控制信号'),
    ('сигнал упр.', 'ctrl. signal', '控制信号'),
    ('управление', 'control', '控制'),
    ('обогреватель', 'heater', '加热器'),
    ('позиционер', 'positioner', '定位器'),
    ('общепром', 'general-purpose', '通用型'),
    ('ИЛИ', 'OR', '或'),
    ('ручка', 'handle', '手柄'),
    ('без МК', 'without MK', '无 MK'),
    ('Сейсмо', 'Seismic', '抗震'),
    ('Сеймо', 'Seismic', '抗震'),
    ('№ б/н', 'No. w/n', '编号 无'),
    (' от ', ' dated ', ' 日期 '),
    (' и ', ' and ', ' 和 '),
    ('кулисный', 'linkage', '连杆'),
    ('с дублерами', 'with overrides', '带手轮'),
    ('с дублером', 'with override', '带手轮'),
    ('дублером', 'override', '手轮'),
    ('червячного типа', 'worm type', '蜗轮型'),
    ('винтового типа', 'screw type', '螺杆型'),
    ('винтовым', 'screw', '螺杆'),
    ('гидравлическим', 'hydraulic', '液压'),
    ('Общий вид', 'General view', '总览'),
    ('Общая', 'General', '总览'),
    ('серий', 'series', '系列'),
    ('серии', 'series', '系列'),
    ('серия', 'series', '系列'),
]


def translate_name(name: str, lang: str):
    """Фразовый перевод названия (коды/бренды остаются как есть)."""
    if not name:
        return name
    result = name
    for ru, en, cn in PHRASES:
        repl = en if lang == 'en' else cn
        result = result.replace(ru, repl)
    return result


class Command(BaseCommand):
    help = 'Backfill en/cn phrase translations for media/cert names.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перезаписать существующие переводы (затирает ручные правки).')

    def handle(self, *args, **options):
        force = options['force']
        total = 0
        for app_label, model_name in [('media_library', 'MediaLibraryItem'), ('cert_doc', 'CertData')]:
            Model = apps.get_model(app_label, model_name)
            updated = 0
            for obj in Model.objects.all():
                name = obj.name or ''
                if not name.strip():
                    continue
                i18n = dict(obj.name_i18n or {})
                changed = False
                for locale in ('en', 'cn'):
                    if force or locale not in i18n:
                        i18n[locale] = translate_name(name, locale)
                        changed = True
                if changed:
                    obj.name_i18n = i18n
                    obj.save(update_fields=['name_i18n'])
                    updated += 1
            if updated:
                total += updated
                self.stdout.write(f'{app_label}.{model_name}: {updated}')
        self.stdout.write(self.style.SUCCESS(f'Done. Translated rows: {total}'))
