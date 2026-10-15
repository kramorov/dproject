# pa_controls/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from pa_controls.views.catalog import LimitSwitchBoxSectionView
from pa_controls.views.posi_catalog import PosiSectionView
from pa_controls.catalog.views_list import LimitSwitchBoxCatalogView
from pa_controls.catalog.views_detail import LimitSwitchBoxDetailView
from pa_controls.catalog.views_filters import LimitSwitchBoxFilterOptionsView
from pa_controls.catalog.views_engineer import LimitSwitchBoxEngineerView
from pa_controls.catalog.views_engineer_filters import LimitSwitchBoxEngineerFilterOptionsView
from pa_controls.views.meta import LimitSwitchBoxMetaView
from pa_controls.views.quickselect import LimitSwitchBoxQuickSelectView
from pa_controls.views.posi_meta import PosiMetaView
from pa_controls.views.posi_quickselect import PosiQuickSelectView
from pa_controls.catalog.views_posi_list import PosiCatalogView
from pa_controls.catalog.views_posi_detail import PosiDetailView
from pa_controls.catalog.views_posi_filters import PosiFilterOptionsView
from pa_controls.catalog.views_posi_engineer import PosiEngineerView
from pa_controls.catalog.views_posi_engineer_filters import PosiEngineerFilterOptionsView
from pa_controls.views.m2m_data import m2m_items
from pa_controls.views.signal_profiles import LimitSwitchSignalProfilesView
from pa_controls.api.views_constructor import PosiConstructorViewSet

router = DefaultRouter()
router.register(r'constructor', PosiConstructorViewSet, basename='posi-constructor')

urlpatterns = [
    path('m2m-items/', m2m_items, name='m2m_items'),
    path('sections/', LimitSwitchBoxSectionView.as_view(), name='lsb_sections'),
    path('signal-profiles/', LimitSwitchSignalProfilesView.as_view(), name='lsb_signal_profiles'),
    path('quickselect/', LimitSwitchBoxQuickSelectView.as_view(), name='lsb_quickselect'),
    path('meta/', LimitSwitchBoxMetaView.as_view(), name='lsb_meta'),
    path('catalog/', LimitSwitchBoxCatalogView.as_view(), name='lsb_catalog'),
    path('catalog/<int:pk>/', LimitSwitchBoxDetailView.as_view(), name='lsb_detail'),
    path('filters/', LimitSwitchBoxFilterOptionsView.as_view(), name='lsb_filters'),
    path('engineer/', LimitSwitchBoxEngineerView.as_view(), name='lsb_engineer'),
    path('engineer/filters/', LimitSwitchBoxEngineerFilterOptionsView.as_view(), name='lsb_engineer_filters'),

    # ── Каталог позиционеров (по образцу БКВ) ──
    path('positioners/sections/', PosiSectionView.as_view(), name='posi_sections'),
    path('positioners/quickselect/', PosiQuickSelectView.as_view(), name='posi_quickselect'),
    path('positioners/meta/', PosiMetaView.as_view(), name='posi_meta'),
    path('positioners/catalog/', PosiCatalogView.as_view(), name='posi_catalog'),
    path('positioners/catalog/<int:pk>/', PosiDetailView.as_view(), name='posi_detail'),
    path('positioners/filters/', PosiFilterOptionsView.as_view(), name='posi_filters'),
    path('positioners/engineer/', PosiEngineerView.as_view(), name='posi_engineer'),
    path('positioners/engineer/filters/', PosiEngineerFilterOptionsView.as_view(), name='posi_engineer_filters'),

    path('', include(router.urls)),
]
