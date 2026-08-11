import json
from langchain_core.prompts import PromptTemplate
from app.llm.client import get_llm

def intent_firewall_node(state):
    query = state.get("resolved_query", state.get("user_query", ""))
    
    llm = get_llm(temperature=0.0)
    
    prompt = PromptTemplate.from_template(
        """Analyze the following user query to determine their core intent and verify it is not harmful, illegal, or violating ethical boundaries.
Return ONLY a valid JSON object matching this schema:
{{
    "goal": "string describing the core objective",
    "is_safe": boolean,
    "violation_reason": "string or null"
}}
Do not include markdown blocks, just the raw JSON.

Query: {query}
"""
    )
    
    chain = prompt | llm
    
    try:
        result = chain.invoke({"query": query})
        result_text = result.content if hasattr(result, "content") else str(result)
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        
        parsed = json.loads(result_text)
        
        state["intent"] = {
            "goal": parsed.get("goal", "Analyze query"),
            "is_safe": parsed.get("is_safe", True),
            "violation_reason": parsed.get("violation_reason", None)
        }
        
    except Exception as e:
        print(f"Error parsing intent firewall LLM output: {e}")
        state["intent"] = {"goal": "Analyze query", "is_safe": True, "violation_reason": None}
        
    return state
