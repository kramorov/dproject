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
    ('Блоки концевых выключателей', 'Limit switch boxes', '限位开关盒'),
    ('Кабельные вводы', 'Cable glands', '电缆接头'),
    ('Кабельный ввод', 'Cable gland', '电缆接头'),
    ('монтажная площадка', 'mounting pad', '安装平台'),
    ('ручной редуктор', 'manual gearbox', '手动减速器'),
    ('пневмоприводы', 'pneumatic actuators', '气动执行器'),
    ('пневмопривод', 'pneumatic actuator', '气动执行器'),
    ('Позиционеры', 'Positioners', '定位器'),
    ('Изображение', 'Image', '图片'),
    ('Техничка', 'Tech doc', '技术文档'),
    ('Сертификат', 'Certificate', '证书'),
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
    ('на пневмоприводы', 'for pneumatic actuators', '用于气动执行器'),
    ('на блоки концевых выключателей', 'for limit switch boxes', '用于限位开关盒'),
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

    def handle(self, *args, **options):
        total = 0
        for app_label, model_name in [('media_library', 'MediaLibraryItem'), ('cert_doc', 'CertData')]:
            Model = apps.get_model(app_label, model_name)
            updated = 0
            for obj in Model.objects.all():
                name = obj.name or ''
                if not name.strip():
                    continue
                i18n = dict(obj.name_i18n or {})
                i18n['en'] = translate_name(name, 'en')
                i18n['cn'] = translate_name(name, 'cn')
                obj.name_i18n = i18n
                obj.save(update_fields=['name_i18n'])
                updated += 1
            if updated:
                total += updated
                self.stdout.write(f'{app_label}.{model_name}: {updated}')
        self.stdout.write(self.style.SUCCESS(f'Done. Translated rows: {total}'))
