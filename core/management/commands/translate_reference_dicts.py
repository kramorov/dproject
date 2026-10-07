"""Заполняет en/cn переводы описательных названий справочников.

Переводит ТОЛЬКО русские описательные фразы. Коды, стандартные обозначения,
уникальные/фирменные названия (ГЕРДА, FLEXICON, NAMUR, модели датчиков,
размеры, "Ex db", "IP67", "NPT", "M", "У1", "T1", "3/2" и т.п.) — НЕ переводятся:
для них локаль вернёт RU-значение (fallback в pick_i18n).

Идемпотентна: повторный запуск просто перезаписывает en/cn.
"""
from django.core.management.base import BaseCommand
from django.apps import apps

TRANSLATIONS = {
    'pneumatic_fittings.FittingShape': {
        'Прямой': ('Straight', '直通'),
        'Угловой (L-образный)': ('Elbow (L-shaped)', '弯头（L形）'),
        'Тройник (T-образный)': ('Tee (T-shaped)', '三通（T形）'),
        'Крестовина (X-образный)': ('Cross (X-shaped)', '四通（X形）'),
        'Y-образный (Разветвитель)': ('Y-shaped (Branch tee)', 'Y形（分流）'),
        'Переборочный (Проходной)': ('Bulkhead (Straight-through)', '穿板（直通）'),
    },
    'pneumatic_fittings.FittingFixationMethod': {
        'Врезное кольцо': ('Cutting ring', '卡套'),
        'Накидная гайка (Rapid / Push-on)': ('Union nut (Rapid / Push-on)', '压紧螺母（Rapid / Push-on）'),
        'Накидная гайка (Ёлочка)': ('Union nut (Barb)', '压紧螺母（宝塔）'),
        'Ниппельный (Хомут)': ('Nipple (Clamp)', '接头（卡箍）'),
        'Обжимной с двумя врезными кольцами (Double Ferrule)': ('Compression, double ferrule', '双卡套压缩'),
        'Обжимной с кольцом (Universal / Compression)': ('Compression (Universal)', '卡套压缩'),
        'Цанговый (Push-in)': ('Push-in (Collet)', '快插（卡箍）'),
    },
    'pneumatic_fittings.PneumaticFittingVariety': {
        'Глушитель': ('Silencer', '消音器'),
        'Заглушка пневматическая': ('Pneumatic plug', '气动堵头'),
        'Фитинг c накидной гайкой (Rapid) L угловой': ('Union nut fitting (Rapid), L elbow', '压紧螺母接头（Rapid）L弯头'),
        'Фитинг c накидной гайкой (Rapid) прямой': ('Union nut fitting (Rapid), straight', '压紧螺母接头（Rapid）直通'),
        'Фитинг обжимной L угловой': ('Compression fitting, L elbow', '卡套接头L弯头'),
        'Фитинг обжимной прямой': ('Compression fitting, straight', '卡套接头直通'),
        'Фитинг обжимной с двумя врезными кольцами прямой': ('Double ferrule fitting, straight', '双卡套接头直通'),
        'Фитинг обжимной с двумя врезными кольцами угловой': ('Double ferrule fitting, elbow', '双卡套接头弯头'),
        'Фитинг цанговый L угловой': ('Push-in fitting, L elbow', '快插接头L弯头'),
        'Фитинг цанговый прямой': ('Push-in fitting, straight', '快插接头直通'),
    },
    'filter_regulator.DrainVariety': {
        'Автоматический (внешний)': ('Automatic (external)', '自动（外部）'),
        'Автоматический слив': ('Automatic drain', '自动排水'),
        'Полуавтоматический слив': ('Semi-automatic drain', '半自动排水'),
        'Ручной слив': ('Manual drain', '手动排水'),
        'Электронный (по таймеру)': ('Electronic (timer)', '电子（定时）'),
    },
    'filter_regulator.FilterRegulatorVariety': {
        'Маслоотделитель': ('Oil separator', '油分离器'),
        'Маслораспылитель': ('Oil mist lubricator', '油雾器'),
        'Прецизионный регулятор': ('Precision regulator', '精密调压阀'),
        'Регулятор давления': ('Pressure regulator', '调压阀'),
        'Фильтр': ('Filter', '过滤器'),
        'Фильтр-регулятор': ('Filter regulator', '过滤调压阀'),
    },
    'solenoid_valves.ManualOverride': {
        'Кнопочный (без фиксации)': ('Push-button (momentary)', '按钮（无锁止）'),
        'Отсутствует': ('None', '无'),
        'Поворотный с фиксацией': ('Rotary with lock', '旋转带锁止'),
        'Под отвертку (со шлицем)': ('Slotted (screwdriver)', '一字（螺丝刀）'),
        'Рычажный ручной дублер без фиксации': ('Lever manual override, non-locking', '杠杆手动，无锁止'),
        'Рычажный ручной дублер с фиксацией': ('Lever manual override, locking', '杠杆手动，带锁止'),
        'Скрытая кнопка (защищенная)': ('Concealed button (protected)', '隐藏按钮（防护）'),
    },
    'solenoid_valves.ValveDesign': {
        'Золотниковый': ('Spool', '滑阀'),
        'Мембранный': ('Diaphragm', '膜片'),
        'Поршневой': ('Piston', '活塞'),
        'Тарельчатый/Седельный': ('Poppet / Seated', '提升阀/座阀'),
    },
    'solenoid_valves.ValveOperationVariety': {
        'Прямого действия': ('Direct acting', '直动式'),
        'С пилотным управлением (Непрямого действия)': ('Pilot operated (Indirect)', '先导式（间接）'),
        'С принудительным подъемом (Комбинированный)': ('Force-lift (Combined)', '强制提升（组合）'),
    },
    'solenoid_valves.ValvePilotVariety': {
        'Механический (Концевой ролик)': ('Mechanical (Limit roller)', '机械（限位滚轮）'),
        'Пневматический (Воздушный сигнал)': ('Pneumatic (Air signal)', '气动（气信号）'),
        'Ручной (Рычаг или Кнопка)': ('Manual (Lever or button)', '手动（杠杆或按钮）'),
        'Электромагнитный (Соленоид)': ('Electromagnetic (Solenoid)', '电磁（电磁阀）'),
        'Электропневматический (Внутренний пилот)': ('Electro-pneumatic (Internal pilot)', '电气动（内部先导）'),
    },
    'solenoid_valves.ValveActuationVariety': {
        'Бистабильный (2 катушки)': ('Bistable (2 coils)', '双稳态（双线圈）'),
        'Моностабильный (Возврат пружиной)': ('Monostable (Spring return)', '单稳态（弹簧复位）'),
        'Моностабильный (Пневмовозврат)': ('Monostable (Pneumatic return)', '单稳态（气动复位）'),
        'Трехпозиционный с возвратом в центр': ('Three-position, spring-centered', '三位中封'),
    },
    'gearbox.GearboxVariety': {
        'Редуктор под привод': ('Gearbox for actuator', '执行器用减速器'),
        'Редуктор ручной': ('Manual gearbox', '手动减速器'),
        'Ручной дублер': ('Manual override', '手动操作机构'),
    },
    'gearbox.OverrideMechanism': {
        'Автоматическое отключение': ('Automatic disengagement', '自动脱开'),
        'Боковой переключатель': ('Side selector', '侧面切换'),
        'Кулисный переключатель': ('Linkage selector', '摇杆切换'),
        'Прямой привод (без отключения)': ('Direct drive (no disengagement)', '直接驱动（无脱开）'),
        'Рычажный переключатель с фиксацией': ('Lever selector with lock', '杠杆切换带锁'),
        'Сдвижной штурвал': ('Sliding handwheel', '滑动手轮'),
        'Эксцентриковый рычаг': ('Eccentric lever', '偏心杠杆'),
        'Электромеханический переключатель': ('Electromechanical selector', '机电切换'),
    },
    'gearbox.TransmissionVariety': {
        'Гипоидная': ('Hypoid', '准双曲面'),
        'Коническая': ('Bevel', '锥齿轮'),
        'Коническо-планетарная': ('Bevel-planetary', '锥行星'),
        'Планетарная': ('Planetary', '行星'),
        'Реечная': ('Rack', '齿条'),
        'Цилиндрическая': ('Spur', '圆柱齿轮'),
        'Червячная': ('Worm', '蜗杆'),
        'Червячно-планетарная': ('Worm-planetary', '蜗杆行星'),
    },
    'pa_controls.ActingType': {
        'Линейный': ('Linear', '直行程'),
        'Ротационный': ('Rotary', '角行程'),
    },
    'media_library.MediaCategory': {
        'Аудио': ('Audio', '音频'),
        'Баннер': ('Banner', '横幅'),
        'Видео': ('Video', '视频'),
        'Галерея товара': ('Product gallery', '产品图库'),
        'Диаграмма': ('Diagram', '图表'),
        'Другое': ('Other', '其他'),
        'Изображение': ('Image', '图片'),
        'Инструкция': ('Instructions', '说明书'),
        'Каталог': ('Catalog', '目录'),
        'Листовка': ('Leaflet', '宣传单'),
        'Презентация': ('Presentation', '演示文稿'),
        'Руководство по эксплуатации': ('Operation manual', '操作手册'),
        'Сертификат': ('Certificate', '证书'),
        'Схема': ('Scheme', '原理图'),
        'Техдокументация': ('Technical documentation', '技术文档'),
        'Чертеж': ('Drawing', '图纸'),
        'Шаблон документа Excel': ('Excel document template', 'Excel文档模板'),
        'Шаблон документа Word': ('Word document template', 'Word文档模板'),
    },
    'valve_data.ConstructionVariety': {
        '2-х составной': ('Two-piece', '两段式'),
        '2-х эксцентриковый': ('Double-eccentric', '双偏心'),
        '3-х составной': ('Three-piece', '三段式'),
        '3-х эксцентриковый': ('Triple-eccentric', '三偏心'),
        'Осевой': ('Axial', '轴向'),
        'разборный': ('Split', '分体式'),
        'цельносварной': ('Welded (integral)', '整体焊接'),
    },
    'valve_data.ValveConnectionToPipe': {
        'Межфланцевое': ('Wafer', '对夹式'),
        'Под сварку тип приварки butt (осн)': ('Butt-weld', '对焊'),
        'Под сварку тип приварки socket': ('Socket-weld', '承插焊'),
        'Резьбовое (муфтовое) - внутренняя резьба G (BSPP)': ('Threaded — G (BSPP) female', '螺纹 — G (BSPP) 内螺纹'),
        'Резьбовое (муфтовое) - внутренняя резьба NPT': ('Threaded — NPT female', '螺纹 — NPT 内螺纹'),
        'Резьбовое (муфтовое) - внутренняя резьба R (BSPT)': ('Threaded — R (BSPT) female', '螺纹 — R (BSPT) 内螺纹'),
        'Фланцевое': ('Flanged', '法兰式'),
    },
    'valve_data.PortQty': {
        '2 порта': ('2 ports', '2通'),
        '3 порта, L-тип': ('3 ports, L-type', '3通L型'),
        '3 порта, T-тип': ('3 ports, T-type', '3通T型'),
    },
    'valve_data.EAVAttribute': {
        'Класс герметичности': ('Leakage class', '密封等级'),
        'Конструкция штока (выдвижной или нет)': ('Stem design (rising or non-rising)', '阀杆结构（明杆或暗杆）'),
        'Направление действия запорного органа': ('Closure element action direction', '关闭件作用方向'),
        'Тип затвора дискового': ('Butterfly disc type', '蝶板类型'),
        'Тип монтажной площадки': ('Mounting pad type', '安装平台类型'),
        'Управление': ('Actuation', '控制方式'),
    },
    'cable_glands.CableType': {
        'Под бронированный кабель': ('For armoured cable', '铠装电缆'),
        'Под бронированный кабель в металлорукаве': ('For armoured cable in conduit', '金属软管铠装电缆'),
        'Под небронированный кабель': ('For unarmoured cable', '非铠装电缆'),
        'Под небронированный кабель в металлорукаве': ('For unarmoured cable in conduit', '金属软管非铠装电缆'),
    },
    'cable_glands.CableGlandBodyMaterial': {
        'Латунь': ('Brass', '黄铜'),
        'Нержавеющая сталь': ('Stainless steel', '不锈钢'),
        'Никелерованная латунь': ('Nickel-plated brass', '镀镍黄铜'),
    },
    'pneumatic_actuators.PneumaticActuatorConstructionVariety': {
        'Кулисный': ('Linkage', '连杆'),
        'Шестерня-рейка': ('Rack-and-pinion', '齿轮齿条'),
    },
    'pneumatic_actuators.PneumaticActuatorSpringsQty': {
        '05 пружин': ('05 springs', '05根弹簧'),
        '06 пружин': ('06 springs', '06根弹簧'),
        '07 пружин': ('07 springs', '07根弹簧'),
        '08 пружин': ('08 springs', '08根弹簧'),
        '09 пружин': ('09 springs', '09根弹簧'),
        '10 пружин': ('10 springs', '10根弹簧'),
        '11 пружин': ('11 springs', '11根弹簧'),
        '12 пружин': ('12 springs', '12根弹簧'),
    },
    'client_requests.ClientRequestStatus': {
        'Архив': ('Archived', '归档'),
        'В работе': ('In progress', '进行中'),
        'Новый': ('New', '新建'),
        'Отклонен': ('Rejected', '已拒绝'),
        'Подбор выполнен': ('Selection completed', '选型完成'),
        'Согласование': ('Approval', '审批'),
        'Требуется уточнение': ('Clarification required', '需澄清'),
        'Утвержден': ('Approved', '已批准'),
    },
    'client_requests.CommentType': {
        'Внутренний комментарий': ('Internal comment', '内部评论'),
        'Документ': ('Document', '文件'),
        'Изменение предложения': ('Proposal change', '方案变更'),
        'Изменение требований': ('Requirements change', '需求变更'),
        'Исходящее письмо': ('Outgoing letter', '外发函件'),
        'Коммерческое': ('Commercial', '商务'),
        'Напоминание': ('Reminder', '提醒'),
        'Отклонение': ('Rejection', '拒绝'),
        'Письмо клиента': ('Customer letter', '客户函件'),
        'Системное': ('System', '系统'),
        'Согласование': ('Approval', '审批'),
        'Техническое замечание': ('Technical note', '技术备注'),
        'Уточнение': ('Clarification', '澄清'),
    },
    'client_requests.RequestItemType': {
        'Подбор Арматуры и ПП к ней': ('Valve and actuator selection', '阀门及执行器选型'),
        'Подбор ПП к арматуре заказчика': ('Actuator selection for customer valve', '为客户阀门选型执行器'),
    },
    'cert_doc.CertVariety': {
        'Отказное письмо': ('Letter of refusal', '拒绝函'),
        'Сейсмостойкость до 9 баллов по MSK-64': ('Seismic resistance up to 9 (MSK-64)', '抗震性MSK-64 9级'),
    },
    'params.PneumaticConnection': {
        'Трубный монтаж': ('Pipe mounting', '管式安装'),
    },
    'materials.MaterialSpecified': {
        'HNBR (Гидронитрильный каучук)': ('HNBR (Nitrile rubber)', 'HNBR（丁腈橡胶）'),
        'FVMQ (Фторосиликон )': ('FVMQ (Fluorosilicone)', 'FVMQ（氟硅橡胶）'),
    },
    'params.StemShapes': {
        'Квадрат': ('Square', '方形'),
        'Вал со шпонкой': ('Keyed shaft', '带键轴'),
        'Левая резьба': ('Left-hand thread', '左旋螺纹'),
        'По заказу, макс.диам.': ('Custom, max. dia.', '定制，最大直径'),
    },
    'params.ActuatorGearboxOutputType': {
        'Четвертьоборотный': ('Quarter-turn', '角行程'),
        'Многоборотный': ('Multi-turn', '多回转'),
        'Линейный': ('Linear', '直行程'),
        'нет': ('none', '无'),
    },
}


class Command(BaseCommand):
    help = 'Backfill en/cn translations for descriptive reference names.'

    def handle(self, *args, **options):
        total = 0
        for label, trans in TRANSLATIONS.items():
            app_label, model_name = label.split('.', 1)
            Model = apps.get_model(app_label, model_name)
            updated = 0
            for obj in Model._meta.default_manager.all():
                if obj.name in trans:
                    en, cn = trans[obj.name]
                    i18n = dict(obj.name_i18n or {})
                    i18n['en'] = en
                    i18n['cn'] = cn
                    obj.name_i18n = i18n
                    obj.save(update_fields=['name_i18n'])
                    updated += 1
            if updated:
                total += updated
                self.stdout.write(f'{label}: {updated}')
        self.stdout.write(self.style.SUCCESS(f'Done. Translated rows: {total}'))
