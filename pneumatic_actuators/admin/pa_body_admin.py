from django import forms
from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path , reverse
from django.utils.translation import gettext_lazy as _

import logging


logger = logging.getLogger(__name__)


from pneumatic_actuators.models import BodyThrustTorqueTable
from pneumatic_actuators.models.pa_body import (
    PneumaticActuatorBodyTable ,
    PneumaticActuatorBody , PneumaticCloseTimeParameter , PneumaticWeightParameter
)

class PneumaticWeightParameterInline(admin.TabularInline):
    model = PneumaticWeightParameter
    extra = 0
    min_num = 1  # ← ДОБАВЬТЕ ЭТУ СТРОКУ
    ordering = ['spring_qty']
    fields = ['spring_qty', 'weight']
    verbose_name = _("Вес")
    verbose_name_plural = _("Вес")

class PneumaticCloseTimeParameterInline(admin.TabularInline):
    model = PneumaticCloseTimeParameter
    extra = 0
    ordering = ['spring_qty']
    fields = ['spring_qty', 'time_open','time_close']
    verbose_name = _("Время открытия/закрытия")
    verbose_name_plural = _("Время открытия/закрытия")


@admin.register(PneumaticActuatorBodyTable)
class PneumaticActuatorBodyTableAdmin(admin.ModelAdmin) :
    """Админка для таблиц корпусов пневмоприводов"""

    list_display = ('name' ,  'related_bodies_display' , 'sorting_order' , 'is_active')
    list_editable = ('sorting_order' , 'is_active')
    list_filter = ('is_active' ,)
    search_fields = ('name' , 'code' , 'description')
    ordering = ('sorting_order' ,)

    fieldsets = (
        (_('Основная информация') , {
            'fields' : ('name' , 'code' , 'description')
        }) ,
        (_('Связанные корпуса') , {
            'fields' : ('related_bodies_display' ,) ,  # ← новая секция
            'classes' : ('collapse' ,)
        }) ,
        (_('Настройки') , {
            'fields' : ('sorting_order' , 'is_active')
        }) ,
    )

    def get_queryset(self , request) :
        """Оптимизация запросов"""
        return super().get_queryset(request).prefetch_related('model_body_body_table')

    readonly_fields = ('related_bodies_display' ,)  # ← поле только для чтения

    def export_torque_data(self , request , object_id) :
        """
        Экспорт данных моментов/усилий для корпусов этой таблицы
        """
        from django.http import HttpResponse
        from django.shortcuts import redirect
        from pneumatic_actuators.models.pa_body import PneumaticActuatorBody
        import os
        from datetime import datetime

        # Получаем таблицу корпусов
        body_table = self.get_object(request , object_id)

        if not body_table :
            self.message_user(request , _("Таблица корпусов не найдена") , level='error')
            return redirect('admin:pneumatic_actuators_pneumaticactuatorbodytable_changelist')

        # Получаем все корпуса этой таблицы
        bodies = body_table.model_body_body_table.filter(is_active=True)

        if not bodies :
            self.message_user(request , _("Нет корпусов для экспорта в этой таблице") , level='error')
            return redirect('admin:pneumatic_actuators_pneumaticactuatorbodytable_changelist')

        try :
            # Экспортируем данные используя статический метод из модели BodyThrustTorqueTable
            output_path = BodyThrustTorqueTable.export_table_template(
                pressure_min=2.5 ,
                pressure_max=8.0 ,
                springs_min=5 ,
                springs_max=12 ,
                output_path=f"torque_export_{body_table.code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )

            # Читаем файл и возвращаем как HTTP response
            with open(output_path , 'rb') as f :
                response = HttpResponse(
                    f.read() ,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(output_path)}"'

            # Удаляем временный файл
            os.unlink(output_path)

            self.message_user(
                request ,
                _(f"Данные моментов/усилий для таблицы '{body_table.name}' успешно экспортированы") ,
                level='success'
            )
            return response

        except Exception as e :
            logger.error(f"Error in export_torque_data: {e}")
            self.message_user(request , _(f"Ошибка при экспорте: {str(e)}") , level='error')
            return redirect('admin:pneumatic_actuators_pneumaticactuatorbodytable_change' , object_id=object_id)

    def import_torque_data(self , request) :
        """
        Импорт данных моментов/усилий из Excel
        """
        from django import forms
        from django.shortcuts import render

        class ImportForm(forms.Form) :
            excel_file = forms.FileField(label='Excel файл')

        if request.method == 'POST' :
            form = ImportForm(request.POST , request.FILES)
            if form.is_valid() :
                try :
                    # Сохраняем временный файл
                    import tempfile
                    import os

                    with tempfile.NamedTemporaryFile(delete=False , suffix='.xlsx') as tmp_file :
                        for chunk in request.FILES['excel_file'].chunks() :
                            tmp_file.write(chunk)
                        tmp_path = tmp_file.name

                    # Импортируем данные
                    imported_count , errors = BodyThrustTorqueTable.import_from_excel(tmp_path)

                    # Удаляем временный файл
                    os.unlink(tmp_path)

                    if errors :
                        for error in errors :
                            self.message_user(request , error , level='error')

                    self.message_user(
                        request ,
                        f"Импорт завершен. Успешно импортировано записей: {imported_count}" ,
                        level='success' if not errors else 'warning'
                    )

                except Exception as e :
                    self.message_user(request , f"Ошибка при импорте: {str(e)}" , level='error')
        else :
            form = ImportForm()

        return render(request , 'admin/pneumatic_actuators/import_torque.html' , {
            'form' : form ,
            'title' : 'Импорт данных моментов/усилий'
        })

    def get_urls(self) :
        """Добавляем URL для экспорта и импорта данных"""
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path('import-torque/' , self.admin_site.admin_view(self.import_torque_data) ,
                 name='pneumatic_actuators_bodythrusttorquetable_import') ,
            path('<path:object_id>/export-torque/' , self.admin_site.admin_view(self.export_torque_data) ,
                 name='pneumatic_actuators_bodythrusttorquetable_export_torque') ,
        ]
        logger.info(f"Registered custom URLs: {custom_urls}")
        return custom_urls + urls

    def change_view(self , request , object_id , form_url='' , extra_context=None) :
        """Добавляем кнопки экспорта и импорта в форму редактирования"""
        logger.info(f"change_view called for object_id: {object_id}")
        logger.info(f"Request path: {request.path}")

        extra_context = extra_context or {}
        extra_context['show_export_button'] = True
        extra_context['show_import_button'] = True

        # Добавляем URL для кнопки экспорта прямо в контекст
        try :
            from django.urls import reverse
            export_url = reverse(
                'admin:pneumatic_actuators_bodythrusttorquetable_export_torque' ,
                args=[object_id]
            )
            import_url = reverse('admin:pneumatic_actuators_bodythrusttorquetable_import')

            extra_context['export_url'] = export_url
            extra_context['import_url'] = import_url
            logger.info(f"Export URL: {export_url}")
            logger.info(f"Import URL: {import_url}")
        except Exception as e :
            logger.error(f"Error generating URLs: {e}")
            extra_context['export_url'] = '#'
            extra_context['import_url'] = '#'

        logger.info(f"Extra context: {extra_context}")

        # ИСПРАВЛЕНИЕ: вызываем change_view, а не changelist_view
        return super().change_view(request , object_id , form_url , extra_context=extra_context)

class PneumaticActuatorBodyForm(forms.ModelForm) :
    """Форма для корпуса пневмопривода с валидацией"""

    class Meta :
        model = PneumaticActuatorBody
        fields = '__all__'

    def clean(self) :
        cleaned_data = super().clean()
        min_pressure = cleaned_data.get('min_pressure_bar')
        max_pressure = cleaned_data.get('max_pressure_bar')

        # Проверка, что минимальное давление не больше максимального
        if min_pressure and max_pressure and min_pressure > max_pressure :
            raise forms.ValidationError(
                _('Минимальное давление не может быть больше максимального давления')
            )

        return cleaned_data


@admin.register(PneumaticActuatorBody)
class PneumaticActuatorBodyAdmin(admin.ModelAdmin) :
    """Админка для корпусов пневмоприводов"""

    form = PneumaticActuatorBodyForm
    list_display = (
        'name' , 'code' , 'body_table' , 'mounting_plate_display', 'stem_info_display' ,
         'sorting_order' , 'is_active'
    )
    list_editable = ('sorting_order' , 'is_active')
    list_filter = ('is_active' , 'body_table' , 'stem_shape' , 'stem_size')
    search_fields = ('name' , 'code' , 'description')
    ordering = ('sorting_order' , 'name')

    # Поля для автодополнения в форме
    autocomplete_fields = ['body_table' , 'stem_shape' , 'stem_size']

    # Фильтры для ManyToMany полей
    filter_horizontal = ('mounting_plate' ,)

    fieldsets = (
        (_('Основная информация') , {
            'fields' : (
                ('name' , 'code' ,'sorting_order' , 'is_active'), 'body_table'
            )
        }) ,
        (_('Монтажные параметры') , {
            'fields' : (
                ('stem_shape' , 'stem_size', 'mounting_plate' ) , ('max_stem_height' , 'max_stem_diameter'),
                ('piston_diameter','turn_angle','turn_tuning_limit',),
                ('weight_spring',),
            )
        }) ,
        (_('Давление и расход воздуха') , {
            'fields' : (
                ('min_pressure_bar' , 'max_pressure_bar' ),
                ('air_usage_open' , 'air_usage_close'),
                ('thread_in','thread_out','pneumatic_connection'),
            )
        }) ,

        (_('Описание') , {
            'fields' : ('description' ,),
            'classes' : ('collapse' ,'pne')
        }) ,
    )
    inlines = [
        PneumaticWeightParameterInline ,
        PneumaticCloseTimeParameterInline,
         ]
    # Группировка полей в форме
    readonly_fields = ()

    def get_queryset(self , request) :
        """Оптимизация запросов к базе данных"""
        return super().get_queryset(request).select_related(
            'body_table' , 'stem_shape' , 'stem_size'
        ).prefetch_related(
        'mounting_plate',
        'pa_weight_parameter',  # ← для PneumaticWeightParameterInline
        'pa_weight_parameter__spring_qty',  # ← для оптимизации spring_qty в весах
        'pa_close_time_parameter',  # ← для PneumaticCloseTimeParameterInline
        'pa_close_time_parameter__spring_qty',  # ← для оптимизации spring_qty во времени
    )

    # Добавьте в list_display кнопку действий
    actions = ['copy_selected']

    def copy_selected(self , request , queryset) :
        """Копирование выбранных моделей"""
        for original in queryset :
            original.create_copy()

        count = queryset.count()
        messages.success(request , f'Успешно скопировано {count} моделей')

    def copy_instance(self , request , object_id) :
        """Копирование одной модели"""
        original = self.get_object(request , object_id)
        if original :
            copy = original.create_copy()
            messages.success(request , 'Модель успешно скопирована')
            return redirect(reverse('admin:pneumatic_actuators_pneumaticactuatorbody_change' , args=[copy.pk]))

        return redirect(reverse('admin:pneumatic_actuators_pneumaticactuatorbody_changelist'))

    # Добавьте URL для копирования
    def get_urls(self) :
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/copy/' , self.copy_instance ,
                 name='pneumatic_actuators_pneumaticactuatorbody_copy') ,
        ]
        return custom_urls + urls


