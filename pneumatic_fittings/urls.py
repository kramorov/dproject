# pneumatic_fittings/urls.py
from django.urls import path
from pneumatic_fittings.catalog.views_filters import PneumaticFittingsFilterOptionsView
from pneumatic_fittings.catalog.views_list import PneumaticFittingsCatalogView
from pneumatic_fittings.catalog.views_detail import PneumaticFittingsDetailView
from pneumatic_fittings.catalog.views_engineer import PneumaticFittingsEngineerView
from pneumatic_fittings.catalog.views_engineer_filters import PneumaticFittingsEngineerFilterOptionsView
from pneumatic_fittings.catalog.views_quickselect import PneumaticFittingsQuickSelectView
from pneumatic_fittings.catalog.views_meta import PneumaticFittingsMetaView

urlpatterns = [
    path('catalog/', PneumaticFittingsCatalogView.as_view()),
    path('catalog/<int:pk>/', PneumaticFittingsDetailView.as_view()),
    path('filters/', PneumaticFittingsFilterOptionsView.as_view()),
    path('engineer/', PneumaticFittingsEngineerView.as_view()),
    path('engineer/filters/', PneumaticFittingsEngineerFilterOptionsView.as_view()),
    path('quickselect/', PneumaticFittingsQuickSelectView.as_view()),
    path('meta/', PneumaticFittingsMetaView.as_view()),
]
