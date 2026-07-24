from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api.views import AnalyzeView, ExecuteView, QueryView, RunQueryView, QuerySampleViewSet, PromptViewSet

router = DefaultRouter()
router.register(r"samples", QuerySampleViewSet, basename="ai-sample")
router.register(r"prompts", PromptViewSet, basename="ai-prompt")

urlpatterns = [
    path("analyze/", AnalyzeView.as_view(), name="ai-analyze"),
    path("execute/", ExecuteView.as_view(), name="ai-execute"),
    path("query/", QueryView.as_view(), name="ai-query"),
    path("run-query/", RunQueryView.as_view(), name="ai-run-query"),
    path("", include(router.urls)),
]
