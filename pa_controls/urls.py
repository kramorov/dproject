# pa_controls/urls.py
from django.urls import path
from pa_controls.views.catalog import (
    LimitSwitchBoxCatalogView,
    LimitSwitchBoxDetailView,
    LimitSwitchBoxFilterOptionsView,
)
from pa_controls.views.meta import LimitSwitchBoxMetaView
from pa_controls.views.quickselect import LimitSwitchBoxQuickSelectView

urlpatterns = [
    path('quickselect/', LimitSwitchBoxQuickSelectView.as_view(), name='lsb_quickselect'),
    path('meta/', LimitSwitchBoxMetaView.as_view(), name='lsb_meta'),
    path('catalog/', LimitSwitchBoxCatalogView.as_view(), name='lsb_catalog'),
    path('catalog/<int:pk>/', LimitSwitchBoxDetailView.as_view(), name='lsb_detail'),
    path('filters/', LimitSwitchBoxFilterOptionsView.as_view(), name='lsb_filters'),
]