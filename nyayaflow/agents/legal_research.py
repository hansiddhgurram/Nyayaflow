"""Agent 4: Legal Research Agent."""
from typing import Dict, Any, List
from services.llm_service import LLMService
from prompts.legal_prompts import LEGAL_RESEARCH_SYSTEM, LEGAL_RESEARCH_PROMPT


class LegalResearchAgent:
    """Summarizes relevance of retrieved legal statutes."""

    def __init__(self):
        self.llm = LLMService()

    def summarize_relevance(self, dispute_type: str, statutes: List[Dict[str, Any]]) -> str:
        """Summarize how statutes apply to the dispute."""
        statutes_text = "\n\n".join([
            f"Act: {s.get('act_name', 'Unknown')}\nSection: {s.get('section', 'N/A')}\nContent: {s.get('content', '')[:500]}"
            for s in statutes
        ])

        prompt = LEGAL_RESEARCH_PROMPT.format(dispute_type=dispute_type, statutes=statutes_text)

        try:
            response = self.llm.generate_sync(prompt, system_prompt=LEGAL_RESEARCH_SYSTEM, temperature=0.2)
            return response
        except Exception:
            return "Legal research summary could not be generated. Please review retrieved statutes manually."
