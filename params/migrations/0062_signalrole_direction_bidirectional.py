# Generated manually — add bidirectional choice to SignalRole.direction

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('params', '0061_add_input_signal_descriptions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='signalrole',
            name='direction',
            field=models.CharField(
                choices=[
                    ('input', 'Входной (команда приводу)'),
                    ('output', 'Выходной (от привода)'),
                    ('bidirectional', 'Двунаправленный'),
                ],
                default='output',
                help_text='Входной — команда приводу от контроллера. Выходной — обратная связь от привода. Двунаправленный — например, 4-20мА+HART.',
                max_length=15,
                verbose_name='Направление сигнала',
            ),
        ),
    ]
