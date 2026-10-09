from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pneumatic_fittings', '0030_pneumaticfitting_weight_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pneumaticfittingmodelline',
            name='pressure_max',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Максимальное рабочее давление, бар', max_digits=6, null=True, verbose_name='P раб.макс, бар'),
        ),
        migrations.AddField(
            model_name='pneumaticfittingmodelline',
            name='pressure_min',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Минимальное рабочее давление, бар', max_digits=6, null=True, verbose_name='P раб.мин, бар'),
        ),
        migrations.AddField(
            model_name='pneumaticfittingmodelline',
            name='temp_max',
            field=models.SmallIntegerField(blank=True, help_text='Максимальная температура окружающей среды', null=True, verbose_name='Темп.макс'),
        ),
        migrations.AddField(
            model_name='pneumaticfittingmodelline',
            name='temp_min',
            field=models.SmallIntegerField(blank=True, help_text='Минимальная температура окружающей среды', null=True, verbose_name='Темп.мин'),
        ),
        migrations.AddField(
            model_name='pneumaticplugmodelline',
            name='pressure_max',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Максимальное рабочее давление, бар', max_digits=6, null=True, verbose_name='P раб.макс, бар'),
        ),
        migrations.AddField(
            model_name='pneumaticplugmodelline',
            name='pressure_min',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Минимальное рабочее давление, бар', max_digits=6, null=True, verbose_name='P раб.мин, бар'),
        ),
        migrations.AddField(
            model_name='pneumaticplugmodelline',
            name='temp_max',
            field=models.SmallIntegerField(blank=True, help_text='Максимальная температура окружающей среды', null=True, verbose_name='Темп.макс'),
        ),
        migrations.AddField(
            model_name='pneumaticplugmodelline',
            name='temp_min',
            field=models.SmallIntegerField(blank=True, help_text='Минимальная температура окружающей среды', null=True, verbose_name='Темп.мин'),
        ),
        migrations.AddField(
            model_name='pneumaticsilencermodelline',
            name='pressure_max',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Максимальное рабочее давление, бар', max_digits=6, null=True, verbose_name='P раб.макс, бар'),
        ),
        migrations.AddField(
            model_name='pneumaticsilencermodelline',
            name='pressure_min',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Минимальное рабочее давление, бар', max_digits=6, null=True, verbose_name='P раб.мин, бар'),
        ),
        migrations.AddField(
            model_name='pneumaticsilencermodelline',
            name='temp_max',
            field=models.SmallIntegerField(blank=True, help_text='Максимальная температура окружающей среды', null=True, verbose_name='Темп.макс'),
        ),
        migrations.AddField(
            model_name='pneumaticsilencermodelline',
            name='temp_min',
            field=models.SmallIntegerField(blank=True, help_text='Минимальная температура окружающей среды', null=True, verbose_name='Темп.мин'),
        ),
        migrations.AlterField(
            model_name='pneumaticsilencer',
            name='pressure_max',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Переопределение максимального давления для позиции. 0 или пусто — берётся значение серии.', max_digits=6, null=True, verbose_name='P раб.макс (override), бар'),
        ),
    ]
