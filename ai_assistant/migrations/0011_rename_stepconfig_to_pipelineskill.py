# Rename StepConfig → PipelineSkill, StepConfigOverride → SkillOverride.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0010_populate_prompt_codes'),
        ('project_customers', '__first__'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='StepConfig',
            new_name='PipelineSkill',
        ),
        migrations.RenameModel(
            old_name='StepConfigOverride',
            new_name='SkillOverride',
        ),
    ]
