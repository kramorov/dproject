# storage_manager/__init__.py
from django.conf import settings
from .storage_backends.local import LocalStorage
from .storage_backends.cloudru import CloudRuStorage


def get_storage(backend=None) :
    """
    Фабрика для получения хранилища.
    Поддерживает: 'local', 'cloudru'
    """
    backend = backend or getattr(settings, 'FILE_STORAGE_BACKEND', 'local')

    if backend == 'cloudru':
        return CloudRuStorage()
    elif backend == 'local':
        return LocalStorage()
    else:
        raise ValueError(f"Unknown storage backend: {backend}")


# Глобальный экземпляр хранилища
default_storage = get_storage()
