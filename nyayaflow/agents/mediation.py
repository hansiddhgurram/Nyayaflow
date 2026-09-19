"""Agent 5: Mediation Agent."""
from typing import Dict, Any
from services.llm_service import LLMService
from prompts.mediation_prompts import MEDIATION_SYSTEM, MEDIATION_PROMPT


class MediationAgent:
    """Facilitates AI-assisted mediation by identifying common ground and suggestions."""

    def __init__(self):
        self.llm = LLMService()

    def mediate(self, evidence_text: str, chat_history: str, dispute_type: str) -> Dict[str, Any]:
        """Generate mediation suggestions."""
        prompt = MEDIATION_PROMPT.format(
            dispute_type=dispute_type,
            evidence_text=evidence_text[:5000],
            chat_history=chat_history[:3000],
        )

        try:
            response = self.llm.generate_sync(prompt, system_prompt=MEDIATION_SYSTEM, temperature=0.3)
            import json
            result = json.loads(response)
            return result
        except Exception:
            return {
                "party_a_position": "Could not be determined automatically.",
                "party_b_position": "Could not be determined automatically.",
                "common_ground": [],
                "suggestions": ["Consider direct negotiation", "Schedule a joint mediation session"],
                "risks_assessment": "Unable to assess risks automatically. Consider legal counsel.",
            }
