import json
from langchain_core.prompts import PromptTemplate
from app.llm.client import get_llm

def query_classifier_node(state):
    # Use the resolved query instead of the raw user query
    query = state.get("resolved_query", state.get("user_query", "")).lower()
    is_continuation = state.get("is_continuation", False)
    
    # Continuation Check
    if is_continuation:
        state["query_class"] = {
            "type": "conversation_query",
            "complexity": "low",
            "requires": {"rag": False, "planner": False, "verification": False}
        }
        state["response_mode"] = "simple"
        return state
    
    llm = get_llm(temperature=0.0)
    
    prompt = PromptTemplate.from_template(
        """Classify the following user query.
Determine the type, complexity, and whether it requires RAG, planning, or verification.
Also, if the query is a single ambiguous word (like "tree", "apple", "bank") that could have multiple vastly different meanings depending on domain (e.g. biology vs computer science), mark it as ambiguous and provide a clarification question.
If it is a command to analyze a document, mark it as document_task. If it is a complex request (like create a platform), mark it as complex_task. Otherwise simple_query.

Return ONLY a valid JSON object matching this schema:
{{
    "type": "simple_query" | "complex_task" | "document_task",
    "complexity": "low" | "high",
    "ambiguous": true | false,
    "clarification_question": "string or null",
    "requires": {{"rag": boolean, "planner": boolean, "verification": boolean}}
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
        
        state["query_class"] = {
            "type": parsed.get("type", "simple_query"),
            "complexity": parsed.get("complexity", "low"),
            "ambiguous": parsed.get("ambiguous", False),
            "clarification_question": parsed.get("clarification_question", None),
            "requires": parsed.get("requires", {"rag": False, "planner": False, "verification": False}),
            "domain": "general",
            "risk_level": "low"
        }
        
        if state["query_class"]["type"] == "document_task":
            state["response_mode"] = "document"
        elif state["query_class"]["type"] == "complex_task":
            state["response_mode"] = "verified"
        else:
            state["response_mode"] = "simple"
            
    except Exception as e:
        print(f"Error parsing query classifier LLM output: {e}")
        # Fallback to simple
        state["query_class"] = {
            "type": "simple_query",
            "complexity": "low",
            "requires": {"rag": False, "planner": False, "verification": False}
        }
        state["response_mode"] = "simple"
        
    return state
