"""VeriMind AI - LangGraph Orchestrator."""
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any

from app.agents.conversation_context_manager import conversation_context_manager_node
from app.agents.conversation_context_resolver import conversation_context_resolver_node
from app.agents.query_classifier import query_classifier_node
from app.agents.simple_generator import simple_generator_node
from app.agents.prompt_firewall import prompt_firewall_node
from app.agents.intent_firewall import intent_firewall_node
from app.agents.planner import planner_node
from app.agents.requirement_lock import requirement_lock_node
from app.agents.knowledge_boundary import knowledge_boundary_node
from app.agents.model_router import model_router_node
from app.agents.generator import generator_node
from app.agents.critic import critic_node
from app.agents.document_prompt_injection_detector import document_prompt_injection_detector_node

class AgentState(TypedDict):
    messages: List[Dict[str, str]]
    user_query: str
    conversation_id: str
    context_manager: Dict[str, Any]
    resolved_query: str
    is_continuation: bool
    query_class: Dict[str, Any]
    response_mode: str
    intent: Dict[str, Any]
    plan: Dict[str, Any]
    requirement_lock: Dict[str, Any]
    context: List[Any]
    response: str
    confidence: Dict[str, Any]
    evidence_ledger: List[Dict[str, Any]]

def route_query(state: AgentState):
    query_type = state.get("query_class", {}).get("type", "complex_task")
    if query_type in ["simple_query", "conversation_query"]:
        return "simple"
    elif query_type == "document_task":
        return "document"
    return "complex"

def build_graph():
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("conversation_context_manager", conversation_context_manager_node)
    workflow.add_node("conversation_context_resolver", conversation_context_resolver_node)
    workflow.add_node("query_classifier", query_classifier_node)
    workflow.add_node("simple_generator", simple_generator_node)
    workflow.add_node("prompt_firewall", prompt_firewall_node)
    workflow.add_node("intent_firewall", intent_firewall_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("requirement_lock", requirement_lock_node)
    workflow.add_node("knowledge_boundary", knowledge_boundary_node)
    workflow.add_node("model_router", model_router_node)
    workflow.add_node("generator", generator_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("document_prompt_injection_detector", document_prompt_injection_detector_node)
    
    # Document parser stub for LangGraph flow
    workflow.add_node("document_parser", lambda s: s)
    workflow.add_node("structure_analyzer", lambda s: s)
    workflow.add_node("rag_retrieval", lambda s: s)
    workflow.add_node("hallucination_validator", lambda s: s)
    workflow.add_node("evidence_ledger", lambda s: s)

    # Set Entry Point
    workflow.set_entry_point("conversation_context_manager")
    workflow.add_edge("conversation_context_manager", "conversation_context_resolver")
    workflow.add_edge("conversation_context_resolver", "query_classifier")

    # Routing
    workflow.add_conditional_edges(
        "query_classifier",
        route_query,
        {
            "simple": "simple_generator",
            "complex": "prompt_firewall",
            "document": "prompt_firewall",
        }
    )

    # Simple Route
    workflow.add_edge("simple_generator", END)

    # Complex Route (from prompt_firewall, how does it know if complex or doc?)
    # For simplicity, we add conditional logic here or route through prompt firewall again.
    # Let's route from prompt firewall based on query_type
    def route_after_firewall(state: AgentState):
        if state.get("query_class", {}).get("type") == "document_task":
            return "document"
        return "complex"

    workflow.add_conditional_edges(
        "prompt_firewall",
        route_after_firewall,
        {
            "complex": "intent_firewall",
            "document": "document_parser",
        }
    )

    # Complex Sub-Pipeline
    workflow.add_edge("intent_firewall", "planner")
    workflow.add_edge("planner", "requirement_lock")
    workflow.add_edge("requirement_lock", "knowledge_boundary")
    workflow.add_edge("knowledge_boundary", "model_router")
    workflow.add_edge("model_router", "generator")
    workflow.add_edge("generator", "critic")
    workflow.add_edge("critic", "hallucination_validator")
    workflow.add_edge("hallucination_validator", "evidence_ledger")
    workflow.add_edge("evidence_ledger", END)

    # Document Sub-Pipeline
    workflow.add_edge("document_parser", "document_prompt_injection_detector")
    workflow.add_edge("document_prompt_injection_detector", "structure_analyzer")
    workflow.add_edge("structure_analyzer", "knowledge_boundary") # Join back to boundary engine, wait, RAG is better
    # The user plan specifically has:
    # prompt_firewall -> document_parser -> document_prompt_injection_detector -> structure_analyzer
    # -> knowledge_boundary -> rag -> generator -> critic -> hallucination_validator -> evidence_ledger
    
    workflow.add_edge("structure_analyzer", "knowledge_boundary")
    # Actually wait, knowledge boundary -> context builder/RAG.
    # We will just route knowledge boundary to RAG if document_task.
    def route_after_boundary(state: AgentState):
        if state.get("query_class", {}).get("type") == "document_task":
            return "rag"
        return "model"
        
    workflow.add_conditional_edges(
        "knowledge_boundary",
        route_after_boundary,
        {
            "rag": "rag_retrieval",
            "model": "model_router"
        }
    )
    
    workflow.add_edge("rag_retrieval", "generator")

    return workflow.compile()
