"""Заполняет en/cn переводы spec_template → spec_template_i18n.

Обрабатывает источники RU-шаблона спецификации:
  - EquipmentType (spec_template);
  - серии с собственным шаблоном: CableGlandModelLine, PneumaticActuatorModelLine.

Ключ перевода — ru-подпись (группа и поле). Подписи, которых нет в словарях,
остаются как есть (fallback ru) — команда сообщает о них в конце.

Идемпотентна: по умолчанию заполняет только отсутствующие локали;
`--force` — перестроить en/cn заново из RU-шаблона (осторожно: затирает
ручные правки переводов). `ru` всегда синхронизируется с текущим шаблоном.
"""

from django.core.management.base import BaseCommand

from cable_glands.models import CableGlandModelLine
from core.models.equipment_type import EquipmentType
from pneumatic_actuators.models import PneumaticActuatorModelLine


# ── Группы ──
GROUPS_EN = {
    'Основные': 'General',
    'Трубка и давление': 'Tubing and pressure',
    'Присоединения': 'Connections',
    'Дополнительно': 'Additional',
    'Параметры глушителя': 'Silencer parameters',
    'Выбранные опции': 'Selected options',
    'Технические': 'Technical',
    'Присоединение к арматуре': 'Valve connection',
    'Подключения корпуса': 'Body connections',
    'Таблица моментов': 'Torque table',
    'Корпус': 'Body',
    'Условия эксплуатации': 'Operating conditions',
    'Пропускная способность': 'Flow capacity',
    'Давление': 'Pressure',
    'Корпус и материалы': 'Body and materials',
    'Электрические параметры': 'Electrical parameters',
    'Защита': 'Protection',
    'Сигналы': 'Signals',
}

GROUPS_CN = {
    'Основные': '基本参数',
    'Трубка и давление': '气管和压力',
    'Присоединения': '连接',
    'Дополнительно': '附加',
    'Параметры глушителя': '消声器参数',
    'Выбранные опции': '所选选项',
    'Технические': '技术参数',
    'Присоединение к арматуре': '与阀门连接',
    'Подключения корпуса': '壳体连接',
    'Таблица моментов': '扭矩表',
    'Корпус': '壳体',
    'Условия эксплуатации': '使用条件',
    'Пропускная способность': '流通能力',
    'Давление': '压力',
    'Корпус и материалы': '壳体和材料',
    'Электрические параметры': '电气参数',
    'Защита': '防护',
    'Сигналы': '信号',
}

# ── Подписи полей ──
LABELS_EN = {
    'DN, мм': 'DN, mm',
    'Ex': 'Ex',
    'IP': 'IP',
    'Kv, м³/ч': 'Kv, m³/h',
    'P раб.макс, бар': 'Max operating pressure, bar',
    'Артикул': 'Article',
    'Бренд': 'Brand',
    'Вес (кг)': 'Weight (kg)',
    'Вес, кг': 'Weight, kg',
    'Взрывозащита': 'Explosion protection',
    'Взрывозащита (кратко)': 'Explosion protection (short)',
    'Возможности': 'Capabilities',
    'Время зарытия, с': 'Closing time, s',
    'Время открытия, с': 'Opening time, s',
    'Давление мин/макс': 'Pressure min/max',
    'Давление питания, бар': 'Supply pressure, bar',
    'Диаметр кабеля, мм': 'Cable diameter, mm',
    'Диаметр трубки, мм': 'Tube diameter, mm',
    'Диаметр штурвала, мм': 'Handwheel diameter, mm',
    'Диапазон выходного давления, бар': 'Outlet pressure range, bar',
    'Исполнение': 'Version',
    'Класс изоляции': 'Insulation class',
    'Конструкция': 'Design',
    'Крепление МР (код)': 'Metal sleeve mount (code)',
    'МР внеш. ⌀, мм': 'MS outer ⌀, mm',
    'МР внутр. ⌀, мм': 'MS inner ⌀, mm',
    'МР внутр./внеш. ⌀, мм': 'MS inner/outer ⌀, mm',
    'Макс. входное давление, бар': 'Max inlet pressure, bar',
    'Макс. входной момент, Нм': 'Max input torque, Nm',
    'Макс. вязкость, сСт': 'Max viscosity, cSt',
    'Макс. давление, бар': 'Max pressure, bar',
    'Макс. момент на выходе, Нм': 'Max output torque, Nm',
    'Марка материала корпуса': 'Body material grade',
    'Марка соленоида': 'Solenoid grade',
    'Материал кожуха': 'Guard material',
    'Материал корпуса': 'Body material',
    'Материал соленоида': 'Solenoid material',
    'Материал стакана': 'Bowl material',
    'Материал трубки': 'Tube material',
    'Металлорукав': 'Metal sleeve',
    'Механизм блокировки': 'Locking mechanism',
    'Механизм отключения': 'Override mechanism',
    'Мин. давление, бар': 'Min pressure, bar',
    'Монтажные площадки': 'Mounting pads',
    'Мощность номинальная, Вт': 'Rated power, W',
    'Мощность пусковая, Вт': 'Inrush power, W',
    'Мощность удержания, Вт': 'Holding power, W',
    'Назначение': 'Purpose',
    'Напряжение, В': 'Voltage, V',
    'Настенное крепление': 'Wall mounting',
    'Отверстие под кабельный ввод': 'Cable entry hole',
    'Отверстия КВ': 'Cable entries',
    'Отсечной клапан': 'Shut-off valve',
    'Передаточное число': 'Gear ratio',
    'Пневмо вход': 'Air inlet',
    'Пневмо выход': 'Air outlet',
    'Пневмоподключение': 'Pneumatic connection',
    'Пневмопривод': 'Pneumatic actuator',
    'Пневмоприсоединение': 'Pneumatic connection',
    'Покрытие корпуса': 'Body coating',
    'Положение безопасности': 'Fail-safe position',
    'Принцип действия': 'Operating principle',
    'Пропускная способность, Нл/мин': 'Flow capacity, Nl/min',
    'Профиль сигналов': 'Signal profile',
    'Пружины': 'Springs',
    'Р раб., бар': 'Operating pressure, bar',
    'Рабочая среда': 'Working medium',
    'Рабочая температура': 'Operating temperature',
    'Расход воздуха': 'Air consumption',
    'Расход, л/мин': 'Flow rate, l/min',
    'Расцепляемый': 'Declutchable',
    'Резьба': 'Thread',
    'Резьба манометра': 'Gauge port thread',
    'Резьба нар/внутр': 'Thread ext/int',
    'Резьба пневмосоединения': 'Pneumatic connection thread',
    'Резьба портов': 'Port thread',
    'Резьба слива': 'Drain port thread',
    'Ручной дублер': 'Manual override',
    'Ручной дублёр': 'Manual override',
    'Рычаг': 'Lever',
    'Серия': 'Series',
    'Сигнал тревоги': 'Alarm signal',
    'Сигнал тревоги (по ролям)': 'Alarm signal (by role)',
    'Сигналы (по ролям)': 'Signals (by role)',
    'Степень защиты IP': 'IP rating',
    'Схема': 'Function',
    'Т раб., °С': 'Operating temp., °C',
    'Температура, °С': 'Temperature, °C',
    'Температурный диапазон': 'Temperature range',
    'Тип': 'Type',
    'Тип действия': 'Acting type',
    'Тип конструкции': 'Design type',
    'Тип передачи': 'Transmission type',
    'Тип привода': 'Actuator type',
    'Тип фитинга': 'Fitting type',
    'Типы пневмоподключений': 'Pneumatic connection types',
    'Тонкость фильтрации, мкм': 'Filtration rating, µm',
    'Угол поворота': 'Rotation angle',
    'Уплотнение': 'Sealing',
    'Управление': 'Actuation',
    'Уровень шума, дБ': 'Noise level, dB',
    'Фильтрующий элемент': 'Filter element',
    'Форма штока': 'Stem shape',
    'Шток, размер': 'Stem size',
}

LABELS_CN = {
    'DN, мм': 'DN, mm',
    'Ex': 'Ex',
    'IP': 'IP',
    'Kv, м³/ч': 'Kv, m³/h',
    'P раб.макс, бар': '最大工作压力, bar',
    'Артикул': '货号',
    'Бренд': '品牌',
    'Вес (кг)': '重量 (kg)',
    'Вес, кг': '重量, kg',
    'Взрывозащита': '防爆',
    'Взрывозащита (кратко)': '防爆（简写）',
    'Возможности': '功能',
    'Время зарытия, с': '关闭时间, s',
    'Время открытия, с': '开启时间, s',
    'Давление мин/макс': '最小/最大压力',
    'Давление питания, бар': '供气压力, bar',
    'Диаметр кабеля, мм': '电缆直径, mm',
    'Диаметр трубки, мм': '气管直径, mm',
    'Диаметр штурвала, мм': '手轮直径, mm',
    'Диапазон выходного давления, бар': '出口压力范围, bar',
    'Исполнение': '型式',
    'Класс изоляции': '绝缘等级',
    'Конструкция': '结构',
    'Крепление МР (код)': '金属软管固定（代码）',
    'МР внеш. ⌀, мм': '软管外径 ⌀, mm',
    'МР внутр. ⌀, мм': '软管内径 ⌀, mm',
    'МР внутр./внеш. ⌀, мм': '软管内/外径 ⌀, mm',
    'Макс. входное давление, бар': '最大入口压力, bar',
    'Макс. входной момент, Нм': '最大输入扭矩, Nm',
    'Макс. вязкость, сСт': '最大粘度, cSt',
    'Макс. давление, бар': '最大压力, bar',
    'Макс. момент на выходе, Нм': '最大输出扭矩, Nm',
    'Марка материала корпуса': '壳体材料牌号',
    'Марка соленоида': '电磁阀牌号',
    'Материал кожуха': '防护罩材料',
    'Материал корпуса': '壳体材料',
    'Материал соленоида': '电磁阀材料',
    'Материал стакана': '滤杯材料',
    'Материал трубки': '气管材料',
    'Металлорукав': '金属软管',
    'Механизм блокировки': '锁定机构',
    'Механизм отключения': '超越机构',
    'Мин. давление, бар': '最小压力, bar',
    'Монтажные площадки': '安装平台',
    'Мощность номинальная, Вт': '额定功率, W',
    'Мощность пусковая, Вт': '启动功率, W',
    'Мощность удержания, Вт': '保持功率, W',
    'Назначение': '用途',
    'Напряжение, В': '电压, V',
    'Настенное крепление': '壁挂安装',
    'Отверстие под кабельный ввод': '电缆入口孔',
    'Отверстия КВ': '电缆入口',
    'Отсечной клапан': '截止阀',
    'Передаточное число': '传动比',
    'Пневмо вход': '进气口',
    'Пневмо выход': '出气口',
    'Пневмоподключение': '气动连接',
    'Пневмопривод': '气动执行器',
    'Пневмоприсоединение': '气动连接',
    'Покрытие корпуса': '壳体涂层',
    'Положение безопасности': '安全位置',
    'Принцип действия': '工作原理',
    'Пропускная способность, Нл/мин': '流量, Nl/min',
    'Профиль сигналов': '信号配置',
    'Пружины': '弹簧',
    'Р раб., бар': '工作压力, bar',
    'Рабочая среда': '工作介质',
    'Рабочая температура': '工作温度',
    'Расход воздуха': '耗气量',
    'Расход, л/мин': '流量, l/min',
    'Расцепляемый': '可脱离',
    'Резьба': '螺纹',
    'Резьба манометра': '压力表螺纹',
    'Резьба нар/внутр': '外/内螺纹',
    'Резьба пневмосоединения': '气动连接螺纹',
    'Резьба портов': '接口螺纹',
    'Резьба слива': '排水螺纹',
    'Ручной дублер': '手动超越',
    'Ручной дублёр': '手动超越',
    'Рычаг': '杠杆',
    'Серия': '系列',
    'Сигнал тревоги': '报警信号',
    'Сигнал тревоги (по ролям)': '报警信号（按功能）',
    'Сигналы (по ролям)': '信号（按功能）',
    'Степень защиты IP': '防护等级 IP',
    'Схема': '功能',
    'Т раб., °С': '工作温度, °C',
    'Температура, °С': '温度, °C',
    'Температурный диапазон': '温度范围',
    'Тип': '类型',
    'Тип действия': '作用类型',
    'Тип конструкции': '结构类型',
    'Тип передачи': '传动类型',
    'Тип привода': '执行器类型',
    'Тип фитинга': '接头类型',
    'Типы пневмоподключений': '气动连接类型',
    'Тонкость фильтрации, мкм': '过滤精度, µm',
    'Угол поворота': '旋转角度',
    'Уплотнение': '密封',
    'Управление': '控制方式',
    'Уровень шума, дБ': '噪音水平, dB',
    'Фильтрующий элемент': '滤芯',
    'Форма штока': '阀杆形状',
    'Шток, размер': '阀杆, 尺寸',
}


def _translate_template(template, groups, labels, existing=None):
    """RU-шаблон {группа: {подпись: ключ}} → переведённый.

    Незнакомые подписи: если передан ``existing`` (текущий перевод той же
    структуры) — берётся его подпись (позиционно), иначе — ru как есть.
    Так ``--force`` не затирает переводы, которых нет в словаре (напр. БКВ).
    """
    if not isinstance(template, dict):
        return template
    result = {}
    ex_group_keys = list(existing.keys()) if isinstance(existing, dict) else []
    for i, (group, fields) in enumerate(template.items()):
        ex_group = ex_group_keys[i] if i < len(ex_group_keys) else None
        translated_group = groups.get(group) or ex_group or group
        if isinstance(fields, dict):
            ex_fields = None
            if ex_group and isinstance(existing, dict):
                candidate = existing.get(ex_group)
                if isinstance(candidate, dict):
                    ex_fields = candidate
            ex_field_keys = list(ex_fields.keys()) if ex_fields else []
            new_fields = {}
            for j, (label, key) in enumerate(fields.items()):
                ex_label = ex_field_keys[j] if j < len(ex_field_keys) else None
                new_fields[labels.get(label) or ex_label or label] = key
            result[translated_group] = new_fields
        else:
            result[translated_group] = fields
    return result


class Command(BaseCommand):
    help = ('Заполняет en/cn переводы spec_template_i18n для EquipmentType и серий '
            'с собственным spec_template (КВ, ПП).')

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перестроить en/cn заново из RU-шаблона (затирает ручные правки).')
        parser.add_argument('--dry-run', action='store_true',
                            help='Только показать, что будет записано.')

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        targets = (
            list(EquipmentType.objects.all())
            + list(CableGlandModelLine.objects.all())
            + list(PneumaticActuatorModelLine.objects.all())
        )

        updated = 0
        skipped_empty = 0
        missing_en = set()
        missing_cn = set()

        for obj in targets:
            template = obj.spec_template
            if isinstance(template, str):
                import json
                try:
                    template = json.loads(template) if template else {}
                except Exception:
                    continue
            if not isinstance(template, dict) or not template:
                skipped_empty += 1
                continue

            i18n = obj.spec_template_i18n or {}
            if not isinstance(i18n, dict):
                i18n = {}
            changed = False

            if not isinstance(i18n.get('ru'), dict):
                i18n['ru'] = template
                changed = True

            for locale, groups, labels in (
                ('en', GROUPS_EN, LABELS_EN),
                ('cn', GROUPS_CN, LABELS_CN),
            ):
                if force or not isinstance(i18n.get(locale), dict):
                    existing = i18n.get(locale) if force else None
                    i18n[locale] = _translate_template(template, groups, labels, existing=existing)
                    changed = True
                    for group, fields in template.items():
                        if group not in groups:
                            (missing_en if locale == 'en' else missing_cn).add(f'<группа> {group}')
                        if isinstance(fields, dict):
                            for label in fields:
                                if label not in labels:
                                    (missing_en if locale == 'en' else missing_cn).add(label)

            if not changed:
                continue

            obj.spec_template_i18n = i18n
            updated += 1
            if not dry_run:
                obj.save()

        self.stdout.write(self.style.SUCCESS(
            f'{("DRY-RUN " if dry_run else "")}обновлено: {updated}, без шаблона: {skipped_empty}'
        ))
        if missing_en:
            self.stdout.write(self.style.WARNING(
                f'EN без перевода (fallback ru): {sorted(missing_en)}'
            ))
        if missing_cn:
            self.stdout.write(self.style.WARNING(
                f'CN без перевода (fallback ru): {sorted(missing_cn)}'
            ))
