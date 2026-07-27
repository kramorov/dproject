"""
Р вЂњР В»Р В°Р Р†Р Р…РЎвЂ№Р в„– Р С•РЎР‚Р С”Р ВµРЎРѓРЎвЂљРЎР‚Р В°РЎвЂљР С•РЎР‚. Р вЂќР Р†РЎС“РЎвЂ¦РЎвЂћР В°Р В·Р Р…РЎвЂ№Р в„–: analyze РІвЂ вЂ™ execute.

Р В¤Р В°Р В·Р В° 1: POST /analyze/  РІвЂ вЂ™ decompose РІвЂ вЂ™ Р Р†Р В°Р В»Р С‘Р Т‘Р В°РЎвЂ Р С‘РЎРЏ РІвЂ вЂ™ РЎРѓРЎвЂљР В°РЎвЂљРЎС“РЎРѓ + Р С—Р В»Р В°Р Р… Р В·Р В°Р Т‘Р В°РЎвЂЎ
Р В¤Р В°Р В·Р В° 2: POST /execute/ РІвЂ вЂ™ TaskGraph.execute() РІвЂ вЂ™ progress_log + РЎР‚Р ВµР В·РЎС“Р В»РЎРЉРЎвЂљР В°РЎвЂљРЎвЂ№
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
    """Р вЂќР Р†РЎС“РЎвЂ¦РЎвЂћР В°Р В·Р Р…РЎвЂ№Р в„–: analyze РІвЂ вЂ™ execute."""

    def __init__(self, tenant: str = "default"):
        """Р ВР Р…Р С‘РЎвЂ Р С‘Р В°Р В»Р С‘Р В·Р С‘РЎР‚РЎС“Р ВµРЎвЂљ Р С•РЎР‚Р С”Р ВµРЎРѓРЎвЂљРЎР‚Р В°РЎвЂљР С•РЎР‚ РЎРѓ DeepSeek-Р С”Р В»Р С‘Р ВµР Р…РЎвЂљР С•Р С Р С‘ Р С”Р В»Р В°РЎРѓРЎРѓР С‘РЎвЂћР С‘Р С”Р В°РЎвЂљР С•РЎР‚Р С•Р С.

        Args:
            tenant: Р ВР Т‘Р ВµР Р…РЎвЂљР С‘РЎвЂћР С‘Р С”Р В°РЎвЂљР С•РЎР‚ РЎвЂљР ВµР Р…Р В°Р Р…РЎвЂљР В° Р Т‘Р В»РЎРЏ Р СРЎС“Р В»РЎРЉРЎвЂљР С‘РЎвЂљР ВµР Р…Р В°Р Р…РЎвЂљР Р…Р С•Р в„– Р С”Р С•Р Р…РЎвЂћР С‘Р С–РЎС“РЎР‚Р В°РЎвЂ Р С‘Р С‘
                (Р С—РЎР‚Р С•Р СР С—РЎвЂљРЎвЂ№, РЎРѓРЎвЂ¦Р ВµР СРЎвЂ№). Р СџР С• РЎС“Р СР С•Р В»РЎвЂЎР В°Р Р…Р С‘РЎР‹ "default".
        """
        self.client = get_deepseek_client()
        self.classifier = InstructorClassifier(self.client)
        self.tenant = tenant

    # РІвЂќР‚РІвЂќР‚ Р В¤Р В°Р В·Р В° 1: analyze РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚

    def analyze(self, text: str, session_key: str = "", customer_id: int = None) -> dict:
        """Р В¤Р В°Р В·Р В° 1: Р Т‘Р ВµР С”Р С•Р СР С—Р С•Р В·Р С‘РЎвЂ Р С‘РЎРЏ Р В·Р В°Р С—РЎР‚Р С•РЎРѓР В° Р С—Р С•Р В»РЎРЉР В·Р С•Р Р†Р В°РЎвЂљР ВµР В»РЎРЏ, Р Р†Р В°Р В»Р С‘Р Т‘Р В°РЎвЂ Р С‘РЎРЏ Р С‘ Р С—Р С•РЎРѓРЎвЂљРЎР‚Р С•Р ВµР Р…Р С‘Р Вµ Р С—Р В»Р В°Р Р…Р В° Р В·Р В°Р Т‘Р В°РЎвЂЎ.

        Р РЋР С•Р В·Р Т‘Р В°РЎвЂРЎвЂљ AIConversation, Р С•РЎвЂљР С—РЎР‚Р В°Р Р†Р В»РЎРЏР ВµРЎвЂљ decompose-Р С—РЎР‚Р С•Р СР С—РЎвЂљ Р Р† LLM,
        Р С—Р В°РЎР‚РЎРѓР С‘РЎвЂљ РЎвЂљР ВµР С”РЎРѓРЎвЂљР С•Р Р†РЎвЂ№Р в„– Р Р†РЎвЂ№Р Р†Р С•Р Т‘ Р С‘ Р Р†Р С•Р В·Р Р†РЎР‚Р В°РЎвЂ°Р В°Р ВµРЎвЂљ РЎРѓРЎвЂљРЎР‚РЎС“Р С”РЎвЂљРЎС“РЎР‚Р С‘РЎР‚Р С•Р Р†Р В°Р Р…Р Р…РЎвЂ№Р в„– Р С—Р В»Р В°Р Р….

        Args:
            text: Р СћР ВµР С”РЎРѓРЎвЂљ Р В·Р В°Р С—РЎР‚Р С•РЎРѓР В° Р С—Р С•Р В»РЎРЉР В·Р С•Р Р†Р В°РЎвЂљР ВµР В»РЎРЏ.
            session_key: Р С™Р В»РЎР‹РЎвЂЎ РЎРѓР ВµРЎРѓРЎРѓР С‘Р С‘ (Р Т‘Р В»РЎРЏ Р В°Р Р…Р С•Р Р…Р С‘Р СР Р…РЎвЂ№РЎвЂ¦ Р С—Р С•Р В»РЎРЉР В·Р С•Р Р†Р В°РЎвЂљР ВµР В»Р ВµР в„–).
            customer_id: ID Р С”Р В»Р С‘Р ВµР Р…РЎвЂљР В° Р Р† РЎРѓР С‘РЎРѓРЎвЂљР ВµР СР Вµ (Р С•Р С—РЎвЂ Р С‘Р С•Р Р…Р В°Р В»РЎРЉР Р…Р С•).

        Returns:
            dict РЎРѓ Р С”Р В»РЎР‹РЎвЂЎР В°Р СР С‘: conversation_id, status, analysis_text,
            global_requirements, tasks, missing_info, reject_reason.
        """
        conversation = AIConversation.objects.create(
            session_key=session_key, customer_id=customer_id, status=AIConversation.PROCESSING,
        )
        AIMessage.objects.create(conversation=conversation, role="user", content=text)

        system_prompt = get_system_prompt(self.tenant)

        # DB-first: Р В·Р В°Р С–РЎР‚РЎС“Р В¶Р В°Р ВµР С decompose-Р С—РЎР‚Р С•Р СР С—РЎвЂљ
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
        cost_estimate = estimate_cost(llm_result.get("model", ""), prompt_tokens, completion_tokens)

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
            "cost_estimate": round(cost_estimate, 6),
        }

    def _parse_decompose(self, raw: str) -> dict:
        """Р СџР В°РЎР‚РЎРѓР С‘РЎвЂљ РЎвЂљР ВµР С”РЎРѓРЎвЂљР С•Р Р†РЎвЂ№Р в„– Р Р†РЎвЂ№Р Р†Р С•Р Т‘ decompose-Р С—РЎР‚Р С•Р СР С—РЎвЂљР В° Р Р† РЎРѓРЎвЂљРЎР‚РЎС“Р С”РЎвЂљРЎС“РЎР‚Р С‘РЎР‚Р С•Р Р†Р В°Р Р…Р Р…РЎвЂ№Р в„– РЎРѓР В»Р С•Р Р†Р В°РЎР‚РЎРЉ.

        Р В Р В°Р В·Р В±Р С‘РЎР‚Р В°Р ВµРЎвЂљ РЎРѓР ВµР С”РЎвЂ Р С‘Р С‘: === Р РЋР СћР С’Р СћР Р€Р РЋ ===, === Р С’Р СњР С’Р вЂєР ВР вЂ” ===, === Р вЂ”Р С’Р вЂќР С’Р В§Р В ===,
        === Р Р€Р СћР С›Р В§Р СњР вЂўР СњР ВР Р‡ ===, === Р СџР В Р ВР В§Р ВР СњР С’ Р С›Р СћР С™Р С’Р вЂ”Р С’ ===.

        Args:
            raw: Р РЋРЎвЂ№РЎР‚Р С•Р в„– РЎвЂљР ВµР С”РЎРѓРЎвЂљР С•Р Р†РЎвЂ№Р в„– Р С•РЎвЂљР Р†Р ВµРЎвЂљ LLM.

        Returns:
            dict РЎРѓ Р С”Р В»РЎР‹РЎвЂЎР В°Р СР С‘: status, global_reqs, tasks, missing_info, reject_reason.
        """
        result = {"status": "needs_info", "global_reqs": {}, "tasks": [], "missing_info": None}

        current_section = None
        for line in raw.split("\n"):
            line = line.strip()
            if "=== Р РЋР СћР С’Р СћР Р€Р РЋ ===" in line:
                current_section = "status"
            elif "=== Р С’Р СњР С’Р вЂєР ВР вЂ” ===" in line or "=== Р вЂњР вЂєР С›Р вЂР С’Р вЂєР В¬Р СњР В«Р вЂў Р СћР В Р вЂўР вЂР С›Р вЂ™Р С’Р СњР ВР Р‡ ===" in line:
                current_section = "analysis"
            elif "=== Р вЂ”Р С’Р вЂќР С’Р В§Р В ===" in line:
                current_section = "tasks"
            elif "=== Р Р€Р СћР С›Р В§Р СњР вЂўР СњР ВР Р‡ ===" in line:
                current_section = "missing_info"
            elif "=== Р СџР В Р ВР В§Р ВР СњР С’ Р С›Р СћР С™Р С’Р вЂ”Р С’ ===" in line:
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
        """Р СџР В°РЎР‚РЎРѓР С‘РЎвЂљ Р С•Р Т‘Р Р…РЎС“ РЎРѓРЎвЂљРЎР‚Р С•Р С”РЎС“ Р В·Р В°Р Т‘Р В°РЎвЂЎР С‘ Р С‘Р В· decompose-Р Р†РЎвЂ№Р Р†Р С•Р Т‘Р В° LLM.

        Р СџР С•Р Т‘Р Т‘Р ВµРЎР‚Р В¶Р С‘Р Р†Р В°Р ВµРЎвЂљ Р Т‘Р Р†Р В° РЎвЂћР С•РЎР‚Р СР В°РЎвЂљР В°:
        - Р СџР С•Р В»Р Р…РЎвЂ№Р в„–: ``[id]: type | depends_on: [ids] | summary``
        - Р С™РЎР‚Р В°РЎвЂљР С”Р С‘Р в„–: ``[id]: type | summary`` (depends_on Р С—РЎС“РЎРѓРЎвЂљ)

        Args:
            line: Р РЋРЎвЂљРЎР‚Р С•Р С”Р В° Р С‘Р В· РЎРѓР ВµР С”РЎвЂ Р С‘Р С‘ === Р вЂ”Р С’Р вЂќР С’Р В§Р В ===.

        Returns:
            dict РЎРѓ Р С”Р В»РЎР‹РЎвЂЎР В°Р СР С‘ (id, type, depends_on, summary) Р С‘Р В»Р С‘ None,
            Р ВµРЎРѓР В»Р С‘ РЎРѓРЎвЂљРЎР‚Р С•Р С”Р В° Р Р…Р Вµ РЎРѓР С•Р С•РЎвЂљР Р†Р ВµРЎвЂљРЎРѓРЎвЂљР Р†РЎС“Р ВµРЎвЂљ РЎвЂћР С•РЎР‚Р СР В°РЎвЂљРЎС“.
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

    # РІвЂќР‚РІвЂќР‚ Р В¤Р В°Р В·Р В° 2: execute РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚

    def execute(self, tasks: list, global_reqs: dict = None) -> dict:
        """Р В¤Р В°Р В·Р В° 2: Р Р†РЎвЂ№Р С—Р С•Р В»Р Р…Р ВµР Р…Р С‘Р Вµ Р С–РЎР‚Р В°РЎвЂћР В° Р В·Р В°Р Т‘Р В°РЎвЂЎ РЎвЂЎР ВµРЎР‚Р ВµР В· TaskGraph.

        Р РЋРЎвЂљРЎР‚Р С•Р С‘РЎвЂљ Р С–РЎР‚Р В°РЎвЂћ Р В·Р В°Р Р†Р С‘РЎРѓР С‘Р СР С•РЎРѓРЎвЂљР ВµР в„– Р С‘Р В· РЎРѓР С—Р С‘РЎРѓР С”Р В° Р В·Р В°Р Т‘Р В°РЎвЂЎ, Р Р†РЎвЂ№Р С—Р С•Р В»Р Р…РЎРЏР ВµРЎвЂљ РЎвЂљР С•Р С—Р С•Р В»Р С•Р С–Р С‘РЎвЂЎР ВµРЎРѓР С”РЎС“РЎР‹
        РЎРѓР С•РЎР‚РЎвЂљР С‘РЎР‚Р С•Р Р†Р С”РЎС“ Р С‘ Р В·Р В°Р С—РЎС“РЎРѓР С”Р В°Р ВµРЎвЂљ Р В·Р В°Р Т‘Р В°РЎвЂЎР С‘ Р С—Р С• РЎС“РЎР‚Р С•Р Р†Р Р…РЎРЏР С.

        Args:
            tasks: Р РЋР С—Р С‘РЎРѓР С•Р С” РЎРѓР В»Р С•Р Р†Р В°РЎР‚Р ВµР в„– Р В·Р В°Р Т‘Р В°РЎвЂЎ (Р С‘Р В· РЎвЂћР В°Р В·РЎвЂ№ analyze).
            global_reqs: Р вЂњР В»Р С•Р В±Р В°Р В»РЎРЉР Р…РЎвЂ№Р Вµ РЎвЂљРЎР‚Р ВµР В±Р С•Р Р†Р В°Р Р…Р С‘РЎРЏ (РЎвЂљР ВµР СР С—Р ВµРЎР‚Р В°РЎвЂљРЎС“РЎР‚Р В°, Exd, IP Р С‘ Р Т‘РЎР‚.).

        Returns:
            dict РЎРѓ Р С”Р В»РЎР‹РЎвЂЎР В°Р СР С‘: progress_log (Р С—Р С•РЎв‚¬Р В°Р С–Р С•Р Р†РЎвЂ№Р в„– Р В»Р С•Р С–),
            results (РЎР‚Р ВµР В·РЎС“Р В»РЎРЉРЎвЂљР В°РЎвЂљРЎвЂ№ Р С”Р В°Р В¶Р Т‘Р С•Р в„– Р В·Р В°Р Т‘Р В°РЎвЂЎР С‘ Р С—Р С• task_id).
        """
        graph = TaskGraph(tasks, global_reqs)
        progress_log = graph.execute(self)
        return {
            "progress_log": progress_log,
            "results": graph.results,
        }

    # РІвЂќР‚РІвЂќР‚ Р СџР В°Р в„–Р С—Р В»Р В°Р в„–Р Р… Р Т‘Р В»РЎРЏ actuator (РЎРѓРЎС“РЎвЂ°Р ВµРЎРѓРЎвЂљР Р†РЎС“РЎР‹РЎвЂ°Р С‘Р в„– Р С”Р С•Р Т‘) РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚

    def _run_actuator_pipeline(self, task: dict, global_reqs: dict, previous_results: dict) -> dict:
        """Р СџР С•Р В»Р Р…РЎвЂ№Р в„– Р С—Р В°Р в„–Р С—Р В»Р В°Р в„–Р Р… Р С—Р С•Р Т‘Р В±Р С•РЎР‚Р В° Р С—Р Р…Р ВµР Р†Р СР С•Р С—РЎР‚Р С‘Р Р†Р С•Р Т‘Р В°: classify РІвЂ вЂ™ extract РІвЂ вЂ™ resolve РІвЂ вЂ™ execute.

        Р В­РЎвЂљР В°Р С—РЎвЂ№:
        1. Classify РІР‚вЂќ Р С•Р С—РЎР‚Р ВµР Т‘Р ВµР В»Р ВµР Р…Р С‘Р Вµ Р С‘Р Р…РЎвЂљР ВµР Р…РЎвЂљР В° РЎвЂЎР ВµРЎР‚Р ВµР В· InstructorClassifier.
        2. Extract РІР‚вЂќ Р С‘Р В·Р Р†Р В»Р ВµРЎвЂЎР ВµР Р…Р С‘Р Вµ РЎвЂћР С‘Р В»РЎРЉРЎвЂљРЎР‚Р С•Р Р† Р С‘Р В· РЎвЂљР ВµР С”РЎРѓРЎвЂљР В° РЎвЂЎР ВµРЎР‚Р ВµР В· LLM.
        3. Resolve РІР‚вЂќ РЎРѓР С•Р С—Р С•РЎРѓРЎвЂљР В°Р Р†Р В»Р ВµР Р…Р С‘Р Вµ РЎвЂћР С‘Р В»РЎРЉРЎвЂљРЎР‚Р С•Р Р† РЎРѓ ID Р С‘Р В· Р вЂР вЂќ.
        4. Execute РІР‚вЂќ Р Р†РЎвЂ№Р В·Р С•Р Р† ``process_selection_params`` Р Т‘Р В»РЎРЏ Р С—Р С•Р С‘РЎРѓР С”Р В° Р СР С•Р Т‘Р ВµР В»Р ВµР в„–.

        Args:
            task: Р РЋР В»Р С•Р Р†Р В°РЎР‚РЎРЉ Р В·Р В°Р Т‘Р В°РЎвЂЎР С‘ РЎРѓ Р С”Р В»РЎР‹РЎвЂЎР В°Р СР С‘ (type, params, depends_on, ...).
            global_reqs: Р вЂњР В»Р С•Р В±Р В°Р В»РЎРЉР Р…РЎвЂ№Р Вµ РЎвЂљРЎР‚Р ВµР В±Р С•Р Р†Р В°Р Р…Р С‘РЎРЏ, Р С—РЎР‚Р С‘Р СР ВµР Р…РЎРЏР ВµР СРЎвЂ№Р Вµ Р С” params Р С—Р С• РЎС“Р СР С•Р В»РЎвЂЎР В°Р Р…Р С‘РЎР‹.
            previous_results: Р В Р ВµР В·РЎС“Р В»РЎРЉРЎвЂљР В°РЎвЂљРЎвЂ№ РЎР‚Р В°Р Р…Р ВµР Вµ Р Р†РЎвЂ№Р С—Р С•Р В»Р Р…Р ВµР Р…Р Р…РЎвЂ№РЎвЂ¦ Р В·Р В°Р Р†Р С‘РЎРѓР С‘Р СРЎвЂ№РЎвЂ¦ Р В·Р В°Р Т‘Р В°РЎвЂЎ.

        Returns:
            dict РЎРѓ Р С”Р В»РЎР‹РЎвЂЎР В°Р СР С‘: status, message, raw_filters, resolved_ids,
            search_results.
        """
        params = task.get("params", {})
        # Р СџРЎР‚Р С‘Р СР ВµР Р…РЎРЏР ВµР С Р С–Р В»Р С•Р В±Р В°Р В»РЎРЉР Р…РЎвЂ№Р Вµ РЎвЂљРЎР‚Р ВµР В±Р С•Р Р†Р В°Р Р…Р С‘РЎРЏ
        for key, val in (global_reqs or {}).items():
            params.setdefault(key, val)

        # Classify
        result = self.classifier.classify(params.get("_text", ""))
        intent = result.intent

        schema_config = get_schema_config(intent)
        if not schema_config:
            return {"status": "skipped", "message": f"Р СњР ВµРЎвЂљ РЎРѓРЎвЂ¦Р ВµР СРЎвЂ№ Р Т‘Р В»РЎРЏ '{intent}'"}

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
            "message": f"Р СњР В°Р в„–Р Т‘Р ВµР Р…Р С• {total} Р СР С•Р Т‘Р ВµР В»Р ВµР в„–" if total else "Р СњР С‘РЎвЂЎР ВµР С–Р С• Р Р…Р Вµ Р Р…Р В°Р в„–Р Т‘Р ВµР Р…Р С•",
            "raw_filters": raw_filters,
            "resolved_ids": resolved,
            "search_results": search_results,
        }

    # РІвЂќР‚РІвЂќР‚ Р вЂ™РЎРѓР С—Р С•Р СР С•Р С–Р В°РЎвЂљР ВµР В»РЎРЉР Р…РЎвЂ№Р Вµ РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚РІвЂќР‚

    def _get_db_context(self, raw_filters):
        """Р РЋР С•Р В±Р С‘РЎР‚Р В°Р ВµРЎвЂљ Р С”Р С•Р Р…РЎвЂљР ВµР С”РЎРѓРЎвЂљ Р С‘Р В· Р вЂР вЂќ Р Т‘Р В»РЎРЏ РЎвЂћР В°Р В·РЎвЂ№ resolve: РЎРѓР С—Р С‘РЎРѓР С”Р С‘ Р С•Р С—РЎвЂ Р С‘Р в„– Р С‘ РЎРѓР С—РЎР‚Р В°Р Р†Р С•РЎвЂЎР Р…Р С‘Р С”Р С•Р Р†.

        Р вЂ”Р В°Р С–РЎР‚РЎС“Р В¶Р В°Р ВµРЎвЂљ Р В°Р С”РЎвЂљР С‘Р Р†Р Р…РЎвЂ№Р Вµ Р В·Р В°Р С—Р С‘РЎРѓР С‘ Р С‘Р В· Р СР С•Р Т‘Р ВµР В»Р ВµР в„–:
        PneumaticIpOption, PneumaticExdOption, PneumaticBodyCoatingOption,
        PneumaticHandWheelOption, ValveTypes, DnVariety, PnVariety,
        PneumaticActuatorVariety.

        Args:
            raw_filters: Р РЋРЎвЂ№РЎР‚РЎвЂ№Р Вµ РЎвЂћР С‘Р В»РЎРЉРЎвЂљРЎР‚РЎвЂ№, Р С‘Р В·Р Р†Р В»Р ВµРЎвЂЎРЎвЂР Р…Р Р…РЎвЂ№Р Вµ Р С‘Р В· Р В·Р В°Р С—РЎР‚Р С•РЎРѓР В° (Р Р…Р Вµ Р С‘РЎРѓР С—Р С•Р В»РЎРЉР В·РЎС“РЎР‹РЎвЂљРЎРѓРЎРЏ
                Р Р…Р В°Р С—РЎР‚РЎРЏР СРЎС“РЎР‹, Р В·Р В°РЎР‚Р ВµР В·Р ВµРЎР‚Р Р†Р С‘РЎР‚Р С•Р Р†Р В°Р Р…РЎвЂ№ Р Т‘Р В»РЎРЏ Р В±РЎС“Р Т‘РЎС“РЎвЂ°Р ВµР в„– РЎвЂћР С‘Р В»РЎРЉРЎвЂљРЎР‚Р В°РЎвЂ Р С‘Р С‘ Р С”Р С•Р Р…РЎвЂљР ВµР С”РЎРѓРЎвЂљР В°).

        Returns:
            dict РЎРѓ Р С”Р В»РЎР‹РЎвЂЎР В°Р СР С‘-Р С”Р В°РЎвЂљР ВµР С–Р С•РЎР‚Р С‘РЎРЏР СР С‘, Р В·Р Р…Р В°РЎвЂЎР ВµР Р…Р С‘РЎРЏ РІР‚вЂќ РЎРѓР С—Р С‘РЎРѓР С”Р С‘ dict РЎРѓ id Р С‘ name.
            Р вЂ™ РЎРѓР В»РЎС“РЎвЂЎР В°Р Вµ Р С•РЎв‚¬Р С‘Р В±Р С•Р С” Р С‘Р СР С—Р С•РЎР‚РЎвЂљР В° Р Р†Р С•Р В·Р Р†РЎР‚Р В°РЎвЂ°Р В°Р ВµРЎвЂљ Р С—РЎС“РЎРѓРЎвЂљР С•Р в„– РЎРѓР В»Р С•Р Р†Р В°РЎР‚РЎРЉ.
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
        """Р В¤Р С•РЎР‚Р СР С‘РЎР‚РЎС“Р ВµРЎвЂљ resolve-Р С—РЎР‚Р С•Р СР С—РЎвЂљ Р Т‘Р В»РЎРЏ РЎРѓР С•Р С—Р С•РЎРѓРЎвЂљР В°Р Р†Р В»Р ВµР Р…Р С‘РЎРЏ РЎвЂћР С‘Р В»РЎРЉРЎвЂљРЎР‚Р С•Р Р† РЎРѓ ID Р С‘Р В· Р вЂР вЂќ.

        Р С›РЎвЂљР С—РЎР‚Р В°Р Р†Р В»РЎРЏР ВµРЎвЂљ LLM Р С—Р В°РЎР‚РЎС“ Р’В«Р С—Р В°РЎР‚Р В°Р СР ВµРЎвЂљРЎР‚РЎвЂ№ РІвЂ вЂ™ Р С•Р С—РЎвЂ Р С‘Р С‘ Р вЂР вЂќР’В» Р С‘ Р С—РЎР‚Р С•РЎРѓР С‘РЎвЂљ Р Р†Р ВµРЎР‚Р Р…РЎС“РЎвЂљРЎРЉ JSON
        РЎРѓ Р С—Р С•Р В»РЎРЏР СР С‘ ``_id`` (Р Р…Р В°Р С—РЎР‚Р С‘Р СР ВµРЎР‚, ``valve_type_id``, ``dn_id``).

        Args:
            raw_filters: Р РЋР В»Р С•Р Р†Р В°РЎР‚РЎРЉ Р С—Р В°РЎР‚Р В°Р СР ВµРЎвЂљРЎР‚Р С•Р Р†, Р С‘Р В·Р Р†Р В»Р ВµРЎвЂЎРЎвЂР Р…Р Р…РЎвЂ№РЎвЂ¦ Р Р…Р В° РЎвЂћР В°Р В·Р Вµ extract.
            db_context: Р РЋР В»Р С•Р Р†Р В°РЎР‚РЎРЉ Р С”Р С•Р Р…РЎвЂљР ВµР С”РЎРѓРЎвЂљР В° Р С‘Р В· ``_get_db_context``.

        Returns:
            str РІР‚вЂќ РЎвЂљР ВµР С”РЎРѓРЎвЂљР С•Р Р†РЎвЂ№Р в„– Р С—РЎР‚Р С•Р СР С—РЎвЂљ Р Т‘Р В»РЎРЏ LLM.
        """
        return f"""Р вЂќР В°Р Р…РЎвЂ№ Р С—Р В°РЎР‚Р В°Р СР ВµРЎвЂљРЎР‚РЎвЂ№ (Р Р†Р С•Р В·Р СР С•Р В¶Р Р…Р С•, Р Р…Р В° РЎР‚РЎС“РЎРѓРЎРѓР С”Р С•Р С) Р С‘ РЎРѓР С—Р С‘РЎРѓР С•Р С” Р С•Р С—РЎвЂ Р С‘Р в„– Р С‘Р В· Р В±Р В°Р В·РЎвЂ№.
Р СњР В°Р в„–Р Т‘Р С‘ РЎРѓР С•Р С•РЎвЂљР Р†Р ВµРЎвЂљРЎРѓРЎвЂљР Р†Р С‘Р Вµ Р С—Р С• РЎРѓР СРЎвЂ№РЎРѓР В»РЎС“.
Р СџР В°РЎР‚Р В°Р СР ВµРЎвЂљРЎР‚РЎвЂ№: {json.dumps(raw_filters, ensure_ascii=False)}
Р С›Р С—РЎвЂ Р С‘Р С‘ Р С‘Р В· Р вЂР вЂќ: {json.dumps(db_context, ensure_ascii=False)}
Р вЂ™Р ВµРЎР‚Р Р…Р С‘ Р СћР С›Р вЂєР В¬Р С™Р С› JSON РЎРѓ Р С—Р С•Р В»РЎРЏР СР С‘ _id (valve_type_id, dn_id, ...). Р СњР Вµ Р Р…Р В°Р в„–Р Т‘Р ВµР Р…Р С• РІР‚вЂќ null."""

    def _save_llm(self, llm_result, conversation, parent_msg, prompt, intent):
        """Р РЋР С•РЎвЂ¦РЎР‚Р В°Р Р…РЎРЏР ВµРЎвЂљ РЎР‚Р ВµР В·РЎС“Р В»РЎРЉРЎвЂљР В°РЎвЂљ LLM-Р Р†РЎвЂ№Р В·Р С•Р Р†Р В° Р Р† AIMessage Р С‘ AITokenUsage.

        Р СџРЎР‚Р С‘ Р С•РЎв‚¬Р С‘Р В±Р С”Р Вµ РЎРѓР С•Р В·Р Т‘Р В°РЎвЂРЎвЂљ РЎРѓР С•Р С•Р В±РЎвЂ°Р ВµР Р…Р С‘Р Вµ РЎРѓ ``is_error=True`` Р В±Р ВµР В· РЎвЂљР С•Р С”Р ВµР Р…Р С•Р Р†.
        Р СџРЎР‚Р С‘ РЎС“РЎРѓР С—Р ВµРЎвЂ¦Р Вµ РЎРѓР С•РЎвЂ¦РЎР‚Р В°Р Р…РЎРЏР ВµРЎвЂљ Р С—Р С•Р В»Р Р…РЎвЂ№Р в„– Р С•РЎвЂљР Р†Р ВµРЎвЂљ, structured_content, reasoning
        Р С‘ РЎС“РЎвЂЎРЎвЂРЎвЂљ РЎвЂљР С•Р С”Р ВµР Р…Р С•Р Р† РЎвЂЎР ВµРЎР‚Р ВµР В· ``save_token_usage``.

        Args:
            llm_result: Р РЋР В»Р С•Р Р†Р В°РЎР‚РЎРЉ РЎР‚Р ВµР В·РЎС“Р В»РЎРЉРЎвЂљР В°РЎвЂљР В° Р С•РЎвЂљ DeepSeek-Р С”Р В»Р С‘Р ВµР Р…РЎвЂљР В° РЎРѓ Р С”Р В»РЎР‹РЎвЂЎР В°Р СР С‘
                (model, raw_text, content, reasoning, latency_ms,
                prompt_tokens, completion_tokens, reasoning_tokens,
                total_tokens, error РІР‚вЂќ Р С•Р С—РЎвЂ Р С‘Р С•Р Р…Р В°Р В»РЎРЉР Р…Р С•).
            conversation: Р В­Р С”Р В·Р ВµР СР С—Р В»РЎРЏРЎР‚ AIConversation, Р С” Р С”Р С•РЎвЂљР С•РЎР‚Р С•Р СРЎС“ Р С—РЎР‚Р С‘Р Р†РЎРЏР В·Р В°РЎвЂљРЎРЉ РЎРѓР С•Р С•Р В±РЎвЂ°Р ВµР Р…Р С‘Р Вµ.
            parent_msg: Р В Р С•Р Т‘Р С‘РЎвЂљР ВµР В»РЎРЉРЎРѓР С”Р С•Р Вµ AIMessage Р С‘Р В»Р С‘ None.
            prompt: Р СћР ВµР С”РЎРѓРЎвЂљ Р С—РЎР‚Р С•Р СР С—РЎвЂљР В°, Р С•РЎвЂљР С—РЎР‚Р В°Р Р†Р В»Р ВµР Р…Р Р…Р С•Р С–Р С• Р Р† LLM.
            intent: Р ВР СРЎРЏ Р С‘Р Р…РЎвЂљР ВµР Р…РЎвЂљР В°/РЎРѓРЎвЂ¦Р ВµР СРЎвЂ№ (Р С‘РЎРѓР С—Р С•Р В»РЎРЉР В·РЎС“Р ВµРЎвЂљРЎРѓРЎРЏ Р С”Р В°Р С” schema_name).
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


