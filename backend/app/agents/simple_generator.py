from langchain_core.prompts import PromptTemplate
from app.llm.client import get_llm

def simple_generator_node(state):
    query_class = state.get("query_class", {})
    resolved_query = state.get("resolved_query", state.get("user_query", ""))
    
    if query_class.get("ambiguous"):
        state["response"] = query_class.get("clarification_question")
    else:
        llm = get_llm(temperature=0.7)
        
        prompt = PromptTemplate.from_template(
            """You are VeriMind AI, a helpful and precise assistant.
Answer the user's query clearly and concisely.

Query: {query}
"""
        )
        
        chain = prompt | llm
        try:
            result = chain.invoke({"query": resolved_query})
            result_text = result.content if hasattr(result, "content") else str(result)
            state["response"] = result_text.strip()
        except Exception as e:
            print(f"Error in simple generator LLM output: {e}")
            state["response"] = "I'm sorry, I encountered an error while generating a response."
        
    # Ensure complex state fields remain null
    state["confidence"] = None
    state["evidence_ledger"] = []
    state["requirement_lock"] = None
    
    return state
