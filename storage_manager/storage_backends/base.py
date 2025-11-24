# storage_manager/storage_backends/base.py
import os
import uuid
import hashlib
from abc import ABC , abstractmethod
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
import logging

logger = logging.getLogger('storage_manager')

@deconstructible
class BaseStorage(Storage , ABC) :
    """
    Абстрактный базовый класс для всех хранилищ
    """

    def __init__(self , location=None , base_url=None) :
        self.location = location
        self.base_url = base_url

    @abstractmethod
    def _save(self , name , content) :
        pass

    @abstractmethod
    def _open(self , name , mode='rb') :
        pass

    @abstractmethod
    def delete(self , name) :
        pass

    @abstractmethod
    def exists(self , name) :
        pass

    @abstractmethod
    def size(self , name) :
        pass

    @abstractmethod
    def url(self , name) :
        pass

    def generate_filename(self , instance , filename , category='files') :
        """
        Генерирует оптимальное имя файла с хешированием
        """
        logger.info(f"🔍 BaseStorage.generate_filename вызван:")
        logger.info(f"   - instance: {instance.__class__.__name__} (id: {getattr(instance , 'id' , 'new')})")
        logger.info(f"   - filename: {filename}")
        logger.info(f"   - category: {category}")  # ← СМОТРИМ КАКАЯ КАТЕГОРИЯ ПРИХОДИТ
        # Извлекаем информацию о модели
        model_name = instance.__class__.__name__.lower()
        instance_id = getattr(instance , 'id' , 'temp')

        # Генерируем хеш для распределения по папкам
        hash_input = f"{filename}_{instance_id}_{uuid.uuid4().hex[:8]}"
        file_hash = hashlib.md5(hash_input.encode()).hexdigest()

        # Извлекаем расширение
        _ , ext = os.path.splitext(filename)
        ext = ext.lower()

        # Структура: category/model/ab/cd/abcdef.ext
        path_parts = [
            category ,
            model_name ,
            file_hash[0 :2] ,  # первые 2 символа хеша
            file_hash[2 :4] ,  # следующие 2 символа
            f"{file_hash}{ext}"
        ]

        return os.path.join(*path_parts)

    def get_available_name(self , name , max_length=None) :
        """
        Генерирует уникальное имя файла
        """
        dir_name , file_name = os.path.split(name)
        file_root , file_ext = os.path.splitext(file_name)

        # Если файл уже существует, добавляем суффикс
        counter = 0
        while self.exists(name) :
            counter += 1
            name = os.path.join(
                dir_name ,
                f"{file_root}_{counter:02d}{file_ext}"
            )

        return name