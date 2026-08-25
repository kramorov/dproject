# pa_controls/urls.py
from django.urls import path
from pa_controls.views.catalog import LimitSwitchBoxSectionView
from pa_controls.catalog.views_list import LimitSwitchBoxCatalogView
from pa_controls.catalog.views_detail import LimitSwitchBoxDetailView
from pa_controls.catalog.views_filters import LimitSwitchBoxFilterOptionsView
from pa_controls.catalog.views_engineer import LimitSwitchBoxEngineerView
from pa_controls.catalog.views_engineer_filters import LimitSwitchBoxEngineerFilterOptionsView
from pa_controls.views.meta import LimitSwitchBoxMetaView
from pa_controls.views.quickselect import LimitSwitchBoxQuickSelectView
from pa_controls.views.m2m_data import m2m_items
from pa_controls.views.signal_profiles import LimitSwitchSignalProfilesView

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
]
