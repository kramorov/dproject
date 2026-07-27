# Populate AIPromptTemplate.code for existing rows before making it non-nullable.

from django.db import migrations, models


def populate_codes(apps, schema_editor):
    AIPromptTemplate = apps.get_model('ai_assistant', 'AIPromptTemplate')
    for tmpl in AIPromptTemplate.objects.filter(code__isnull=True):
        tmpl.code = f"tmpl_{tmpl.id}"
        tmpl.save(update_fields=['code'])


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0009_add_code_to_prompt_and_stepconfig'),
    ]

    operations = [
        migrations.RunPython(populate_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='aiprompttemplate',
            name='code',
            field=models.CharField(
                db_index=True,
                help_text=(
                    "Уникальный код шаблона для подстановки в другие шаблоны через {code}. "
                    "Пример: 'system_prompt', 'decompose_v2', 'extract_actuator'. "
                    "Используется в template_text других промптов для композиции."
                ),
                max_length=64,
                unique=True,
            ),
        ),
    ]
