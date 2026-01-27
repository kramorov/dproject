# features/views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.contrib.contenttypes.models import ContentType
import json

from .models import (
    EquipmentType, FeatureVariety,
    FeatureTemplate, FeatureSet
)


@login_required
@require_GET
def get_equipment_type_level(request):
    """Получить уровень типа оборудования по ID родителя"""
    parent_id = request.GET.get('parent_id')

    if parent_id:
        try:
            parent = EquipmentType.objects.get(id=parent_id)
            return JsonResponse({
                'success': True,
                'level': parent.level + 1
            })
        except EquipmentType.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Родительский тип не найден'
            })

    return JsonResponse({
        'success': True,
        'level': 0
    })


@login_required
@require_GET
def get_active_equipment_type_ids(request):
    """Получить ID всех активных типов оборудования"""
    ids = list(EquipmentType.objects.filter(is_active=True).values_list('id', flat=True))

    return JsonResponse({
        'success': True,
        'ids': ids
    })


@login_required
@require_GET
def get_features_by_equipment_type(request, equipment_type_id):
    """Получить характеристики для типа оборудования"""
    try:
        features = FeatureVariety.objects.filter(
            equipment_types=equipment_type_id,
            is_active=True
        ).order_by('sorting_order', 'name')

        features_data = []
        for feature in features:
            features_data.append({
                'id': feature.id,
                'name': feature.name,
                'code': feature.code,
                'data_type': feature.data_type,
                'data_type_display': feature.get_data_type_display(),
                'unit': feature.unit,
                'is_required': feature.is_required,
            })

        return JsonResponse({
            'success': True,
            'features': features_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST
def save_template_features(request, template_id):
    """Сохранить характеристики шаблона"""
    try:
        template = FeatureTemplate.objects.get(id=template_id)
        features_data = json.loads(request.POST.get('features', '[]'))

        # Обновляем данные шаблона
        template.features_data = features_data
        template.save()

        return JsonResponse({
            'success': True,
            'message': 'Характеристики сохранены',
            'features_table': template.get_features_table()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST
def save_featureset_values(request, featureset_id):
    """Сохранить значения характеристик набора"""
    try:
        featureset = FeatureSet.objects.get(id=featureset_id)

        # Проверяем, что набор не утвержден
        if featureset.is_approved:
            return JsonResponse({
                'success': False,
                'error': 'Нельзя изменять утвержденный набор характеристик'
            })

        # Получаем и обновляем значения
        features_values = json.loads(request.POST.get('features', '{}'))
        featureset.feature_values = features_values
        featureset.save()

        # Возвращаем обновленную статистику
        return JsonResponse({
            'success': True,
            'message': 'Значения сохранены',
            'preview_table': featureset.get_features_table(),
            'stats': {
                'total': len(featureset.get_feature_values_with_details()),
                'filled': sum(1 for item in featureset.get_feature_values_with_details() if item['value']),
                'percentage': featureset.get_completion_percentage()
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_GET
def search_objects(request):
    """Поиск объектов по типу контента"""
    content_type_id = request.GET.get('content_type_id')
    search_text = request.GET.get('search', '')

    if not content_type_id or len(search_text) < 2:
        return JsonResponse({
            'success': True,
            'objects': []
        })

    try:
        content_type = ContentType.objects.get(id=content_type_id)
        model_class = content_type.model_class()

        # Ищем объекты по названию и коду
        objects = []

        # Проверяем наличие полей name и code
        if hasattr(model_class, 'name') and hasattr(model_class, 'code'):
            queryset = model_class.objects.filter(
                models.Q(name__icontains=search_text) |
                models.Q(code__icontains=search_text)
            )[:10]

            for obj in queryset:
                objects.append({
                    'id': obj.id,
                    'text': f"{obj.name} ({obj.code})" if obj.code else obj.name
                })
        elif hasattr(model_class, '__str__'):
            queryset = model_class.objects.filter(
                models.Q(pk__icontains=search_text)
            )[:10]

            for obj in queryset:
                objects.append({
                    'id': obj.id,
                    'text': str(obj)
                })

        return JsonResponse({
            'success': True,
            'objects': objects
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_GET
def get_equipment_type_tree(request) :
    """Получить дерево типов оборудования"""
    try :
        # Параметры запроса
        show_inactive = request.GET.get('show_inactive' , 'false').lower() == 'true'
        include_counts = request.GET.get('include_counts' , 'true').lower() == 'true'

        # Строим базовый queryset
        queryset = EquipmentType.objects.all()

        if not show_inactive :
            queryset = queryset.filter(is_active=True)

        # Предзагружаем связи для оптимизации
        queryset = queryset.select_related('parent').order_by('level' , 'sorting_order' , 'name')

        if include_counts :
            # Добавляем аннотации для подсчета
            queryset = queryset.annotate(
                children_count=Count('children' , distinct=True) ,
                # Можно добавить другие подсчеты при необходимости
                # features_count=Count('features', distinct=True),
                # templates_count=Count('featuretemplates', distinct=True),
            )

        # Преобразуем в древовидную структуру
        equipment_types = list(queryset)

        # Создаем словарь для быстрого доступа по ID
        type_dict = {}
        for eq_type in equipment_types :
            type_dict[eq_type.id] = {
                'id' : eq_type.id ,
                'name' : eq_type.name ,
                'code' : eq_type.code ,
                'level' : eq_type.level ,
                'parent_id' : eq_type.parent_id ,
                'icon' : eq_type.icon ,
                'is_active' : eq_type.is_active ,
                'sorting_order' : eq_type.sorting_order ,
                'description' : eq_type.description ,
                'children' : []
            }

            if include_counts and hasattr(eq_type , 'children_count') :
                type_dict[eq_type.id]['children_count'] = eq_type.children_count

        # Строим дерево
        tree = []
        for eq_type in equipment_types :
            node = type_dict[eq_type.id]

            if eq_type.parent_id :
                # Добавляем к родителю
                if eq_type.parent_id in type_dict :
                    type_dict[eq_type.parent_id]['children'].append(node)
                else :
                    # Родитель не в выборке (например, неактивен) - добавляем в корень
                    tree.append(node)
            else :
                # Корневой элемент
                tree.append(node)

        # Функция для рекурсивной сортировки детей
        def sort_tree_nodes(nodes) :
            """Рекурсивно сортирует узлы дерева"""
            nodes.sort(key=lambda x : (
                x.get('sorting_order' , 0) ,
                x.get('name' , '')
            ))
            for node in nodes :
                if node['children'] :
                    sort_tree_nodes(node['children'])

        # Сортируем дерево
        sort_tree_nodes(tree)

        # Формируем полные пути для каждого узла
        def add_full_paths(nodes , parent_path="") :
            """Добавляет полные пути к узлам дерева"""
            for node in nodes :
                current_path = f"{parent_path} → {node['name']}" if parent_path else node['name']
                node['full_path'] = current_path
                node['display_name'] = f"{'  ' * node['level']}{node['name']}" if node['level'] > 0 else node['name']

                if node['children'] :
                    add_full_paths(node['children'] , current_path)

        add_full_paths(tree)

        # Дополнительная статистика
        stats = {
            'total' : len(equipment_types) ,
            'active' : sum(1 for t in equipment_types if t.is_active) ,
            'max_level' : max((t.level for t in equipment_types) , default=0) ,
            'root_count' : len(tree) ,
        }

        return JsonResponse({
            'success' : True ,
            'tree' : tree ,
            'stats' : stats ,
            'options' : {
                'show_inactive' : show_inactive ,
                'include_counts' : include_counts ,
            }
        })

    except Exception as e :
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_equipment_type_tree: {e}")

        return JsonResponse({
            'success' : False ,
            'error' : str(e) ,
            'message' : 'Ошибка при получении дерева типов оборудования'
        } , status=500)


# Альтернативная версия - плоский список с отступами (для select элементов)
@login_required
@require_GET
def get_equipment_type_flat_list(request) :
    """Получить плоский список типов оборудования с отступами (для select)"""
    try :
        show_inactive = request.GET.get('show_inactive' , 'false').lower() == 'true'

        queryset = EquipmentType.objects.all()

        if not show_inactive :
            queryset = queryset.filter(is_active=True)

        queryset = queryset.select_related('parent').order_by('level' , 'sorting_order' , 'name')

        equipment_types = list(queryset)

        # Формируем плоский список с отступами
        flat_list = []
        for eq_type in equipment_types :
            indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * eq_type.level
            display_name = f"{indent}{eq_type.name}"

            if not eq_type.is_active :
                display_name = f"<span style='color: #999;'>{display_name} (неактивен)</span>"

            flat_list.append({
                'id' : eq_type.id ,
                'name' : eq_type.name ,
                'display_name' : display_name ,
                'level' : eq_type.level ,
                'parent_id' : eq_type.parent_id ,
                'is_active' : eq_type.is_active ,
                'full_path' : eq_type.get_full_path() if hasattr(eq_type , 'get_full_path') else eq_type.name ,
            })

        return JsonResponse({
            'success' : True ,
            'list' : flat_list ,
            'count' : len(flat_list)
        })

    except Exception as e :
        return JsonResponse({
            'success' : False ,
            'error' : str(e)
        } , status=500)


# Для админки - быстрый поиск типов оборудования
@login_required
@require_GET
def search_equipment_types(request) :
    """Поиск типов оборудования для автокомплита"""
    search_term = request.GET.get('q' , '').strip()

    if len(search_term) < 2 :
        return JsonResponse({
            'success' : True ,
            'results' : []
        })

    try :
        # Ищем по имени, коду и полному пути
        types = EquipmentType.objects.filter(
            models.Q(name__icontains=search_term) |
            models.Q(code__icontains=search_term) |
            models.Q(description__icontains=search_term)
        ).select_related('parent')[:20]

        results = []
        for eq_type in types :
            results.append({
                'id' : eq_type.id ,
                'text' : f"{eq_type.name} ({eq_type.code})" if eq_type.code else eq_type.name ,
                'full_path' : eq_type.get_full_path() if hasattr(eq_type , 'get_full_path') else eq_type.name ,
                'level' : eq_type.level ,
                'is_active' : eq_type.is_active ,
            })

        return JsonResponse({
            'success' : True ,
            'results' : results
        })

    except Exception as e :
        return JsonResponse({
            'success' : False ,
            'error' : str(e)
        } , status=500)