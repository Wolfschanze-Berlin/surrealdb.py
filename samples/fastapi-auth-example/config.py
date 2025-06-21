import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application configuration settings."""
    
    # SurrealDB Settings
    SURREALDB_URL: str = os.getenv("SURREALDB_URL", "ws://localhost:8001/rpc")
    SURREALDB_NAMESPACE: str = os.getenv("SURREALDB_NAMESPACE", "test")
    SURREALDB_DATABASE: str = os.getenv("SURREALDB_DATABASE", "test")
    SURREALDB_USERNAME: str = os.getenv("SURREALDB_USERNAME", "root")
    SURREALDB_PASSWORD: str = os.getenv("SURREALDB_PASSWORD", "root")
    
    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # App Settings
    APP_NAME: str = os.getenv("APP_NAME", "FastAPI SurrealDB Auth Example")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Admin Settings
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    
    # Logging Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()