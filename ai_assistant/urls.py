from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api.views import (
    AnalyzeView, ExecuteView, QueryView, RunQueryView,
    QuerySampleViewSet, PromptViewSet,
    DecomposeView, ExtractView, FilterView, SelectView,
    CompareView, EBOMView, MBOMView, TreeView,
)

router = DefaultRouter()
router.register(r"samples", QuerySampleViewSet, basename="ai-sample")
router.register(r"prompts", PromptViewSet, basename="ai-prompt")

urlpatterns = [
    # Legacy
    path("analyze/", AnalyzeView.as_view(), name="ai-analyze"),
    path("execute/", ExecuteView.as_view(), name="ai-execute"),
    path("query/", QueryView.as_view(), name="ai-query"),
    path("run-query/", RunQueryView.as_view(), name="ai-run-query"),

    # Pipeline steps
    path("decompose/", DecomposeView.as_view(), name="ai-decompose"),
    path("extract/<int:node_id>/", ExtractView.as_view(), name="ai-extract"),
    path("filter/<int:node_id>/", FilterView.as_view(), name="ai-filter"),
    path("select/<int:node_id>/", SelectView.as_view(), name="ai-select"),
    path("compare/<int:node_id>/", CompareView.as_view(), name="ai-compare"),

    # Results
    path("ebom/<int:conversation_id>/", EBOMView.as_view(), name="ai-ebom"),
    path("mbom/<int:conversation_id>/", MBOMView.as_view(), name="ai-mbom"),
    path("tree/<int:conversation_id>/", TreeView.as_view(), name="ai-tree"),

    path("", include(router.urls)),
]
