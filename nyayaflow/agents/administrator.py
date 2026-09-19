"""Agent 7: Administrator Agent."""
from typing import Dict, Any, List
from services.llm_service import LLMService


class AdministratorAgent:
    """Assists admin review by flagging issues in AI outputs."""

    def __init__(self):
        self.llm = LLMService()

    def review_settlement(self, settlement_text: str, case_facts: str) -> Dict[str, Any]:
        """Review settlement draft for potential issues."""
        prompt = f"""Review the following proposed settlement agreement for a mediation case in India.
Flag any potential issues, unfair terms, missing standard clauses, or compliance gaps with Indian law.
Do NOT make binding legal determinations. Provide suggestions for admin review.

Case Facts:
{case_facts[:3000]}

Settlement Draft:
{settlement_text[:4000]}

Respond in this exact JSON format:
{{
  "flags": ["issue1", "issue2"],
  "missing_clauses": ["clause1"],
  "suggestions": ["suggestion1"],
  "risk_level": "low|medium|high",
  "notes": "Overall review notes"
}}
"""

        try:
            response = self.llm.generate_sync(prompt, temperature=0.2)
            import json
            return json.loads(response)
        except Exception:
            return {
                "flags": [],
                "missing_clauses": [],
                "suggestions": ["Manual review recommended"],
                "risk_level": "medium",
                "notes": "Automated review could not be completed.",
            }

    def review_evidence_completeness(self, evidence_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check if evidence is sufficient to proceed."""
        return {
            "sufficient": len(evidence_list) >= 2,
            "notes": "At least 2 evidence items recommended for meaningful mediation." if len(evidence_list) < 2 else "Evidence base appears adequate.",
            "recommendations": ["Request counter-evidence from other party"] if len(evidence_list) < 2 else [],
        }
