"""Agent 3: Dispute Classification Agent."""
from typing import Dict, Any
from services.llm_service import LLMService
from prompts.legal_prompts import CLASSIFICATION_SYSTEM, CLASSIFICATION_PROMPT


class DisputeClassificationAgent:
    """Classifies dispute type based on evidence."""

    def __init__(self):
        self.llm = LLMService()

    def classify(self, evidence_text: str) -> Dict[str, Any]:
        """Classify dispute and return type with confidence."""
        prompt = CLASSIFICATION_PROMPT.format(text=evidence_text[:6000])

        try:
            response = self.llm.generate_sync(prompt, system_prompt=CLASSIFICATION_SYSTEM, temperature=0.1)
            import json
            result = json.loads(response)
            # Validate dispute type
            valid_types = {"consumer", "freelance", "msme", "rental", "service", "other"}
            if result.get("dispute_type") not in valid_types:
                result["dispute_type"] = "other"
            return result
        except Exception:
            return {
                "dispute_type": "other",
                "confidence": 0.0,
                "reasoning": "Classification failed. Defaulting to 'other'. Manual review required.",
            }
