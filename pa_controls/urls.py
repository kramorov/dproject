# pa_controls/urls.py
from django.urls import path
from pa_controls.views.catalog import LimitSwitchBoxSectionView
from pa_controls.catalog.views_list import LimitSwitchBoxCatalogView
from pa_controls.catalog.views_detail import LimitSwitchBoxDetailView
from pa_controls.catalog.views_filters import LimitSwitchBoxFilterOptionsView
from pa_controls.views.meta import LimitSwitchBoxMetaView
from pa_controls.views.quickselect import LimitSwitchBoxQuickSelectView
from pa_controls.views.m2m_data import m2m_items

urlpatterns = [
    path('m2m-items/', m2m_items, name='m2m_items'),
    path('sections/', LimitSwitchBoxSectionView.as_view(), name='lsb_sections'),
    path('quickselect/', LimitSwitchBoxQuickSelectView.as_view(), name='lsb_quickselect'),
    path('meta/', LimitSwitchBoxMetaView.as_view(), name='lsb_meta'),
    path('catalog/', LimitSwitchBoxCatalogView.as_view(), name='lsb_catalog'),
    path('catalog/<int:pk>/', LimitSwitchBoxDetailView.as_view(), name='lsb_detail'),
    path('filters/', LimitSwitchBoxFilterOptionsView.as_view(), name='lsb_filters'),
]
