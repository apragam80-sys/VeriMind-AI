from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from app.config import get_settings

settings = get_settings()

def get_llm(temperature: float = 0.1, model_size: str = "small") -> ChatHuggingFace:
    """Returns a ChatHuggingFace LLM instance configured with our settings."""
    repo_id = settings.LLM_MODEL_SMALL if model_size == "small" else settings.LLM_MODEL_LARGE
    
    # We use HuggingFaceEndpoint directly since it handles the inference API
    endpoint = HuggingFaceEndpoint(
        repo_id=repo_id,
        huggingfacehub_api_token=settings.HUGGINGFACE_API_KEY,
        task="text-generation",
        temperature=temperature,
        max_new_tokens=1024,
        do_sample=True if temperature > 0 else False,
        return_full_text=False
    )
    
    # Wrap it in ChatHuggingFace to support ChatPromptTemplate and structured chat
    chat_model = ChatHuggingFace(llm=endpoint)
    
    return chat_model
