# storage_manager/__init__.py
from django.conf import settings
from .storage_backends.local import LocalStorage
# from .storage_backends.yandex_cloud import YandexCloudStorage


def get_storage(backend=None) :
    """
    Фабрика для получения хранилища
    """
    # Пока используем только локальное хранилище
    return LocalStorage()
    # backend = backend or getattr(settings , 'FILE_STORAGE_BACKEND' , 'local')
    #
    # if backend == 'yandex_cloud' :
    #     return YandexCloudStorage()
    # elif backend == 'local' :
    #     return LocalStorage()
    # else :
    #     raise ValueError(f"Unknown storage backend: {backend}")


# Глобальный экземпляр хранилища
default_storage = get_storage()