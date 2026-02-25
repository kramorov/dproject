# options/migrations/0002_create_cablegland_through_model.py
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('options', '0001_cablegland_through_model'),
        ('electric_actuators', '0029_alter_electricactuatormodelline_description_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CableGlandHolesSetThroughOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('encoding', models.CharField(blank=True, help_text='Код опции для подстановки в артикул', max_length=50, verbose_name='Кодировка')),
                ('description', models.TextField(blank=True, help_text='Дополнительное описание этой опции', verbose_name='Описание')),
                ('sorting_order', models.IntegerField(default=0, verbose_name='Порядок сортировки')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('is_default', models.BooleanField(default=False, help_text='Является ли эта опция стандартной для серии', verbose_name='Стандартная опция')),
                ('cg_set', models.ForeignKey(help_text='Отверстия под кабельные вводы', on_delete=django.db.models.deletion.CASCADE, to='electric_actuators.cableglandholesset', verbose_name='Отверстия под КВ')),
            ],
            options={
                'verbose_name': 'Опция кабельных вводов',
                'verbose_name_plural': 'Опции кабельных вводов',
                'ordering': ['sorting_order'],
                'abstract': False,
            },
        ),
    ]