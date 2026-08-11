import json
from langchain_core.prompts import PromptTemplate
from app.llm.client import get_llm

def conversation_context_resolver_node(state):
    """
    Resolves the true meaning of the user query by merging it with the active topic.
    Handles follow-ups like 'biology' or 'explain that' by querying the LLM.
    """
    user_query = state.get("user_query", "")
    context_manager = state.get("context_manager", {})
    
    active_topic = context_manager.get("active_topic", "general")
    summary = context_manager.get("summary", "")
    
    resolved_query = user_query
    is_continuation = False
    
    llm = get_llm(temperature=0.0)
    
    prompt = PromptTemplate.from_template(
        """Given a conversation summary, active topic, and a new user query, determine if the new query is a continuation/follow-up. 
If it is a continuation (e.g. it lacks context on its own like "biology" or "explain that"), rewrite it into a standalone resolved query that includes the context. 
If it is completely new, just return the exact user query.
Return ONLY a valid JSON object with exactly two keys: "resolved_query" (string) and "is_continuation" (boolean).
Do not include markdown blocks, just the raw JSON.

Summary: {summary}
Active Topic: {active_topic}
New Query: {query}
"""
    )
    
    chain = prompt | llm
    try:
        result = chain.invoke({
            "summary": summary,
            "active_topic": active_topic,
            "query": user_query
        })
        
        result_text = result.content if hasattr(result, "content") else str(result)
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        
        parsed = json.loads(result_text)
        resolved_query = parsed.get("resolved_query", user_query)
        is_continuation = parsed.get("is_continuation", False)
    except Exception as e:
        print(f"Error parsing context resolver LLM output: {e}")
        pass

    state["resolved_query"] = resolved_query
    state["is_continuation"] = is_continuation
    
    return state
