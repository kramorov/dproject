from rest_framework import serializers
from django.apps import apps
from django.utils.text import capfirst
from django.db import models


def get_model_serializer(model, depth=0):
    """Динамически создает сериализатор для любой модели Django."""
    meta_attrs = {
        'model': model,
        'fields': '__all__',
        'depth': depth,
    }
    Meta = type('Meta', (), meta_attrs)

    serializer_attrs = {
        'Meta': Meta,
        'model_name': serializers.CharField(default=model.__name__, read_only=True),
    }

    serializer_name = f"{model.__name__}Serializer"
    return type(serializer_name, (serializers.ModelSerializer,), serializer_attrs)


def get_model_field_info(model):
    """Возвращает метаданные полей модели."""
    field_info = []
    print('get_model_field_info', model)

    for field in model._meta.get_fields():
        # Обработка значения по умолчанию
        default = None
        if hasattr(field , 'default') :
            if field.default == models.NOT_PROVIDED :
                default = None
            elif callable(field.default) :  # Для UUIDField.default=uuid.uuid4
                default = "callable"
            else :
                default = field.default
        field_data = {
            'name': field.name,
            'type': field.get_internal_type() if hasattr(field, 'get_internal_type') else type(field).__name__,
            'verbose_name': getattr(field, 'verbose_name', None),
            'help_text': getattr(field, 'help_text', None),
            # 'null': getattr(field, 'null', None),
            # 'blank': getattr(field, 'blank', None),
            'default': default,
            'max_length': getattr(field, 'max_length', None),
            # 'unique': getattr(field, 'unique', None),
            # 'editable': getattr(field, 'editable', None),
            'choices': getattr(field, 'choices', None),
        }

        # Для ForeignKey, OneToOne, ManyToMany
        if hasattr(field, 'related_model') and field.related_model:
            field_data.update({
                'type': 'Relation',
                'related_model': field.related_model.__name__,
                'related_app': field.related_model._meta.app_label,
                'related_name': getattr(field, 'related_name', None),
                'on_delete': str(getattr(field, 'on_delete', None)),
            })
        field_info.append(field_data)
    return field_info

def get_app_models(app_name):
    """Возвращает список всех моделей в указанном приложении."""
    try:
        app_config = apps.get_app_config(app_name)
        return [
            {
                "model_name": model.__name__,
                "verbose_name": model._meta.verbose_name,
            }
            for model in app_config.get_models()
        ]
    except LookupError:
        return None

# 5. Примеры запросов
# 1. Получить все объекты модели app1.Book
# GET /api/universal/?model=app1.Book
# 2. Получить структуру модели app2.Author
# GET /api/universal/?model=app2.Author&action=form-structure
# 3. Получить книгу с id=5 (глубина вложенности=2)
# GET /api/universal/?model=app1.Book&id=5&depth=2
# 4. Отфильтровать книги по year=2023
# GET /api/universal/?model=app1.Book&year=2023
# 6. Дополнительные улучшения
# Поддержка POST/PUT/DELETE
# Можно расширить UniversalAPIView:
#
# python
# class UniversalAPIView(APIView):
#     def post(self, request):
#         model_name = request.data.get('model')
#         model = apps.get_model(*model_name.split('.'))
#         serializer_class = get_model_serializer(model)
#         serializer = serializer_class(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=201)
#         return Response(serializer.errors, status=400)
# Пагинация
# Добавить в get():
#
# python
# from rest_framework.pagination import PageNumberPagination
#
# class UniversalAPIView(APIView):
#     def get(self, request):
#         # ... (предыдущий код)
#         paginator = PageNumberPagination()
#         paginated_queryset = paginator.paginate_queryset(queryset, request)
#         serializer = serializer_class(paginated_queryset, many=True)
#         return paginator.get_paginated_response(serializer.data)