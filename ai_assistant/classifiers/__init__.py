"""
Classifier for request intents (selection, price, cert, etc.).
One prompt → classify → ClassificationResult → route to handler.
"""
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

INTENTS = [
    "selection",     # equipment or component selection
    "price_check",   # price request
    "cert_search",   # certificate/document search
    "replacement",   # find replacement/analog
    "specs",         # technical specs
    "catalog",       # catalog/literature request
    "general",       # everything else
    "rejected",      # not our topic
    "needs_info",    # missing required data
]

CLASSIFIER_PROMPT_TEMPLATE = """Classify the user request about industrial valves and actuators.

Intents:
- selection: equipment selection (actuator, solenoid, BKV, cable gland, fittings, filter-regulator). Includes requests phrased as "выставить счет", "КП", "предложение" when they describe equipment to be selected. Set subtype: "equipment" if standalone, "component" if for customer's valve.
- price_check: ask price for a SPECIFIC product (by article or model). NOT for "выставить счет на подбор" — that's selection.
- cert_search: certificate search, compliance documents, Ex-proof certificates
- replacement: find replacement or analog for an existing model
- specs: technical specs, dimensions, weight, materials
- catalog: request for catalog, technical documentation, brochure
- general: greetings, unrelated questions, context not understood
- rejected: topic clearly outside industrial valves/actuators
- needs_info: missing critical parameters (torque, voltage, etc.)

Return JSON:
{{
    "intent": "<one of intents>",
    "confidence": 0.0-1.0,
    "entities": {{}},
    "subtype": "equipment" | "component" | null
}}

User request:
{user_text}"""


@dataclass
class ClassificationResult:
    intent: str
    confidence: float
    subtype: Optional[str] = None  # "equipment" | "component"
    entities: Optional[dict] = None
    _usage: Optional[Dict[str, Any]] = field(default=None, repr=False)


class InstructorClassifier:
    def __init__(self, client):
        self.client = client

    def classify(self, text: str) -> "ClassificationResult":
        prompt = CLASSIFIER_PROMPT_TEMPLATE.format(user_text=text)
        result = self.client.classify(prompt)
        content = result.get("content", {})
        if isinstance(content, dict):
            return ClassificationResult(
                intent=content.get("intent", "general"),
                confidence=content.get("confidence", 0.0),
                subtype=content.get("subtype"),
                entities=content.get("entities", {}),
                _usage={
                    "model": result.get("model", "unknown"),
                    "prompt_tokens": result.get("prompt_tokens", 0),
                    "completion_tokens": result.get("completion_tokens", 0),
                    "reasoning_tokens": result.get("reasoning_tokens", 0),
                    "total_tokens": result.get("total_tokens", 0),
                },
            )
        return ClassificationResult(intent="general", confidence=0.0)
