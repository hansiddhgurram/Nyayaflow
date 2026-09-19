"""Agent 1: Evidence Intake Agent."""
from typing import Dict, Any
from services.llm_service import LLMService
from prompts.evidence_prompts import EVIDENCE_INTAKE_SYSTEM, EVIDENCE_INTAKE_PROMPT


class EvidenceIntakeAgent:
    """Extracts entities and timeline from evidence text using LLM."""

    def __init__(self):
        self.llm = LLMService()

    def process(self, text: str) -> Dict[str, Any]:
        """Process evidence text and return structured extraction."""
        if not text or len(text.strip()) < 10:
            return {
                "entities": {"people": [], "organizations": [], "amounts": [], "dates": [], "identifiers": []},
                "timeline": [],
            }

        prompt = EVIDENCE_INTAKE_PROMPT.format(text=text[:8000])  # Limit context
        try:
            response = self.llm.generate_sync(prompt, system_prompt=EVIDENCE_INTAKE_SYSTEM, temperature=0.1)
            # Try to parse as JSON
            import json
            result = json.loads(response)
            return result
        except Exception:
            # Fallback: return empty structure
            return {
                "entities": {"people": [], "organizations": [], "amounts": [], "dates": [], "identifiers": []},
                "timeline": [],
            }
