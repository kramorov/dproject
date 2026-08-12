"""
Загружает начальные промпты и схемы из SCHEMA_REGISTRY в БД (AIPromptTemplate).

Использование:
    python manage.py seed_ai_prompts
    python manage.py seed_ai_prompts --force  # перезаписать существующие
"""
from django.core.management.base import BaseCommand

from ai_assistant.schemas import SCHEMA_REGISTRY
from ai_assistant.schemas.actuator_selection import ACTUATOR_SELECTION_SCHEMA, ACTUATOR_SELECTION_PROMPT_TEMPLATE
from ai_assistant.schemas.decompose import SYSTEM_PROMPT_ABRA, SYSTEM_PROMPT_DEFAULT, DECOMPOSE_PROMPT_TEMPLATE
from ai_assistant.models import AIPromptTemplate


class Command(BaseCommand):
    help = "Seed AIPromptTemplate from SCHEMA_REGISTRY"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Overwrite existing templates")

    def handle(self, *args, **options):
        force = options["force"]
        created = 0
        updated = 0

        templates = [
            {
                "name": "actuator_selection",
                "version": "1",
                "intent": "actuator_selection",
                "schema_name": "actuator_selection",
                "description": "Извлечение параметров для подбора пневмопривода",
                "template_text": ACTUATOR_SELECTION_PROMPT_TEMPLATE,
                "schema_json": ACTUATOR_SELECTION_SCHEMA,
            },
            {
                "name": "decompose",
                "version": "1",
                "intent": "decompose",
                "schema_name": "decompose",
                "description": "Pass 0: текстовый анализ запроса",
                "template_text": DECOMPOSE_PROMPT_TEMPLATE,
                "schema_json": None,
            },
            {
                "name": "system_prompt",
                "version": "default",
                "intent": "",
                "schema_name": "",
                "description": "Системный промпт по умолчанию",
                "template_text": SYSTEM_PROMPT_DEFAULT,
                "schema_json": None,
            },
            {
                "name": "system_prompt",
                "version": "abra",
                "intent": "",
                "schema_name": "",
                "description": "Системный промпт для партнёров ABRA (ограниченная номенклатура)",
                "template_text": SYSTEM_PROMPT_ABRA,
                "schema_json": None,
            },
        ]

        for tmpl_data in templates:
            existing = AIPromptTemplate.objects.filter(
                name=tmpl_data["name"], version=tmpl_data["version"]
            ).first()

            if existing and not force:
                self.stdout.write(f"Skipping {tmpl_data['name']} v{tmpl_data['version']} (exists, use --force)")
                continue

            if existing and force:
                for k, v in tmpl_data.items():
                    setattr(existing, k, v)
                existing.save()
                updated += 1
                self.stdout.write(f"Updated {tmpl_data['name']} v{tmpl_data['version']}")
            else:
                AIPromptTemplate.objects.create(**tmpl_data)
                created += 1
                self.stdout.write(f"Created {tmpl_data['name']} v{tmpl_data['version']}")

        self.stdout.write(self.style.SUCCESS(f"Done: {created} created, {updated} updated"))
