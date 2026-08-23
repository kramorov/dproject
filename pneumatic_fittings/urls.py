# pneumatic_fittings/urls.py
"""
Маршруты трёх каталогов фитингов (одна модель, три вида):

  fittings_urlpatterns   — /api/pneumatic-fittings/    (резьба-трубка)
  silencers_urlpatterns  — /api/pneumatic-silencers/   (глушители)
  plugs_urlpatterns      — /api/pneumatic-plugs/       (заглушки)

Подключаются в djangoProject1/urls.py через include('pneumatic_fittings.urls.<имя>').
"""
from django.urls import path
from pneumatic_fittings.catalog.views_filters import (
    PneumaticFittingsFilterOptionsView,
    PneumaticSilencersFilterOptionsView,
    PneumaticPlugsFilterOptionsView,
)
from pneumatic_fittings.catalog.views_list import (
    PneumaticFittingsCatalogView,
    PneumaticSilencersCatalogView,
    PneumaticPlugsCatalogView,
)
from pneumatic_fittings.catalog.views_detail import (
    PneumaticFittingsDetailView,
    PneumaticSilencersDetailView,
    PneumaticPlugsDetailView,
)
from pneumatic_fittings.catalog.views_engineer import (
    PneumaticFittingsEngineerView,
    PneumaticSilencersEngineerView,
    PneumaticPlugsEngineerView,
)
from pneumatic_fittings.catalog.views_engineer_filters import (
    PneumaticFittingsEngineerFilterOptionsView,
    PneumaticSilencersEngineerFilterOptionsView,
    PneumaticPlugsEngineerFilterOptionsView,
)
from pneumatic_fittings.catalog.views_quickselect import (
    PneumaticFittingsQuickSelectView,
    PneumaticSilencersQuickSelectView,
    PneumaticPlugsQuickSelectView,
)
from pneumatic_fittings.catalog.views_meta import PneumaticFittingsMetaView


def _catalog_patterns(catalog_view, detail_view, filters_view,
                      engineer_view, engineer_filters_view, quickselect_view,
                      meta_view=None):
    """Стандартный набор маршрутов каталога (по паттерну остальных каталогов)."""
    patterns = [
        path('catalog/', catalog_view.as_view()),
        path('catalog/<int:pk>/', detail_view.as_view()),
        path('filters/', filters_view.as_view()),
        path('engineer/', engineer_view.as_view()),
        path('engineer/filters/', engineer_filters_view.as_view()),
        path('quickselect/', quickselect_view.as_view()),
    ]
    if meta_view is not None:
        patterns.append(path('meta/', meta_view.as_view()))
    return patterns


fittings_urlpatterns = _catalog_patterns(
    PneumaticFittingsCatalogView,
    PneumaticFittingsDetailView,
    PneumaticFittingsFilterOptionsView,
    PneumaticFittingsEngineerView,
    PneumaticFittingsEngineerFilterOptionsView,
    PneumaticFittingsQuickSelectView,
    meta_view=PneumaticFittingsMetaView,
)

silencers_urlpatterns = _catalog_patterns(
    PneumaticSilencersCatalogView,
    PneumaticSilencersDetailView,
    PneumaticSilencersFilterOptionsView,
    PneumaticSilencersEngineerView,
    PneumaticSilencersEngineerFilterOptionsView,
    PneumaticSilencersQuickSelectView,
)

plugs_urlpatterns = _catalog_patterns(
    PneumaticPlugsCatalogView,
    PneumaticPlugsDetailView,
    PneumaticPlugsFilterOptionsView,
    PneumaticPlugsEngineerView,
    PneumaticPlugsEngineerFilterOptionsView,
    PneumaticPlugsQuickSelectView,
)

# Обратная совместимость: include('pneumatic_fittings.urls') → каталог трубок
urlpatterns = fittings_urlpatterns
