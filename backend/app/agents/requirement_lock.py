import json
from langchain_core.prompts import PromptTemplate
from app.llm.client import get_llm

def requirement_lock_node(state):
    query = state.get("resolved_query", state.get("user_query", ""))
    
    llm = get_llm(temperature=0.0)
    
    prompt = PromptTemplate.from_template(
        """Analyze the user query and lock down the requirements and constraints. 
Identify exactly what topics are allowed, what topics must be forbidden to prevent scope creep, what technical assumptions are allowed, and what assumptions are forbidden.
Return ONLY a valid JSON object matching this schema:
{{
    "allowed_topics": ["string"],
    "forbidden_topics": ["string"],
    "assumptions_allowed": ["string"],
    "assumptions_forbidden": ["string"],
    "confidence": 0.0 to 1.0
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
        state["requirement_lock"] = {
            "allowed_topics": parsed.get("allowed_topics", []),
            "forbidden_topics": parsed.get("forbidden_topics", []),
            "assumptions_allowed": parsed.get("assumptions_allowed", []),
            "assumptions_forbidden": parsed.get("assumptions_forbidden", []),
            "confidence": parsed.get("confidence", 0.95)
        }
    except Exception as e:
        print(f"Error parsing requirement lock LLM output: {e}")
        state["requirement_lock"] = {
            "allowed_topics": ["General"],
            "forbidden_topics": ["Malicious"],
            "assumptions_allowed": ["Standard Context"],
            "assumptions_forbidden": ["External knowledge"],
            "confidence": 0.95
        }
        
    return state
