# core/models/__init__.py
"""
Инициализация моделей ядра системы.

Использование:
    from core.models import BaseModel, StructuredDataMixin, TimestampMixin
    from core.models import get_model_by_name, get_all_models_with_mixin
"""

import sys
from django.apps import apps
from django.db.models import Model

# Импортируем все из модулей для удобного доступа
from .base import BaseAbstractModel
from .mixins import (
    StructuredDataMixin ,
    TimestampMixin ,
    SoftDeleteMixin ,
)

# Экспортируем всё что нужно наружу
__all__ = [
    # Базовые модели
    'BaseAbstractModel',

    # Миксины
    'StructuredDataMixin' ,
    'TimestampMixin' ,
    'SoftDeleteMixin' ,

    # Утилиты
    'get_model_by_name' ,
    'get_all_models_with_mixin' ,
    'get_all_base_models' ,
    'register_model_signal' ,
]

# Регистрируем модели для Django
default_app_config = 'core.apps.CoreConfig'


# Вспомогательные функции для работы с моделями
def get_model_by_name(model_name: str , app_label: str = None) :
    """
    Получить модель по имени.

    Args:
        model_name: имя модели (например, 'CertData')
        app_label: имя приложения (опционально)

    Returns:
        Класс модели или None

    Пример:
        >>> CertData = get_model_by_name('CertData', 'certificates')
    """
    try :
        if app_label :
            return apps.get_model(app_label , model_name)
        else :
            # Ищем во всех установленных приложениях
            for app_config in apps.get_app_configs() :
                try :
                    return app_config.get_model(model_name)
                except LookupError :
                    continue
    except LookupError :
        return None


def get_all_models_with_mixin(mixin_class) :
    """
    Получить все модели, которые используют указанный миксин.

    Args:
        mixin_class: класс миксина

    Returns:
        Список классов моделей

    Пример:
        >>> models_with_data = get_all_models_with_mixin(StructuredDataMixin)
    """
    models_with_mixin = []

    for app_config in apps.get_app_configs() :
        for model in app_config.get_models() :
            if issubclass(model , mixin_class) and model != mixin_class :
                models_with_mixin.append(model)

    return models_with_mixin


def get_all_base_models() :
    """
    Получить все модели, которые наследуются от BaseModel.
    """
    return get_all_models_with_mixin(BaseAbstractModel)


def get_models_for_admin() :
    """
    Получить модели для автоматической регистрации в админке.

    Returns:
        Список кортежей (модель, админ-класс)
    """
    models_list = []

    # Здесь можно добавить логику автоматического обнаружения
    # моделей, которые нужно зарегистрировать в админке

    return models_list


def register_model_signal(signal , receiver , sender=None) :
    """
    Универсальная регистрация сигналов для моделей.

    Args:
        signal: сигнал Django
        receiver: функция-обработчик
        sender: отправитель (модель), если None - для всех моделей
    """
    from django.db.models.signals import post_save , pre_save , post_delete

    if sender is None :
        # Регистрируем для всех моделей BaseModel
        for model in get_all_base_models() :
            signal.connect(receiver , sender=model)
    else :
        signal.connect(receiver , sender=sender)


# Автоматическая проверка при импорте
def _validate_model_structure() :
    """
    Валидация структуры моделей при запуске.
    Проверяет, что все модели BaseModel реализуют required методы.
    """
    import inspect

    if 'test' in sys.argv or 'migrate' in sys.argv :
        # Пропускаем проверку во время тестов и миграций
        return

    required_methods = ['get_compact_data' , 'get_display_data' , 'get_full_data']

    for model in get_all_base_models() :
        for method_name in required_methods :
            if not hasattr(model , method_name) :
                print(f"⚠️  Внимание: Модель {model.__name__} не реализует {method_name}()")

            # Проверяем, что метод не абстрактный (не из миксина)
            method = getattr(model , method_name , None)
            if method and hasattr(method , '__qualname__') :
                if 'StructuredDataMixin' in method.__qualname__ :
                    print(f"❌ Ошибка: Модель {model.__name__} должна переопределить {method_name}()")


# Опционально: вызываем валидацию при импорте
# _validate_model_structure()

# Информация о модуле
__version__ = '1.0.0'
__author__ = 'Sergey Kramorov'
__description__ = 'Базовые модели и миксины для Django проекта'