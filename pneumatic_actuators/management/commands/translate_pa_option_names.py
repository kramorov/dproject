"""
python manage.py translate_pa_option_names [--force]

Заполняет name_i18n (ru/en/cn) у through-опций пневмоприводов (fill-missing;
--force — перезаписать все локали).

en/cn строятся из локализованных имён справочников (localized_name) + служебные
слова (localize_service_word: «(Стандарт)»/«(Опция)»/«Не указано» и т.д.).
"""
from django.apps import apps
from django.core.management.base import BaseCommand

from core.utils.localization import localized_name, localize_service_word

# (путь модели, ref-поле для локализации имени справочника; None — только служебные слова;
#  'display_locale' — у модели есть get_display_name(locale))
MODEL_CONFIGS = [
    ('pneumatic_actuators.PneumaticTemperatureOption', None),
    ('pneumatic_actuators.PneumaticIpOption', 'ip_option'),
    ('pneumatic_actuators.PneumaticExdOption', None),
    ('pneumatic_actuators.PneumaticBodyDesignOption', 'display_locale'),
    ('pneumatic_actuators.PneumaticBodyColorOption', 'color_option'),
    ('pneumatic_actuators.PneumaticSafetyPositionOption', 'safety_position'),
    ('pneumatic_actuators.PneumaticSpringsQtyOption', 'springs_qty'),
    ('pneumatic_actuators.PneumaticManualOverrideOption', 'hand_wheel_option'),
]


def _translate_with_ref(obj, ref_field, locale):
    """Локализовать имя через-опции: имя справочника из ru-строки → перевод + служебные слова."""
    ru = str(obj)
    ref = getattr(obj, ref_field, None)
    if ref is not None:
        ru_ref = getattr(ref, 'name', '') or str(ref)
        loc_ref = localized_name(ref, locale)
        if ru_ref and loc_ref and ru_ref != loc_ref and ru_ref in ru:
            ru = ru.replace(ru_ref, loc_ref)
    return localize_service_word(ru, locale)


def _translate(obj, ref_field, locale):
    if ref_field == 'display_locale':
        try:
            return localize_service_word(obj.get_display_name(locale), locale)
        except TypeError:
            return localize_service_word(str(obj), locale)
    if ref_field:
        return _translate_with_ref(obj, ref_field, locale)
    return localize_service_word(str(obj), locale)


class Command(BaseCommand):
    help = 'Заполнить name_i18n (ru/en/cn) у through-опций пневмоприводов'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перезаписать существующие переводы')

    def handle(self, **options):
        force = options['force']
        filled = 0
        no_translation = 0

        for model_path, ref_field in MODEL_CONFIGS:
            model = apps.get_model(*model_path.rsplit('.', 1))
            for obj in model.objects.all():
                ru = str(obj)
                i18n = dict(obj.name_i18n or {})
                changed = False
                if not i18n.get('ru') or force:
                    if ru:
                        i18n['ru'] = ru
                        changed = True
                for loc in ('en', 'cn'):
                    if not i18n.get(loc) or force:
                        translated = _translate(obj, ref_field, loc)
                        i18n[loc] = translated
                        changed = True
                if changed:
                    model.objects.filter(pk=obj.pk).update(name_i18n=i18n)
                    filled += 1
                else:
                    no_translation += 1

        self.stdout.write(self.style.SUCCESS(
            f'Готово: заполнено {filled}, пропущено (без изменений) {no_translation}'))
