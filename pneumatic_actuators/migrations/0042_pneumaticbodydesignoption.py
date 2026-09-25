# Replace PneumaticBodyCoatingOption with PneumaticBodyDesignOption.
#
# Order matters: the data migration runs before the FKs are repointed and before
# the old model is dropped, so the RunPython can read the old rows and remap the
# selected_body_coating FKs to the new rows. SQLite FK enforcement is disabled
# for the duration of the migration and re-checked only at the very end.

import django.db.models.deletion
from django.db import migrations, models


def migrate_body_coating_to_design(apps, schema_editor):
    OldCoating = apps.get_model('pneumatic_actuators', 'PneumaticBodyCoatingOption')
    NewDesign = apps.get_model('pneumatic_actuators', 'PneumaticBodyDesignOption')
    Selected = apps.get_model('pneumatic_actuators', 'PneumaticActuatorSelected')
    Constructor = apps.get_model('pneumatic_actuators', 'PneumaticActuatorConstructor')

    old_to_new = {}   # old through id -> new design id
    key_to_new = {}   # (model_line_id, body_coating_option_id) -> new design id

    for old in OldCoating.objects.select_related('body_coating_option').all():
        new = NewDesign.objects.create(
            model_line_id=old.model_line_id,
            body_material_id=None,
            body_coating=(old.body_coating_option.name if old.body_coating_option else ''),
            body_color_id=None,
            encoding=old.encoding or '',
            description=old.description or '',
            sorting_order=old.sorting_order,
            is_active=old.is_active,
            is_default=old.is_default,
        )
        old_to_new[old.id] = new.id
        key_to_new[(old.model_line_id, old.body_coating_option_id)] = new.id

    # Selected.selected_body_coating referenced the old through model directly.
    for sel in Selected.objects.all():
        if sel.selected_body_coating_id in old_to_new:
            sel.selected_body_coating_id = old_to_new[sel.selected_body_coating_id]
            sel.save(update_fields=['selected_body_coating'])

    # Constructor.selected_body_coating referenced params.BodyCoatingOption (master).
    for con in Constructor.objects.select_related('selected_model_line_item').all():
        if not con.selected_body_coating_id:
            continue
        ml_id = con.selected_model_line_item.model_line_id if con.selected_model_line_item else None
        key = (ml_id, con.selected_body_coating_id)
        if key in key_to_new:
            con.selected_body_coating_id = key_to_new[key]
            con.save(update_fields=['selected_body_coating'])


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0008_alter_materialgeneral_options_and_more'),
        ('params', '0069_add_way_switch_x2_role'),
        ('pneumatic_actuators', '0041_alter_pneumaticactuatorconstructionvariety_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='PneumaticBodyDesignOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('encoding', models.CharField(blank=True, help_text='Код опции для подстановки в артикул', max_length=50, verbose_name='Кодировка')),
                ('description', models.TextField(blank=True, help_text='Дополнительное описание этой опции', verbose_name='Описание')),
                ('sorting_order', models.IntegerField(default=0, verbose_name='Порядок сортировки')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('is_default', models.BooleanField(default=False, help_text='Является ли эта опция стандартной для серии', verbose_name='Стандартная опция')),
                ('body_coating', models.CharField(blank=True, max_length=250, verbose_name='Покрытие корпуса')),
                ('body_color', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pa_body_design_colors', to='params.bodycolor', verbose_name='Цвет корпуса')),
                ('body_material', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pa_body_design_materials', to='materials.materialgeneral', verbose_name='Материал корпуса')),
                ('model_line', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='body_design_options', to='pneumatic_actuators.pneumaticactuatormodelline', verbose_name='Серия пневмоприводов')),
            ],
            options={
                'verbose_name': 'Исполнение корпуса пневмопривода',
                'verbose_name_plural': 'Исполнения корпуса пневмоприводов',
                'ordering': ['is_default', 'sorting_order'],
                'unique_together': {('model_line', 'encoding')},
            },
        ),
        migrations.RunPython(migrate_body_coating_to_design, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='pneumaticactuatorconstructor',
            name='selected_body_coating',
            field=models.ForeignKey(blank=True, help_text='Выбранное исполнение корпуса (материал/покрытие/цвет)', null=True, on_delete=django.db.models.deletion.SET_NULL, to='pneumatic_actuators.pneumaticbodydesignoption', verbose_name='Исполнение корпуса'),
        ),
        migrations.AlterField(
            model_name='pneumaticactuatoritem',
            name='selected_body_coating',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pa_items_coating', to='pneumatic_actuators.pneumaticbodydesignoption', verbose_name='Исполнение корпуса'),
        ),
        migrations.AlterField(
            model_name='pneumaticactuatorselected',
            name='selected_body_coating',
            field=models.ForeignKey(blank=True, help_text='Выбранное исполнение корпуса (материал/покрытие/цвет)', null=True, on_delete=django.db.models.deletion.SET_NULL, to='pneumatic_actuators.pneumaticbodydesignoption', verbose_name='Исполнение корпуса'),
        ),
        migrations.DeleteModel(
            name='PneumaticBodyCoatingOption',
        ),
    ]
