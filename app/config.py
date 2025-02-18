# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Script Manager"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["*", "http://localhost:5173", "https://zp1v56uxy8rdx5ypatb0ockcb9tr6a-oci3--5173--7f809d15.local-credentialless.webcontainer-api.io/"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]

    # Database Settings
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    # Azure Blob Storage Settings
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_CONTAINER_NAME: Optional[str] = None
    AZURE_ALLOWED_FILE_TYPES: List[str] = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB in bytes

    # Supabase Settings
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: str
    
    # JWT Settings
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Security Settings
    SECURITY_BCRYPT_ROUNDS: int = 12
    AUTH_TOKEN_LIFETIME_SECONDS: int = 3600
    
    # Cache Settings
    CACHE_TTL: int = 3600  # 1 hour in seconds
    
    # Rate Limiting
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour in seconds
    RATE_LIMIT_MAX_REQUESTS: int = 100  # Maximum requests per window
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_API_VERSION: str = "2024-09-12"
    AZURE_OPENAI_DEPLOYMENT_NAME: str
    AZURE_OPENAI_MAX_TOKENS: int = 65000
    AZURE_OPENAI_TEMPERATURE: float = 1

    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # Can be "development", "staging", "production"
    ENABLE_TEST_ENDPOINTS: bool = False  # Specific flag for test endpoints


    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Returns:
        Settings: Application settings instance
    """
    return Settings()

# Create a global settings instance
settings = get_settings()