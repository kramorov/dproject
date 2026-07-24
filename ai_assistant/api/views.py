"""API views для AI-ассистента подбора оборудования.

Эндпоинты:
- /analyze/ — фаза 1: декомпозиция запроса, валидация, план задач.
- /execute/ — фаза 2: выполнение графа задач.
- /query/ — однофазный эндпоинт обратной совместимости.
- /run-query/ — отладочный эндпоинт (только для администраторов).
- QuerySampleViewSet — CRUD для эталонных запросов.
- PromptViewSet — CRUD для шаблонов промптов.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework import viewsets

from .serializers import (
    QueryRequestSerializer, QueryResponseSerializer,
    AIQuerySampleSerializer, AIPromptTemplateSerializer,
)
from ..orchestrator import QueryOrchestrator
from ..models import AIQuerySample, AIPromptTemplate


class AnalyzeView(APIView):
    """POST /api/ai-assistant/analyze/ — Фаза 1: decompose + валидация.

    Принимает текст запроса пользователя, запускает ``QueryOrchestrator.analyze()``,
    возвращает статус (ready/needs_info/rejected), план задач и анализ.
    """
    permission_classes = []

    def post(self, request):
        """Обрабатывает POST-запрос фазы analyze.

        Args:
            request: DRF Request с полем ``text`` в теле.

        Returns:
            Response с результатом ``QueryOrchestrator.analyze()``
            или ошибкой 400, если поле ``text`` не передано.
        """
        text = request.data.get("text", "")
        if not text:
            return Response({"error": "text required"}, status=400)
        result = QueryOrchestrator().analyze(text=text)
        return Response(result)


class ExecuteView(APIView):
    """POST /api/ai-assistant/execute/ — Фаза 2: выполнение графа задач.

    Принимает список задач и глобальные требования, запускает
    ``QueryOrchestrator.execute()``, возвращает progress_log и results.
    """
    permission_classes = []

    def post(self, request):
        """Обрабатывает POST-запрос фазы execute.

        Args:
            request: DRF Request с полями ``tasks`` (список задач)
                и ``global_requirements`` (опционально).

        Returns:
            Response с progress_log и results или ошибкой 400,
            если поле ``tasks`` не передано.
        """
        tasks = request.data.get("tasks", [])
        global_reqs = request.data.get("global_requirements", {})
        if not tasks:
            return Response({"error": "tasks required"}, status=400)
        result = QueryOrchestrator().execute(tasks=tasks, global_reqs=global_reqs)
        return Response(result)


class QueryView(APIView):
    """POST /api/ai-assistant/query/ — старый однофазный эндпоинт.

    Сохранён для обратной совместимости. Делегирует вызов в ``analyze()``.
    """
    permission_classes = []

    def post(self, request):
        """Обрабатывает однофазный POST-запрос (совместимость).

        Args:
            request: DRF Request с полем ``text`` в теле.

        Returns:
            Response с результатом ``QueryOrchestrator.analyze()``
            или ошибкой 400.
        """
        text = request.data.get("text", "")
        if not text:
            return Response({"error": "text required"}, status=400)
        result = QueryOrchestrator().analyze(text=text)
        return Response(result)


class RunQueryView(APIView):
    """POST /api/ai-assistant/run-query/ — отладочный эндпоинт.

    Доступен только администраторам (``IsAdminUser``). Используется
    для ручного тестирования decompose-пайплайна без аутентификации клиента.
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        """Обрабатывает отладочный POST-запрос.

        Args:
            request: DRF Request с полем ``text`` в теле.

        Returns:
            Response с результатом ``QueryOrchestrator.analyze()``
            или ошибкой 400.
        """
        text = request.data.get("text", "")
        if not text:
            return Response({"error": "text required"}, status=400)
        result = QueryOrchestrator().analyze(text=text)
        return Response(result)


class QuerySampleViewSet(viewsets.ModelViewSet):
    """ViewSet для управления эталонными запросами (AIQuerySample).

    Предоставляет стандартные CRUD-операции. Доступен только
    администраторам. Используется для пополнения и валидации
    набора тестовых запросов.
    """
    queryset = AIQuerySample.objects.all()
    serializer_class = AIQuerySampleSerializer
    permission_classes = [IsAuthenticated]


class PromptViewSet(viewsets.ModelViewSet):
    """ViewSet для управления шаблонами промптов (AIPromptTemplate).

    Предоставляет CRUD для версионированных промптов. Доступен
    авторизованным пользователям.
    """
    queryset = AIPromptTemplate.objects.all()
    serializer_class = AIPromptTemplateSerializer
    permission_classes = [IsAuthenticated]
