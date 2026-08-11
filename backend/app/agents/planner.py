import json
from langchain_core.prompts import PromptTemplate
from app.llm.client import get_llm

def planner_node(state):
    query = state.get("resolved_query", state.get("user_query", ""))
    
    llm = get_llm(temperature=0.2)
    
    prompt = PromptTemplate.from_template(
        """You are a master task planner. Break down the following complex user request into a step-by-step execution plan.
Return ONLY a valid JSON object matching this schema:
{{
    "steps": ["Step 1 description", "Step 2 description", ...]
}}
Do not include markdown blocks, just the raw JSON.

Request: {query}
"""
    )
    
    chain = prompt | llm
    
    try:
        result = chain.invoke({"query": query})
        result_text = result.content if hasattr(result, "content") else str(result)
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        
        parsed = json.loads(result_text)
        state["plan"] = {"steps": parsed.get("steps", ["Analyze request"])}
    except Exception as e:
        print(f"Error parsing planner LLM output: {e}")
        state["plan"] = {"steps": ["Analyze request", "Generate response", "Verify constraints"]}
        
    return state
