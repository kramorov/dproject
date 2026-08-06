#core/urls.py
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import UniversalAPIView, DebugAPIView, ExdStructureView, ExdParseView, ExdCompatibleView, AiSchemaView
from .wizard_views import WizardConfigView, WizardFilterOptionsView, WizardResultsView, WizardModelFiltersView, WizardAdminListView, WizardAdminDetailView, WizardEquipmentTypesView
from .question_graph_views import QuestionGraphConfigView, QuestionGraphAdvanceView, QuestionGraphResultsView, QuestionGraphAdminListView, QuestionGraphAdminDetailView, QuestionGraphToWizardView, CatalogWizardAdapterView, QuestionGraphVisibleParamsView
from .climate_views import ClimateStructureView, ClimateParseView
from params.views import ThreadFilterOptionsView
from .ref_views import SectionsView, AllowedAppsView, BrandsView, DjangoUsersView

urlpatterns = [
    path('', csrf_exempt(UniversalAPIView.as_view()), name='universal_api'),
    path('debug/', DebugAPIView.as_view(), name='debug_api'),
    path('exd/structure/', ExdStructureView.as_view(), name='exd_structure'),
    path('exd/parse/', ExdParseView.as_view(), name='exd_parse'),
    path('exd/compatible/', ExdCompatibleView.as_view(), name='exd_compatible'),
    path('climate/structure/', ClimateStructureView.as_view(), name='climate_structure'),
    path('climate/parse/', ClimateParseView.as_view(), name='climate_parse'),
    path('sections/', SectionsView.as_view(), name='sections'),
    path('allowed-apps/', AllowedAppsView.as_view(), name='allowed_apps'),
    path('brands/', BrandsView.as_view(), name='brands'),
    path('django-users/', DjangoUsersView.as_view(), name='django_users'),
    # Wizard endpoints
    path('wizard/<int:equipment_type_id>/', WizardConfigView.as_view(), name='wizard_config'),
    path('wizard/<int:equipment_type_id>/filter-options/', WizardFilterOptionsView.as_view(), name='wizard_filter_options'),
    path('wizard/<int:equipment_type_id>/results/', WizardResultsView.as_view(), name='wizard_results'),
    path('wizard/model-filters/', WizardModelFiltersView.as_view(), name='wizard_model_filters'),
    # Wizard equipment types (admin helper)
    path('wizard/model-filters/equipment-types/', WizardEquipmentTypesView.as_view(), name='wizard_equipment_types'),
    path('wizard/model-filters/equipment-types/<int:et_id>/', WizardEquipmentTypesView.as_view(), name='wizard_equipment_type_detail'),
    # Wizard admin (CRUD)
    path('wizard/admin/', WizardAdminListView.as_view(), name='wizard_admin_list'),
    path('wizard/admin/<int:wizard_id>/', WizardAdminDetailView.as_view(), name='wizard_admin_detail'),
    # Catalog wizard adapter (graph or flat)
    path('catalog-wizard/<str:code>/', CatalogWizardAdapterView.as_view(), name='catalog_wizard_adapter'),
    # Thread filter options
    path('thread-filter-options/', ThreadFilterOptionsView.as_view(), name='thread_filter_options'),
    # QuestionGraph endpoints
    path('question-graph/admin/', QuestionGraphAdminListView.as_view(), name='question_graph_admin_list'),
    path('question-graph/admin/<int:graph_id>/', QuestionGraphAdminDetailView.as_view(), name='question_graph_admin_detail'),
    path('question-graph/<str:code>/', QuestionGraphConfigView.as_view(), name='question_graph_config'),
    path('question-graph/<str:code>/advance/', QuestionGraphAdvanceView.as_view(), name='question_graph_advance'),
    path('question-graph/<str:code>/results/', QuestionGraphResultsView.as_view(), name='question_graph_results'),
    path('question-graph/<str:code>/to-wizard/', QuestionGraphToWizardView.as_view(), name='question_graph_to_wizard'),
    path('question-graph/<str:code>/visible-params/', QuestionGraphVisibleParamsView.as_view(), name='question_graph_visible_params'),
    # AI Schema
    path('ai-schema/<str:code>/', AiSchemaView.as_view(), name='ai_schema'),
]
