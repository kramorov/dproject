"""
Management command: предзагрузка ONNX-моделей RapidOCR (детекция + классификация +
распознавание) в каталог моделей.

Использование:
    python manage.py preload_ocr_models                  # eslav (кириллица), по умолчанию
    python manage.py preload_ocr_models --lang=cyrillic  # другая rec-модель

Зачем: при переносе в Docker модели можно скачать на этапе сборки или первого
старта, чтобы они лежали в volume (см. настройку MEDIA_OCR_MODEL_DIR / env
MEDIA_OCR_MODEL_DIR) и не качались из сети при каждом распознавании.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from media_library.table_extractor import _rapidocr_params


class Command(BaseCommand):
    help = 'Скачивает ONNX-модели RapidOCR (det/cls/rec) в каталог моделей'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lang',
            type=str,
            default='eslav',
            help='Язык rec-модели: eslav (рус/укр/бел, по умолчанию) или cyrillic.',
        )

    def handle(self, *args, **options):
        lang = (options.get('lang') or 'eslav').strip().lower()

        from rapidocr import RapidOCR

        params = _rapidocr_params(**{'Rec.lang_type': lang})
        model_dir = params.get('Global.model_root_dir') or getattr(
            settings, 'MEDIA_OCR_MODEL_DIR', None
        )

        self.stdout.write(f'Загрузка моделей RapidOCR (Rec.lang_type={lang})…')
        RapidOCR(params=params)
        self.stdout.write(
            self.style.SUCCESS(
                f'Готово. Модели: {model_dir or "site-packages/rapidocr/models"}'
            )
        )
