from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: str = "development"
    app_name: str = "ContextPilot AI"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "REPLACE_WITH_A_RANDOM_64_CHAR_SECRET"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:3000"

    # LLM providers (dummy defaults — override via .env)
    llm_provider: str = "openai"
    openai_api_key: str = "sk-REPLACE_WITH_YOUR_OPENAI_API_KEY"
    openai_chat_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    anthropic_api_key: str = "sk-ant-REPLACE_WITH_YOUR_ANTHROPIC_API_KEY"
    anthropic_model: str = "claude-sonnet-5"

    # Vector store
    vector_store_provider: str = "faiss"
    vector_store_dir: str = "./data/vector_store"
    upload_dir: str = "./data/uploads"
    pinecone_api_key: str = "REPLACE_WITH_YOUR_PINECONE_API_KEY"
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "contextpilot-kb"
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: str = "REPLACE_WITH_YOUR_WEAVIATE_API_KEY"

    # Database
    database_url: str = "postgresql+psycopg2://contextpilot:contextpilot@localhost:5432/contextpilot"

    # Cache / queue
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Observability
    langsmith_api_key: str = "REPLACE_WITH_YOUR_LANGSMITH_API_KEY"
    langsmith_project: str = "contextpilot-ai"
    langchain_tracing_v2: bool = False

    # Confidence thresholds
    confidence_escalation_threshold: float = 0.62
    confidence_auto_answer_threshold: float = 0.80

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
