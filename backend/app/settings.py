from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="backend/.env", env_file_encoding="utf-8")

    app_env: str = "dev"
    app_name: str = "rag-web"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_web"
    upload_dir: str = "backend/uploads"

    default_llm_provider: str = "openai_compat"
    default_llm_model: str = "gpt-4o-mini"

    openai_compat_base_url: str = "https://api.openai.com/v1"
    openai_compat_api_key: str = ""

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b-instruct"

    embeddings_provider: str = "openai_compat"
    embeddings_model: str = "text-embedding-3-small"
    embeddings_dim: int = 1536


settings = Settings()
