from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import render , redirect
from django.http import HttpResponse
from django.utils.html import format_html
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from valve_data.models import ValveLine, ValveLineBodyColor,    ValveModelDataTable, ValveModelKvDataTable, ValveLineModelKvData, AllowedDnTemplate


def duplicate_selected_action(model_admin , request , queryset) :
    for obj in queryset :
        try :
            # Создаем копию основных данных
            new_obj = ValveLine.objects.get(pk=obj.pk)
            new_obj.pk = None
            new_obj.id = None

            # Модифицируем уникальные поля
            if new_obj.name :
                new_obj.name = f"{new_obj.name} (Копия)"
            if new_obj.code :
                new_obj.code = f"{new_obj.code}_copy"

            # Сохраняем основную запись
            new_obj.save()

            # Функция для копирования through-отношений
            def copy_through_relations(through_model , related_field_name , source_obj , target_obj) :
                through_objects = through_model.objects.filter(**{related_field_name : source_obj})
                for through_obj in through_objects :
                    # Создаем копию through-объекта
                    new_through_obj = through_model()
                    for field in through_obj._meta.fields :
                        if field.name not in ['id' , 'pk' , related_field_name] :
                            setattr(new_through_obj , field.name , getattr(through_obj , field.name))
                    # Связываем с новой записью
                    setattr(new_through_obj , related_field_name , target_obj)
                    new_through_obj.save()

            # Копируем все through-отношения
            copy_through_relations(ValveLineBodyColor , 'valve_line' , obj , new_obj)


        except Exception as e :
            model_admin.message_user(request , f"Ошибка при копировании {obj}: {str(e)}" , level='error')
            continue

    model_admin.message_user(request , "Выбранные записи успешно скопированы.")


class ValveLineBodyColorInline(admin.TabularInline) :
    model = ValveLineBodyColor
    extra = 1
    verbose_name = _("Цвет корпуса")
    verbose_name_plural = _("Цвета корпусов")
    # Минимальный набор полей
    fields = [
        'body_color' ,
        'option_code_template' ,
        'option_variety' ,
    ]

    class Media :
        css = {
            'all' : ('admin/css/hide_icons.css' ,)
        }

class ValveLineAdmin(admin.ModelAdmin):
    change_list_template = 'admin/valve_line_change_list.html'
    change_form_template = 'admin/valve_line_change_form.html'
    list_display = (
       'id', 'name', 'valve_variety', 'valve_producer', 'valve_brand', 'is_approved', 'is_active', 'text_info_button')
    list_select_related = ('valve_variety', 'valve_producer', 'valve_brand')
    list_editable = ['is_approved', 'is_active']
    search_fields = ('name', 'valve_variety__name', 'valve_variety__text_description')
    list_filter = ('valve_variety', 'valve_producer', 'valve_brand', 'is_approved', 'is_active')
    actions = [duplicate_selected_action, 'export_as_text', 'export_with_sources']  # Добавлено новое действие
    inlines = [ValveLineBodyColorInline]

    # Поля остаются без изменений
    fieldsets = (
        (_('Основные характеристики'), {
            'fields': (('name', 'code', 'item_code_template'),
                       ('valve_variety' , 'valve_actuation') ,
                       ('original_valve_line' ,  'option_variety', 'construction_variety') ,
                       ('valve_producer', 'valve_brand'),
                       ('valve_function', 'valve_sealing_class'),
                       ('pipe_connection', 'port_qty'),
                       ('is_approved', 'is_active'))
        }),
        (_('Материалы основных компонентов'), {
            'fields': (
                ('body_material', 'body_material_specified'),
                ('shut_element_material', 'shut_element_material_specified'),
                ('sealing_element_material' , 'sealing_element_material_specified') ,
            )
        }),
        (_('Таблицы данных:') , {
            'fields' : ('allowed_dn_table', 'valve_model_data_table','valve_model_kv_data_table' )
        }) ,
        (_('Рабочие температуры (°C)') , {
            'fields' : (
                ('work_temp_min' , 'work_temp_max', 'temp_min' , 'temp_max') ,
            )
        }) ,

        (_('Гарантийный срок, сроки службы'), {
            'fields': (
                ('warranty_period_min', 'warranty_period_min_variety'),
                ('warranty_period_max', 'warranty_period_max_variety'),
                ('valve_in_service_years', 'valve_in_service_years_comment'),
                ('valve_in_service_cycles', 'valve_in_service_cycles_comment')
            )
        }),

        (_('Описание') , {
            'fields' : ('description' , 'features_text' , 'application_text') ,
            'classes' : ('collapse' ,)
        }) ,
    )
    class Media :
        css = {
            'all' : ('admin/css/hide_icons.css' ,)
        }
    def text_info_button(self, obj):
        if obj.pk:
            return format_html(
                '<a href="{}" target="_blank" style="background: #417690; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; display: inline-block; font-size: 12px;">📄</a>',
                reverse('admin:valve_line_text_info', args=[obj.pk])
            )
        return "-"
    text_info_button.short_description = "Текст"
    text_info_button.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('valve_line_text_info/<int:object_id>/',
                 self.admin_site.admin_view(self.text_info_view),
                 name='valve_line_text_info'),
        ]
        return custom_urls + urls

    def text_info_view(self, request, object_id):
        try:
            valve_line = ValveLine.objects.get(id=object_id)
        except ValveLine.DoesNotExist:
            return HttpResponse("Объект не найден", status=404)

        # Получаем параметр show_data_source из запроса
        show_data_source = request.GET.get('show_data_source', 'false').lower() == 'true'

        # Используем методы модели для получения данных
        structured_data = valve_line.get_full_data(show_data_source)

        # ВАЖНО: убрать html_content, так как теперь используем structured_data в шаблоне
        return render(request, 'admin/valve_line_text_info.html', {
            'valve_line': valve_line,
            'structured_data': structured_data,
            'show_data_source': show_data_source,
            'title': f'Полная информация: {valve_line.name}'
        })

    def export_as_text(self, request, queryset):
        """Действие для экспорта выбранных объектов в текстовом виде"""
        response = HttpResponse(content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="valve_lines.txt"'

        content = []
        for obj in queryset:
            # Используем метод модели для форматирования текста
            text_info = obj.format_text_info(show_data_source=False)
            content.append(text_info)
            content.append("\n" + "=" * 80 + "\n")

        response.write("\n".join(content))
        return response
    export_as_text.short_description = "Экспорт в текстовом виде"

    def export_with_sources(self, request, queryset):
        """Экспорт с информацией об источниках данных"""
        response = HttpResponse(content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="valve_lines_with_sources.txt"'

        content = []
        for obj in queryset:
            # Используем метод модели с показом источников
            text_info = obj.format_text_info(show_data_source=True)
            content.append(text_info)
            content.append("\n" + "=" * 80 + "\n")

        response.write("\n".join(content))
        return response

    export_with_sources.short_description = "Экспорт с источниками данных"

    def get_queryset(self, request):
        """Оптимизируем запрос для админки"""
        return super().get_queryset(request).select_related(
            'valve_variety', 'valve_producer', 'valve_brand',
            'valve_function', 'valve_sealing_class', 'valve_model_data_table'
        ).prefetch_related(
            'body_colors'
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Оптимизация выбора связанных объектов"""
        if db_field.name == "original_valve_line":
            kwargs["queryset"] = ValveLine.objects.filter(is_active=True).order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """Дополнительная проверка при сохранении в админке"""
        # Показываем предупреждения, но разрешаем сохранение
        warnings = obj.get_validation_warnings()
        if warnings:
            messages.warning(request, f"Предупреждения: {'; '.join(warnings)}")

        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        """Делаем поля readonly, если они будут унаследованы"""
        # if obj and obj.original_valve_line:
        #     readonly_fields = list(self.readonly_fields) if self.readonly_fields else []
        #
        #     # Добавляем поля, которые будут унаследованы
        #     for field in ['name', 'code', 'valve_brand', 'valve_producer']:
        #         if obj._will_inherit(field) and field not in readonly_fields:
        #             readonly_fields.append(field)
        #
        #     return readonly_fields
        # return self.readonly_fields
        return []



    def get_fields(self, request, obj=None):
        """Показываем подсказки о наследовании"""
        fields = super().get_fields(request, obj)

        if obj and obj.original_valve_line:
            # Можно добавить логику для отображения подсказок
            pass

        return fields