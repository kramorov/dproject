# features/admin/equipment_type_admin.py
from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from core.models.equipment_type import EquipmentType


class EquipmentTypeForm(forms.ModelForm):
    class Meta:
        model = EquipmentType
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Исключаем сам объект и его потомков из parent
        if self.instance and self.instance.pk:
            exclude_ids = self.instance.get_descendants_ids()
            self.fields['parent'].queryset = EquipmentType.objects.exclude(
                id__in=exclude_ids + [self.instance.pk]
            )


@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    form = EquipmentTypeForm
    list_display = [
        'name', 'code', 'level_display',
        'parent_display', 'children_count',
        'ai_support_display',
        'content_type',
        'sorting_order', 'is_active'
    ]
    list_editable = ['content_type']

    list_filter = ['level', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering = ['level', 'sorting_order', 'name']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'code', 'description', 'icon')
        }),
        ('Шаблоны отображения', {
            'fields': ('title_template',),
            'description': 'Шаблон заголовка карточки товара. Плейсхолдеры: {model_code}, {brand}, {ip}, {exd}, {work_temp_min}, {work_temp_max}, {body_material} и др.',
        }),
        ('AI Assistant', {
            'fields': ('filter_endpoint', 'param_semantics'),
            'classes': ('collapse',),
        }),
        ('Иерархия', {
            'fields': ('parent', 'level_display', 'hierarchy_visualization'),
            'classes': ('wide', 'collapse'),
        }),
        ('Настройки', {
            'fields': ('content_type', 'sorting_order', 'is_active')
        }),
    )

    readonly_fields = ['level_display', 'hierarchy_visualization']

    def level_display(self, obj):
        """Отображение уровня с иконками"""
        if obj.level == 0:
            icon = '🏠'
            color = 'green'
        elif obj.level == 1:
            icon = '📁'
            color = 'blue'
        elif obj.level == 2:
            icon = '📄'
            color = 'orange'
        else:
            icon = '📋'
            color = 'gray'

        return format_html(
            '<span style="display: inline-flex; align-items: center; gap: 5px; padding: 2px 8px; '
            'background: {}; color: white; border-radius: 10px;">'
            '{} Уровень {}'
            '</span>',
            color, icon, obj.level
        )

    level_display.short_description = "Уровень"

    def parent_display(self, obj):
        """Отображение родителя"""
        if obj.parent:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:core_equipmenttype_change', args=[obj.parent.id]),
                obj.parent.name
            )
        return "—"

    parent_display.short_description = "Родитель"

    def children_count(self, obj):
        """Количество дочерних элементов"""
        count = obj.children.count()
        if count > 0:
            url = reverse('admin:core_equipmenttype_changelist') + f'?parent__id__exact={obj.id}'
            return format_html(
                '<a href="{}" class="badge" style="background: #4CAF50; color: white; '
                'padding: 2px 8px; border-radius: 10px;">{} шт.</a>',
                url, count
            )
        return "—"

    children_count.short_description = "Дочерние"

    def hierarchy_visualization(self, obj):
        """Визуализация иерархии"""
        if not obj.pk:
            return "Сначала сохраните объект"

        html = '<div id="hierarchy-visualization" style="margin: 20px 0;">'
        html += f'<h4>Полный путь: {obj.get_full_path()}</h4>'

        # Показываем родителей
        if obj.parent:
            html += '<div style="margin-bottom: 15px;">'
            html += '<strong>Родители:</strong><br>'
            parents = []
            current = obj.parent
            while current:
                url = reverse('admin:core_equipmenttype_change', args=[current.id])
                parents.insert(0, f'<a href="{url}">{current.name}</a>')
                current = current.parent

            html += " → ".join(parents)
            html += '</div>'

        # Показываем детей
        children = obj.children.all()
        if children.exists():
            html += '<div style="margin-bottom: 15px;">'
            html += f'<strong>Дочерние типы ({children.count()}):</strong><br>'
            html += '<ul style="list-style-type: none; padding-left: 0;">'
            for child in children:
                url = reverse('admin:core_equipmenttype_change', args=[child.id])
                html += f'<li style="margin: 5px 0; padding-left: 20px; position: relative;">'
                html += f'<span style="position: absolute; left: 0;">↳</span>'
                html += f'<a href="{url}">{child.name}</a>'
                html += f' <span style="color: #666;">({child.code})</span>'
                html += '</li>'
            html += '</ul>'
            html += '</div>'

        html += '</div>'
        return format_html(html)

    hierarchy_visualization.short_description = "Визуализация иерархии"

    def ai_support_display(self, obj):
        """Показывает, участвует ли тип в AI-подборе"""
        if obj.filter_endpoint:
            return format_html(
                '<span style="color: #4CAF50;">🤖 Да</span>'
            )
        return format_html('<span style="color: #999;">—</span>')

    ai_support_display.short_description = "AI"

    class Media:
        css = {
            'all': ('features/css/admin-equipment-type.css',)
        }
        js = ('features/js/admin-equipment-type.js',)