# configurator/urls.py
from django.urls import path

from rest_framework.routers import DefaultRouter

from configurator.api.views import (
    AssemblyListView,
    AssemblyDetailView,
    AssemblyExpandView,
    AssemblyBomView,
    AssemblyForkView,
    AssemblyFixateView,
    ComponentDetailView,
    ComponentRequirementsView,
    ComponentFilterView,
    ComponentSelectView,
    FilterSchemaView,
)
from configurator.api.admin_views import (
    ParameterRuleViewSet,
    ParameterBindingViewSet,
    DerivationRuleViewSet,
    EquipmentTypeParameterViewSet,
    FittingPatternViewSet,
    FittingPatternItemViewSet,
    EquipmentTypeViewSet,
    ModelFieldSnapshotViewSet,
    ParameterCatalogViewSet,
)

urlpatterns = [
    # Assemblies
    path('assemblies/', AssemblyListView.as_view(), name='configurator_assembly_list'),
    path('assemblies/<int:pk>/', AssemblyDetailView.as_view(), name='configurator_assembly_detail'),
    path('assemblies/<int:pk>/expand/', AssemblyExpandView.as_view(), name='configurator_assembly_expand'),
    path('assemblies/<int:pk>/bom/', AssemblyBomView.as_view(), name='configurator_assembly_bom'),
    path('assemblies/<int:pk>/fork/', AssemblyForkView.as_view(), name='configurator_assembly_fork'),
    path('assemblies/<int:pk>/fixate/', AssemblyFixateView.as_view(), name='configurator_assembly_fixate'),

    # Components
    path('components/<int:pk>/', ComponentDetailView.as_view(), name='configurator_component_detail'),
    path('components/<int:pk>/requirements/', ComponentRequirementsView.as_view(), name='configurator_component_requirements'),
    path('components/<int:pk>/filter/', ComponentFilterView.as_view(), name='configurator_component_filter'),
    path('components/<int:pk>/select/', ComponentSelectView.as_view(), name='configurator_component_select'),

    # Schema
    path('equipment-types/<int:pk>/filter-schema/', FilterSchemaView.as_view(), name='configurator_filter_schema'),
]

# ── Admin CRUD ──
router = DefaultRouter()
router.register(r'admin/parameter-rules', ParameterRuleViewSet, basename='admin_parameter_rule')
router.register(r'admin/parameter-bindings', ParameterBindingViewSet, basename='admin_parameter_binding')
router.register(r'admin/derivation-rules', DerivationRuleViewSet, basename='admin_derivation_rule')
router.register(r'admin/equipment-type-parameters', EquipmentTypeParameterViewSet, basename='admin_equipment_type_parameter')
router.register(r'admin/field-snapshots', ModelFieldSnapshotViewSet, basename='admin_field_snapshot')
router.register(r'admin/parameter-catalog', ParameterCatalogViewSet, basename='admin_parameter_catalog')
router.register(r'admin/fitting-patterns', FittingPatternViewSet, basename='admin_fitting_pattern')
router.register(r'admin/fitting-pattern-items', FittingPatternItemViewSet, basename='admin_fitting_pattern_item')
router.register(r'admin/equipment-types', EquipmentTypeViewSet, basename='admin_equipment_type')
urlpatterns += router.urls
