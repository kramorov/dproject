# Fix AITokenUsage fields: rename token fields + add customer, latency_ms
# Also add avg_latency_ms + latency_sample_count to PipelineSkill

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0011_rename_stepconfig_to_pipelineskill'),
        ('project_customers', '__first__'),
    ]

    operations = [
        # -- AITokenUsage: rename old fields to abbreviated names (preserve data) --
        migrations.RenameField(
            model_name='aitokenusage',
            old_name='prompt_tokens',
            new_name='pt',
        ),
        migrations.RenameField(
            model_name='aitokenusage',
            old_name='completion_tokens',
            new_name='ct',
        ),
        migrations.RenameField(
            model_name='aitokenusage',
            old_name='reasoning_tokens',
            new_name='rt',
        ),
        migrations.RenameField(
            model_name='aitokenusage',
            old_name='total_tokens',
            new_name='tt',
        ),
        migrations.RenameField(
            model_name='aitokenusage',
            old_name='cost_estimate',
            new_name='cost',
        ),
        # -- AITokenUsage: add new fields --
        migrations.AddField(
            model_name='aitokenusage',
            name='customer',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=models.SET_NULL,
                related_name='token_usages',
                to='project_customers.projectcustomer',
            ),
        ),
        migrations.AddField(
            model_name='aitokenusage',
            name='lat',
            field=models.IntegerField(
                blank=True, null=True,
                help_text='LLM call latency (ms)',
            ),
        ),
        # -- PipelineSkill: add latency tracking fields --
        migrations.AddField(
            model_name='pipelineskill',
            name='avg_latency_ms',
            field=models.IntegerField(
                blank=True, null=True,
                help_text='Rolling average LLM latency (ms), last 5 samples',
            ),
        ),
        migrations.AddField(
            model_name='pipelineskill',
            name='latency_sample_count',
            field=models.IntegerField(
                default=0,
                help_text='Number of samples in rolling average',
            ),
        ),
    ]
