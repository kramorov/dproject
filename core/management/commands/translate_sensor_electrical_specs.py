"""Заполняет en/cn переводы поля electrical_specs датчиков (БКВ).

Поле electrical_specs (RU, CharField) остаётся рабочим; рядом
``electrical_specs_i18n`` (JSON) хранит переводы по общему паттерну
``{"ru": ..., "en": ..., "cn": ...}``.

Идемпотентна: перезаписывает en/cn (ru синхронизируется миксином при save).
"""
from django.core.management.base import BaseCommand
from django.apps import apps

from core.utils.localization import localize_service_word

# RU-строка electrical_specs → (en, cn)
TRANSLATIONS = {
    '250 В (AC) / 0.25 А (опц. 60 В / 1.5 А)': ('250 V (AC) / 0.25 A (opt. 60 V / 1.5 A)', '250 V (AC) / 0.25 A（可选 60 V / 1.5 A）'),
    '~250В AC / 5А или 24В DC / 1А': ('~250 V AC / 5 A or 24 V DC / 1 A', '~250 V AC / 5 A 或 24 V DC / 1 A'),
    '8,2 В DC / выходной сигнал на включение >1,8 мА, выходной сигнал на отключение ≤1,5 мА': ('8.2 V DC / output signal ON >1.8 mA, output signal OFF ≤1.5 mA', '8.2 V DC / 接通输出信号 >1.8 mA，断开输出信号 ≤1.5 mA'),
    '8.5-34 В / 4-20 мА': ('8.5–34 V / 4–20 mA', '8.5–34 V / 4–20 mA'),
    'до 250 В / до 15 А': ('up to 250 V / up to 15 A', '至 250 V / 至 15 A'),
    '8.2 В (NAMUR)': ('8.2 V (NAMUR)', '8.2 V (NAMUR)'),
    '8.2 В / OFF ≤1 мА / ON >3 мА': ('8.2 V / OFF ≤1 mA / ON >3 mA', '8.2 V / OFF ≤1 mA / ON >3 mA'),
    '10…30 В (DC) / 0…100 мА': ('10…30 V (DC) / 0…100 mA', '10…30 V (DC) / 0…100 mA'),
    '230В(10А) / 24В(3А) / Пуск. 36А': ('230 V (10 A) / 24 V (3 A) / inrush 36 A', '230 V（10 A）/ 24 V（3 A）/ 浪涌 36 A'),
    '230В (0.2А) / 24В (2А) / макс. 250В': ('230 V (0.2 A) / 24 V (2 A) / max. 250 V', '230 V（0.2 A）/ 24 V（2 A）/ 最大 250 V'),
    'Активный токовый сигнал 4–20 мА; номинальное напряжение цепи 24 В пост. тока; максимальное сопротивление нагрузки (включая линию связи) — 500 Ом': ('Active current signal 4–20 mA; rated circuit voltage 24 V DC; max. load resistance (incl. line) — 500 Ω', '有源电流信号 4–20 mA；额定回路电压 24 V DC；最大负载电阻（含线路）— 500 Ω'),
    'Активный омический сигнал 0–1 кОм; максимальное измерительное сопротивление (включая линию связи) — 1000 Ом': ('Active resistive signal 0–1 kΩ; max. measurement resistance (incl. line) — 1000 Ω', '有源电阻信号 0–1 kΩ；最大测量电阻（含线路）— 1000 Ω'),
    'Пассивный токовый сигнал 4–20 мА (требует внешнего питания токовой петли); номинальное напряжение измерительной цепи до 30 В пост. тока (определяется внешним источником); максимальное сопротивление нагрузки зависит от напряжения внешнего питания': ('Passive current signal 4–20 mA (requires external loop power); rated measurement-circuit voltage up to 30 V DC (determined by external source); max. load resistance depends on external supply voltage', '无源电流信号 4–20 mA（需要外部回路供电）；额定测量回路电压至 30 V DC（由外部源决定）；最大负载电阻取决于外部供电电压'),
    '4-20 мА DC, 2-проводное подключение': ('4–20 mA DC, 2-wire connection', '4–20 mA DC，两线制连接'),
    'SPDT (перекидной контакт)': ('SPDT (change-over contact)', 'SPDT（转换触点）'),
    'Пассивный токовый сигнал (требует внешнего питания токовой петли); номинальное напряжение измерительной цепи 9-28 В пост. тока (определяется внешним источником); сопротивление нагрузки задается пользователем. Сигнал "Закрыто" - ток менее 1мА, сигнал "Открыто" - ток более 3мА': ('Passive current signal (requires external loop power); rated measurement-circuit voltage 9–28 V DC (determined by external source); load resistance set by user. "Closed" signal — current below 1 mA, "Open" signal — current above 3 mA', '无源电流信号（需要外部回路供电）；额定测量回路电压 9–28 V DC（由外部源决定）；负载电阻由用户设置。“关闭”信号 — 电流低于 1 mA，“打开”信号 — 电流高于 3 mA'),
    '~ 250 В - до 15 А; 24VDC до 3 А': ('~ 250 V — up to 15 A; 24 V DC up to 3 A', '~ 250 V — 至 15 A；24 V DC 至 3 A'),
}


class Command(BaseCommand):
    help = 'Backfill en/cn translations for SensorComponent.electrical_specs.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перезаписать существующие переводы (затирает ручные правки).')

    def handle(self, *args, **options):
        force = options['force']
        Sensor = apps.get_model('pa_controls', 'SensorComponent')
        updated = 0
        for obj in Sensor.objects.all():
            ru = obj.electrical_specs or ''
            if not ru.strip():
                continue
            en, cn = TRANSLATIONS.get(ru, (None, None))
            if not en:
                en = localize_service_word(ru, 'en')
                cn = localize_service_word(ru, 'cn')
            i18n = dict(obj.electrical_specs_i18n or {})
            changed = False
            for locale, value in (('en', en), ('cn', cn)):
                if force or locale not in i18n:
                    i18n[locale] = value
                    changed = True
            if changed:
                obj.electrical_specs_i18n = i18n
                obj.save(update_fields=['electrical_specs_i18n'])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f'Translated sensors: {updated}'))
