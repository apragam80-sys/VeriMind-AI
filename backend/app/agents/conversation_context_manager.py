import json
from langchain_core.prompts import PromptTemplate
from app.llm.client import get_llm

def conversation_context_manager_node(state):
    """
    Manages the context window.
    Truncates history and identifies active topic using the LLM to save tokens and prevent confusion.
    """
    messages = state.get("messages", [])
    
    # We only care about the last 5 messages for context limit
    recent_messages = messages[-5:] if len(messages) > 5 else messages
    
    active_topic = "general"
    summary = ""
    
    if len(recent_messages) > 0:
        llm = get_llm(temperature=0.0)
        
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in recent_messages])
        
        prompt = PromptTemplate.from_template(
            """Analyze the following conversation history and extract the current active topic and a brief summary.
Return ONLY a valid JSON object with exactly two keys: "active_topic" (string) and "summary" (string).
Do not include markdown blocks, just the raw JSON.

Conversation:
{history}
"""
        )
        
        chain = prompt | llm
        try:
            result = chain.invoke({"history": history_text})
            # Clean up potential markdown formatting from the response
            result_text = result.content if hasattr(result, "content") else str(result)
            result_text = result_text.replace("```json", "").replace("```", "").strip()
            
            parsed = json.loads(result_text)
            active_topic = parsed.get("active_topic", "general")
            summary = parsed.get("summary", "")
        except Exception as e:
            print(f"Error parsing context manager LLM output: {e}")
            pass
    
    state["context_manager"] = {
        "recent_messages": len(recent_messages),
        "summary": summary,
        "active_topic": active_topic,
        "truncated_history": recent_messages
    }
    
    return state
