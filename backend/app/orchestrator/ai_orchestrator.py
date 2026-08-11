"""VeriMind AI - Orchestrator Interface."""
from typing import Any, AsyncGenerator
import json
import asyncio
from app.orchestrator.graph import build_graph

class AIOrchestrator:
    def __init__(self):
        self.graph = build_graph()

    async def process_query(self, user_message: str, conversation_id: str, conversation_history: list) -> dict[str, Any]:
        """Process a query through the LangGraph synchronously (waiting for completion)."""
        state = {
            "messages": conversation_history + [{"role": "user", "content": user_message}],
            "user_query": user_message,
            "conversation_id": conversation_id,
            "intent": None,
            "plan": None,
            "requirement_lock": None,
            "context": [],
            "response": "",
            "confidence": None,
            "evidence_ledger": [],
        }
        
        # Run graph
        final_state = await self.graph.ainvoke(state)
        
        return {
            "response": final_state.get("response", ""),
            "response_mode": final_state.get("response_mode", "verified"),
            "confidence": final_state.get("confidence", {}),
            "evidence_ledger": final_state.get("evidence_ledger", []),
            "requirement_lock": final_state.get("requirement_lock"),
            "intent": final_state.get("intent"),
            "plan": final_state.get("plan"),
        }

    async def process_query_stream(self, user_message: str, conversation_id: str, conversation_history: list) -> AsyncGenerator[dict, None]:
        """Process a query and stream state updates as SSE events."""
        state = {
            "messages": conversation_history + [{"role": "user", "content": user_message}],
            "user_query": user_message,
            "conversation_id": conversation_id,
            "intent": None,
            "plan": None,
            "requirement_lock": None,
            "context": [],
            "response": "",
            "confidence": None,
            "evidence_ledger": [],
        }

        # Stream graph steps
        async for step in self.graph.astream(state):
            node_name = list(step.keys())[0]
            node_state = step[node_name]
            
            event = {
                "event": "node_complete",
                "data": {
                    "node": node_name,
                    "requirement_lock": node_state.get("requirement_lock"),
                    "confidence": node_state.get("confidence"),
                    "evidence_ledger": node_state.get("evidence_ledger"),
                }
            }
            yield event
            await asyncio.sleep(0.1)
            
        final_state = node_state
        yield {
            "event": "final_response",
            "data": {
                "response": final_state.get("response", ""),
                "response_mode": final_state.get("response_mode", "verified"),
                "confidence": final_state.get("confidence"),
                "evidence_ledger": final_state.get("evidence_ledger"),
            }
        }

def get_orchestrator() -> AIOrchestrator:
    return AIOrchestrator()
