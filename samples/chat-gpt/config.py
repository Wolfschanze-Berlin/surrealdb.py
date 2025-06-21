import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application configuration settings."""
    
    # SurrealDB Settings
    SURREALDB_URL: str = os.getenv("SURREALDB_URL", "ws://localhost:8001/rpc")
    SURREALDB_NAMESPACE: str = os.getenv("SURREALDB_NAMESPACE", "chatgpt")
    SURREALDB_DATABASE: str = os.getenv("SURREALDB_DATABASE", "conversations")
    SURREALDB_USERNAME: str = os.getenv("SURREALDB_USERNAME", "root")
    SURREALDB_PASSWORD: str = os.getenv("SURREALDB_PASSWORD", "root")
    
    # OpenAI Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    # App Settings
    APP_NAME: str = os.getenv("APP_NAME", "ChatGPT FastAPI Integration")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Logging Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()