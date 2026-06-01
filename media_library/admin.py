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
from .models import MediaCategory ,MediaLibraryItem
from .models import ImageGallerySet, ImageGallerySetItem, MediaVariant
from .services import delete_variants, generate_variants

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

class MediaVariantInline(admin.TabularInline):
    model = MediaVariant
    extra = 0
    fields = ('role', 'width', 'height', 'format', 'file_size', 'page_num', 'created_at')
    readonly_fields = fields
    can_delete = False
    verbose_name = _("Вариант")
    verbose_name_plural = _("Варианты")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(MediaLibraryItem)
class MediaLibraryItemAdmin(admin.ModelAdmin) :
    form = MediaLibraryItemForm
    inlines = [MediaVariantInline]
    list_display = [
        'preview_display' , 'name' , 'code' , 'category' ,  'keywords_short' ,  'is_active' , 'created_at'
    ]
    list_display_links = ['preview_display' , 'name']
    list_filter = ['category' , 'is_active' , 'is_public' , 'created_at' ]
    search_fields = ['name' , 'code' , 'description', 'keywords' ]
    readonly_fields = [
        'preview_display' , 'file_type_display' , 'file_size_display' ,
        'filename_display' , 'created_at' , 'updated_at' , 'replace_file_action' ,
         'preview_actions'
    ]
    list_editable = ['is_active']

    fieldsets = (
        (_("Основная информация") , {
            'fields' : (('name' , 'code' , 'category' ),('created_by',  'is_public' , 'is_active' ,'created_at' , 'updated_at' ))
        }) ,
        (_("Описание") , {
            'fields' : ('description'  , 'keywords')
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

    @admin.display(description="Ключевые слова")
    def keywords_short(self , obj) :
        if obj.keywords :
            return obj.keywords[:80] + ('…' if len(obj.keywords) > 80 else '')
        return '-'

    def preview_actions(self , obj) :
        """Кнопки для управления вариантами"""
        if not obj.pk :
            return "Сохраните объект для управления вариантами"

        if not (obj.is_image() or obj._is_pdf()) :
            return format_html(
                '<div style="padding: 10px; background: #f8d7da; border-radius: 4px;">'
                '⚠️ Варианты поддерживаются только для изображений и PDF'
                '</div>'
            )

        variant_count = obj.variants.count()
        variant_status = f"✅ {variant_count} вариантов" if variant_count else "❌ Отсутствуют"

        return format_html(
            '''
            <div style="margin: 10px 0;">
                <div style="margin-bottom: 10px;">
                    <strong>Статус вариантов:</strong> {status}
                </div>
                <button type="button" class="button" style="background: #28a745; color: white; 
                        padding: 8px 15px; border: none; border-radius: 4px; font-size: 13px; 
                        margin: 5px 5px 5px 0; cursor: pointer;" 
                        onclick="recreatePreview({id})">
                    🔄 Перегенерировать варианты
                </button>
                <button type="button" class="button" style="background: #dc3545; color: white; 
                        padding: 8px 15px; border: none; border-radius: 4px; font-size: 13px; 
                        margin: 5px 0; cursor: pointer;" 
                        onclick="deletePreview({id})">
                    🗑️ Удалить варианты
                </button>
                <div id="preview-status-{id}" style="margin-top: 10px; font-size: 12px;"></div>
            </div>

            <script>
            function recreatePreview(itemId) {{
                var statusDiv = document.getElementById('preview-status-' + itemId);
                statusDiv.innerHTML = '<span style="color: #856404;">⏳ Генерируем варианты...</span>';

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
                statusDiv.innerHTML = '<span style="color: #856404;">⏳ Удаляем варианты...</span>';

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
            status=variant_status ,
            id=obj.pk
        )

    preview_actions.short_description = _("Варианты")

    def preview_display(self , obj) :
        """Отображает превью изображения"""
        if obj.is_image() :
            preview_url = obj.preview_url
            if not preview_url and obj.media_file and hasattr(obj.media_file, 'url'):
                preview_url = obj.media_file.url

            if preview_url :
                return format_html(
                    '<img id="preview-img-{2}" src="{0}" style="max-width: 80px; max-height: 80px; '
                    'border-radius: 4px; border: 1px solid #ddd; object-fit: cover;" '
                    'title="{1}" onerror="this.style.display=\'none\'" />' ,
                    preview_url , obj.name , obj.pk
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
            obj.name , icon , obj.file_extension
        )

    preview_display.short_description = _("Превью")

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
                            // Update preview image in-place
                            var previewImg = document.getElementById('preview-img-' + itemId);
                            if (previewImg && data.new_preview_url) {{
                                previewImg.src = data.new_preview_url + '?t=' + Date.now();
                                previewImg.style.display = '';
                            }}
                            // Update file info fields
                            var fileSizeEl = document.getElementById('file-size-' + itemId);
                            if (fileSizeEl && data.new_file_size_display) {{
                                fileSizeEl.textContent = data.new_file_size_display;
                            }}
                            var filenameEl = document.getElementById('filename-' + itemId);
                            if (filenameEl && data.new_filename) {{
                                filenameEl.textContent = data.new_filename;
                            }}
                            var fileTypeEl = document.getElementById('file-type-' + itemId);
                            if (fileTypeEl && data.new_file_type_html) {{
                                fileTypeEl.innerHTML = data.new_file_type_html;
                            }}
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
            html = format_html('<span style="color: green;">🖼️ {}</span>' , ext)
        elif obj.is_video() :
            html = format_html('<span style="color: blue;">🎬 {}</span>' , ext)
        elif obj.is_document() :
            html = format_html('<span style="color: orange;">📄 {}</span>' , ext)
        else :
            html = format_html('<span>📁 {}</span>' , ext)
        return format_html('<span id="file-type-{}">{}</span>' , obj.pk , html)

    file_type_display.short_description = _("Тип файла")

    def file_size_display(self , obj) :
        return format_html('<span id="file-size-{}">{}</span>' , obj.pk , obj.file_size_display)

    file_size_display.short_description = _("Размер")

    def filename_display(self , obj) :
        return format_html('<span id="filename-{}">{}</span>' , obj.pk , obj.filename)

    filename_display.short_description = _("Имя файла")

    def get_urls(self) :
        urls = super().get_urls()
        custom_urls = [
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
                '<path:object_id>/regenerate-variants/' ,
                self.admin_site.admin_view(self.regenerate_variants_ajax) ,
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
        """AJAX view для перегенерации вариантов"""
        try :
            media_item = MediaLibraryItem.objects.get(pk=object_id)
        except MediaLibraryItem.DoesNotExist :
            return JsonResponse({
                'success' : False ,
                'message' : 'Элемент медиабиблиотеки не найден'
            })

        if request.method == 'POST' :
            try :
                if not (media_item.is_image() or media_item._is_pdf()):
                    return JsonResponse({
                        'success': False,
                        'message': 'Варианты поддерживаются только для изображений и PDF'
                    })
                delete_variants(media_item)
                count = generate_variants(media_item)
                message = f'Сгенерировано {count} вариантов' if count else 'Варианты не созданы (нет профиля)'
                logger.info(f"Варианты перегенерированы для {object_id}: {count}")
                return JsonResponse({
                    'success' : True ,
                    'message' : message
                })
            except Exception as e :
                logger.error(f"Ошибка при генерации вариантов {object_id}: {str(e)}" , exc_info=True)
                return JsonResponse({
                    'success' : False ,
                    'message' : f'Ошибка: {str(e)}'
                })

        return JsonResponse({
            'success' : False ,
            'message' : 'Неверный метод запроса'
        })

    @csrf_exempt
    def regenerate_variants_ajax(self, request, object_id):
        """AJAX view для генерации вариантов из загруженного файла (без замены media_file)."""
        try:
            media_item = MediaLibraryItem.objects.get(pk=object_id)
        except MediaLibraryItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Элемент не найден'})

        if request.method != 'POST' or not request.FILES.get('file'):
            return JsonResponse({'success': False, 'message': 'Файл не передан'})

        uploaded = request.FILES['file']
        try:
            if not (media_item.is_image() or media_item._is_pdf()):
                return JsonResponse({'success': False, 'message': 'Только изображения и PDF'})

            delete_variants(media_item)
            count = generate_variants(media_item, source_file=uploaded)

            logger.info(f"Варианты сгенерированы из внешнего файла для {object_id}: {count}")
            return JsonResponse({'success': True, 'message': f'Сгенерировано {count} вариантов'})
        except Exception as e:
            logger.error(f"Ошибка генерации вариантов {object_id}: {e}", exc_info=True)
            return JsonResponse({'success': False, 'message': str(e)})

    @csrf_exempt
    def delete_preview_ajax(self , request , object_id) :
        """AJAX view для удаления вариантов"""
        try :
            media_item = MediaLibraryItem.objects.get(pk=object_id)
        except MediaLibraryItem.DoesNotExist :
            return JsonResponse({
                'success' : False ,
                'message' : 'Элемент медиабиблиотеки не найден'
            })

        if request.method == 'POST' :
            try :
                if media_item.variants.exists():
                    delete_variants(media_item)
                    logger.info(f"Варианты удалены для {object_id}")
                    return JsonResponse({
                        'success' : True ,
                        'message' : 'Варианты успешно удалены'
                    })
                else :
                    return JsonResponse({
                        'success' : False ,
                        'message' : 'Варианты отсутствуют'
                    })
            except Exception as e :
                logger.error(f"Ошибка при удалении вариантов {object_id}: {str(e)}")
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
                if media_item.replace_file(new_file) :
                    # Обновляем описание
                    if not media_item.description or media_item.description.startswith("Файл: ") :
                        filename_without_ext = MediaLibraryItemForm()._get_filename_without_extension(new_file.name)
                        media_item.description = f"Файл: {filename_without_ext}"
                        media_item.save()

                    media_item.refresh_from_db()

                    response_data = {
                        'success' : True ,
                        'message' : 'Файл успешно заменен' ,
                        'new_filename' : media_item.filename ,
                        'new_preview_url' : media_item.preview_url if media_item.is_image() else None ,
                        'new_file_size_display' : media_item.file_size_display ,
                        'new_file_type_html' : self.file_type_display(media_item) ,
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
        Сохранение модели в админке. Варианты генерируются в MediaLibraryItem.save().
        """
        if not change :  # change=False означает создание нового объекта
            obj.created_by = request.user
            logger.info(f"Установлен created_by: {request.user} для нового объекта")
        else :
            logger.info(f"Объект редактируется, created_by остается: {obj.created_by}")

        super().save_model(request , obj , form , change)

    def response_add(self , request , obj , post_url_continue=None) :
        return super().response_add(request , obj , post_url_continue)

    def response_change(self , request , obj) :
        return super().response_change(request , obj)

    def get_queryset(self , request) :
        return super().get_queryset(request).select_related(
            'category' , 'created_by'
        )

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


# ═══════════════════════════════════════════════════════════════
# ImageGallerySet — админка с инлайном элементов
# ═══════════════════════════════════════════════════════════════

class ImageGallerySetItemInline(admin.TabularInline):
    model = ImageGallerySetItem
    extra = 1
    fields = ('image', 'sorting_order', 'is_default')
    raw_id_fields = ('image',)
    autocomplete_fields = ('image',)


@admin.register(ImageGallerySet)
class ImageGallerySetAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'sorting_order', 'items_count')
    search_fields = ('name', 'code', 'keywords')
    inlines = [ImageGallerySetItemInline]

    @admin.display(description="Изображений")
    def items_count(self, obj):
        return obj.items.count()
        return super().has_delete_permission(request , obj)