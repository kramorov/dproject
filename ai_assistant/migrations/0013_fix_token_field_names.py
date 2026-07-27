# Rename AITokenUsage abbreviated fields back to proper names.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0012_fix_token_usage_fields'),
    ]

    operations = [
        migrations.RenameField(model_name='aitokenusage', old_name='pt', new_name='prompt_tokens'),
        migrations.RenameField(model_name='aitokenusage', old_name='ct', new_name='completion_tokens'),
        migrations.RenameField(model_name='aitokenusage', old_name='rt', new_name='reasoning_tokens'),
        migrations.RenameField(model_name='aitokenusage', old_name='tt', new_name='total_tokens'),
        migrations.RenameField(model_name='aitokenusage', old_name='cost', new_name='cost_estimate'),
        migrations.RenameField(model_name='aitokenusage', old_name='lat', new_name='latency_ms'),
    ]
