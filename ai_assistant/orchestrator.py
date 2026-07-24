"""
Главный оркестратор. Двухфазный: analyze → execute.

Фаза 1: POST /analyze/  → decompose → валидация → статус + план задач
Фаза 2: POST /execute/ → TaskGraph.execute() → progress_log + результаты
"""
import json
import logging

from django.db import transaction

from .models import AIConversation, AIMessage
from .classifiers import InstructorClassifier
from .schemas import get_schema_config, get_system_prompt
from .task_manager import TaskGraph, DECOMPOSE_V2_PROMPT, EQUIPMENT_REQUIREMENTS
from .services.deepseek_client import get_deepseek_client
from .services.token_tracker import save_token_usage, estimate_cost

logger = logging.getLogger(__name__)


class QueryOrchestrator:
    """Двухфазный: analyze → execute."""

    def __init__(self, tenant: str = "default"):
        """Инициализирует оркестратор с DeepSeek-клиентом и классификатором.

        Args:
            tenant: Идентификатор тенанта для мультитенантной конфигурации
                (промпты, схемы). По умолчанию "default".
        """
        self.client = get_deepseek_client()
        self.classifier = InstructorClassifier(self.client)
        self.tenant = tenant

    # ── Фаза 1: analyze ──────────────────────────────────────────

    def analyze(self, text: str, session_key: str = "", customer_id: int = None) -> dict:
        """Фаза 1: декомпозиция запроса пользователя, валидация и построение плана задач.

        Создаёт AIConversation, отправляет decompose-промпт в LLM,
        парсит текстовый вывод и возвращает структурированный план.

        Args:
            text: Текст запроса пользователя.
            session_key: Ключ сессии (для анонимных пользователей).
            customer_id: ID клиента в системе (опционально).

        Returns:
            dict с ключами: conversation_id, status, analysis_text,
            global_requirements, tasks, missing_info, reject_reason.
        """
        conversation = AIConversation.objects.create(
            session_key=session_key, customer_id=customer_id, status=AIConversation.PROCESSING,
        )
        AIMessage.objects.create(conversation=conversation, role="user", content=text)

        system_prompt = get_system_prompt(self.tenant)

        # DB-first: загружаем decompose-промпт
        decompose_config = get_schema_config("decompose")
        if decompose_config:
            prompt = decompose_config["prompt_template"].format(system_prompt=system_prompt, user_text=text)
        else:
            from .task_manager import DECOMPOSE_V2_PROMPT
            prompt = DECOMPOSE_V2_PROMPT.format(system_prompt=system_prompt, user_text=text)

        llm_result = self.client.debug(prompt)

        self._save_llm(llm_result, conversation, None, prompt, "decompose")

        raw = llm_result.get("raw_text", "")
        parsed = self._parse_decompose(raw)

        conversation.status = AIConversation.COMPLETED
        conversation.intent = "batch"
        conversation.save(update_fields=["status", "intent"])

        total_tokens = llm_result.get("total_tokens", 0) or 0
        prompt_tokens = llm_result.get("prompt_tokens", 0) or 0
        completion_tokens = llm_result.get("completion_tokens", 0) or 0
        reasoning_tokens = llm_result.get("reasoning_tokens", 0) or 0
        cost = estimate_cost(llm_result.get("model", ""), prompt_tokens, completion_tokens)

        return {
            "conversation_id": conversation.id,
            "status": parsed["status"],
            "analysis_text": raw,
            "global_requirements": parsed.get("global_reqs", {}),
            "tasks": parsed.get("tasks", []),
            "missing_info": parsed.get("missing_info"),
            "reject_reason": parsed.get("reject_reason"),
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "reasoning_tokens": reasoning_tokens,
            "cost": round(cost, 6),
        }

    def _parse_decompose(self, raw: str) -> dict:
        """Парсит текстовый вывод decompose-промпта в структурированный словарь.

        Разбирает секции: === СТАТУС ===, === АНАЛИЗ ===, === ЗАДАЧИ ===,
        === УТОЧНЕНИЯ ===, === ПРИЧИНА ОТКАЗА ===.

        Args:
            raw: Сырой текстовый ответ LLM.

        Returns:
            dict с ключами: status, global_reqs, tasks, missing_info, reject_reason.
        """
        result = {"status": "needs_info", "global_reqs": {}, "tasks": [], "missing_info": None}

        current_section = None
        for line in raw.split("\n"):
            line = line.strip()
            if "=== СТАТУС ===" in line:
                current_section = "status"
            elif "=== АНАЛИЗ ===" in line or "=== ГЛОБАЛЬНЫЕ ТРЕБОВАНИЯ ===" in line:
                current_section = "analysis"
            elif "=== ЗАДАЧИ ===" in line:
                current_section = "tasks"
            elif "=== УТОЧНЕНИЯ ===" in line:
                current_section = "missing_info"
            elif "=== ПРИЧИНА ОТКАЗА ===" in line:
                current_section = "reject_reason"
            elif line and current_section:
                if current_section == "status":
                    for s in ["ready", "needs_info", "rejected"]:
                        if s in line.lower():
                            result["status"] = s
                elif current_section == "tasks":
                    task = self._parse_task_line(line)
                    if task:
                        result["tasks"].append(task)
                elif current_section == "missing_info":
                    if not result["missing_info"]:
                        result["missing_info"] = line
                    else:
                        result["missing_info"] += "\n" + line
                elif current_section == "reject_reason":
                    result["reject_reason"] = line

        return result

    def _parse_task_line(self, line: str) -> dict:
        """Парсит одну строку задачи из decompose-вывода LLM.

        Поддерживает два формата:
        - Полный: ``[id]: type | depends_on: [ids] | summary``
        - Краткий: ``[id]: type | summary`` (depends_on пуст)

        Args:
            line: Строка из секции === ЗАДАЧИ ===.

        Returns:
            dict с ключами (id, type, depends_on, summary) или None,
            если строка не соответствует формату.
        """
        import re
        m = re.match(r'\[(\d+)\]:\s*(\w+)\s*\|\s*depends_on:\s*\[([^\]]*)\]\s*\|\s*(.*)', line)
        if not m:
            m = re.match(r'\[(\d+)\]:\s*(\w+)\s*\|\s*(.*)', line)
            if m:
                return {"id": int(m.group(1)), "type": m.group(2), "depends_on": [], "summary": m.group(3).strip()}
            return None
        deps = [int(x.strip()) for x in m.group(3).split(",") if x.strip()]
        return {"id": int(m.group(1)), "type": m.group(2), "depends_on": deps, "summary": m.group(4).strip()}

    # ── Фаза 2: execute ──────────────────────────────────────────

    def execute(self, tasks: list, global_reqs: dict = None) -> dict:
        """Фаза 2: выполнение графа задач через TaskGraph.

        Строит граф зависимостей из списка задач, выполняет топологическую
        сортировку и запускает задачи по уровням.

        Args:
            tasks: Список словарей задач (из фазы analyze).
            global_reqs: Глобальные требования (температура, Exd, IP и др.).

        Returns:
            dict с ключами: progress_log (пошаговый лог),
            results (результаты каждой задачи по task_id).
        """
        graph = TaskGraph(tasks, global_reqs)
        progress_log = graph.execute(self)
        return {
            "progress_log": progress_log,
            "results": graph.results,
        }

    # ── Пайплайн для actuator (существующий код) ─────────────────

    def _run_actuator_pipeline(self, task: dict, global_reqs: dict, previous_results: dict) -> dict:
        """Полный пайплайн подбора пневмопривода: classify → extract → resolve → execute.

        Этапы:
        1. Classify — определение интента через InstructorClassifier.
        2. Extract — извлечение фильтров из текста через LLM.
        3. Resolve — сопоставление фильтров с ID из БД.
        4. Execute — вызов ``process_selection_params`` для поиска моделей.

        Args:
            task: Словарь задачи с ключами (type, params, depends_on, ...).
            global_reqs: Глобальные требования, применяемые к params по умолчанию.
            previous_results: Результаты ранее выполненных зависимых задач.

        Returns:
            dict с ключами: status, message, raw_filters, resolved_ids,
            search_results.
        """
        params = task.get("params", {})
        # Применяем глобальные требования
        for key, val in (global_reqs or {}).items():
            params.setdefault(key, val)

        # Classify
        result = self.classifier.classify(params.get("_text", ""))
        intent = result.intent

        schema_config = get_schema_config(intent)
        if not schema_config:
            return {"status": "skipped", "message": f"Нет схемы для '{intent}'"}

        # Extract
        prompt = schema_config["prompt_template"].format(user_text=params.get("_text", ""))
        llm_result = self.client.extract_filters(prompt)
        if "error" in llm_result:
            return {"status": "error", "message": llm_result["error"]}

        raw_filters = llm_result.get("content", {})

        # Resolve
        db_context = self._get_db_context(raw_filters)
        if db_context:
            resolve_prompt = self._build_resolve_prompt(raw_filters, db_context)
            llm_result2 = self.client.extract_filters(resolve_prompt)
            resolved = llm_result2.get("content", raw_filters)
        else:
            resolved = raw_filters

        # Execute
        search_results = {}
        try:
            from pneumatic_actuators.actuator_selector_handler import process_selection_params
            search_results = process_selection_params(resolved)
        except Exception as e:
            logger.error(f"Actuator selection failed: {e}")
            search_results = {"error": str(e)}

        total = search_results.get("total_found", 0)
        return {
            "status": "done",
            "message": f"Найдено {total} моделей" if total else "Ничего не найдено",
            "raw_filters": raw_filters,
            "resolved_ids": resolved,
            "search_results": search_results,
        }

    # ── Вспомогательные ──────────────────────────────────────────

    def _get_db_context(self, raw_filters):
        """Собирает контекст из БД для фазы resolve: списки опций и справочников.

        Загружает активные записи из моделей:
        PneumaticIpOption, PneumaticExdOption, PneumaticBodyCoatingOption,
        PneumaticHandWheelOption, ValveTypes, DnVariety, PnVariety,
        PneumaticActuatorVariety.

        Args:
            raw_filters: Сырые фильтры, извлечённые из запроса (не используются
                напрямую, зарезервированы для будущей фильтрации контекста).

        Returns:
            dict с ключами-категориями, значения — списки dict с id и name.
            В случае ошибок импорта возвращает пустой словарь.
        """
        ctx = {}
        try:
            from pneumatic_actuators.models.pa_options import (
                PneumaticIpOption, PneumaticExdOption,
                PneumaticBodyCoatingOption, PneumaticHandWheelOption,
            )
            for key, cls in [
                ("ip_options", PneumaticIpOption),
                ("exd_options", PneumaticExdOption),
                ("coating_options", PneumaticBodyCoatingOption),
                ("hand_wheel_options", PneumaticHandWheelOption),
            ]:
                items = cls.get_for_select(active_only=True)
                ctx[key] = [{"id": it.get("id"), "name": it.get("name")} for it in items[:30]]
        except Exception as e:
            logger.warning(f"DB context failed: {e}")
        try:
            from params.models import ValveTypes, DnVariety, PnVariety
            ctx["valve_types"] = list(ValveTypes.objects.filter(is_active=True).values("id", "name", "code")[:10])
            ctx["dn_varieties"] = list(DnVariety.objects.filter(is_active=True).values("id", "name")[:20])
            ctx["pn_varieties"] = list(PnVariety.objects.filter(is_active=True).values("id", "name")[:10])
        except Exception as e:
            logger.warning(f"DB params failed: {e}")
        try:
            from pneumatic_actuators.models import PneumaticActuatorVariety
            ctx["actuator_varieties"] = list(
                PneumaticActuatorVariety.objects.filter(is_active=True).values("id", "name", "code")[:5]
            )
        except Exception:
            pass
        return ctx

    def _build_resolve_prompt(self, raw_filters, db_context):
        """Формирует resolve-промпт для сопоставления фильтров с ID из БД.

        Отправляет LLM пару «параметры → опции БД» и просит вернуть JSON
        с полями ``_id`` (например, ``valve_type_id``, ``dn_id``).

        Args:
            raw_filters: Словарь параметров, извлечённых на фазе extract.
            db_context: Словарь контекста из ``_get_db_context``.

        Returns:
            str — текстовый промпт для LLM.
        """
        return f"""Даны параметры (возможно, на русском) и список опций из базы.
Найди соответствие по смыслу.
Параметры: {json.dumps(raw_filters, ensure_ascii=False)}
Опции из БД: {json.dumps(db_context, ensure_ascii=False)}
Верни ТОЛЬКО JSON с полями _id (valve_type_id, dn_id, ...). Не найдено — null."""

    def _save_llm(self, llm_result, conversation, parent_msg, prompt, intent):
        """Сохраняет результат LLM-вызова в AIMessage и AITokenUsage.

        При ошибке создаёт сообщение с ``is_error=True`` без токенов.
        При успехе сохраняет полный ответ, structured_content, reasoning
        и учёт токенов через ``save_token_usage``.

        Args:
            llm_result: Словарь результата от DeepSeek-клиента с ключами
                (model, raw_text, content, reasoning, latency_ms,
                prompt_tokens, completion_tokens, reasoning_tokens,
                total_tokens, error — опционально).
            conversation: Экземпляр AIConversation, к которому привязать сообщение.
            parent_msg: Родительское AIMessage или None.
            prompt: Текст промпта, отправленного в LLM.
            intent: Имя интента/схемы (используется как schema_name).
        """
        if "error" in llm_result:
            AIMessage.objects.create(
                conversation=conversation, parent=parent_msg, role="orchestrator",
                content="", is_error=True, error_message=llm_result["error"],
            )
            return
        parsed = llm_result.get("content", {})
        if not isinstance(parsed, dict):
            parsed = {}
        msg = AIMessage.objects.create(
            conversation=conversation, parent=parent_msg, role="orchestrator",
            content=llm_result.get("raw_text", ""), structured_content=parsed,
            schema_name=intent, prompt_used=prompt, reasoning=llm_result.get("reasoning"),
            latency_ms=llm_result.get("latency_ms"),
        )
        save_token_usage(msg, {
            "model": llm_result["model"],
            "prompt_tokens": llm_result["prompt_tokens"],
            "completion_tokens": llm_result["completion_tokens"],
            "reasoning_tokens": llm_result.get("reasoning_tokens") or 0,
            "total_tokens": llm_result["total_tokens"],
            "cost_estimate": estimate_cost(llm_result["model"], llm_result["prompt_tokens"], llm_result["completion_tokens"]),
        })
