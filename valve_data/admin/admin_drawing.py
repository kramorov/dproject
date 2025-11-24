# # valve_data/admin/admin_drawing.py
# import logging
# from django.contrib import admin
# from django.utils.html import format_html
# from valve_data.models.drawing_models import DimensionTableDrawing
#
# # Создаем логгер для этого модуля
# logger = logging.getLogger('valve_data')
#
#
# @admin.register(DimensionTableDrawing)
# class DimensionTableDrawingAdmin(admin.ModelAdmin) :
#     list_display = [
#         'name' , 'dimension_table' , 'file_type' , 'file_size_display' ,
#         'is_active' , 'created_at' , 'applicable_dns_display'
#     ]
#     list_filter = ['dimension_table' , 'file_type' , 'is_active']
#     search_fields = ['name' , 'description']
#
#     # ЗАМЕНЯЕМ inline на filter_horizontal для ManyToMany поля
#     filter_horizontal = ('allowed_dn' ,)
#
#     # Убираем inline, так как используем filter_horizontal
#     # inlines = [DrawingDnRelationInline]
#
#     # ДОБАВИТЬ: поле только для чтения с информацией о файле
#     readonly_fields = ['file_info_display' , 'created_at' , 'updated_at' , 'applicable_dns_list']
#
#     fieldsets = (
#         ('Основная информация' , {
#             'fields' : (
#                 'dimension_table' , 'name' , 'description' ,
#                 'drawing_file' , 'file_info_display'
#             )
#         }) ,
#         ('Применимые DN' , {
#             'fields' : (
#                 'allowed_dn' ,  # Будет отображаться как два окна
#                 'applicable_dns_list' ,  # Только для чтения - список текущих DN
#             )
#         }) ,
#         ('Дополнительные настройки' , {
#             'fields' : (
#                 'file_type' , 'sorting_order' , 'is_active' ,
#                 'created_at' , 'updated_at'
#             )
#         }) ,
#     )
#
#     def applicable_dns_display(self , obj) :
#         """Отображает DN в списке"""
#         dns = obj.allowed_dn.all()
#         if dns :
#             return ", ".join([f"DN{dn.name}" for dn in dns])
#         return "Все DN"
#
#     applicable_dns_display.short_description = "Применимые DN"
#
#     def applicable_dns_list(self , obj) :
#         """Отображает список применимых DN в виде читаемого списка"""
#         if not obj.pk :
#             return "Сохраните чертеж чтобы управлять DN"
#
#         dns = obj.allowed_dn.all()
#         if not dns :
#             return format_html(
#                 '<div style="color: #666; font-style: italic;">Общий чертеж для всех DN</div>'
#             )
#
#         dn_list = "".join([f"<li>DN{dn.name}</li>" for dn in dns])
#         return format_html(
#             f'<div style="margin: 10px 0;">'
#             f'<strong>Текущие применимые DN:</strong>'
#             f'<ul style="margin: 5px 0; padding-left: 20px;">{dn_list}</ul>'
#             f'</div>'
#         )
#
#     applicable_dns_list.short_description = "Текущие DN"
#
#     def file_info_display(self , obj) :
#         """Отображает информацию о файле в админке"""
#         logger.debug(f"Отображение информации о файле для чертежа {obj.id}")
#
#         try :
#             if obj.drawing_file :
#                 info = obj.get_file_info()
#                 if info :
#                     logger.debug(
#                         f"Информация о файле получена: размер={obj.file_size_display}, путь={info.get('path' , '')}")
#                     return format_html(
#                         """
#                         <div style="padding: 10px; background: #f8f9fa; border-radius: 5px;">
#                             <strong>Информация о файле:</strong><br>
#                             Имя: {}<br>
#                             Размер: {}<br>
#                             Путь: {}<br>
#                             <a href="{}" target="_blank">📎 Скачать файл</a>
#                         </div>
#                         """ ,
#                         info.get('name' , '') ,
#                         obj.file_size_display ,
#                         info.get('path' , '') ,
#                         obj.file_url
#                     )
#             logger.debug("Файл не загружен или информация недоступна")
#             return "Файл не загружен"
#
#         except Exception as e :
#             logger.error(f"Ошибка при отображении информации о файле для чертежа {obj.id}: {str(e)}")
#             return format_html(
#                 '<div style="color: red;">Ошибка при получении информации о файле: {}</div>' ,
#                 str(e)
#             )
#
#     file_info_display.short_description = "Информация о файле"
#
#     def save_model(self , request , obj , form , change) :
#         """Логирование сохранения модели"""
#         logger.info(f"save_model Сохранение DimensionTableDrawing: id={obj.id}, name={obj.name}, change={change}")
#         logger.debug(f"save_model Данные формы: {form.cleaned_data}")
#
#         try :
#             logger.info(f"Вызываем super().save_model(request, obj, form, change)")
#             super().save_model(request , obj , form , change)
#             logger.info(f"DimensionTableDrawing успешно сохранен: {obj}")
#
#             # Логируем информацию о файле после сохранения
#             if obj.drawing_file :
#                 logger.debug(
#                     f"Файл чертежа: {obj.drawing_file.name}, тип: {obj.file_type}, размер: {obj.file_size_display}")
#
#         except Exception as e :
#             logger.error(f"Ошибка при сохранении DimensionTableDrawing {obj.id}: {str(e)}" , exc_info=True)
#             raise
#
#     def save_related(self , request , form , formsets , change) :
#         """Логирование сохранения связанных объектов (ManyToMany)"""
#         logger.debug(f"Сохранение связанных объектов для DimensionTableDrawing: change={change}")
#
#         try :
#             super().save_related(request , form , formsets , change)
#
#             # Логируем сохраненные DN
#             obj = form.instance
#             dns = obj.allowed_dn.all()
#             logger.info(f"Сохранены применимые DN для чертежа {obj.id}: {[f'DN{dn.name}' for dn in dns]}")
#
#         except Exception as e :
#             logger.error(f"Ошибка при сохранении связанных объектов: {str(e)}" , exc_info=True)
#             raise
#
#     def delete_model(self , request , obj) :
#         """Логирование удаления модели"""
#         logger.warning(f"Удаление DimensionTableDrawing: id={obj.id}, name={obj.name}")
#
#         # Логируем информацию о файле перед удалением
#         if obj.drawing_file :
#             logger.debug(f"Будет удален файл: {obj.drawing_file.name}")
#
#         try :
#             super().delete_model(request , obj)
#             logger.info(f"DimensionTableDrawing успешно удален: id={obj.id}, name={obj.name}")
#         except Exception as e :
#             logger.error(f"Ошибка при удалении DimensionTableDrawing {obj.id}: {str(e)}" , exc_info=True)
#             raise
#
#     def response_add(self , request , obj , post_url_continue=None) :
#         """Логирование после добавления объекта"""
#         logger.debug(f"Ответ после добавления DimensionTableDrawing: id={obj.id}")
#         response = super().response_add(request , obj , post_url_continue)
#         logger.info(f"DimensionTableDrawing добавлен: {obj}")
#         return response
#
#     def response_change(self , request , obj) :
#         """Логирование после изменения объекта"""
#         logger.debug(f"Ответ после изменения DimensionTableDrawing: id={obj.id}")
#         response = super().response_change(request , obj)
#         logger.info(f"DimensionTableDrawing изменен: {obj}")
#         return response
#
#     def response_delete(self , request , obj_display , obj_id) :
#         """Логирование после удаления объекта"""
#         logger.debug(f"Ответ после удаления DimensionTableDrawing: id={obj_id}")
#         response = super().response_delete(request , obj_display , obj_id)
#         logger.info(f"DimensionTableDrawing удален: id={obj_id}, display={obj_display}")
#         return response
#
#     def get_queryset(self , request) :
#         """Логирование запроса queryset"""
#         logger.debug(f"Запрос queryset для DimensionTableDrawingAdmin пользователем: {request.user}")
#         queryset = super().get_queryset(request)
#         logger.debug(f"Queryset возвращает {queryset.count()} объектов")
#         return queryset
#
#     def render_change_form(self , request , context , add=False , change=False , form_url='' , obj=None) :
#         """Логирование рендеринга формы изменения"""
#         if add :
#             logger.debug("Рендеринг формы добавления нового чертежа")
#         elif change and obj :
#             logger.debug(f"Рендеринг формы изменения чертежа: id={obj.id}, name={obj.name}")
#
#         return super().render_change_form(request , context , add , change , form_url , obj)
#
#     def log_addition(self , request , object , message) :
#         """Логирование добавления объекта в history"""
#         logger.debug(f"Log addition: {object}, message: {message}")
#         super().log_addition(request , object , message)
#
#     def log_change(self , request , object , message) :
#         """Логирование изменения объекта в history"""
#         logger.debug(f"Log change: {object}, message: {message}")
#         super().log_change(request , object , message)
#
#     def log_deletion(self , request , object , object_repr) :
#         """Логирование удаления объекта в history"""
#         logger.debug(f"Log deletion: {object}, object_repr: {object_repr}")
#         super().log_deletion(request , object , object_repr)
#
#     def formfield_for_dbfield(self , db_field , request , **kwargs) :
#         """Логирование для полей формы"""
#         logger.debug(f"Генерация поля формы для: {db_field.name}")
#         return super().formfield_for_dbfield(db_field , request , **kwargs)