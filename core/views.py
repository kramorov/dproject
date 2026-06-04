from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.response import Response
from rest_framework import status
from django.apps import apps
from django.db.models import Q
from .serializers import get_model_serializer , get_model_field_info , get_app_models

import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class UniversalAPIView(APIView) :
    authentication_classes = []
    permission_classes = []
    """
    Универсальная вьюха для работы с любыми моделями.
    Поддерживает StructuredDataMixin методы.

    Доступные параметры:
    - model (обязательно): app_name.ModelName
    - app: имя приложения (для получения списка моделей)
    - action: form-structure, model-meta
    - id: получить один объект
    - fmt: serializer (default), compact, display, full
    - view: list, card, detail, badge (только для fmt=display)
    - depth: глубина вложенности сериализатора
    - include: список включений для full формата (form,metadata,related,certificates)
    - filter_field=value: фильтрация по полям

    Примеры запросов:
    GET /api/core/?model=pneumatic_actuators.PneumaticActuatorModelLine&id=1&fmt=compact
    GET /api/core/?model=pneumatic_actuators.PneumaticActuatorModelLine&fmt=display&view=card
    GET /api/core/?model=pneumatic_actuators.PneumaticActuatorModelLine&action=form-structure
    GET /api/core/?app=pneumatic_actuators
    """
    def get(self , request) :
        import sys
        print("=" * 80 , file=sys.stderr)
        print(f"🔥 UniversalAPIView ВЫЗВАН!" , file=sys.stderr)
        print(f"🔥 Path: {request.path}" , file=sys.stderr)
        print(f"🔥 Full path: {request.get_full_path()}" , file=sys.stderr)
        print(f"🔥 GET: {dict(request.GET)}" , file=sys.stderr)
        sys.stderr.flush()
        # Логируем ВСЕ параметры
        logger.info(f"=== REQUEST PARAMS ===")
        for key , value in request.query_params.items() :
            logger.info(f"Key-Value:  {key}: {value}")

        model_param = request.query_params.get('model')
        logger.info(f"model param raw: '{model_param}'")

        if model_param :
            logger.info(f"model param type: {type(model_param)}")
            logger.info(f"'.' in model_param: {'.' in model_param}")

            if '.' in model_param :
                try :
                    app_name , model_name = model_param.split('.')
                    logger.info(f"Split: app='{app_name}', model='{model_name}'")

                    # Пробуем получить модель
                    model = apps.get_model(app_name , model_name)
                    logger.info(f"Model found: {model}")
                    logger.info(f"Objects count: {model.objects.count()}")

                except Exception as e :
                    logger.error(f"Error: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())

        model_name = request.query_params.get('model')
        app_name = request.query_params.get('app')
        action = request.query_params.get('action')
        data_format = request.query_params.get('fmt' , 'serializer')
        view_type = request.query_params.get('view' , 'detail')
        obj_id = request.query_params.get('id')
        depth = int(request.query_params.get('depth' , 0))

        logger.info(f"=== PROCESSING REQUEST ===")
        logger.info(f"model_name: {model_name}")
        logger.info(f"app_name: {app_name}")
        logger.info(f"obj_id: {obj_id}")
        logger.info(f"data_format: {data_format}")
        logger.info(f"view_type: {view_type}")
        logger.info(f"action: {action}")


        if not model_name and not app_name :
            return Response(
                {
                    "success" : False ,
                    "error" : "Вы не указали model_name и app_name" ,
                    "available_endpoints" : {
                        "get_model" : "/api/core/?model=app_name.ModelName" ,
                        "get_object" : "/api/core/?model=app_name.ModelName&id=1" ,
                        "list_models" : "/api/core/?app=app_name" ,
                        "model_meta" : "/api/core/?model=app_name.ModelName&action=model-meta" ,
                        "form_structure" : "/api/core/?model=app_name.ModelName&action=form-structure"
                    } ,
                    "examples" : {
                        "list_brands" : "/api/core/?model=producers.Brand" ,
                        "get_model_line" : "/api/core/?model=pneumatic_actuators.PneumaticActuatorModelLine&id=1" ,
                        "app_models" : "/api/core/?app=pneumatic_actuators"
                    }
                } ,
                status=status.HTTP_400_BAD_REQUEST ,
            )
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
        if model.__name__ == 'PneumaticActuatorModelLine' and not obj_id :
            queryset = model.objects.all()
            data = []
            for obj in queryset :
                try :
                    data.append(obj.get_compact_data())
                except Exception as e :
                    data.append({'id' : obj.id , 'error' : str(e)})

            return Response({
                'test' : True ,
                'count' : len(data) ,
                'data' : data ,
            })

        logger.info(f"Model class: {model.__name__}")
        logger.info(f"Model has get_compact_data: {hasattr(model() , 'get_compact_data')}")
        # Если запрошен один объект
        if obj_id :
            try :
                obj = model.objects.get(pk=obj_id)

                logger.info(f"=== OBJECT FOUND ===")
                logger.info(f"Object ID: {obj_id}")
                logger.info(f"Object class: {obj.__class__.__name__}")
                logger.info(f"Has get_compact_data: {hasattr(obj , 'get_compact_data')}")
                logger.info(f"Has get_display_data: {hasattr(obj , 'get_display_data')}")
                logger.info(f"Has get_full_data: {hasattr(obj , 'get_full_data')}")

                response_data = {
                    'success' : True ,
                    'model' : model.__name__ ,
                    'app' : app_name ,
                    'id' : obj_id ,
                }

                # Используем методы из StructuredDataMixin если они есть
                if hasattr(obj , 'get_compact_data') :
                    try :
                        if data_format == 'compact' :
                            logger.info("Calling get_compact_data()")
                            response_data['data'] = obj.get_compact_data()
                            response_data['format'] = 'compact'

                        elif data_format == 'display' :
                            logger.info(f"Calling get_display_data(view_type={view_type})")
                            response_data['data'] = obj.get_display_data(view_type)
                            response_data['format'] = 'display'
                            response_data['view'] = view_type

                        elif data_format == 'full' :
                            include = request.query_params.get('include' , 'form,metadata,related').split(',')
                            logger.info(f"Calling get_full_data(include={include})")
                            response_data['data'] = obj.get_full_data(include)
                            response_data['format'] = 'full'
                            response_data['include'] = include

                        else :  # serializer (default)
                            serializer_class = get_model_serializer(model , depth=depth)
                            serializer = serializer_class(obj)
                            response_data['data'] = serializer.data
                            response_data['format'] = 'serializer'

                    except Exception as e :
                        logger.error(f"Error calling StructuredDataMixin method: {str(e)}" , exc_info=True)
                        # Fallback к сериализатору при ошибке
                        serializer_class = get_model_serializer(model , depth=depth)
                        serializer = serializer_class(obj)
                        response_data['data'] = serializer.data
                        response_data['format'] = 'serializer'
                        response_data['error'] = f"StructuredDataMixin error: {str(e)}"

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
                    {
                        "success" : False ,
                        "error" : f"Object with id={obj_id} not found" ,
                        "model" : model_name ,
                        "app" : app_name ,
                        "available_ids" : list(model.objects.values_list('id' , flat=True)[:10])
                    } ,
                    status=status.HTTP_404_NOT_FOUND ,
                )
        # Если нет obj_id (список)
        if not obj_id :
            logger.info(f"Processing LIST request")
            logger.info(f"data_format: {data_format}")

            if data_format == 'compact' and hasattr(model() , 'get_compact_data') :
                logger.info(f"Using get_compact_data() for list")
                # ... твой код
            else :
                logger.info(f"Using serializer for list")


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
                logger.info(f"Processing object {obj_id} with format={data_format}")

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
                    {
                        "success" : False ,
                        "error" : f"Object with id={obj_id} not found" ,
                        "model" : model_name ,
                        "app" : app_name ,
                        "available_ids" : list(model.objects.values_list('id' , flat=True)[:10])  # покажем первые 10 ID
                    } ,
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
        exclude_filters = {'model' , 'app' , 'action' , 'id' , 'format' , 'fmt' , 'view' , 'depth' , 'include', 'limit', 'offset', 'keyword', 'search'}

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

        # Поиск по ключевому слову (маппинг 'keyword' -> 'keywords__icontains')
        keyword = request.query_params.get('keyword', '').strip()
        if keyword and hasattr(model, 'keywords'):
            queryset = queryset.filter(**{'keywords__icontains': keyword})

        # Поиск по подстроке (поддерживает поля name, code, title)
        search_query = request.query_params.get('search', '').strip()
        if search_query:
            search_q = Q()
            for field_base in ('name', 'code', 'title'):
                if hasattr(model, field_base):
                    search_q |= Q(**{f'{field_base}__icontains': search_query})
            if search_q:
                queryset = queryset.filter(search_q)

        # Пагинация
        limit_str = request.query_params.get('limit')
        limit_val = None
        offset_val = 0
        if limit_str:
            try:
                limit_val = int(limit_str)
                offset_val = int(request.query_params.get('offset', 0))
            except (ValueError, TypeError):
                limit_val = None

        def _eval_queryset(qs):
            """Оценить queryset и вернуть список данных."""
            data = []
            if data_format == 'compact' and hasattr(model(), 'get_compact_data'):
                for obj in qs:
                    data.append(obj.get_compact_data())
            elif data_format == 'display' and hasattr(model(), 'get_display_data'):
                for obj in qs:
                    disp = obj.get_display_data('list')
                    if isinstance(disp, dict) and 'fields' in disp:
                        flat = {'id': obj.id}
                        for fn, fd in disp['fields'].items():
                            flat[fn] = fd.get('formatted', fd.get('value'))
                        data.append(flat)
                    else:
                        data.append(disp)
                response_data['view'] = 'list'
            else:
                serializer_class = get_model_serializer(model, depth=depth)
                serializer = serializer_class(qs, many=True)
                data = serializer.data
            return data

        try:
            if limit_val:
                response_data['total'] = queryset.count()
                queryset = queryset[offset_val:offset_val + limit_val]
            data = _eval_queryset(queryset)
        except Exception as e:
            # Fallback: raw SQL для моделей с битыми M2M through-таблицами
            logger.warning(f'ORM list failed for {model.__name__}: {e}, falling back to raw SQL')
            from django.db import connection
            table = model._meta.db_table
            with connection.cursor() as c:
                c.execute(f'SELECT COUNT(*) FROM "{table}"')
                response_data['total'] = c.fetchone()[0]
                if limit_val:
                    c.execute(
                        f'SELECT id FROM "{table}" ORDER BY sorting_order LIMIT %s OFFSET %s',
                        [limit_val, offset_val]
                    )
                else:
                    c.execute(f'SELECT id FROM "{table}" ORDER BY sorting_order')
                ids = [r[0] for r in c.fetchall()]
            qs = model.objects.filter(id__in=ids)
            data = _eval_queryset(qs)

        response_data['count'] = len(data)
        response_data['data'] = data
        if data_format == 'serializer' or (data_format != 'compact' and data_format != 'display'):
            response_data['format'] = 'serializer' if data_format == 'serializer' else f'serializer (requested: {data_format})'

        return Response(response_data)

    def post(self, request):
        return self._write(request, 'create')

    def put(self, request):
        return self._write(request, 'update')

    def delete(self, request):
        model_param = request.query_params.get('model') or request.data.get('model')
        obj_id = request.query_params.get('id') or request.data.get('id')
        if not model_param or not obj_id:
            return Response({'error': 'model and id required'}, status=400)
        try:
            app_name, model_name = model_param.split('.')
            model = apps.get_model(app_name, model_name)
            obj = model.objects.get(pk=obj_id)
            obj.delete()
            return Response({'success': True, 'deleted': obj_id})
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    def _write(self, request, action):
        try:
            data = request.data if hasattr(request, 'data') else {}
            model_param = data.get('model') or request.query_params.get('model')
            if not model_param:
                return Response({'error': 'model required'}, status=400)
            app_name, model_name = model_param.split('.')
            model = apps.get_model(app_name, model_name)

            # M2M-поля обрабатываем отдельно (поддержка raw-SQL моделей)
            m2m_names = {f.name for f in model._meta.many_to_many}
            all_f = {k: v for k, v in data.items() if k != 'model'}
            regular = {k: v for k, v in all_f.items() if k not in m2m_names}
            m2m = {k: v for k, v in all_f.items() if k in m2m_names}

            if action == 'create':
                obj = model.objects.create(**regular)
                for fn, vals in m2m.items():
                    if vals:
                        self._set_m2m(obj, fn, vals)
                return Response({'success': True, 'id': obj.pk})
            else:
                obj_id = data.get('id') or request.query_params.get('id')
                if not obj_id:
                    return Response({'error': 'id required for update'}, status=400)
                obj = model.objects.get(pk=obj_id)
                fields = {k: v for k, v in data.items() if k not in ('model', 'id')}
                m2m_update = {}
                for field, value in fields.items():
                    if field in m2m_names:
                        m2m_update[field] = value
                    else:
                        setattr(obj, field, value)
                obj.save()
                for fn, vals in m2m_update.items():
                    if vals is not None:
                        self._set_m2m(obj, fn, vals)
                return Response({'success': True, 'id': obj.pk})
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)

    def _set_m2m(self, obj, field_name, values):
        """Установить M2M-связи. Использует raw-SQL если есть кастомный метод."""
        setter = getattr(obj, f'set_{field_name}_ids', None) or getattr(obj, f'{field_name}_set_ids', None)
        if callable(setter):
            setter(values)
        else:
            getattr(obj, field_name).set(values)


class DebugAPIView(APIView) :
    """Endpoint для диагностики"""

    def get(self , request) :
        from django.apps import apps

        response = {
            'request_params' : dict(request.query_params) ,
            'installed_apps' : [] ,
            'available_models' : {} ,
        }

        # Все установленные приложения
        for app_config in apps.get_app_configs() :
            response['installed_apps'].append({
                'name' : app_config.name ,
                'label' : app_config.label ,
                'models' : [m.__name__ for m in app_config.get_models()]
            })

            # Модели для каждого приложения
            response['available_models'][app_config.name] = [
                m.__name__ for m in app_config.get_models()
            ]

        # Если есть параметр model, пробуем его получить
        model_param = request.query_params.get('model')
        if model_param :
            response['model_param'] = model_param
            response['has_dot'] = '.' in model_param

            if '.' in model_param :
                try :
                    app_name , model_name = model_param.split('.')
                    response['split'] = {'app' : app_name , 'model' : model_name}

                    model = apps.get_model(app_name , model_name)
                    response['model_found'] = True
                    response['model_info'] = {
                        'name' : model.__name__ ,
                        'db_table' : model._meta.db_table ,
                        'objects_count' : model.objects.count() ,
                    }

                except Exception as e :
                    response['model_error'] = str(e)

        return Response(response)


class BaseFilterOptionsView(APIView):
    """
    Общий View для опций фильтров каталога — единая реализация для всех каталогов.

    New (preferred): set catalog_config = SomeCatalogConfig.
    Old (backward compat): set filter_definitions + model_class + scope_exclude.

    Пример:
        class GearboxFilterOptionsView(BaseFilterOptionsView):
            permission_classes = [AllowAny]
            catalog_config = GEARBOX_CONFIG

    Ответ (JSON):
        {
            filters: { param_name: { label, order, filter_type, options: [{id, name, code}] } },
            show_compatible: bool,
        }
        filter_type — строка ('exact', 'exd_compatible', ...) для выбора UI-компонента на фронте.
    """
    permission_classes = []
    # ── New path ──
    catalog_config = None  # CatalogConfig instance
    # ── Old path (backward compat) ──
    filter_definitions = None
    model_class = None
    scope_exclude = {
        'model_line': ['model_line_id', 'brand_id'],
    }

    def get(self, request):
        scope = request.query_params.get('scope', getattr(self, 'default_scope', 'list'))

        # ── New path: CatalogConfig ──
        if self.catalog_config is not None:
            config = self.catalog_config
            filter_set = config.get_filter_set(scope)
            model_line_id = request.query_params.get('model_line_id')

            # Scoped queryset for filter options
            base_qs = None
            if filter_set.scoped and model_line_id:
                base_qs = config.get_scoped_queryset(model_line_id)

            result = {}
            for fd in filter_set.definitions:
                try:
                    options = fd.get_options(config.model_class, queryset=base_qs)
                    # CUSTOM filters (exd_compatible, climate_cascade) may return empty list —
                    # still include them so frontend renders special UI components
                    is_custom = fd.data_source_type.value == 'custom'
                    if options or is_custom:
                        result[fd.param_name] = {
                            'label': fd.label,
                            'order': fd.order,
                            'filter_type': fd.filter_type.value,
                            'options': options,
                            'default_value': fd.default_value,
                            'show_code': fd.show_code,
                        }
                except Exception as e:
                    result[fd.param_name] = {
                        'label': fd.label,
                        'order': fd.order,
                        'options': [],
                        'error': str(e),
                    }

            return Response({
                'filters': result,
                'show_compatible': filter_set.show_compatible,
            })

        # ── Old path: filter_definitions + scope_exclude ──
        if self.filter_definitions is None:
            return Response({'error': 'filter_definitions not configured'}, status=500)

        exclude = self.scope_exclude.get(scope, [])
        result = {}
        for fd in self.filter_definitions:
            if fd.param_name in exclude:
                continue
                try:
                    options = fd.get_options(self.model_class)
                    if options:
                        result[fd.param_name] = {
                            'label': fd.label,
                            'order': fd.order,
                            'options': options,
                        }
                except Exception as e:
                    result[fd.param_name] = {
                        'label': fd.label,
                        'order': fd.order,
                        'options': [],
                        'error': str(e),
                    }

            return Response({
                'filters': result,
                'show_compatible': filter_set.show_compatible,
            })


class BaseQuickSelectView(APIView):
    """
    Общий View для «Быстрого подбора» — чипсовые фильтры + одна карточка товара.

    Заменяет EngineerCatalogView, делает паттерн доступным для всех каталогов.
    Возвращает { model_line, items, filters: { key: [{id/value, name/label, count}] } }.

    Подкласс должен определить атрибуты:
        quickselect_filters  — список param_name для быстрого подбора
        filter_definitions   — полные FILTER_DEFINITIONS
        model_class          — класс модели Django
        model_line_model     — модель серии
        select_related       — список полей для select_related
        prefetch_fields      — список полей для prefetch_related (опционально)
        auto_select_rules    — dict: { param_name: 'min'|'max' }

    См. также:
        filter_regulator/views/engineer.py  — пример использования
    """
    permission_classes = []
    quickselect_filters = None
    filter_definitions = None
    model_class = None
    model_line_model = None
    select_related = None
    prefetch_fields = None
    auto_select_rules = {}

    def get(self, request):
        params = request.query_params
        model_line_id = params.get('model_line_id')
        brand_id = params.get('brand_id')

        if not model_line_id and not brand_id:
            return Response({'error': 'model_line_id or brand_id is required'}, status=400)

        qs = self.model_class.objects.filter(is_active=True)

        if model_line_id:
            qs = qs.filter(model_line_id=model_line_id)
        if brand_id:
            qs = qs.filter(model_line__brand_id=brand_id)

        if self.select_related:
            qs = qs.select_related(*self.select_related)
        if self.prefetch_fields:
            qs = qs.prefetch_related(*self.prefetch_fields)

        # Применяем фильтры из запроса
        allowed_params = set(self.quickselect_filters or []) | {'work_temp_min', 'work_temp_max'}
        for fd in (self.filter_definitions or []):
            if fd.param_name not in allowed_params:
                continue
            value = params.get(fd.param_name)
            if value is None or value == '' or value == 'all':
                continue
            lookup, converted = fd.build_filter_lookup(value)
            if lookup and converted is not None:
                qs = qs.filter(**{lookup: converted})

        items = [obj.to_dict() for obj in qs[:50]]

        # Опции фильтров с подсчётом
        filters_out = {}
        for fd in (self.filter_definitions or []):
            if fd.param_name not in (self.quickselect_filters or []):
                continue
            options = self._get_filter_options(qs, fd)
            if options:
                filters_out[fd.param_name] = options

        ml_info = None
        if model_line_id and self.model_line_model:
            ml_info = self._get_model_line_info(model_line_id)

        return Response({
            'model_line': ml_info,
            'total': qs.count(),
            'items': items,
            'filters': filters_out,
        })

    def _get_filter_options(self, qs, fd):
        """Собрать доступные значения фильтра с подсчётом."""
        from core.models.smart_catalog_mixin import FilterType as _FT
        from django.db.models import Count
        field_name = fd.model_field

        if fd.filter_type in (_FT.EXACT,):
            try:
                parts = field_name.split('__')
                rel_model = self.model_class
                for part in parts:
                    fld = rel_model._meta.get_field(part)
                    if fld.is_relation:
                        rel_model = fld.remote_field.model

                rows = (
                    qs.values(f'{field_name}_id')
                    .annotate(count=Count('id'))
                    .order_by(f'{field_name}_id')
                )
                ids = [r[f'{field_name}_id'] for r in rows if r[f'{field_name}_id'] is not None]
                if not ids:
                    return []

                objects = rel_model.objects.filter(id__in=ids)
                obj_map = {obj.id: obj for obj in objects}

                return [
                    {'id': oid, 'name': str(obj_map[oid]), 'count': row['count']}
                    for row in rows
                    if (oid := row[f'{field_name}_id']) and oid in obj_map
                ]
            except Exception:
                return []

        elif fd.filter_type in (_FT.MIN,):
            values = (
                qs.values_list(field_name, flat=True)
                .distinct()
                .order_by(field_name)
            )
            return [
                {'value': v, 'label': str(v), 'count': qs.filter(**{f'{field_name}__gte': v}).count()}
                for v in values if v is not None
            ]

        return []

    def _get_model_line_info(self, model_line_id):
        if not self.model_line_model:
            return None
        try:
            ml = self.model_line_model.objects.get(id=model_line_id)
            return {'id': ml.id, 'name': ml.name, 'code': getattr(ml, 'code', '') or ''}
        except Exception:
            return None


class ExdStructureView(APIView):
    """GET /api/core/exd/structure/ — иерархия взрывозащиты для каскадного фильтра."""
    permission_classes = []

    def get(self, request):
        from params.exd_models import ExdOption
        return Response(ExdOption.get_structured_choices())


class ExdParseView(APIView):
    """POST /api/core/exd/parse/ — парсинг строки Exd в ID каскада."""
    permission_classes = []

    def post(self, request):
        import logging
        logging.warning(f"[ExdParseView] GOT POST: {request.data}")
        from core.models.exd_parser import ExdStringParser
        from params.exd_models import (
            ExplosionProtectionMethod, ExplosionProtectionType,
            HazardousGroup, TemperatureClass,
        )

        exd_string = request.data.get('exd_string', '').strip()
        if not exd_string:
            return Response({'error': 'Пустая строка'}, status=400)

        parsed = ExdStringParser.parse(exd_string)
        print(f"[ExdParseView] input: {exd_string!r}")
        print(f"[ExdParseView] parsed: {parsed}")
        if not parsed:
            return Response({'error': 'Не удалось распознать строку взрывозащиты'}, status=400)

        result = {}

        # Type → ID (primary: type code like 'db', 'ia'. If not found, try starts_with)
        t = None
        if parsed.protection_type_code:
            code = parsed.protection_type_code
            t = (ExplosionProtectionType.objects.filter(code__iexact=code).first()
                 or ExplosionProtectionType.objects.filter(code__startswith=code).first())
        if t:
            result['type_id'] = t.id

        # Method → ID (from type FK, or direct lookup)
        if parsed.method_code or t:
            m = None
            if t and t.method:
                m = t.method
            if not m and parsed.method_code:
                code = parsed.method_code
                m = (ExplosionProtectionMethod.objects.filter(code__iexact=code).first()
                     or ExplosionProtectionMethod.objects.filter(code__icontains=code).first())
            if m:
                result['method_id'] = m.id
            elif not t and parsed.method_code:
                return Response({'error': f'Метод "{parsed.method_code}" не найден'}, status=400)

        # Group → ID
        if parsed.group_code:
            g = HazardousGroup.objects.filter(code=parsed.group_code).first()
            if g:
                result['group_id'] = g.id
            else:
                return Response({'error': f'Группа "{parsed.group_code}" не найдена'}, status=400)

        # Temperature class → ID
        if parsed.temperature_code:
            tc = TemperatureClass.objects.filter(temperature_class=parsed.temperature_code).first()
            if tc:
                result['temp_id'] = tc.id
            else:
                return Response({'error': f'Темп. класс "{parsed.temperature_code}" не найден'}, status=400)

        print(f"[ExdParseView] returning: {result}", flush=True)
        return Response(result)


class ExdCompatibleView(APIView):
    """GET /api/core/exd/compatible/?method_id=&type_id=&group_id=&temp_id= — совместимые ExdOption."""
    permission_classes = []

    def get(self, request):
        from params.exd_models import ExdOption
        try:
            method_id = request.GET.get('method_id') or None
            type_id = request.GET.get('type_id') or None
            group_id = request.GET.get('group_id') or None
            temp_id = request.GET.get('temp_id') or None

            if method_id:
                method_id = int(method_id)
            if type_id:
                type_id = int(type_id)
            if group_id:
                group_id = int(group_id)
            if temp_id:
                temp_id = int(temp_id)

            ids = ExdOption.get_compatible_ids_by_components(
                method_id=method_id, type_id=type_id,
                group_id=group_id, temp_id=temp_id,
            )
            return Response({'ids': sorted(ids)})
        except Exception as e:
            return Response({'error': str(e), 'ids': []}, status=400)