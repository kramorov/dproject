# storage_manager/storage_backends/local.py
import os
from django.core.files.storage import FileSystemStorage
from .base import BaseStorage


class LocalStorage(BaseStorage , FileSystemStorage) :
    """
    Локальное хранилище с хешированной структурой папок
    """

    def __init__(self , location=None , base_url=None) :
        if location is None :
            from django.conf import settings
            location = settings.MEDIA_ROOT

        if base_url is None :
            from django.conf import settings
            base_url = settings.MEDIA_URL

        super().__init__(location , base_url)
        FileSystemStorage.__init__(self , location , base_url)

    def _save(self , name , content) :
        return FileSystemStorage._save(self , name , content)

    def _open(self , name , mode='rb') :
        return FileSystemStorage._open(self , name , mode)

    def delete(self , name) :
        return FileSystemStorage.delete(self , name)

    def exists(self , name) :
        return FileSystemStorage.exists(self , name)

    def size(self , name) :
        return FileSystemStorage.size(self , name)

    def url(self , name) :
        return FileSystemStorage.url(self , name)