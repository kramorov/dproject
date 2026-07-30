# core/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
import json


class BaseAdmin(admin.ModelAdmin) :
    """
    Базовый класс админки для всех моделей с StructuredDataMixin
    """
    list_per_page = 50
    save_on_top = True

    # Добавляем предпросмотр данных
    readonly_fields = ['data_preview' , 'json_preview']

    fieldsets = (
        ('Основная информация' , {
            'fields' : ('name' , 'code' , 'description')
        }) ,
        ('Предпросмотр данных' , {
            'fields' : ('data_preview' , 'json_preview') ,
            'classes' : ('collapse' , 'wide')
        }) ,
        ('Дополнительно' , {
            'fields' : ('sorting_order' , 'is_active') ,
            'classes' : ('collapse' ,)
        })
    )

    def data_preview(self , obj) :
        """Предпросмотр данных для отображения"""
        if not obj.pk :
            return "Сначала сохраните объект"

        try :
            display_data = obj.get_display_data()

            if 'fields' in display_data :
                # Детальное отображение
                html = ['<div class="data-preview">']

                for field_name , field_data in display_data['fields'].items() :
                    if not field_data.get('is_empty' , True) :
                        label = field_data.get('label' , field_name)
                        value = field_data.get('formatted' , '—')
                        icon = field_data.get('icon' , '')

                        html.append(
                            f'<div class="field">'
                            f'<span class="label">{icon} {label}:</span> '
                            f'<span class="value">{value}</span>'
                            f'</div>'
                        )

                html.append('</div>')
                return format_html(''.join(html))

            elif 'title' in display_data :
                # Карточка
                return format_html(
                    '<div class="card-preview">'
                    '<h3>{title}</h3>'
                    '<p>{subtitle}</p>'
                    '</div>' ,
                    title=display_data.get('title' , '') ,
                    subtitle=display_data.get('subtitle' , '')
                )

        except NotImplementedError :
            return "Модель не реализует get_display_data()"

        return "Нет данных для предпросмотра"

    data_preview.short_description = "Предпросмотр"

    def json_preview(self , obj) :
        """JSON предпросмотр всех данных"""
        if not obj.pk :
            return "Сначала сохраните объект"

        try :
            data = {
                'compact' : obj.get_compact_data() ,
                'display' : obj.get_display_data() ,
                'full' : obj.get_full_data() ,
            }

            formatted = json.dumps(data , ensure_ascii=False , indent=2)

            return format_html(
                '<div style="background: #f5f5f5; padding: 10px; '
                'border-radius: 5px; max-height: 300px; overflow-y: auto;">'
                '<pre style="margin: 0; font-size: 11px;">{}</pre>'
                '</div>' ,
                formatted
            )

        except Exception as e :
            return f"Ошибка: {str(e)}"

    json_preview.short_description = "JSON данные"


# ── SelectionWizard Admin ──
from core.models.selection_wizard import SelectionWizard

@admin.register(SelectionWizard)
class SelectionWizardAdmin(admin.ModelAdmin):
    list_display = ['name', 'equipment_type', 'is_active', 'sorting_order']
    list_filter = ['is_active', 'equipment_type']
    search_fields = ['name', 'code', 'equipment_type__name']
    autocomplete_fields = ['equipment_type']

    fieldsets = (
        (_('Основное'), {
            'fields': ('name', 'code', 'description', ('equipment_type', 'is_active'), 'sorting_order'),
        }),
        (_('Конфигурация шагов'), {
            'fields': ('steps_json',),
            'description': _(
                'JSON с двумя секциями: "pages" и "filters".<br>'
                '<b>pages</b>: [{"step_number": 1, "title": "...", "description": "..."}, ...]<br>'
                '<b>filters</b>: [{"param_name": "...", "page": 1, "order": 1, "label": "...", "default_value": null}, ...]'
            ),
        }),
    )
