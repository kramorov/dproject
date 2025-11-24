import logging
from django.db import models
from . import get_storage

logger = logging.getLogger('storage_manager')


class ManagedFileField(models.FileField) :
    """
    Универсальное FileField для файлов и изображений с интегрированным менеджером хранилища
    """

    def __init__(self , verbose_name=None , name=None , upload_to='' ,
                 storage=None , category=None , **kwargs) :
        self.category = category or 'files'

        # Автоматически определяем категорию для изображений
        if kwargs.get('max_length') is None and 'Image' in self.__class__.__name__ :
            self.category = 'images'

        actual_storage = storage or get_storage()
        super().__init__(verbose_name , name , upload_to , actual_storage , **kwargs)

    def generate_filename(self , instance , filename) :
        """
        Генерирует имя файла с использованием менеджера хранилища
        """
        logger.info(f"🔍 ManagedFileField.generate_filename вызван:")
        logger.info(f"   - instance: {instance}")
        logger.info(f"   - filename: {filename}")
        logger.info(f"   - self.category: {self.category}")  # ← СМОТРИМ КАКАЯ КАТЕГОРИЯ У ПОЛЯ
        logger.debug(
            f"ManagedFileField.generate_filename: instance={instance}, filename={filename}, category={self.category}")

        try :
            if callable(self.upload_to) :
                filename = self.upload_to(instance , filename)
                logger.debug(f"Использована callable upload_to: {filename}")
            else :
                filename = self.storage.generate_filename(instance , filename , self.category)
                logger.debug(f"Сгенерировано хранилищем: {filename}")

            return filename

        except Exception as e :
            logger.error(f"Ошибка в ManagedFileField.generate_filename: {str(e)}")
            return super().generate_filename(instance , filename)

# ManagedImageField больше не нужен - используем ManagedFileField
# Для изображений он автоматически установит category='images'