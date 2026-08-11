from langchain_core.prompts import PromptTemplate
from app.llm.client import get_llm

def generator_node(state):
    query = state.get("resolved_query", state.get("user_query", ""))
    plan = state.get("plan", {}).get("steps", [])
    limits = state.get("requirement_lock", {})
    
    plan_str = "\n".join([f"- {step}" for step in plan])
    limits_str = f"Allowed topics: {limits.get('allowed_topics')}\nForbidden topics: {limits.get('forbidden_topics')}"
    
    llm = get_llm(temperature=0.7, model_size="large")
    
    prompt = PromptTemplate.from_template(
        """You are VeriMind AI, an enterprise-grade assistant. 
Execute the following plan to answer the user's query. Ensure you strictly follow the topic boundaries.

Query: {query}

Plan to follow:
{plan}

Boundaries:
{limits}

Response:
"""
    )
    
    chain = prompt | llm
    
    try:
        result = chain.invoke({"query": query, "plan": plan_str, "limits": limits_str})
        result_text = result.content if hasattr(result, "content") else str(result)
        state["response"] = result_text.strip()
    except Exception as e:
        print(f"Error in complex generator LLM output: {e}")
        state["response"] = "I'm sorry, I encountered an error while processing this complex request."
        
    return state
