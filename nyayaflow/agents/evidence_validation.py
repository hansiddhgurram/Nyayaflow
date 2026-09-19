"""Agent 2: Evidence Validation Agent."""
from typing import Dict, Any, List
from services.llm_service import LLMService
from prompts.evidence_prompts import EVIDENCE_VALIDATION_SYSTEM, EVIDENCE_VALIDATION_PROMPT


class EvidenceValidationAgent:
    """Validates evidence consistency and detects contradictions."""

    def __init__(self):
        self.llm = LLMService()

    def validate(self, new_evidence: str, existing_evidence: List[str]) -> Dict[str, Any]:
        """Validate new evidence against existing evidence."""
        new_evidence_str = (new_evidence or "").strip()
        existing_cleaned = [e for e in (existing_evidence or []) if e and e.strip()]
        existing_text = "\n---\n".join(existing_cleaned[:5])  # Limit to last 5 pieces

        if not new_evidence_str:
            return {
                "confidence_score": 0.0,
                "contradictions": [],
                "missing_evidence": ["readable evidence text"],
                "notes": "No readable text extracted from new evidence piece.",
            }

        if not existing_text:
            return {
                "confidence_score": 0.5,
                "contradictions": [],
                "missing_evidence": ["counter-evidence from other party"],
                "notes": "First evidence piece uploaded. Awaiting response from other party.",
            }

        prompt = EVIDENCE_VALIDATION_PROMPT.format(
            new_evidence=new_evidence_str[:4000],
            existing_evidence=existing_text[:4000],
        )

        try:
            response = self.llm.generate_sync(prompt, system_prompt=EVIDENCE_VALIDATION_SYSTEM, temperature=0.2)
            import json
            result = json.loads(response)
            return result
        except Exception:
            return {
                "confidence_score": 0.5,
                "contradictions": [],
                "missing_evidence": [],
                "notes": "Validation could not be completed automatically. Manual review recommended.",
            }
