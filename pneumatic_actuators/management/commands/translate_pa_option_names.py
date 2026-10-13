"""
python manage.py translate_pa_option_names [--force]

УСТАРЕЛО (2026-10-13): through-опции ПП больше не хранят переводы в ``name_i18n`` —
локализованное имя собирается на лету из справочника (reference-опции) или
derived-полей (get_display_name / localize_service_word), а суффикс
«(Стандарт)/(Опция)» добавляется автоматически в ``localized_name()``.

Команда оставлена как no-op для совместимости со старыми сценариями.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'УСТАРЕЛО: through-опции ПП больше не заполняют name_i18n (no-op)'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Перезаписать существующие переводы')

    def handle(self, **options):
        self.stdout.write(self.style.WARNING(
            'Команда устарела: name_i18n у through-опций ПП больше не используется. '
            'Локализация идёт через справочники/derived-поля в localized_name().'))
