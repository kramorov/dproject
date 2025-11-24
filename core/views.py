from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.apps import apps
from django.db.models import Q
from .serializers import get_model_serializer, get_model_field_info, get_app_models


class UniversalAPIView(APIView):
    """
    Универсальная вьюха для работы с любыми моделями.
    Доступные параметры:
    - ?model=app_name.ModelName (обязательно)
    - ?depth=N (глубина вложенности)
    - ?filter_field=value (фильтрация)
    - ?action=form-structure (получить структуру модели)
    - ?id=PK (получить один объект)
    """
    def get(self, request):
        model_name = request.query_params.get('model')
        app_name = request.query_params.get('app')
        action = request.query_params.get('action')

        # Если запрошен список моделей приложения
        if app_name and not model_name:
            models_list = get_app_models(app_name)
            if models_list is None:
                return Response(
                    {"error": f"App '{app_name}' not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response({"app": app_name, "models": models_list})

        if not model_name:
            return Response(
                {"error": "Parameter 'model' (app_name.ModelName) is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            app_name, model_name = model_name.split('.')
            model = apps.get_model(app_name, model_name)
        except (ValueError, LookupError) as e:
            return Response(
                {"error": f"Model {model_name} not found. Error: {str(e)}"},
                status=status.HTTP_404_NOT_FOUND,
            )
        # Если запрошена мета-информация модели
        if action == 'model-meta':
            if not model_name:
                return Response({"error": "Parameter 'model' is required for model-meta"}, status=400)

            try:
                app_name, model_name = model_name.split('.')
                model = apps.get_model(app_name, model_name)
            except (ValueError, LookupError) as e:
                return Response({"error": f"Model not found: {str(e)}"}, status=404)

            meta_info = {
                'model': model.__name__,
                'app': model._meta.app_label,
                'verbose_name': model._meta.verbose_name,
                'verbose_name_plural': model._meta.verbose_name_plural,
                'db_table': model._meta.db_table,
                'abstract': model._meta.abstract,
                'fields': get_model_field_info(model),
            }
            return Response(meta_info)

        if action == 'form-structure':
            return Response(get_model_field_info(model))

        if 'id' in request.query_params:
            try:
                obj = model.objects.get(pk=request.query_params['id'])
                serializer = get_model_serializer(model, depth=int(request.query_params.get('depth', 0)))(obj)
                return Response(serializer.data)
            except model.DoesNotExist:
                return Response(
                    {"error": "Object not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Фильтрация (поддержка ?field=value)
        filters = {
            key: value
            for key, value in request.query_params.items()
            if key not in {'model', 'depth', 'action', 'id'}
        }
        queryset = model.objects.filter(**filters) if filters else model.objects.all()

        # Сериализация с учетом глубины
        serializer_class = get_model_serializer(model, depth=int(request.query_params.get('depth', 0)))
        serializer = serializer_class(queryset, many=True)
        return Response(serializer.data)