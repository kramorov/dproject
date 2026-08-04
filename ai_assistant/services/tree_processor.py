"""Процессор дерева подбора — центральный сервис конвейера.

Реализует все шаги:
- decompose: текст → дерево SelectionNode (LLM)
- extract: узел → structured filters (LLM)
- filter: фильтры → options (API)
- select: выбор + каскад параметров
- compare: требования vs факт
- build_ebom/build_mbom: генерация спецификаций
"""

import json
import logging
import re
from typing import Optional

from django.db import transaction

from core.models.equipment_type import EquipmentType

from ai_assistant.models import (
    AIConversation, AIMessage,
    PipelineSkill, SkillOverride, CascadeRule, SelectionNode,
)
from ai_assistant.services.deepseek_client import get_deepseek_client
from ai_assistant.services.token_tracker import save_token_usage, update_skill_latency, estimate_cost

logger = logging.getLogger(__name__)


class TreeProcessor:
    """Процессор дерева подбора.

    Работает в контексте одной AIConversation.
    Все мутации дерева — через этот класс.
    """

    def __init__(self, conversation: AIConversation, customer=None):
        self.conversation = conversation
        self.customer = customer
        self.client = get_deepseek_client()

    # ── Разрешение конфигурации ──────────────────────────────────

    def _get_config(self, step: str = "", equipment_type: Optional[EquipmentType] = None, code: str = "") -> Optional[dict]:
        """Разрешает конфигурацию шага: Override → StepConfig → None.

        Args:
            step: Код шага ('decompose', 'extract', 'filter', ...).
            equipment_type: Тип оборудования (None для общих шагов).

        Returns:
            dict с ключами step, prompt_template, model_role, output_schema,
            prompt_text — или None, если конфигурация не найдена.
        """

        if code:
            base = PipelineSkill.objects.filter(code=code, is_active=True).first()
        else:
            base = PipelineSkill.objects.filter(
                step=step, equipment_type=equipment_type, is_active=True
            ).first()
        if not base:
            return None

        if self.customer:
            override = SkillOverride.objects.filter(
                customer=self.customer, step_config=base, is_active=True
            ).first()
            if override:
                return self._apply_override(base, override)

        # Return dict for consistent interface (no ORM mutation)
        return {
            "skill": base,
            "step": base.step,
            "prompt_template": base.prompt_template,
            "model_role": base.model_role,
            "output_schema": base.output_schema,
            "prompt_text": base.prompt_template.template_text if base.prompt_template else "",
        }

    def _apply_override(self, base: PipelineSkill, override: SkillOverride) -> dict:
        """Применяет переопределение к конфигурации.

        Не мутирует ORM-объекты — возвращает runtime dict.
        """
        tmpl = override.prompt_template if override.prompt_template else base.prompt_template
        model_role = override.model_role if override.model_role else base.model_role
        output_schema = override.output_schema if override.output_schema else base.output_schema

        if override.prompt_suffix and tmpl:
            prompt_text = (tmpl.template_text or "") + "\n" + override.prompt_suffix
        else:
            prompt_text = tmpl.template_text if tmpl else ""

        return {
            "skill": base,
            "step": base.step,
            "prompt_template": tmpl,
            "model_role": model_role,
            "output_schema": output_schema,
            "prompt_text": prompt_text,
        }

    # ── Шаг 1: Decompose ─────────────────────────────────────────

    def decompose(self, text: str, prompt_id: Optional[int] = None, skill_code: str = "") -> dict:
        """Фаза 1: текст запроса → дерево SelectionNode.

        Args:
            text: Текст запроса пользователя.
            prompt_id: ID промпта из AIPromptTemplate (если None — из StepConfig).

        Returns:
            dict: {'conversation_id', 'status', 'tree': [...]}
        """

        # Сохраняем сообщение пользователя
        AIMessage.objects.create(
            conversation=self.conversation, role="user", content=text
        )

        # Загружаем конфигурацию decompose
        config = self._get_config(code=skill_code) or self._get_config("decompose")
        if not config or not config["prompt_template"]:
            return {"status": "error", "message": "No decompose StepConfig"}

        # Промпт: приоритет — явно переданный prompt_id, иначе из StepConfig
        from ai_assistant.models import AIPromptTemplate
        prompt_template = None
        if prompt_id:
            prompt_template = AIPromptTemplate.objects.filter(id=prompt_id).first()
        if not prompt_template:
            prompt_template = config["prompt_template"]

        prompt_text = self._resolve_prompt(config["prompt_text"], user_text=text)

                # LLM call — OUTSIDE transaction (slow, SQLite lock issue)
        llm_result = self.client.debug(prompt_text)

        raw_text = llm_result.get("raw_text", "")
        tree_data = self._parse_tree_output(raw_text)

        # DB writes — inside atomic transaction
        with transaction.atomic():
            ai_msg = AIMessage.objects.create(
                conversation=self.conversation, role="assistant",
                content=raw_text, prompt_used=prompt_text,
                latency_ms=llm_result.get("latency_ms"),
                prompt_template=prompt_template,
                intent="decompose",
            )
            save_token_usage(ai_msg, llm_result, customer=self.customer)

            # Cache user_text BEFORE extract (prompts need it for resolution)
            tree_data["user_text"] = text
            self.conversation.selection_tree = tree_data
            self.conversation.save(update_fields=["selection_tree"])

            # Create SelectionNodes
            nodes = self._create_nodes_from_tree(tree_data)

            # Auto-extract for all component nodes
            all_nodes = self._all_nodes(nodes)
            extracted = {}
            for n in all_nodes:
                if not n.equipment_type:
                    continue
                try:
                    result = self.extract(node_id=n.id)
                    resolved_labels = self._resolve_labels(n)
                    result["_field_labels"] = resolved_labels.pop('_field_labels', {})
                    result["_labels"] = resolved_labels
                    extracted[n.decompose_output.get("id") or str(n.id)] = result
                except Exception as e:
                    logger.warning(f"Auto-extract failed for node {n.id}: {e}")

        # Update skill latency estimate (outside transaction)
        skill = config.get("skill")
        if skill:
            update_skill_latency(skill, llm_result.get("latency_ms"))

        return {
            "conversation_id": self.conversation.id,
            "status": "ready" if nodes else "needs_info",
            "extracted": extracted,
            "tokens": llm_result.get("total_tokens", 0),
            "prompt_tokens": llm_result.get("prompt_tokens", 0),
            "completion_tokens": llm_result.get("completion_tokens", 0),
            "cost": estimate_cost(llm_result.get("model", "deepseek"), llm_result.get("prompt_tokens", 0), llm_result.get("completion_tokens", 0)),
            "tasks": _safe_task_list(self._all_nodes(nodes)),
            "tree": tree_data,
            "node_ids": [{"id": n.id, "type": n.equipment_type.code if n.equipment_type else None, "tree_id": n.decompose_output.get("id") if n.decompose_output else None} for n in self._all_nodes(nodes)],
        }

    def _parse_tree_output(self, raw_text: str) -> dict:
        """Парсит JSON из вывода decompose.

        Пытается найти JSON-блок в ответе LLM.
        """
        # Find all JSON code blocks; pick the best one
        json_matches = list(re.finditer(r"```(?:json)?\s*([\s\S]*?)```", raw_text))
        candidates = [m.group(1) for m in json_matches]

        # Prefer the block containing "positions", otherwise the longest one
        best = None
        for c in candidates:
            if '"positions"' in c or "'positions'" in c:
                best = c
                break
        if best is None and candidates:
            best = max(candidates, key=len)

        if best:
            try:
                return json.loads(best)
            except json.JSONDecodeError:
                pass

        # Try whole text
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            pass

        # Try text tree format
        return self._parse_text_tree(raw_text)

    def _parse_text_tree(self, raw_text: str) -> dict:
        """Parse markdown text tree: [id]: type | depends_on: [...] | params."""
        positions = []
        global_reqs = {}
        current_pos = None

        for line in raw_text.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("==="):
                continue
            if ":" in stripped and stripped.startswith(("температура", "Exd", "IP", "давление")):
                key, val = stripped.split(":", 1)
                global_reqs[key.strip()] = val.strip()
                continue
            if stripped.startswith("---") and "ПОЗИЦИЯ" in stripped:
                current_pos = {"description": "", "components": []}
                positions.append(current_pos)
                continue
            if not current_pos:
                continue
            if stripped.startswith(("описание:", "description:")):
                current_pos["description"] = stripped.split(":", 1)[1].strip()
                continue
            m = re.match(r"\[([\w.]+)\]:\s*(\w+)\s*\|\s*depends_on:\s*\[([^\]]*)\]\s*\|?\s*(.*)", stripped)
            if m:
                deps = [x.strip() for x in m.group(3).split(",") if x.strip()]
                current_pos["components"].append({
                    "id": m.group(1), "type": m.group(2),
                    "depends_on": deps,
                    "summary": m.group(4).strip() if m.group(4) else "",
                })

        if positions:
            return {"positions": positions, "global_requirements": global_reqs}
        return {"raw_analysis": raw_text, "positions": []}

    def _all_nodes(self, nodes):
        """Recursively collect all nodes from a list (positions + components)."""
        result = []
        for n in nodes:
            result.append(n)
            result.extend(self._all_nodes(list(n.children.all())))
        return result

    def _create_nodes_from_tree(self, tree_data: dict) -> list:
        """Создаёт SelectionNode рекурсивно из данных дерева.

        Args:
            tree_data: {'positions': [{...components: [...]}]}

        Returns:
            list of root SelectionNode.
        """
        # Batch EquipmentType lookup: collect all eq_codes first
        codes = set()
        _collect_codes(tree_data, codes)
        eq_type_map = {}
        if codes:
            for et in EquipmentType.objects.filter(code__in=codes):
                eq_type_map[et.code] = et

        nodes = []
        positions = tree_data.get("positions", [])
        for pos_idx, pos_data in enumerate(positions, 1):
            node = self._create_node(
                level=1, order=pos_idx, path=str(pos_idx),
                data=pos_data, parent=None, eq_type_map=eq_type_map,
            )
            nodes.append(node)
        return nodes

    def _create_node(self, level: int, order: int, path: str,
                     data: dict, parent: Optional[SelectionNode],
                     eq_type_map: dict = None) -> SelectionNode:
        """Создаёт один SelectionNode и рекурсивно — его детей.

        Args:
            level: Уровень вложенности.
            order: Порядок среди siblings.
            path: Materialized path.
            data: Данные узла из decompose-вывода.
            parent: Родительский узел.
            eq_type_map: Предзагруженный dict {code: EquipmentType}.

        Returns:
            SelectionNode.
        """
        if eq_type_map is None:
            eq_type_map = {}

        eq_code = data.get("type")
        equipment_type = eq_type_map.get(eq_code) if eq_code else None

        # Safe float conversion
        try:
            quantity = float(data.get("quantity", data.get("qty", 1.0)))
        except (ValueError, TypeError):
            quantity = 1.0

        node = SelectionNode.objects.create(
            conversation=self.conversation,
            parent=parent,
            equipment_type=equipment_type,
            task_type=data.get("task", "selection"),
            level=level,
            order=order,
            path=path,
            label=data.get("description", data.get("type", f"Node {path}")),
            quantity=quantity,
            quantity_unit=data.get("quantity_unit", data.get("unit", "pcs")),
            decompose_output=data,
            extract_output=data.get("requirements", data.get("params")),
            status="decomposed",
        )

        # Children
        children = data.get("components", [])
        for child_idx, child_data in enumerate(children, 1):
            child_path = f"{path}/{child_idx}"
            self._create_node(
                level=level + 1, order=child_idx,
                path=child_path, data=child_data, parent=node,
                eq_type_map=eq_type_map,
            )

        return node

    # ── Шаг 2: Extract ───────────────────────────────────────────

    def extract(self, node_id: int) -> dict:
        """Фаза 2: извлечение структурированных фильтров для узла.

        Использует промпт, специфичный для типа оборудования узла.

        Args:
            node_id: ID SelectionNode.

        Returns:
            dict: {'status', 'extract_output'}
        """

        node = SelectionNode.objects.get(id=node_id)
        if not node.equipment_type:
            return {"status": "skipped", "message": "No equipment_type — nothing to extract"}

        config = self._get_config("extract", node.equipment_type)
        if not config or not config["prompt_template"]:
            return {"status": "skipped", "message": f"No extract config for {node.equipment_type.code}"}

        node.status = "extracting"
        node.save(update_fields=["status"])

        prompt = self._resolve_prompt(
            config["prompt_text"],
                user_text=node.conversation.selection_tree.get("user_text", "") if node.conversation.selection_tree else "",
                requirements=json.dumps(node.decompose_output or {}, ensure_ascii=False),
                global_requirements=json.dumps(
                    self.conversation.selection_tree.get("global_requirements", {}) if self.conversation.selection_tree else {},
                    ensure_ascii=False,
                ),
            )

        # Use structured output if JSONSchema is configured
        llm_result = self.client.debug(prompt)

        raw_text = llm_result.get("raw_text", "")
        try:
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw_text)
            filters = json.loads(json_match.group(1) if json_match else raw_text)
        except (json.JSONDecodeError, AttributeError):
            filters = {"raw_output": raw_text}
        else:
            try:
                json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw_text)
                filters = json.loads(json_match.group(1) if json_match else raw_text)
            except (json.JSONDecodeError, AttributeError):
                filters = {"raw_output": raw_text}

        node.extract_output = filters
        node.status = "extracted"
        node.save(update_fields=["extract_output", "status"])

        # Resolve labels for frontend display
        labels = self._resolve_labels(node)
        filters["_field_labels"] = labels.pop('_field_labels', {}) if labels else {}
        if labels:
            filters["_labels"] = labels

        # Log
        msg = AIMessage.objects.create(
            conversation=self.conversation, role="assistant",
            content=raw_text, prompt_used=prompt,
            prompt_template=config["prompt_template"],
            intent="extract",
        )

        # Validate mandatory fields
        missing = self._validate_required(node)
        if missing:
            node.status = "needs_info"
            node.status_message = missing
            node.save(update_fields=["status", "status_message"])
            return {"status": "needs_info", "message": missing}

        save_token_usage(msg, llm_result, customer=self.customer)

        # Update skill latency
        skill = config.get("skill")
        if skill:
            update_skill_latency(skill, llm_result.get("latency_ms"))

        return {"status": "extracted", "extract_output": filters}

    def _validate_required(self, node) -> str:
        """Проверяет обязательные поля после extract. Возвращает сообщение или None."""
        from core.wizard_filter_registry import get_filter_definitions_for_ct
        if not node.equipment_type or not node.equipment_type.content_type:
            return None
        defs = get_filter_definitions_for_ct(node.equipment_type.content_type_id)
        if not defs:
            return None
        missing = []
        for fd in defs:
            if getattr(fd, 'mandatory', 'any') != 'yes':
                continue
            value = node.extract_output.get(fd.param_name) if node.extract_output else None
            if value is None or value == '':
                missing.append(fd.label)
        if not missing:
            return None
        labels = '», «'.join(missing)
        return f"Не удалось определить: «{labels}» для {node.equipment_type.name}. Уточните запрос."

    def _resolve_labels(self, node) -> dict:
        labels = {}
        field_labels = {}
        eo = node.extract_output or {}
        if not eo or not node.equipment_type or not node.equipment_type.content_type:
            return {'_field_labels': field_labels}
        from core.wizard_filter_registry import get_filter_definitions_for_ct
        defs = get_filter_definitions_for_ct(node.equipment_type.content_type_id)
        if not defs:
            return {'_field_labels': field_labels}
        model_class = node.equipment_type.content_type.model_class()
        for fd in defs:
            field_labels[fd.param_name] = fd.label or fd.param_name
            value = eo.get(fd.param_name)
            if value is None or value == '':
                continue
            try:
                opts = fd.get_options(model_class) if model_class else []
                for o in opts:
                    if o.get('id') == value:
                        labels[fd.param_name] = o.get('name', str(value))
                        break
            except:
                pass
        labels['_field_labels'] = field_labels
        return labels

    # ── Шаг 3: Filter ────────────────────────────────────────────

    def filter_node(self, node_id: int) -> dict:
        """Фаза 3: вызов API-фильтра для получения вариантов.

        Args:
            node_id: ID SelectionNode.

        Returns:
            dict: {'status', 'options', 'total'}
        """

        node = SelectionNode.objects.get(id=node_id)
        if not node.equipment_type or not node.equipment_type.filter_endpoint:
            return {"status": "skipped", "message": "No filter endpoint"}

        node.status = "filtering"
        node.save(update_fields=["status"])

        # Collect params
        params = node.effective_params

        # Call handler directly instead of HTTP
        endpoint = node.equipment_type.filter_endpoint

        try:
            data = self._call_filter_handler(endpoint, params)
        except Exception as e:
            logger.error(f"Filter error for node {node_id}: {e}")
            node.status = "error"
            node.status_message = str(e)
            node.save(update_fields=["status", "status_message"])
            return {"status": "error", "message": str(e)}

        node.filter_output = data
        node.status = "filtered"
        node.save(update_fields=["filter_output", "status"])

        return {
            "status": "filtered",
            "options": data.get("options", data.get("search_results", [])),
            "total": data.get("total", data.get("total_found", 0)),
        }

    def _call_filter_handler(self, endpoint: str, params: dict) -> dict:
        """Вызывает локальный handler по endpoint без HTTP-запроса.

        Args:
            endpoint: Строка вида '/api/actuators/search/' или
                      'actuator_selector_handler.process_selection_params'.
            params: Параметры для передачи в handler.

        Returns:
            dict с результатами фильтрации.
        """
        # Map known endpoints to handler functions
        handler_map = {
            "/api/actuators/search/": "pneumatic_actuators.actuator_selector_handler.process_selection_params",
            "/api/pneumatic_actuators/selector/search/": "pneumatic_actuators.actuator_selector_handler.process_selection_params",
            "/api/solenoid_valves/filter/": "ai_assistant.services.filter_handlers.solenoid_valves_filter",
            "/api/options/bkv/filter/": "ai_assistant.services.filter_handlers.limit_switch_filter",
            "/api/manual_override/filter/": "ai_assistant.services.filter_handlers.gearbox_filter",
            "/api/filter_regulator/filter/": "ai_assistant.services.filter_handlers.filter_regulator_filter",
            "/api/pneumatic_fittings/filter/": "ai_assistant.services.filter_handlers.pneumatic_fittings_filter",
        }

        handler_path = handler_map.get(endpoint)
        if not handler_path:
            # Try to infer from endpoint: strip slashes, convert to module path
            # e.g. '/api/actuators/search/' → 'api.actuators.search'
            cleaned = endpoint.strip("/").replace("/", ".")
            handler_path = cleaned

        try:
            module_path, func_name = handler_path.rsplit(".", 1)
            import importlib
            mod = importlib.import_module(module_path)
            handler_func = getattr(mod, func_name)
            result = handler_func(params)
            if isinstance(result, dict):
                return result
            return {"options": result, "total": len(result) if isinstance(result, list) else 0}
        except (ImportError, AttributeError, ValueError) as e:
            logger.warning(f"Cannot import handler for endpoint '{endpoint}': {e}")
            return {"status": "skipped", "message": f"handler not implemented: {e}"}

    # ── Шаг 4: Select + Cascade ──────────────────────────────────

    def select_product(self, node_id: int, product_type: str, product_id: int) -> dict:
        """Выбор продукта для узла + каскад параметров дочерним узлам.

        Args:
            node_id: ID SelectionNode.
            product_type: Тип продукта (app_label.ModelName).
            product_id: ID продукта.

        Returns:
            dict: {'status', 'cascaded_to': [child_node_ids]}
        """

        node = SelectionNode.objects.get(id=node_id)

        # Загружаем спецификацию продукта
        specs = self._load_product_specs(product_type, product_id)

        node.selected_product_type = product_type
        node.selected_product_id = product_id
        node.selected_product_specs = specs
        node.status = "selected"
        node.save(update_fields=[
            "selected_product_type", "selected_product_id",
            "selected_product_specs", "status",
        ])

        # Каскад: для каждого дочернего узла
        cascaded = []
        for child in node.children.all():
            if not child.equipment_type:
                continue
            rule = CascadeRule.objects.filter(
                parent_type=node.equipment_type,
                child_type=child.equipment_type,
                is_active=True,
            ).first()
            if not rule:
                continue

            cascade_params = {}
            for src_field, dst_field in rule.mapping.items():
                if src_field in specs:
                    cascade_params[dst_field] = specs[src_field]

            if cascade_params:
                child.cascade_params = cascade_params
                child.status = "pending"  # готов к повторному filter
                child.save(update_fields=["cascade_params", "status"])
                cascaded.append(child.id)

        return {"status": "selected", "product_specs": specs, "cascaded_to": cascaded}

    def _load_product_specs(self, product_type: str, product_id: int) -> dict:
        """Загружает характеристики продукта из соответствующей модели.

        Args:
            product_type: 'app_label.ModelName'.
            product_id: ID записи.

        Returns:
            dict с характеристиками продукта.
        """

        from django.apps import apps
        try:
            model = apps.get_model(product_type)
            obj = model.objects.filter(pk=product_id).first()
            if not obj:
                return {}
            # Отдаём __dict__ без служебных полей
            return {
                k: v for k, v in obj.__dict__.items()
                if not k.startswith("_") and k != "id"
            }
        except Exception as e:
            logger.warning(f"Cannot load product specs for {product_type}#{product_id}: {e}")
            return {}

    # ── Шаг 5: Compare ───────────────────────────────────────────

    def compare(self, node_id: int) -> dict:
        """Сравнение требований пользователя с фактическими характеристиками.

        Использует param_semantics из EquipmentType для определения
        направления сравнения ('min', 'max', 'exact').

        Args:
            node_id: ID SelectionNode.

        Returns:
            dict: {'status', 'comparisons': [...]}
        """

        node = SelectionNode.objects.get(id=node_id)
        if not node.selected_product_specs or not node.extract_output:
            return {"status": "skipped", "message": "Need both extract_output and selected_product_specs"}

        required = node.extract_output
        actual = node.selected_product_specs
        semantics = {}
        if node.equipment_type and node.equipment_type.param_semantics:
            semantics = node.equipment_type.param_semantics

        comparisons = []
        for param, req_val in required.items():
            act_val = actual.get(param)
            sem = semantics.get(param, {})

            if act_val is None:
                comparisons.append({
                    "param": param,
                    "required": req_val,
                    "actual": None,
                    "match": False,
                    "note": "не найдено в характеристиках продукта",
                })
                continue

            direction = sem.get("direction", "exact")
            label = sem.get("label", "")

            if direction == "exact":
                match = str(req_val) == str(act_val)
            elif direction == "min":
                try:
                    match = float(act_val) >= float(req_val)
                except (ValueError, TypeError):
                    match = str(act_val) == str(req_val)
            elif direction == "max":
                try:
                    match = float(act_val) <= float(req_val)
                except (ValueError, TypeError):
                    match = str(act_val) == str(req_val)
            else:
                match = str(req_val) == str(act_val)

            note = ""
            if not match:
                note = f"треб: {label} {req_val}" if label else f"треб: {req_val}"
            elif direction in ("min", "max") and str(req_val) != str(act_val):
                note = "выше требуемого" if direction == "min" else "ниже требуемого"

            comparisons.append({
                "param": param,
                "required": req_val,
                "actual": act_val,
                "match": match,
                "direction": direction,
                "label": label,
                "note": note,
            })

        node.compare_output = comparisons
        node.status = "compared"
        node.save(update_fields=["compare_output", "status"])

        return {"status": "compared", "comparisons": comparisons}

    # ── EBOM / MBOM ──────────────────────────────────────────────

    def build_ebom(self) -> dict:
        """Строит Engineering BOM: иерархический состав с требованиями.

        Использует extract_output (исходные требования) — база для
        переподбора замены.

        Returns:
            dict: {'positions': [{'items': [...]}]}
        """

        root_nodes = self.conversation.selection_nodes.filter(parent__isnull=True)
        return {
            "conversation_id": self.conversation.id,
            "positions": [self._node_to_ebom_item(n) for n in root_nodes],
        }

    def build_mbom(self) -> dict:
        """Строит Manufacturing BOM: иерархический состав с артикулами.

        Использует selected_product_type/id — конкретные SKU.

        Returns:
            dict: {'positions': [{'items': [...]}]}
        """

        root_nodes = self.conversation.selection_nodes.filter(parent__isnull=True)
        return {
            "conversation_id": self.conversation.id,
            "positions": [self._node_to_mbom_item(n) for n in root_nodes],
        }

    def _node_to_ebom_item(self, node: SelectionNode) -> dict:
        """Рекурсивно строит элемент EBOM."""
        item = {
            "label": node.label,
            "type": node.equipment_type.code if node.equipment_type else "position",
            "level": node.level,
            "quantity": node.total_quantity,
            "unit": node.quantity_unit,
            "requirements": node.extract_output,
            "compare": node.compare_output,
        }
        children = node.children.all()
        if children:
            item["items"] = [self._node_to_ebom_item(c) for c in children]
        return item

    def _node_to_mbom_item(self, node: SelectionNode) -> dict:
        """Рекурсивно строит элемент MBOM."""
        item = {
            "label": node.label,
            "type": node.equipment_type.code if node.equipment_type else "position",
            "level": node.level,
            "quantity": node.total_quantity,
            "unit": node.quantity_unit,
        }
        if node.selected_product_type and node.selected_product_id:
            item["product_type"] = node.selected_product_type
            item["product_id"] = node.selected_product_id
            item["product_specs"] = node.selected_product_specs
        children = node.children.all()
        if children:
            item["items"] = [self._node_to_mbom_item(c) for c in children]
        return item

    @staticmethod
    def _resolve_prompt(template_text: str, **extra) -> str:
        """Resolve {code} placeholders via AIPromptTemplate + extra kwargs."""
        from ai_assistant.models import AIPromptTemplate
        import re
        placeholders = set(re.findall(r"\{(\w+)\}", template_text))
        if not placeholders:
            return template_text
        templates = {t.code: t.template_text for t in AIPromptTemplate.objects.filter(code__in=placeholders, is_active=True)}
        result = template_text
        for ph in placeholders:
            val = templates.get(ph) or extra.get(ph)
            if val:
                result = result.replace("{" + ph + "}", str(val))
            else:
                result = result.replace("{" + ph + "}", "{" + ph + "}")  # keep literal
        return result

    def _get_system_prompt(self) -> str:
        """Системный промпт из БД или default."""
        from ai_assistant.models import AIPromptTemplate
        tmpl = AIPromptTemplate.objects.filter(
            name="system_prompt", is_active=True
        ).first()
        return tmpl.template_text if tmpl else "Ты — AI-ассистент компании АБРА."


def _safe_task_list(all_nodes) -> list:
    """Safely build task list from already-collected nodes."""
    result = []
    for n in all_nodes:
        decode = n.decompose_output or {}
        eq_code = n.equipment_type.code if n.equipment_type else "?"
        summary = decode.get("description") or (n.equipment_type.name if n.equipment_type else "")
        depends = decode.get("depends_on", []) if isinstance(decode, dict) else []
        result.append({"id": n.id, "type": eq_code, "summary": summary, "depends_on": depends})
    return result


def _collect_codes(tree_data: dict, codes: set) -> None:
    """Рекурсивно собирает все eq_code из данных дерева."""
    positions = tree_data.get("positions", [])
    for pos in positions:
        code = pos.get("type")
        if code:
            codes.add(code)
        for child in pos.get("components", []):
            _collect_codes({"positions": [child]}, codes)
