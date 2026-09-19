"""LangGraph ODR workflow orchestration."""
from typing import Dict, Any, TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

from agents.evidence_intake import EvidenceIntakeAgent
from agents.evidence_validation import EvidenceValidationAgent
from agents.dispute_classification import DisputeClassificationAgent
from agents.legal_research import LegalResearchAgent
from agents.mediation import MediationAgent
from agents.settlement_drafting import SettlementDraftingAgent
from agents.administrator import AdministratorAgent
from rag.retriever import LegalRetriever


class ODRState(TypedDict):
    """State schema for the ODR workflow."""
    case_id: int
    evidence_texts: list
    extracted_entities: Dict[str, Any]
    validation_result: Dict[str, Any]
    dispute_type: str
    legal_statutes: list
    legal_summary: str
    mediation_result: Dict[str, Any]
    settlement_draft: str
    payment_schedule: Dict[str, Any]
    admin_review: Dict[str, Any]
    status: str
    error: str | None


def create_odr_graph() -> StateGraph:
    """Create the LangGraph workflow for ODR."""

    def evidence_intake_node(state: ODRState) -> ODRState:
        agent = EvidenceIntakeAgent()
        all_entities = {"people": [], "organizations": [], "amounts": [], "dates": [], "identifiers": []}
        all_timeline = []

        for text in state.get("evidence_texts", []):
            result = agent.process(text) or {}
            entities = result.get("entities") or {}
            for key in all_entities:
                all_entities[key].extend(entities.get(key, []) or [])
            all_timeline.extend(result.get("timeline", []) or [])

        state["extracted_entities"] = all_entities
        state["status"] = "evidence_extracted"
        return state

    def validation_node(state: ODRState) -> ODRState:
        agent = EvidenceValidationAgent()
        if len(state["evidence_texts"]) > 1:
            result = agent.validate(state["evidence_texts"][-1], state["evidence_texts"][:-1])
        else:
            result = {"confidence_score": 0.5, "contradictions": [], "missing_evidence": ["counter-evidence"], "notes": "Awaiting more evidence"}
        state["validation_result"] = result
        state["status"] = "validated"
        return state

    def classification_node(state: ODRState) -> ODRState:
        agent = DisputeClassificationAgent()
        all_text = "\n".join(state["evidence_texts"])
        result = agent.classify(all_text)
        state["dispute_type"] = result.get("dispute_type", "other")
        state["status"] = "classified"
        return state

    def legal_research_node(state: ODRState) -> ODRState:
        retriever = LegalRetriever()
        all_text = "\n".join(state["evidence_texts"])
        statutes = retriever.retrieve(all_text, top_k=5)
        state["legal_statutes"] = statutes

        agent = LegalResearchAgent()
        summary = agent.summarize_relevance(state["dispute_type"], statutes)
        state["legal_summary"] = summary
        state["status"] = "legal_researched"
        return state

    def mediation_node(state: ODRState) -> ODRState:
        agent = MediationAgent()
        all_text = "\n".join(state["evidence_texts"])
        result = agent.mediate(all_text, "", state["dispute_type"])
        state["mediation_result"] = result
        state["status"] = "mediated"
        return state

    def settlement_node(state: ODRState) -> ODRState:
        agent = SettlementDraftingAgent()
        all_text = "\n".join(state["evidence_texts"])
        mediation = state["mediation_result"]
        result = agent.draft(
            dispute_type=state["dispute_type"],
            facts=all_text,
            common_ground=mediation.get("common_ground", []),
            suggestions=mediation.get("suggestions", []),
        )
        state["settlement_draft"] = result["draft_text"]
        state["payment_schedule"] = result.get("payment_schedule")
        state["status"] = "settlement_drafted"
        return state

    def admin_review_node(state: ODRState) -> ODRState:
        agent = AdministratorAgent()
        review = agent.review_settlement(state["settlement_draft"], "\n".join(state["evidence_texts"]))
        state["admin_review"] = review
        state["status"] = "admin_reviewed"
        return state

    # Build graph
    workflow = StateGraph(ODRState)

    workflow.add_node("evidence_intake", evidence_intake_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("classification", classification_node)
    workflow.add_node("legal_research", legal_research_node)
    workflow.add_node("mediation", mediation_node)
    workflow.add_node("settlement", settlement_node)
    workflow.add_node("admin_review", admin_review_node)

    workflow.set_entry_point("evidence_intake")
    workflow.add_edge("evidence_intake", "validation")
    workflow.add_edge("validation", "classification")
    workflow.add_edge("classification", "legal_research")
    workflow.add_edge("legal_research", "mediation")
    workflow.add_edge("mediation", "settlement")
    workflow.add_edge("settlement", "admin_review")
    workflow.add_edge("admin_review", END)

    return workflow.compile()
