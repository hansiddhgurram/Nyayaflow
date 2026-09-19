"""Agent 6: Settlement Drafting Agent."""
from typing import Dict, Any, List, Optional
from services.llm_service import LLMService
from prompts.mediation_prompts import SETTLEMENT_DRAFT_SYSTEM, SETTLEMENT_DRAFT_PROMPT
from prompts.settlement_prompts import PAYMENT_SCHEDULE_SYSTEM, PAYMENT_SCHEDULE_PROMPT


class SettlementDraftingAgent:
    """Drafts proposed Mediated Settlement Agreements."""

    def __init__(self):
        self.llm = LLMService()

    def draft(
        self,
        dispute_type: str,
        facts: str,
        common_ground: List[str],
        suggestions: List[str],
        terms_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate settlement draft and payment schedule."""
        terms_section = f"Additional Terms Specified: {terms_override}" if terms_override else ""

        prompt = SETTLEMENT_DRAFT_PROMPT.format(
            dispute_type=dispute_type,
            facts=facts[:4000],
            common_ground="\n".join([f"- {c}" for c in common_ground]),
            suggestions="\n".join([f"- {s}" for s in suggestions]),
            terms_override=terms_section,
        )

        try:
            draft_text = self.llm.generate_sync(prompt, system_prompt=SETTLEMENT_DRAFT_SYSTEM, temperature=0.2)

            # Extract payment schedule
            payment = self._extract_payment_schedule(draft_text)

            return {
                "draft_text": draft_text,
                "payment_schedule": payment,
            }
        except Exception as e:
            return {
                "draft_text": f"Error generating draft: {str(e)}. Please try again or contact support.",
                "payment_schedule": None,
            }

    def _extract_payment_schedule(self, draft_text: str) -> Optional[Dict[str, Any]]:
        """Extract payment schedule from draft."""
        prompt = PAYMENT_SCHEDULE_PROMPT.format(text=draft_text[:3000])
        try:
            response = self.llm.generate_sync(prompt, system_prompt=PAYMENT_SCHEDULE_SYSTEM, temperature=0.1)
            import json
            return json.loads(response)
        except Exception:
            return None
