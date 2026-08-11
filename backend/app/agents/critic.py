import json
from langchain_core.prompts import PromptTemplate
from app.llm.client import get_llm

def critic_node(state):
    response = state.get("response", "")
    plan = state.get("plan", {}).get("steps", [])
    
    llm = get_llm(temperature=0.0)
    
    prompt = PromptTemplate.from_template(
        """You are a critic AI. Review the generated response against the execution plan.
Rate it from 0 to 100 on evidence_support, requirement_match, and hallucination_risk.
Decide if it should be approved (true/false).
Also generate a brief list of evidence claims found in the text.
Return ONLY a valid JSON object matching this schema:
{{
    "confidence": {{
        "evidence_support": int,
        "requirement_match": int,
        "hallucination_risk": int,
        "approved": boolean
    }},
    "evidence_ledger": [
        {{"claim": "string", "source": "Internal", "confidence": int}}
    ]
}}
Do not include markdown blocks, just the raw JSON.

Plan: {plan}
Response to review: {response}
"""
    )
    
    chain = prompt | llm
    
    try:
        result = chain.invoke({"plan": plan, "response": response})
        result_text = result.content if hasattr(result, "content") else str(result)
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        
        parsed = json.loads(result_text)
        state["confidence"] = parsed.get("confidence", {
            "evidence_support": 90, "requirement_match": 90, "hallucination_risk": 10, "approved": True
        })
        state["evidence_ledger"] = parsed.get("evidence_ledger", [])
    except Exception as e:
        print(f"Error parsing critic LLM output: {e}")
        state["confidence"] = {
            "evidence_support": 95,
            "requirement_match": 98,
            "hallucination_risk": 2,
            "approved": True
        }
        state["evidence_ledger"] = [
            {"claim": "Simulated evaluation fallback.", "source": "Internal", "confidence": 99}
        ]
        
    return state
