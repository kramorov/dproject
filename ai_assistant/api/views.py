"""API views РґР»СЏ AI-Р°СЃСЃРёСЃС‚РµРЅС‚Р° РїРѕРґР±РѕСЂР° РѕР±РѕСЂСѓРґРѕРІР°РЅРёСЏ.

Р­РЅРґРїРѕРёРЅС‚С‹:
- /analyze/ вЂ” С„Р°Р·Р° 1: РґРµРєРѕРјРїРѕР·РёС†РёСЏ Р·Р°РїСЂРѕСЃР°, РІР°Р»РёРґР°С†РёСЏ, РїР»Р°РЅ Р·Р°РґР°С‡.
- /execute/ вЂ” С„Р°Р·Р° 2: РІС‹РїРѕР»РЅРµРЅРёРµ РіСЂР°С„Р° Р·Р°РґР°С‡.
- /query/ вЂ” РѕРґРЅРѕС„Р°Р·РЅС‹Р№ СЌРЅРґРїРѕРёРЅС‚ РѕР±СЂР°С‚РЅРѕР№ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё.
- /run-query/ вЂ” РѕС‚Р»Р°РґРѕС‡РЅС‹Р№ СЌРЅРґРїРѕРёРЅС‚ (С‚РѕР»СЊРєРѕ РґР»СЏ Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂРѕРІ).
- QuerySampleViewSet вЂ” CRUD РґР»СЏ СЌС‚Р°Р»РѕРЅРЅС‹С… Р·Р°РїСЂРѕСЃРѕРІ.
- PromptViewSet вЂ” CRUD РґР»СЏ С€Р°Р±Р»РѕРЅРѕРІ РїСЂРѕРјРїС‚РѕРІ.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from core.permissions import SystemObjectPermission
from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from core.models.equipment_type import EquipmentType
from project_customers.models import ProjectCustomer
from sku.models.mbom import MBOM, MBOMItem

from .serializers import (
    QueryRequestSerializer, QueryResponseSerializer,
    AIQuerySampleSerializer, AIPromptTemplateSerializer, PipelineSkillSerializer, SkillOverrideSerializer, JSONSchemaSerializer,
)
from ..models import (
    AIQuerySample, AIPromptTemplate, AIConversation, SelectionNode,
    PipelineSkill, SkillOverride, JSONSchema, CompositionGroup,
)
from ..services.tree_processor import TreeProcessor
from ..services.customer_resolver import resolve_customer
from ..classifiers import InstructorClassifier

class QuerySampleViewSet(viewsets.ModelViewSet):
    """ViewSet РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ СЌС‚Р°Р»РѕРЅРЅС‹РјРё Р·Р°РїСЂРѕСЃР°РјРё (AIQuerySample).

    РџСЂРµРґРѕСЃС‚Р°РІР»СЏРµС‚ СЃС‚Р°РЅРґР°СЂС‚РЅС‹Рµ CRUD-РѕРїРµСЂР°С†РёРё. Р”РѕСЃС‚СѓРїРµРЅ С‚РѕР»СЊРєРѕ
    Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂР°Рј. РСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ РґР»СЏ РїРѕРїРѕР»РЅРµРЅРёСЏ Рё РІР°Р»РёРґР°С†РёРё
    РЅР°Р±РѕСЂР° С‚РµСЃС‚РѕРІС‹С… Р·Р°РїСЂРѕСЃРѕРІ.
    """
    queryset = AIQuerySample.objects.all()
    serializer_class = AIQuerySampleSerializer
    permission_classes = [SystemObjectPermission]
    required_object = 'ai.debug'

class PromptViewSet(viewsets.ModelViewSet):
    """ViewSet РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ С€Р°Р±Р»РѕРЅР°РјРё РїСЂРѕРјРїС‚РѕРІ (AIPromptTemplate).

    РџСЂРµРґРѕСЃС‚Р°РІР»СЏРµС‚ CRUD РґР»СЏ РІРµСЂСЃРёРѕРЅРёСЂРѕРІР°РЅРЅС‹С… РїСЂРѕРјРїС‚РѕРІ. Р”РѕСЃС‚СѓРїРµРЅ
    Р°РІС‚РѕСЂРёР·РѕРІР°РЅРЅС‹Рј РїРѕР»СЊР·РѕРІР°С‚РµР»СЏРј.
    """
    queryset = AIPromptTemplate.objects.all()
    serializer_class = AIPromptTemplateSerializer
    permission_classes = [SystemObjectPermission]
    required_object = 'ai.debug'

class DecomposeView(APIView):
    """POST /api/ai-assistant/decompose/ вЂ” Р¤Р°Р·Р° 1: С‚РµРєСЃС‚ в†’ РґРµСЂРµРІРѕ.

    РџСЂРёРЅРёРјР°РµС‚ С‚РµРєСЃС‚ Р·Р°РїСЂРѕСЃР° Рё РѕРїС†РёРѕРЅР°Р»СЊРЅС‹Р№ prompt_id (РёР· С‡РµРєР±РѕРєСЃР° РЅР° С„СЂРѕРЅС‚Рµ).
    РЎРѕР·РґР°С‘С‚ AIConversation Рё SelectionNode-РґРµСЂРµРІРѕ С‡РµСЂРµР· TreeProcessor.
    """
    permission_classes = []

    def post(self, request):
        text = request.data.get("text", "")
        if not text:
            return Response({"error": "text required"}, status=400)
        prompt_id = request.data.get("prompt_id")
        source = request.data.get("source", request.GET.get("source", "web_form"))
        email = request.data.get("email", "")
        api_key = request.headers.get("X-Api-Key", "")

        customer = resolve_customer(source=source, email=email, api_key=api_key)

        # Step 0: classify intent
        from ..services.deepseek_client import get_deepseek_client
        classifier = InstructorClassifier(get_deepseek_client())
        classification = classifier.classify(text)

        conversation = AIConversation.objects.create(
            status=AIConversation.PROCESSING,
            source=source,
            customer=customer,
            intent=classification.intent,
        )

        # Route by intent
        if classification.intent != "selection":
            conversation.status = AIConversation.COMPLETED
            conversation.save(update_fields=["status"])
            return Response({
                "status": classification.intent,
                "confidence": classification.confidence,
                "subtype": classification.subtype,
                "message": _intent_message(classification.intent),
                "source": source,
                "customer": customer.name if customer else None,
            })

        processor = TreeProcessor(conversation, customer=customer)
        skill_code = request.data.get("skill_code", "")
        result = processor.decompose(text=text, prompt_id=prompt_id, skill_code=skill_code)
        return Response({
            **result,
            "source": source,
            "customer": customer.name if customer else None,
        })

class ExtractView(APIView):
    """POST /api/ai-assistant/extract/{node_id}/ вЂ” Р¤Р°Р·Р° 2: РёР·РІР»РµС‡РµРЅРёРµ С„РёР»СЊС‚СЂРѕРІ.

    Р”Р»СЏ СѓР·Р»Р° РґРµСЂРµРІР° Р·Р°РїСѓСЃРєР°РµС‚ extract-РїСЂРѕРјРїС‚, СЃРїРµС†РёС„РёС‡РЅС‹Р№ РґР»СЏ С‚РёРїР° РѕР±РѕСЂСѓРґРѕРІР°РЅРёСЏ.
    """
    permission_classes = []

    def post(self, request, node_id):
        try:
            node = SelectionNode.objects.get(id=node_id)
        except SelectionNode.DoesNotExist:
            return Response({"error": "node not found"}, status=404)

        processor = TreeProcessor(node.conversation, customer=node.conversation.customer)
        result = processor.extract(node_id=node.id)
        return Response(result)

class FilterView(APIView):
    """POST /api/ai-assistant/filter/{node_id}/ вЂ” Р¤Р°Р·Р° 3: РІС‹Р·РѕРІ API-С„РёР»СЊС‚СЂР°.

    Р’С‹Р·С‹РІР°РµС‚ С„РёР»СЊС‚СЂ РѕР±РѕСЂСѓРґРѕРІР°РЅРёСЏ (СЌРЅРґРїРѕРёРЅС‚ РёР· EquipmentType.filter_endpoint)
    СЃ effective_params СѓР·Р»Р°.
    """
    permission_classes = []

    def post(self, request, node_id):
        try:
            node = SelectionNode.objects.get(id=node_id)
        except SelectionNode.DoesNotExist:
            return Response({"error": "node not found"}, status=404)

        processor = TreeProcessor(node.conversation, customer=node.conversation.customer)
        result = processor.filter_node(node_id=node.id)
        return Response(result)

class SelectView(APIView):
    """POST /api/ai-assistant/select/{node_id}/ вЂ” Р¤Р°Р·Р° 4: РІС‹Р±РѕСЂ РїСЂРѕРґСѓРєС‚Р° + РєР°СЃРєР°Рґ.

    РџСЂРёРЅРёРјР°РµС‚ {product_type: "...", product_id: N}.
    РЎРѕС…СЂР°РЅСЏРµС‚ РІС‹Р±РѕСЂ Рё РїСЂРѕР±СЂР°СЃС‹РІР°РµС‚ РїР°СЂР°РјРµС‚СЂС‹ РґРѕС‡РµСЂРЅРёРј СѓР·Р»Р°Рј С‡РµСЂРµР· DerivationRule.
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

        processor = TreeProcessor(node.conversation, customer=node.conversation.customer)
        result = processor.select_product(
            node_id=node.id, product_type=product_type, product_id=int(product_id)
        )
        return Response(result)

class CompareView(APIView):
    """POST /api/ai-assistant/compare/{node_id}/ вЂ” Р¤Р°Р·Р° 5: СЃСЂР°РІРЅРµРЅРёРµ С‚СЂРµР±РѕРІР°РЅРёР№ Рё С„Р°РєС‚Р°.

    РЎСЂР°РІРЅРёРІР°РµС‚ extract_output СЃ selected_product_specs РїРѕ СЃРµРјР°РЅС‚РёРєРµ РїР°СЂР°РјРµС‚СЂРѕРІ.
    """
    permission_classes = []

    def post(self, request, node_id):
        try:
            node = SelectionNode.objects.get(id=node_id)
        except SelectionNode.DoesNotExist:
            return Response({"error": "node not found"}, status=404)

        processor = TreeProcessor(node.conversation, customer=node.conversation.customer)
        result = processor.compare(node_id=node.id)
        return Response(result)

class EBOMView(APIView):
    """GET /api/ai-assistant/ebom/{conversation_id}/ вЂ” РёРЅР¶РµРЅРµСЂРЅР°СЏ СЃРїРµС†РёС„РёРєР°С†РёСЏ.

    Р’РѕР·РІСЂР°С‰Р°РµС‚ EBOM: РёРµСЂР°СЂС…РёС‡РµСЃРєРёР№ СЃРѕСЃС‚Р°РІ СЃ РёСЃС…РѕРґРЅС‹РјРё С‚СЂРµР±РѕРІР°РЅРёСЏРјРё.
    """
    permission_classes = []

    def get(self, request, conversation_id):
        try:
            conversation = AIConversation.objects.get(id=conversation_id)
        except AIConversation.DoesNotExist:
            return Response({"error": "conversation not found"}, status=404)

        processor = TreeProcessor(conversation, customer=conversation.customer)
        return Response(processor.build_ebom())

class MBOMView(APIView):
    """GET /api/ai-assistant/mbom/{conversation_id}/ вЂ” РїСЂРѕРёР·РІРѕРґСЃС‚РІРµРЅРЅР°СЏ СЃРїРµС†РёС„РёРєР°С†РёСЏ.

    Р’РѕР·РІСЂР°С‰Р°РµС‚ MBOM: РёРµСЂР°СЂС…РёС‡РµСЃРєРёР№ СЃРѕСЃС‚Р°РІ СЃ Р°СЂС‚РёРєСѓР»Р°РјРё РІС‹Р±СЂР°РЅРЅС‹С… РїСЂРѕРґСѓРєС‚РѕРІ.
    """
    permission_classes = []

    def get(self, request, conversation_id):
        try:
            conversation = AIConversation.objects.get(id=conversation_id)
        except AIConversation.DoesNotExist:
            return Response({"error": "conversation not found"}, status=404)

        processor = TreeProcessor(conversation, customer=conversation.customer)
        return Response(processor.build_mbom())

class TreeView(APIView):
    """GET /api/ai-assistant/tree/{conversation_id}/ вЂ” РїРѕР»РЅРѕРµ РґРµСЂРµРІРѕ РїРѕРґР±РѕСЂР°.

    Р’РѕР·РІСЂР°С‰Р°РµС‚ РІСЃРµ SelectionNode РґР»СЏ РґРёР°Р»РѕРіР° РІ РІРёРґРµ РІР»РѕР¶РµРЅРЅРѕРіРѕ РґРµСЂРµРІР°.
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
            "extract_labels": self._resolve_labels(node),
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

    def _resolve_labels(self, node) -> dict:
        """Resolve human-readable labels via EquipmentTypeParameter.get_options()."""
        labels = {}
        eo = node.extract_output or {}
        if not eo or not node.equipment_type:
            return labels
        from configurator.models import EquipmentTypeParameter
        etp_params = EquipmentTypeParameter.objects.filter(
            equipment_type=node.equipment_type,
            is_active=True,
        )
        if not etp_params:
            return labels
        for p in etp_params:
            value = eo.get(p.param_name)
            if value is None or value == '':
                continue
            try:
                opts = p.get_options()
                for o in opts:
                    if o.get('id') == value:
                        labels[p.param_name] = o.get('name', str(value))
                        break
            except Exception:
                pass
        return labels

# в”Ђв”Ђ Pipeline Configurator ViewSets в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

class PipelineSkillViewSet(viewsets.ModelViewSet):
    pagination_class = None
    serializer_class = PipelineSkillSerializer
    queryset = PipelineSkill.objects.select_related("equipment_type", "prompt_template", "output_schema")
    permission_classes = [IsAdminUser]

class SkillOverrideViewSet(viewsets.ModelViewSet):
    pagination_class = None
    serializer_class = SkillOverrideSerializer
    queryset = SkillOverride.objects.select_related("customer", "step_config")
    permission_classes = [IsAdminUser]

class JSONSchemaViewSet(viewsets.ModelViewSet):
    pagination_class = None
    serializer_class = JSONSchemaSerializer
    queryset = JSONSchema.objects.all()
    permission_classes = [IsAdminUser]

def _intent_message(intent: str) -> str:
    """Human-readable message for non-selection intents."""
    messages = {
        "price_check": "Запрос цены. Функция в разработке.",
        "cert_search": "Поиск сертификата. Функция в разработке.",
        "replacement": "Подбор аналога. Функция в разработке.",
        "specs": "Характеристики. Функция в разработке.",
        "catalog": "Каталог. Функция в разработке.",
        "rejected": "Запрос не относится к тематике арматуры и приводов.",
        "needs_info": "Недостаточно данных. Уточните параметры.",
    }
    return messages.get(intent, "Не удалось определить тип запроса.")

# ── Configurator support: EquipmentType & Customer lists ──────

class EquipmentTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentType
        fields = ["id", "code", "name", "level", "filter_endpoint", "param_semantics", "is_active"]

class EquipmentTypeListView(ListAPIView):
    pagination_class = None
    queryset = EquipmentType.objects.filter(is_active=True).order_by("level", "name")
    serializer_class = EquipmentTypeListSerializer
    permission_classes = [IsAdminUser]

    def get_object(self):
        return EquipmentType.objects.get(pk=self.kwargs.get("pk"))

    def patch(self, request, pk=None):
        obj = EquipmentType.objects.get(pk=pk)
        ser = self.serializer_class(obj, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

class CustomerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCustomer
        fields = ["id", "name", "short_name", "email", "is_active"]

class ModelRolesView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        from ..models import AIProvider
        roles = []
        for p in AIProvider.objects.filter(is_active=True):
            for role in (p.model_mapping or {}).keys():
                if role not in roles:
                    roles.append(role)
        return Response(sorted(roles))

class CustomerListView(ListAPIView):
    pagination_class = None
    queryset = ProjectCustomer.objects.filter(is_active=True).order_by("name")
    serializer_class = CustomerListSerializer
    permission_classes = [IsAdminUser]

# ── CompositionGroup CRUD ──

class CompositionGroupViewSet(viewsets.ModelViewSet):
    pagination_class = None
    serializer_class = None
    queryset = CompositionGroup.objects.prefetch_related("equipment_types", "children", "references")
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        from .serializers import CompositionGroupSerializer
        return CompositionGroupSerializer

    @action(detail=True, methods=["post"])
    def add_reference(self, request, pk=None):
        group = self.get_object()
        ref_id = request.data.get("reference_id")
        if not ref_id:
            return Response({"error": "reference_id required"}, status=400)
        if int(ref_id) == group.id:
            return Response({"error": "Cannot reference self"}, status=400)
        ref_group = CompositionGroup.objects.filter(id=ref_id, is_active=True).first()
        if not ref_group:
            return Response({"error": "Reference group not found"}, status=404)
        if ref_group.parent_id == group.id:
            return Response({"error": "Group is already a child, cannot also reference"}, status=400)
        group.references.add(ref_group)
        return Response({"ok": True})

    @action(detail=True, methods=["post"])
    def remove_reference(self, request, pk=None):
        group = self.get_object()
        ref_id = request.data.get("reference_id")
        if not ref_id:
            return Response({"error": "reference_id required"}, status=400)
        group.references.remove(ref_id)
        return Response({"ok": True})

    @action(detail=True, methods=["get"])
    def referenced_by(self, request, pk=None):
        group = self.get_object()
        refs = group.referenced_by.filter(is_active=True).values("id", "name", "code")
        return Response(list(refs))

class CompositionGroupTreeView(APIView):
    """Получить полное дерево CompositionGroup + EquipmentType."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        from .serializers import CompositionGroupTreeSerializer
        roots = CompositionGroup.objects.filter(parent__isnull=True, is_active=True).order_by("sorting_order", "name")
        return Response(CompositionGroupTreeSerializer(roots, many=True).data)

class EquipmentTypeTreeView(APIView):
    """Получить дерево EquipmentType (для drag-drop источника)."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        from .serializers import EquipmentTypeTreeSerializer
        roots = EquipmentType.objects.filter(parent__isnull=True, is_active=True).order_by("sorting_order", "name")
        return Response(EquipmentTypeTreeSerializer(roots, many=True).data)

# ── MBOM CRUD ──

class MBOMViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = MBOM.objects.prefetch_related("items__children", "items__sku", "items__equipment_type")
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        from .serializers import MBOMSerializer
        return MBOMSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class MBOMItemViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = MBOMItem.objects.select_related("equipment_type", "sku", "composition_group")
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        from .serializers import MBOMItemSerializer
        return MBOMItemSerializer

# ── Schema generation from model FILTER_DEFINITIONS ──
