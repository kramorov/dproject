import os
from django.apps import apps
from django.conf import settings

# Путь для сохранения сериализаторов
SERIALIZERS_DIR = os.path.join(settings.BASE_DIR, 'serializers')

# Создаем папку, если её нет
os.makedirs(SERIALIZERS_DIR, exist_ok=True)

# Получаем все модели проекта
models = apps.get_models()

# Шаблон для сериализатора
SERIALIZER_TEMPLATE = """
from rest_framework import serializers
from {app_name}.models import {model_name}

class {model_name}Serializer(serializers.ModelSerializer):
    class Meta:
        model = {model_name}
        fields = '__all__'
"""

# Генерация сериализаторов
for model in models:
    app_name = model._meta.app_label
    model_name = model.__name__
    serializer_name = f"{model_name}Serializer"

    # Создаем файл сериализатора
    with open(os.path.join(SERIALIZERS_DIR, f"{model_name.lower()}_serializer.py"), "w") as f:
        f.write(SERIALIZER_TEMPLATE.format(
            app_name=app_name,
            model_name=model_name,
            serializer_name=serializer_name,
        ))

print(f"Сериализаторы созданы в папке {SERIALIZERS_DIR}")