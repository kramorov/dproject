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