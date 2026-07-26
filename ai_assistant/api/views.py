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
from ..models import AIQuerySample, AIPromptTemplate, AIConversation, SelectionNode
from ..services.tree_processor import TreeProcessor


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


class DecomposeView(APIView):
    """POST /api/ai-assistant/decompose/ — Фаза 1: текст → дерево.

    Принимает текст запроса и опциональный prompt_id (из чекбокса на фронте).
    Создаёт AIConversation и SelectionNode-дерево через TreeProcessor.
    """
    permission_classes = []

    def post(self, request):
        text = request.data.get("text", "")
        if not text:
            return Response({"error": "text required"}, status=400)
        prompt_id = request.data.get("prompt_id")

        conversation = AIConversation.objects.create(status=AIConversation.PROCESSING)
        processor = TreeProcessor(conversation)
        result = processor.decompose(text=text, prompt_id=prompt_id)
        return Response(result)


class ExtractView(APIView):
    """POST /api/ai-assistant/extract/{node_id}/ — Фаза 2: извлечение фильтров.

    Для узла дерева запускает extract-промпт, специфичный для типа оборудования.
    """
    permission_classes = []

    def post(self, request, node_id):
        try:
            node = SelectionNode.objects.get(id=node_id)
        except SelectionNode.DoesNotExist:
            return Response({"error": "node not found"}, status=404)

        processor = TreeProcessor(node.conversation)
        result = processor.extract(node_id=node.id)
        return Response(result)


class FilterView(APIView):
    """POST /api/ai-assistant/filter/{node_id}/ — Фаза 3: вызов API-фильтра.

    Вызывает фильтр оборудования (эндпоинт из EquipmentType.filter_endpoint)
    с effective_params узла.
    """
    permission_classes = []

    def post(self, request, node_id):
        try:
            node = SelectionNode.objects.get(id=node_id)
        except SelectionNode.DoesNotExist:
            return Response({"error": "node not found"}, status=404)

        processor = TreeProcessor(node.conversation)
        result = processor.filter_node(node_id=node.id)
        return Response(result)


class SelectView(APIView):
    """POST /api/ai-assistant/select/{node_id}/ — Фаза 4: выбор продукта + каскад.

    Принимает {product_type: "...", product_id: N}.
    Сохраняет выбор и пробрасывает параметры дочерним узлам через CascadeRule.
    """
    permission_classes = []

    def post(self, request, node_id):
        product_type = request.data.get("product_type", "")
        product_id = request.data.get("product_id")
        if not product_type or not product_id:
            return Response({"error": "product_type and product_id required"}, status=400)

        try:
            node = SelectionNode.objects.get(id=node_id)
        except SelectionNode.DoesNotExist:
            return Response({"error": "node not found"}, status=404)

        processor = TreeProcessor(node.conversation)
        result = processor.select_product(
            node_id=node.id, product_type=product_type, product_id=int(product_id)
        )
        return Response(result)


class CompareView(APIView):
    """POST /api/ai-assistant/compare/{node_id}/ — Фаза 5: сравнение требований и факта.

    Сравнивает extract_output с selected_product_specs по семантике параметров.
    """
    permission_classes = []

    def post(self, request, node_id):
        try:
            node = SelectionNode.objects.get(id=node_id)
        except SelectionNode.DoesNotExist:
            return Response({"error": "node not found"}, status=404)

        processor = TreeProcessor(node.conversation)
        result = processor.compare(node_id=node.id)
        return Response(result)


class EBOMView(APIView):
    """GET /api/ai-assistant/ebom/{conversation_id}/ — инженерная спецификация.

    Возвращает EBOM: иерархический состав с исходными требованиями.
    """
    permission_classes = []

    def get(self, request, conversation_id):
        try:
            conversation = AIConversation.objects.get(id=conversation_id)
        except AIConversation.DoesNotExist:
            return Response({"error": "conversation not found"}, status=404)

        processor = TreeProcessor(conversation)
        return Response(processor.build_ebom())


class MBOMView(APIView):
    """GET /api/ai-assistant/mbom/{conversation_id}/ — производственная спецификация.

    Возвращает MBOM: иерархический состав с артикулами выбранных продуктов.
    """
    permission_classes = []

    def get(self, request, conversation_id):
        try:
            conversation = AIConversation.objects.get(id=conversation_id)
        except AIConversation.DoesNotExist:
            return Response({"error": "conversation not found"}, status=404)

        processor = TreeProcessor(conversation)
        return Response(processor.build_mbom())


class TreeView(APIView):
    """GET /api/ai-assistant/tree/{conversation_id}/ — полное дерево подбора.

    Возвращает все SelectionNode для диалога в виде вложенного дерева.
    """
    permission_classes = []

    def get(self, request, conversation_id):
        try:
            conversation = AIConversation.objects.get(id=conversation_id)
        except AIConversation.DoesNotExist:
            return Response({"error": "conversation not found"}, status=404)

        root_nodes = conversation.selection_nodes.filter(parent__isnull=True)
        tree = [self._serialize_node(n) for n in root_nodes]
        return Response({
            "conversation_id": conversation.id,
            "status": conversation.status,
            "tree": tree,
        })

    def _serialize_node(self, node):
        data = {
            "id": node.id,
            "level": node.level,
            "path": node.path,
            "label": node.label,
            "equipment_type": node.equipment_type.code if node.equipment_type else None,
            "task_type": node.task_type,
            "quantity": node.quantity,
            "quantity_unit": node.quantity_unit,
            "total_quantity": node.total_quantity,
            "status": node.status,
            "status_message": node.status_message,
            "extract_output": node.extract_output,
            "cascade_params": node.cascade_params,
            "filter_output": node.filter_output,
            "selected_product_type": node.selected_product_type,
            "selected_product_id": node.selected_product_id,
            "compare_output": node.compare_output,
        }
        children = node.children.all()
        if children:
            data["children"] = [self._serialize_node(c) for c in children]
        return data
