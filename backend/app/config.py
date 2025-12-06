"""Configuration management for the Medical Chatbot Backend"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_PORT: int = 8000
    API_HOST: str = "0.0.0.0"
    
    # Azure OpenAI - GPT Model (matches test/env.example)
    OPENAI_GPT_ENDPOINT: str
    OPENAI_GPT_API_KEY: str
    OPENAI_GPT_API_VERSION: str = "2024-12-01-preview"
    OPENAI_GPT4_DEPLOYMENT: str
    
    # Azure OpenAI - Embedding Model
    OPENAI_EMBEDDING_ENDPOINT: str
    OPENAI_EMBEDDING_API_KEY: str
    OPENAI_EMBEDDING_API_VERSION: str = "2024-08-01-preview"
    OPENAI_EMBEDDING_DEPLOYMENT: str
    
    # Azure Blob Storage
    STORAGE_ACCOUNT_NAME: str
    STORAGE_ACCOUNT_KEY: str
    STORAGE_CONNECTION_STRING: str
    
    # Blob Container Names (6 total)
    # Existing containers (for raw files)
    BLOB_CONTAINER_PRESCRIPTIONS_UPLOADS: str = "prescription-uploads"
    BLOB_CONTAINER_EXTRACTED_DATA: str = "extracted-data"
    BLOB_CONTAINER_MEDICAL_IMAGES: str = "medical-images"
    # New containers (for vector embeddings)
    BLOB_CONTAINER_PRESCRIPTIONS_VECTORS: str = "prescription-vectors"
    BLOB_CONTAINER_MEDICAL_KNOWLEDGE: str = "medical-knowledge"
    BLOB_CONTAINER_DRUG_DATABASE: str = "drug-database"
    
    # Azure SQL Databases (matches test/env.example)
    SQL_SERVER_1: str
    SQL_DATABASE_1: str  # medicalchatbot-users
    SQL_USERNAME_1: str
    SQL_PASSWORD_1: str
    SQL_CONNECTION_STRING_1: str
    
    SQL_SERVER_2: str
    SQL_DATABASE_2: str  # medicalchatbot-drugs
    SQL_USERNAME_2: str
    SQL_PASSWORD_2: str
    SQL_CONNECTION_STRING_2: str
    
    # Third database (analytics) - optional
    SQL_SERVER_3: Optional[str] = None
    SQL_DATABASE_3: Optional[str] = None
    SQL_USERNAME_3: Optional[str] = None
    SQL_PASSWORD_3: Optional[str] = None
    SQL_CONNECTION_STRING_3: Optional[str] = None
    
    # Azure Cosmos DB (matches test/env.example)
    COSMOS_ACCOUNT: Optional[str] = None
    COSMOS_ENDPOINT: str
    COSMOS_KEY: str
    COSMOS_DATABASE: str = "medical-chatbot-cosmos"
    COSMOS_CONTAINER_CONVERSATIONS: str = "conversations"
    COSMOS_CONTAINER_MESSAGES: str = "messages"
    
    # Azure Redis Cache (matches test/env.example)
    REDIS_CONNECTION_STRING: str
    
    # Azure Document Intelligence
    DOCUMENT_INTELLIGENCE_ENDPOINT: str
    DOCUMENT_INTELLIGENCE_KEY: str
    DOCUMENT_INTELLIGENCE_MODEL_ID: str = "prebuilt-read"
    
    # Azure Key Vault (Optional)
    KEY_VAULT_NAME: Optional[str] = None
    KEY_VAULT_URL: Optional[str] = None
    
    # Security
    JWT_SECRET_KEY: str = "change-this-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    
    # CORS (comma-separated string in .env, converted to list)
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080"
    
    @property
    def cors_origins_list(self) -> list:
        """Get CORS origins as a list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Caching TTL (in seconds)
    CACHE_TTL_DRUG_INFO: int = 604800  # 7 days
    CACHE_TTL_CHAT_RESPONSE: int = 3600  # 1 hour
    CACHE_TTL_USER_SESSION: int = 3600  # 1 hour
    CACHE_TTL_RAG_RESULTS: int = 21600  # 6 hours
    
    # Vector Search Settings
    EMBEDDING_DIMENSION: int = 1536
    VECTOR_SEARCH_TOP_K: int = 5
    CHUNK_SIZE: int = 500  # words per chunk
    CHUNK_OVERLAP: int = 50  # word overlap between chunks
    
    # Agent Settings
    ORCHESTRATOR_TEMPERATURE: float = 0.3
    MEDICAL_QA_TEMPERATURE: float = 0.5
    DRUG_AGENT_TEMPERATURE: float = 0.2
    DOCTOR_AGENT_TEMPERATURE: float = 0.4
    MAX_TOKENS_RESPONSE: int = 1024
    
    # Document Processing
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_EXTENSIONS: str = "jpg,jpeg,png,pdf"
    OCR_CONFIDENCE_THRESHOLD: float = 0.75
    
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @property
    def sql_connection_string_users(self) -> str:
        """Get SQL connection string for users database"""
        return self.SQL_CONNECTION_STRING_1
    
    @property
    def sql_connection_string_drugs(self) -> str:
        """Get SQL connection string for drugs database"""
        return self.SQL_CONNECTION_STRING_2
    
    @property
    def redis_host(self) -> str:
        """Extract Redis host from connection string"""
        # Parse REDIS_CONNECTION_STRING to get host
        # Format: host:port,password=pwd,ssl=True
        parts = self.REDIS_CONNECTION_STRING.split(',')[0]
        return parts.split(':')[0]
    
    @property
    def redis_port(self) -> int:
        """Extract Redis port from connection string"""
        parts = self.REDIS_CONNECTION_STRING.split(',')[0]
        return int(parts.split(':')[1]) if ':' in parts else 6380
    
    @property
    def redis_password(self) -> str:
        """Extract Redis password from connection string"""
        for part in self.REDIS_CONNECTION_STRING.split(','):
            if 'password=' in part.lower():
                return part.split('=', 1)[1]
        return ""
    
    @property
    def allowed_extensions_list(self) -> list:
        """Get list of allowed file extensions"""
        return [ext.strip() for ext in self.ALLOWED_FILE_EXTENSIONS.split(",")]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes"""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    def validate_required_settings(self) -> None:
        """Validate that all required settings are present"""
        required_fields = [
            "OPENAI_GPT_ENDPOINT",
            "OPENAI_GPT_API_KEY",
            "OPENAI_GPT4_DEPLOYMENT",
            "OPENAI_EMBEDDING_ENDPOINT",
            "OPENAI_EMBEDDING_API_KEY",
            "OPENAI_EMBEDDING_DEPLOYMENT",
            "STORAGE_CONNECTION_STRING",
            "SQL_SERVER_1",
            "SQL_DATABASE_1",
            "SQL_USERNAME_1",
            "SQL_PASSWORD_1",
            "SQL_CONNECTION_STRING_1",
            "SQL_SERVER_2",
            "SQL_DATABASE_2",
            "SQL_USERNAME_2",
            "SQL_PASSWORD_2",
            "SQL_CONNECTION_STRING_2",
            "COSMOS_ENDPOINT",
            "COSMOS_KEY",
            "REDIS_CONNECTION_STRING",
            "DOCUMENT_INTELLIGENCE_ENDPOINT",
            "DOCUMENT_INTELLIGENCE_KEY",
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(self, field, None):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_fields)}"
            )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Uses lru_cache to ensure settings are loaded only once
    """
    settings = Settings()
    settings.validate_required_settings()
    return settings


# Global settings instance
settings = get_settings()


# Helper functions
def is_production() -> bool:
    """Check if running in production environment"""
    return settings.ENVIRONMENT.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment"""
    return settings.ENVIRONMENT.lower() == "development"

