# pa_controls/views/m2m_data.py
"""API для получения M2M-данных (id, code, name) без DRF-сериализаторов.

GET /api/pa-controls/m2m-items/?model=media_library.MediaLibraryItem&ids=55,56,57
→ {data: [{id, code, name}, ...]}

Используется ChipList/BasePicker для batch-загрузки M2M-связей одним запросом.
Не зависит от DRF — прямой JsonResponse через model.objects.filter(id__in=ids).
"""
from django.http import JsonResponse
from django.apps import apps


def m2m_items(request):
    """
    GET /api/pa-controls/m2m-items/?model=media_library.MediaLibraryItem&ids=55,56,57

    Возвращает [{id, code, name}] для переданных ID.
    """
    model_name = request.GET.get('model', '')
    ids_str = request.GET.get('ids', '')

    if not model_name or not ids_str:
        return JsonResponse({'error': 'model and ids required'}, status=400)

    try:
        ids = [int(x.strip()) for x in ids_str.split(',') if x.strip()]
    except ValueError:
        return JsonResponse({'error': 'ids must be comma-separated integers'}, status=400)

    try:
        app_label, model_cls = model_name.split('.')
        model = apps.get_model(app_label, model_cls)
    except (ValueError, LookupError):
        return JsonResponse({'error': f'Model {model_name} not found'}, status=404)

    queryset = model.objects.filter(id__in=ids)
    data = []
    for obj in queryset:
        item = {'id': obj.id}
        item['code'] = getattr(obj, 'code', '') or ''
        item['name'] = getattr(obj, 'name', '') or ''
        data.append(item)

    return JsonResponse({'data': data})
