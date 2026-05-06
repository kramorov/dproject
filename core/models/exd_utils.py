# exd_utils.py
from params.exd_models import ExplosionProtectionType , HazardousGroup , TemperatureClass , ExplosionProtectionLevel , \
    ExplosionProtectionMethod


def get_exd_choices():
    """
    Возвращает словарь с иерархическими данными для выбора взрывозащиты.
    Структура:
    {
        "methods": [
            {"id": 1, "code": "d", "name": "Взрывонепроницаемая оболочка", "types": [...]},
            ...
        ],
        "gas_groups": [...],
        "dust_groups": [...],
        "temperature_classes": [...],
        "protection_levels": {"gas": [...], "dust": [...]}
    }
    """
    # 1. Методы взрывозащиты + связанные типы
    methods_qs = ExplosionProtectionMethod.objects.filter(is_active=True).order_by('sorting_order')
    methods = []
    for method in methods_qs:
        types = ExplosionProtectionType.objects.filter(method=method, is_active=True).order_by('sorting_order')
        methods.append({
            'id': method.id,
            'code': method.code,
            'name': method.name,
            'description': method.description,
            'types': [{'id': t.id, 'code': t.code, 'name': t.name} for t in types]
        })

    # 2. Группы газа и пыли
    gas_groups = [
        {'id': g.id, 'code': g.code, 'name': g.name, 'rating': g.rating}
        for g in HazardousGroup.objects.filter(group_type='GAS').order_by('rating')
    ]
    dust_groups = [
        {'id': g.id, 'code': g.code, 'name': g.name, 'rating': g.rating}
        for g in HazardousGroup.objects.filter(group_type='DUST').order_by('rating')
    ]

    # 3. Температурные классы
    temp_classes = [
        {'id': t.id, 'code': t.temperature_class, 'name': t.name, 'max_temp': t.max_surface_temp}
        for t in TemperatureClass.objects.filter(is_active=True).order_by('sorting_order')
    ]

    # 4. Уровни взрывозащиты
    all_levels = ExplosionProtectionLevel.objects.all().order_by('code')
    gas_levels = [{'id': l.id, 'code': l.code, 'name': l.name} for l in all_levels if l.code in ('Ga', 'Gb', 'Gc')]
    dust_levels = [{'id': l.id, 'code': l.code, 'name': l.name} for l in all_levels if l.code in ('Da', 'Db', 'Dc')]

    return {
        'methods': methods,
        'gas_groups': gas_groups,
        'dust_groups': dust_groups,
        'temperature_classes': temp_classes,
        'protection_levels': {
            'gas': gas_levels,
            'dust': dust_levels
        }
    }