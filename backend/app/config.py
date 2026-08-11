"""VeriMind AI - Configuration."""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "VeriMind AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_NAME: str = "verimind"
    
    HUGGINGFACE_API_KEY: str = ""
    LLM_PROVIDER: str = "huggingface"
    LLM_MODEL_LARGE: str = "Qwen/Qwen2.5-72B-Instruct"
    LLM_MODEL_SMALL: str = "Qwen/Qwen2.5-7B-Instruct"
    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"
    
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    CHROMA_COLLECTION: str = "verimind_docs"
    
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

def get_settings() -> Settings:
    return Settings()
