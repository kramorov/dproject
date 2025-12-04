from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.apps import apps
from django.db.models import Q
from .serializers import get_model_serializer , get_model_field_info , get_app_models


class UniversalAPIView(APIView) :
    """
    Универсальная вьюха для работы с любыми моделями.
    Поддерживает StructuredDataMixin методы.

    Доступные параметры:
    - model (обязательно): app_name.ModelName
    - app: имя приложения (для получения списка моделей)
    - action: form-structure, model-meta
    - id: получить один объект
    - format: serializer (default), compact, display, full
    - view: list, card, detail, badge (только для format=display)
    - depth: глубина вложенности сериализатора
    - include: список включений для full формата (form,metadata,related,certificates)
    - filter_field=value: фильтрация по полям

    Примеры запросов:
    GET /api/core/?model=pneumatic_actuators.PneumaticActuatorModelLine&id=1&format=compact
    GET /api/core/?model=pneumatic_actuators.PneumaticActuatorModelLine&format=display&view=card
    GET /api/core/?model=pneumatic_actuators.PneumaticActuatorModelLine&action=form-structure
    GET /api/core/?app=pneumatic_actuators
    """

    def get(self , request) :
        model_name = request.query_params.get('model')
        app_name = request.query_params.get('app')
        action = request.query_params.get('action')
        data_format = request.query_params.get('format' , 'serializer')
        view_type = request.query_params.get('view' , 'detail')
        obj_id = request.query_params.get('id')
        depth = int(request.query_params.get('depth' , 0))

        # Если запрошен список моделей приложения
        if app_name and not model_name :
            models_list = get_app_models(app_name)
            if models_list is None :
                return Response(
                    {"error" : f"App '{app_name}' not found"} ,
                    status=status.HTTP_404_NOT_FOUND ,
                )
            return Response({
                "success" : True ,
                "app" : app_name ,
                "models" : models_list
            })

        if not model_name :
            return Response(
                {"error" : "Parameter 'model' (app_name.ModelName) is required"} ,
                status=status.HTTP_400_BAD_REQUEST ,
            )

        try :
            app_name , model_name = model_name.split('.')
            model = apps.get_model(app_name , model_name)
        except (ValueError , LookupError) as e :
            return Response(
                {"error" : f"Model {model_name} not found. Error: {str(e)}"} ,
                status=status.HTTP_404_NOT_FOUND ,
            )

        # Если запрошена мета-информация модели
        if action == 'model-meta' :
            meta_info = {
                'model' : model.__name__ ,
                'app' : model._meta.app_label ,
                'verbose_name' : model._meta.verbose_name ,
                'verbose_name_plural' : model._meta.verbose_name_plural ,
                'db_table' : model._meta.db_table ,
                'abstract' : model._meta.abstract ,
                'fields' : get_model_field_info(model) ,
                'has_structured_data' : hasattr(model() , 'get_compact_data') ,
            }
            return Response({
                'success' : True ,
                'data' : meta_info
            })

        # Если запрошена структура формы
        if action == 'form-structure' :
            return Response({
                'success' : True ,
                'model' : model.__name__ ,
                'app' : app_name ,
                'fields' : get_model_field_info(model) ,
            })

        # Если запрошен один объект
        if obj_id :
            try :
                obj = model.objects.get(pk=obj_id)

                response_data = {
                    'success' : True ,
                    'model' : model.__name__ ,
                    'app' : app_name ,
                    'id' : obj_id ,
                }

                # Используем методы из StructuredDataMixin если они есть
                if hasattr(obj , 'get_compact_data') :
                    if data_format == 'compact' :
                        response_data['data'] = obj.get_compact_data()
                        response_data['format'] = 'compact'

                    elif data_format == 'display' :
                        response_data['data'] = obj.get_display_data(view_type)
                        response_data['format'] = 'display'
                        response_data['view'] = view_type

                    elif data_format == 'full' :
                        include = request.query_params.get('include' , 'form,metadata,related').split(',')
                        response_data['data'] = obj.get_full_data(include)
                        response_data['format'] = 'full'
                        response_data['include'] = include

                    else :  # serializer (default)
                        serializer_class = get_model_serializer(model , depth=depth)
                        serializer = serializer_class(obj)
                        response_data['data'] = serializer.data
                        response_data['format'] = 'serializer'

                else :
                    # Fallback к стандартному сериализатору
                    serializer_class = get_model_serializer(model , depth=depth)
                    serializer = serializer_class(obj)
                    response_data['data'] = serializer.data
                    response_data['format'] = 'serializer'

                # Добавляем URL если есть методы
                if hasattr(obj , 'get_absolute_url') :
                    response_data['urls'] = {
                        'absolute' : obj.get_absolute_url() ,
                        'admin' : obj.get_admin_url() if hasattr(obj , 'get_admin_url') else None ,
                    }

                return Response(response_data)

            except model.DoesNotExist :
                return Response(
                    {"success" : False , "error" : "Object not found"} ,
                    status=status.HTTP_404_NOT_FOUND ,
                )

        # СПИСОК ОБЪЕКТОВ
        response_data = {
            'success' : True ,
            'model' : model.__name__ ,
            'app' : app_name ,
            'format' : data_format ,
        }

        # Фильтрация
        filters = {}
        exclude_filters = {'model' , 'app' , 'action' , 'id' , 'format' , 'view' , 'depth' , 'include'}

        for key , value in request.query_params.items() :
            if key not in exclude_filters :
                # Поддержка сложных фильтров: field__contains, field__in и т.д.
                if '__' in key :
                    filters[key] = value
                else :
                    # Простые фильтры
                    filters[key] = value

        # Базовый queryset
        if hasattr(model , 'is_active') :
            queryset = model.objects.filter(is_active=True)
        else :
            queryset = model.objects.all()

        # Применяем фильтры
        if filters :
            try :
                queryset = queryset.filter(**filters)
            except Exception as e :
                return Response({
                    'success' : False ,
                    'error' : f'Filter error: {str(e)}' ,
                    'filters' : filters
                } , status=status.HTTP_400_BAD_REQUEST)

        # Используем методы StructuredDataMixin для списка если доступно
        if data_format == 'compact' and hasattr(model() , 'get_compact_data') :
            data = []
            for obj in queryset :
                data.append(obj.get_compact_data())

            response_data['count'] = len(data)
            response_data['data'] = data

        elif data_format == 'display' and hasattr(model() , 'get_display_data') :
            data = []
            for obj in queryset :
                display_data = obj.get_display_data('list')  # Для списков используем 'list' view
                if isinstance(display_data , dict) and 'fields' in display_data :
                    # Преобразуем fields в плоскую структуру для таблиц
                    flat_data = {'id' : obj.id}
                    for field_name , field_data in display_data['fields'].items() :
                        flat_data[field_name] = field_data.get('formatted' , field_data.get('value'))
                    data.append(flat_data)
                else :
                    data.append(display_data)

            response_data['count'] = len(data)
            response_data['data'] = data
            response_data['view'] = 'list'

        else :
            # Стандартный сериализатор
            serializer_class = get_model_serializer(model , depth=depth)
            serializer = serializer_class(queryset , many=True)

            response_data['count'] = len(serializer.data)
            response_data['data'] = serializer.data
            response_data[
                'format'] = 'serializer' if data_format == 'serializer' else f'serializer (requested: {data_format})'

        return Response(response_data)