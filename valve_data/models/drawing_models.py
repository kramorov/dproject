# valve_data/models/drawing_models.py
import os
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from storage_manager.fields import ManagedFileField  # Импортируем кастомное поле
from storage_manager.services import file_service
import logging

logger = logging.getLogger('valve_data')
#
# class DimensionTableDrawing(models.Model) :
#     """Чертеж для таблицы весо-габаритных характеристик"""
#     dimension_table = models.ForeignKey(
#         'ValveDimensionData' ,
#         related_name='drawings_data' ,
#         on_delete=models.CASCADE ,
#         verbose_name=_("Таблица ВГХ") ,
#         help_text=_("Таблица ВГХ, которую иллюстрирует этот чертеж")
#     )
#     name = models.CharField(
#         max_length=200 ,
#         verbose_name=_("Название чертежа") ,
#         help_text=_("Название чертежа (например, 'Общий вид', 'Габаритные размеры')")
#     )
#     description = models.TextField(
#         blank=True ,
#         null=True ,
#         verbose_name=_("Описание чертежа") ,
#         help_text=_("Подробное описание чертежа и что на нем изображено")
#     )
#
#     # ИЗМЕНИТЬ: использовать ManagedFileField вместо обычного FileField
#     drawing_file = ManagedFileField(
#         blank=True, null=True,
#         category='valve_drawings' ,  # ДОБАВИТЬ: категория для структуры папок
#         verbose_name=_("Файл чертежа") ,
#         help_text=_("Загрузите файл чертежа (PDF, JPG, PNG, DWF)")
#     )
#
#     file_type = models.CharField(
#         max_length=10 ,
#         blank=True ,
#         choices=[
#             ('PDF' , 'PDF') ,
#             ('JPG' , 'JPG') ,
#             ('PNG' , 'PNG') ,
#             ('DWF' , 'DWF') ,
#             ('DWG' , 'DWG') ,
#         ] ,
#         verbose_name=_("Тип файла")
#     )
#
#     # Связь с DN для  чертежей
#     allowed_dn = models.ManyToManyField(
#         'params.DnVariety' ,
#         blank=True ,
#         related_name='allowed_dn' ,
#         verbose_name=_("Применимые DN") ,
#         help_text=_("DN, для которых применим этот чертеж.")
#     )
#
#     sorting_order = models.IntegerField(
#         default=0 ,
#         verbose_name=_("Порядок сортировки")
#     )
#     is_active = models.BooleanField(
#         default=True ,
#         verbose_name=_("Активный")
#     )
#     created_at = models.DateTimeField(
#         auto_now_add=True ,
#         verbose_name=_("Дата создания")
#     )
#     updated_at = models.DateTimeField(  # ДОБАВИТЬ: поле для отслеживания изменений
#         auto_now=True ,
#         verbose_name=_("Дата обновления")
#     )
#
#     class Meta :
#         verbose_name = _("Чертеж таблицы ВГХ")
#         verbose_name_plural = _("Чертежи таблиц ВГХ")
#         ordering = ['sorting_order' , 'name']
#
#     def __str__(self) :
#         return f"{self.dimension_table.name} - {self.name}"
#
#     # В models/drawing_models.py
#     def save(self , *args , **kwargs) :
#         """Автоматически определяем тип файла при сохранении"""
#         logger.info(f"Начало сохранения DimensionTableDrawing id={self.id}")
#
#         try :
#             if self.drawing_file :
#                 ext = os.path.splitext(self.drawing_file.name)[1].upper().replace('.' , '')
#                 if ext in ['PDF' , 'JPG' , 'JPEG' , 'PNG' , 'DWF' , 'DWG'] :
#                     self.file_type = ext
#
#             # ДЕТАЛЬНАЯ ДИАГНОСТИКА: логируем перед вызовом super().save()
#             logger.info("ПЕРЕД вызовом super().save()")
#
#             # Получаем информацию о текущем stack trace
#             import traceback
#             stack_trace = traceback.format_stack()
#             logger.debug("Stack trace перед super().save():")
#             for line in stack_trace[-10 :] :  # Последние 10 вызовов
#                 logger.debug(line.strip())
#
#             super().save(*args , **kwargs)
#             logger.info(f"Успешно сохранено")
#
#         except Exception as e :
#             logger.error(f"Ошибка в save(): {str(e)}")
#             logger.error("Полный traceback ошибки:")
#             logger.error(traceback.format_exc())
#             raise
#
#     def clean(self) :
#         """Валидация файла чертежа"""
#         logger.info(f"Начало clean() для DimensionTableDrawing id={self.id}")
#
#         try :
#             if self.drawing_file :
#                 logger.debug(f"Валидация файла: {self.drawing_file.name}")
#                 ext = os.path.splitext(self.drawing_file.name)[1].upper()
#                 allowed_extensions = ['.PDF' , '.JPG' , '.JPEG' , '.PNG' , '.DWF' , '.DWG']
#                 logger.debug(f"Расширение: {ext}, разрешенные: {allowed_extensions}")
#
#                 if ext not in allowed_extensions :
#                     error_msg = f"Недопустимый формат файла. Разрешены: PDF, JPG, PNG, DWF, DWG"
#                     logger.error(error_msg)
#                     raise ValidationError(_(error_msg))
#
#             logger.info("Clean() завершен успешно")
#
#         except Exception as e :
#             logger.error(f"Ошибка в clean(): {str(e)}" , exc_info=True)
#             raise
#     # ДОБАВИТЬ: метод для замены файла через сервис
#     # В модели DimensionTableDrawing
#
#     def replace_drawing_file(self , new_file) :
#         """Заменяет файл чертежа без изменения ссылок через сервис"""
#         logger.info(f"Замена файла чертежа для {self.id}")
#
#         old_file_path = self.drawing_file.name if self.drawing_file else None
#         logger.debug(f"Старый путь файла: {old_file_path}")
#
#         try :
#             # Загружаем новый файл через ИСПРАВЛЕННЫЙ сервис
#             new_file_path = file_service.upload_file(
#                 self , new_file , category='valve_drawings'
#             )
#             logger.debug(f"Новый путь файла: {new_file_path}")
#
#             self.drawing_file = new_file_path
#             self.save()
#
#             # Удаляем старый файл
#             if old_file_path :
#                 logger.debug(f"Удаление старого файла: {old_file_path}")
#                 file_service.delete_file(old_file_path)
#
#             logger.info(f"Файл успешно заменен: {old_file_path} -> {new_file_path}")
#             return new_file_path
#
#         except Exception as e :
#             logger.error(f"Ошибка при замене файла чертежа: {str(e)}" , exc_info=True)
#             raise
#
#     def get_file_info(self) :
#         """Возвращает информацию о файле чертежа"""
#         logger.debug(f"Запрос информации о файле для чертежа {self.id}")
#
#         if not self.drawing_file :
#             logger.debug("Файл чертежа не установлен")
#             return None
#
#         try :
#             file_info = file_service.get_file_info(self.drawing_file.name)
#             logger.debug(f"Информация о файле получена: {file_info}")
#             return file_info
#         except Exception as e :
#             logger.error(f"Ошибка при получении информации о файле: {str(e)}")
#             return None
#
#     @property
#     def file_url(self) :
#         """URL для доступа к файлу"""
#         if self.drawing_file :
#             try :
#                 url = file_service.get_file_url(self.drawing_file.name)
#                 logger.debug(f"URL файла: {url}")
#                 return url
#             except Exception as e :
#                 logger.error(f"Ошибка при получении URL файла: {str(e)}")
#         return None
#
#     @property
#     def file_size(self) :
#         """Размер файла в байтах"""
#         if self.drawing_file and self.drawing_file.name :
#             try :
#                 size = file_service.get_file_size(self.drawing_file.name)
#                 logger.debug(f"Размер файла: {size} байт")
#                 return size
#             except Exception as e :
#                 logger.error(f"Ошибка при получении размера файла: {str(e)}")
#         return 0
#
#     # ДОБАВИТЬ: свойство для размера файла в читаемом формате
#     @property
#     def file_size_display(self) :
#         """Размер файла в читаемом формате (КБ, МБ)"""
#         size_bytes = self.file_size
#         if size_bytes == 0 :
#             return "0 Б"
#
#         for unit in ['Б' , 'КБ' , 'МБ' , 'ГБ'] :
#             if size_bytes < 1024.0 :
#                 return f"{size_bytes:.1f} {unit}"
#             size_bytes /= 1024.0
#         return f"{size_bytes:.1f} ТБ"
#
#     @property
#     def is_general(self) :
#         """Проверяет, является ли чертеж общим для всех DN"""
#         return not self.allowed_dn.exists()

