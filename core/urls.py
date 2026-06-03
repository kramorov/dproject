#core/urls.py
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import UniversalAPIView, DebugAPIView, ExdStructureView, ExdParseView, ExdCompatibleView
from .climate_views import ClimateStructureView, ClimateParseView

urlpatterns = [
    path('', csrf_exempt(UniversalAPIView.as_view()), name='universal_api'),
    path('debug/', DebugAPIView.as_view(), name='debug_api'),
    path('exd/structure/', ExdStructureView.as_view(), name='exd_structure'),
    path('exd/parse/', ExdParseView.as_view(), name='exd_parse'),
    path('exd/compatible/', ExdCompatibleView.as_view(), name='exd_compatible'),
    path('climate/structure/', ClimateStructureView.as_view(), name='climate_structure'),
    path('climate/parse/', ClimateParseView.as_view(), name='climate_parse'),
]
