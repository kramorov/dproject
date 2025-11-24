# media_library/admin.py
import os
import logging
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django import forms
from .models import MediaCategory , MediaTag , MediaLibraryItem

logger = logging.getLogger(__name__)


class MediaLibraryItemForm(forms.ModelForm) :
    """Форма для элемента медиабиблиотеки с дополнительной логикой"""

    class Meta :
        model = MediaLibraryItem
        fields = '__all__'
        widgets = {
            'description' : forms.Textarea(attrs={
                'rows' : 2 ,'cols': 120,
                'style' : 'height: 4em; min-height: 4em; resize: vertical;' ,
                'placeholder' : 'Введите краткое описание...'
            }) ,
        }

    def __init__(self , *args , **kwargs) :
        super().__init__(*args , **kwargs)
        # Если объект уже существует, показываем кто создал
        if self.instance and self.instance.pk and self.instance.created_by :
            self.fields['created_by'].help_text = f"Создал: {self.instance.created_by}"

    def save(self , commit=True) :
        """Переопределяем save для автоматического заполнения данных"""
        instance = super().save(commit=False)

        # Автоматически заполняем данные только для новых объектов
        if not instance.pk and instance.media_file :
            # Заполняем описание из имени файла
            if not instance.description :
                filename_without_ext = self._get_filename_without_extension(instance.media_file.name)
                instance.description = f"Файл: {filename_without_ext}"

            # Ищем существующие теги в имени файла
            self._find_existing_tags_in_filename(instance.media_file.name , instance)

        if commit :
            instance.save()
            self.save_m2m()

        return instance

    def _get_filename_without_extension(self , filename) :
        """Извлекает имя файла без расширения"""
        name = os.path.splitext(filename)[0]
        separators = ['_' , '-' , '.' , ',' , ';' , '—' , '–']
        for sep in separators :
            name = name.replace(sep , ' ')
        return name.strip()

    def _find_existing_tags_in_filename(self , filename , instance) :
        """Ищет существующие теги в имени файла"""
        name_without_ext = os.path.splitext(filename)[0].upper()
        all_tags = MediaTag.objects.filter(is_active=True)

        matching_tags = []
        for tag in all_tags :
            tag_name_upper = tag.name.upper()
            if tag_name_upper in name_without_ext :
                matching_tags.append(tag)

        if matching_tags :
            if not instance.pk :
                instance.save()
            instance.tags.add(*matching_tags)
            logger.info(f"Автоматически добавлены теги: {[tag.name for tag in matching_tags]}")


@admin.register(MediaLibraryItem)
class MediaLibraryItemAdmin(admin.ModelAdmin) :
    form = MediaLibraryItemForm
    list_display = [
        'preview_display' , 'title' , 'category' , 'tags_display' , 'is_active' , 'created_at'
    ]
    list_display_links = ['preview_display' , 'title']
    list_filter = ['category' , 'is_active' , 'is_public' , 'created_at' , 'tags']
    search_fields = ['title' , 'description' , 'tags__name']
    readonly_fields = [
        'preview_display' , 'file_type_display' , 'file_size_display' ,
        'filename_display' , 'created_at' , 'updated_at' , 'replace_file_action' ,
        'auto_tags_info', 'preview_actions'
    ]
    list_editable = ['is_active']
    filter_horizontal = ['tags']

    fieldsets = (
        (_("Основная информация") , {
            'fields' : (('title' , 'category' ),('created_by',  'is_public' , 'is_active' ,'created_at' , 'updated_at' ))
        }) ,
        (_("Описание") , {
            'fields' : ('description'  , ('tags', 'auto_tags_info'))
        }) ,
        (_("Файл") , {
            'fields' : ('media_file', ('replace_file_action', 'preview_actions', 'preview_display'))
        }) ,


        (_("Информация о файле") , {
            'fields' : ('filename_display' ,( 'file_type_display' , 'file_size_display' , 'mime_type')) ,
            'classes' : ('collapse' ,)
        }) ,
        # (_("Системная информация") , {
        #     'fields' : (('created_at' , 'updated_at') ),
        #     'classes' : ('collapse' ,)
        # }) ,
    )

    def preview_actions(self , obj) :
        """Кнопки для управления превью"""
        if not obj.pk :
            return "Сохраните объект для управления превью"

        if not obj.is_image() :
            return format_html(
                '<div style="padding: 10px; background: #f8d7da; border-radius: 4px;">'
                '⚠️ Файл не является изображением'
                '</div>'
            )

        preview_status = "❌ Отсутствует"
        if obj.preview_file :
            preview_status = "✅ Создано"

        return format_html(
            '''
            <div style="margin: 10px 0;">
                <div style="margin-bottom: 10px;">
                    <strong>Статус превью:</strong> {status}
                </div>
                <button type="button" class="button" style="background: #28a745; color: white; 
                        padding: 8px 15px; border: none; border-radius: 4px; font-size: 13px; 
                        margin: 5px 5px 5px 0; cursor: pointer;" 
                        onclick="recreatePreview({id})">
                    🔄 Создать/Обновить превью
                </button>
                <button type="button" class="button" style="background: #dc3545; color: white; 
                        padding: 8px 15px; border: none; border-radius: 4px; font-size: 13px; 
                        margin: 5px 0; cursor: pointer;" 
                        onclick="deletePreview({id})">
                    🗑️ Удалить превью
                </button>
                <div id="preview-status-{id}" style="margin-top: 10px; font-size: 12px;"></div>
            </div>

            <script>
            function recreatePreview(itemId) {{
                var statusDiv = document.getElementById('preview-status-' + itemId);
                statusDiv.innerHTML = '<span style="color: #856404;">⏳ Создаем превью...</span>';

                fetch('/admin/media_library/medialibraryitem/' + itemId + '/recreate-preview/', {{
                    method: 'POST',
                    headers: {{
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                        'Content-Type': 'application/json',
                    }}
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        statusDiv.innerHTML = '<span style="color: #155724;">✅ ' + data.message + '</span>';
                        // Обновляем страницу через 2 секунды
                        setTimeout(function() {{ location.reload(); }}, 2000);
                    }} else {{
                        statusDiv.innerHTML = '<span style="color: #721c24;">❌ ' + data.message + '</span>';
                    }}
                }})
                .catch(error => {{
                    statusDiv.innerHTML = '<span style="color: #721c24;">❌ Ошибка сети: ' + error + '</span>';
                }});
            }}

            function deletePreview(itemId) {{
                var statusDiv = document.getElementById('preview-status-' + itemId);
                statusDiv.innerHTML = '<span style="color: #856404;">⏳ Удаляем превью...</span>';

                fetch('/admin/media_library/medialibraryitem/' + itemId + '/delete-preview/', {{
                    method: 'POST',
                    headers: {{
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                        'Content-Type': 'application/json',
                    }}
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        statusDiv.innerHTML = '<span style="color: #155724;">✅ ' + data.message + '</span>';
                        // Обновляем страницу через 2 секунды
                        setTimeout(function() {{ location.reload(); }}, 2000);
                    }} else {{
                        statusDiv.innerHTML = '<span style="color: #721c24;">❌ ' + data.message + '</span>';
                    }}
                }})
                .catch(error => {{
                    statusDiv.innerHTML = '<span style="color: #721c24;">❌ Ошибка сети: ' + error + '</span>';
                }});
            }}
            </script>
            ''' ,
            status=preview_status ,
            id=obj.pk
        )

    preview_actions.short_description = _("Управление превью")

    def preview_display(self , obj) :
        """Отображает превью изображения"""
        if obj.is_image() :
            preview_url = None
            if obj.preview_file and hasattr(obj.preview_file , 'url') :
                preview_url = obj.preview_file.url
            elif obj.media_file and hasattr(obj.media_file , 'url') :
                preview_url = obj.media_file.url

            if preview_url :
                return format_html(
                    '<img src="{}" style="max-width: 80px; max-height: 80px; '
                    'border-radius: 4px; border: 1px solid #ddd; object-fit: cover;" '
                    'title="{}" onerror="this.style.display=\'none\'" />' ,
                    preview_url , obj.title
                )

        # Иконка для не-изображений
        icons = {
            'pdf' : '📄' , 'doc' : '📝' , 'docx' : '📝' ,
            'xls' : '📊' , 'xlsx' : '📊' , 'ppt' : '📽️' , 'pptx' : '📽️' ,
            'mp4' : '🎬' , 'avi' : '🎬' , 'mov' : '🎬' , 'mkv' : '🎬' ,
            'mp3' : '🎵' , 'wav' : '🎵' , 'ogg' : '🎵' ,
            'zip' : '📦' , 'rar' : '📦' , '7z' : '📦' ,
            'txt' : '📄' , 'rtf' : '📄' , 'csv' : '📊' ,
        }
        icon = icons.get(obj.file_extension , '📁')
        return format_html(
            '<div style="width: 80px; height: 80px; display: flex; '
            'align-items: center; justify-content: center; '
            'font-size: 32px; border: 1px solid #ddd; border-radius: 4px; '
            'background: #f8f9fa;" title="{}">{}'
            '<div style="font-size: 10px; position: absolute; bottom: 2px; color: #666;">.{}</div>'
            '</div>' ,
            obj.title , icon , obj.file_extension
        )

    preview_display.short_description = _("Превью")

    def tags_display(self , obj) :
        """Отображает теги в списке"""
        tags = obj.tags.all()[:5]
        if tags :
            tag_html = []
            for tag in tags :
                tag_html.append(
                    f'<span style="background: #e9ecef; padding: 2px 6px; '
                    f'border-radius: 12px; font-size: 11px; margin: 1px;">{tag.name}</span>'
                )
            return format_html(' '.join(tag_html))
        return "-"

    tags_display.short_description = _("Теги")

    def auto_tags_info(self , obj) :
        """Информация о автоматическом создании тегов"""
        if obj.pk :
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 4px; border-left: 4px solid #007bff;">'
                '<strong>ℹ️ Автоматические теги</strong><br>'
                'При загрузке нового файла система автоматически:<br>'
                '• Добавит имя файла (без расширения) в описание<br>'
                '• Найдет существующие теги в имени файла<br>'
                '<small>Разделители: _ - . , ; — – пробел</small>'
                '</div>'
            )
        return ""

    auto_tags_info.short_description = _("Автоматизация")

    def replace_file_action(self , obj) :
        """Кнопка для замены файла через JavaScript/AJAX"""
        if obj.pk :
            return format_html(
                '''
                <div id="replace-file-container-{0}">
                    <input type="file" id="replace-file-input-{0}" style="display: none;" 
                           accept="*/*" onchange="handleFileReplace({0})">
                    <button type="button" class="button" style="background: #ff6b35; color: white; 
                            padding: 8px 15px; border: none; border-radius: 4px; font-size: 13px; 
                            margin: 5px 0; cursor: pointer;" 
                            onclick="document.getElementById('replace-file-input-{0}').click()">
                        🔄 Заменить файл
                    </button>
                    <div id="replace-file-status-{0}" style="margin-top: 5px; font-size: 12px;"></div>
                </div>
                <script>
                function handleFileReplace(itemId) {{
                    var fileInput = document.getElementById('replace-file-input-' + itemId);
                    var statusDiv = document.getElementById('replace-file-status-' + itemId);
                    var file = fileInput.files[0];

                    if (!file) return;

                    if (file.size > 100 * 1024 * 1024) {{
                        statusDiv.innerHTML = '<span style="color: #721c24;">❌ Файл слишком большой (макс. 100MB)</span>';
                        return;
                    }}

                    statusDiv.innerHTML = '<span style="color: #856404;">⏳ Загружаем файл...</span>';

                    var formData = new FormData();
                    formData.append('file', file);
                    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

                    fetch('/admin/media_library/medialibraryitem/' + itemId + '/replace-file-ajax/', {{
                        method: 'POST',
                        body: formData
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success) {{
                            statusDiv.innerHTML = '<span style="color: #155724;">✅ ' + data.message + '</span>';
                            setTimeout(function() {{ location.reload(); }}, 2000);
                        }} else {{
                            statusDiv.innerHTML = '<span style="color: #721c24;">❌ ' + data.message + '</span>';
                        }}
                    }})
                    .catch(error => {{
                        statusDiv.innerHTML = '<span style="color: #721c24;">❌ Ошибка сети</span>';
                        console.error('Error:', error);
                    }});
                }}
                </script>
                ''' ,
                obj.pk
            )
        return "-"

    replace_file_action.short_description = _("Действия с файлом")

    def file_type_display(self , obj) :
        ext = obj.file_extension.upper() if obj.file_extension else "-"
        if obj.is_image() :
            return format_html('<span style="color: green;">🖼️ {}</span>' , ext)
        elif obj.is_video() :
            return format_html('<span style="color: blue;">🎬 {}</span>' , ext)
        elif obj.is_document() :
            return format_html('<span style="color: orange;">📄 {}</span>' , ext)
        else :
            return format_html('<span>📁 {}</span>' , ext)

    file_type_display.short_description = _("Тип файла")

    def file_size_display(self , obj) :
        return obj.file_size_display

    file_size_display.short_description = _("Размер")

    def filename_display(self , obj) :
        return obj.filename

    filename_display.short_description = _("Имя файла")

    def get_urls(self) :
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/replace-file/' ,
                self.admin_site.admin_view(self.replace_file_view) ,
                name='media_library_medialibraryitem_replace_file' ,
            ) ,
            path(
                '<path:object_id>/replace-file-ajax/' ,
                self.admin_site.admin_view(self.replace_file_ajax) ,
                name='media_library_medialibraryitem_replace_file_ajax' ,
            ) ,
            path(
                '<path:object_id>/replace-file-ajax/' ,
                self.admin_site.admin_view(self.replace_file_ajax) ,
                name='media_library_medialibraryitem_replace_file_ajax' ,
            ) ,
            path(
                '<path:object_id>/recreate-preview/' ,
                self.admin_site.admin_view(self.recreate_preview_ajax) ,
                name='media_library_medialibraryitem_recreate_preview' ,
            ) ,
            path(
                '<path:object_id>/delete-preview/' ,
                self.admin_site.admin_view(self.delete_preview_ajax) ,
                name='media_library_medialibraryitem_delete_preview' ,
            ) ,
        ]
        return custom_urls + urls

    @csrf_exempt
    def recreate_preview_ajax(self , request , object_id) :
        """AJAX view для пересоздания превью"""
        try :
            media_item = MediaLibraryItem.objects.get(pk=object_id)
        except MediaLibraryItem.DoesNotExist :
            return JsonResponse({
                'success' : False ,
                'message' : 'Элемент медиабиблиотеки не найден'
            })

        if request.method == 'POST' :
            try :
                success , message = media_item.recreate_preview()
                logger.info(f"Результат создания превью для {object_id}: {success} - {message}")
                return JsonResponse({
                    'success' : success ,
                    'message' : message
                })
            except Exception as e :
                logger.error(f"Ошибка при создании превью {object_id}: {str(e)}" , exc_info=True)
                return JsonResponse({
                    'success' : False ,
                    'message' : f'Ошибка: {str(e)}'
                })

        return JsonResponse({
            'success' : False ,
            'message' : 'Неверный метод запроса'
        })

    @csrf_exempt
    def delete_preview_ajax(self , request , object_id) :
        """AJAX view для удаления превью"""
        try :
            media_item = MediaLibraryItem.objects.get(pk=object_id)
        except MediaLibraryItem.DoesNotExist :
            return JsonResponse({
                'success' : False ,
                'message' : 'Элемент медиабиблиотеки не найден'
            })

        if request.method == 'POST' :
            try :
                if media_item.preview_file :
                    preview_name = media_item.preview_file.name
                    media_item.preview_file.delete(save=False)
                    media_item.save(update_fields=['preview_file'])
                    logger.info(f"Превью удалено: {preview_name}")
                    return JsonResponse({
                        'success' : True ,
                        'message' : 'Превью успешно удалено'
                    })
                else :
                    return JsonResponse({
                        'success' : False ,
                        'message' : 'Превью не существует'
                    })
            except Exception as e :
                logger.error(f"Ошибка при удалении превью {object_id}: {str(e)}")
                return JsonResponse({
                    'success' : False ,
                    'message' : f'Ошибка: {str(e)}'
                })

        return JsonResponse({
            'success' : False ,
            'message' : 'Неверный метод запроса'
        })

    @csrf_exempt
    def replace_file_ajax(self , request , object_id) :
        """AJAX view для замены файла"""
        try :
            media_item = MediaLibraryItem.objects.get(pk=object_id)
        except MediaLibraryItem.DoesNotExist :
            return JsonResponse({
                'success' : False ,
                'message' : 'Элемент медиабиблиотеки не найден'
            })

        if request.method == 'POST' and request.FILES.get('file') :
            new_file = request.FILES['file']

            try :
                # Заменяем файл
                if media_item.replace_file(new_file , create_preview=True) :
                    # Обновляем описание
                    if not media_item.description or media_item.description.startswith("Файл: ") :
                        filename_without_ext = MediaLibraryItemForm()._get_filename_without_extension(new_file.name)
                        media_item.description = f"Файл: {filename_without_ext}"
                        media_item.save()

                    # Принудительно создаем превью если нужно
                    if media_item.is_image() and not media_item.preview_file :
                        media_item.create_preview()
                        media_item.save(update_fields=['preview_file'])

                    media_item.refresh_from_db()

                    response_data = {
                        'success' : True ,
                        'message' : 'Файл успешно заменен' ,
                        'new_filename' : new_file.name ,
                    }

                    logger.info(f"Файл заменен для {media_item.pk}")
                    return JsonResponse(response_data)
                else :
                    return JsonResponse({
                        'success' : False ,
                        'message' : 'Ошибка при замене файла'
                    })

            except Exception as e :
                logger.error(f"Ошибка при замене файла {object_id}: {str(e)}" , exc_info=True)
                return JsonResponse({
                    'success' : False ,
                    'message' : f'Ошибка: {str(e)}'
                })

        return JsonResponse({
            'success' : False ,
            'message' : 'Не выбран файл для замены'
        })

    def save_model(self , request , obj , form , change) :
        """
        Переопределяем сохранение модели в админке
        """
        # MIME-тип должен определяться автоматически в модели
        # Превью создается автоматически после сохранения

        # Автоматически устанавливаем created_by при создании
        # Если объект создается впервые (не редактируется)
        if not change :  # change=False означает создание нового объекта
            obj.created_by = request.user
            logger.info(f"Установлен created_by: {request.user} для нового объекта")
        else :
            logger.info(f"Объект редактируется, created_by остается: {obj.created_by}")

        super().save_model(request , obj , form , change)

        # После сохранения принудительно проверяем превью
        if obj.is_image() and not obj.preview_file :
            logger.info(f"Принудительное создание превью в админке для {obj.pk}")
            if obj.create_preview() :
                # Сохраняем только поле preview_file
                MediaLibraryItem.objects.filter(pk=obj.pk).update(
                    preview_file=obj.preview_file
                )

    def response_add(self , request , obj , post_url_continue=None) :
        """Принудительно создаем превью после добавления"""
        if obj.is_image() and not obj.preview_file :
            obj.create_preview()
            obj.save(update_fields=['preview_file'])
        return super().response_add(request , obj , post_url_continue)

    def response_change(self , request , obj) :
        """Принудительно создаем превью после изменения"""
        if obj.is_image() and not obj.preview_file :
            obj.create_preview()
            obj.save(update_fields=['preview_file'])
        return super().response_change(request , obj)

    def get_queryset(self , request) :
        return super().get_queryset(request).select_related(
            'category' , 'created_by'
        ).prefetch_related('tags')

    def replace_file_view(self , request , object_id) :
        """View для отдельной страницы замены файла"""
        from .views import replace_file_view
        return replace_file_view(request , object_id)

@admin.register(MediaCategory)
class MediaCategoryAdmin(admin.ModelAdmin) :
    list_display = [
        'icon_display' , 'name' , 'code' , 'is_predefined_display' ,
        'media_items_count' , 'is_active' , 'sorting_order'
    ]
    list_filter = ['is_predefined' , 'is_active' , 'created_at']
    search_fields = ['name' , 'code' , 'description']
    readonly_fields = ['is_predefined' , 'created_at' , 'updated_at' , 'media_items_count']
    list_editable = ['is_active' , 'sorting_order']

    fieldsets = (
        (_("Основная информация") , {
            'fields' : ('name' , 'code' , 'description' , 'icon')
        }) ,
        (_("Настройки") , {
            'fields' : ('is_active' , 'sorting_order')
        }) ,
        (_("Системная информация") , {
            'fields' : ('is_predefined' , 'media_items_count' , 'created_at' , 'updated_at') ,
            'classes' : ('collapse' ,)
        }) ,
    )

    def icon_display(self , obj) :
        return obj.icon

    icon_display.short_description = "🎯"

    def is_predefined_display(self , obj) :
        if obj.is_predefined :
            return format_html('<span style="color: green;">⚙️ Предопределенная</span>')
        return format_html('<span style="color: blue;">📁 Пользовательская</span>')

    is_predefined_display.short_description = _("Тип")

    def media_items_count(self , obj) :
        return obj.media_items_count

    media_items_count.short_description = _("Медиа элементов")

    def get_readonly_fields(self , request , obj=None) :
        if obj and obj.is_predefined :
            return self.readonly_fields + ['code']
        return super().get_readonly_fields(request , obj)

    def has_delete_permission(self , request , obj=None) :
        if obj and obj.is_predefined :
            return False
        return super().has_delete_permission(request , obj)


@admin.register(MediaTag)
class MediaTagAdmin(admin.ModelAdmin) :
    list_display = ['name' , 'is_active' , 'media_items_count' , 'created_at']
    list_filter = ['is_active' , 'created_at']
    search_fields = ['name']
    list_editable = ['is_active']
    readonly_fields = ['created_at' , 'updated_at']

    def media_items_count(self , obj) :
        return obj.media_items.count()

    media_items_count.short_description = _("Медиа элементов")