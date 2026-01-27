# features/urls.py
from django.urls import path
from features import views

urlpatterns = [
    # AJAX эндпоинты для EquipmentType
    path('equipment-type/get_level/', views.get_equipment_type_level, name='equipment_type_level'),
    path('equipment-type/get_tree/', views.get_equipment_type_tree, name='equipment_type_tree'),
    path('equipment-type/get_active_ids/', views.get_active_equipment_type_ids, name='active_equipment_type_ids'),

    # AJAX эндпоинты для FeatureVariety
    path('feature-variety/get_by_equipment_type/<int:equipment_type_id>/',
         views.get_features_by_equipment_type, name='features_by_equipment_type'),

    # AJAX эндпоинты для FeatureTemplate
    path('feature-template/save_features/<int:template_id>/',
         views.save_template_features, name='save_template_features'),

    # AJAX эндпоинты для FeatureSet
    path('featureset/save_values/<int:featureset_id>/',
         views.save_featureset_values, name='save_featureset_values'),

    # Поиск объектов
    path('search/objects/', views.search_objects, name='search_objects'),
]