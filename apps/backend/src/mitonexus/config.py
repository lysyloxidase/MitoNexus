from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """MitoNexus backend configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MITONEXUS_",
        case_sensitive=False,
    )

    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Database
    database_url: PostgresDsn
    redis_url: RedisDsn

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str
    neo4j_database: str = "neo4j"

    # Ollama
    ollama_host: str = "http://localhost:11434"
    model_router: str = "qwen2.5:7b"
    model_primary: str = "qwen2.5:14b"
    model_reasoner: str = "deepseek-r1:14b"
    model_medical: str = "meditron:7b"
    model_embedding: str = "nomic-embed-text"

    # External APIs
    pubmed_api_key: str | None = None
    semantic_scholar_key: str | None = None

    # Langfuse
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "http://localhost:3001"


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
