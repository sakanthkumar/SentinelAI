from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_provider: str = Field(default="groq", alias="LLM_PROVIDER")

    groq_api_key: str = Field(alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")

    ollama_model: str = Field(default="qwen3:8b", alias="OLLAMA_MODEL")

    database_url: str = Field(alias="DATABASE_URL")

    chroma_db_path: str = Field(default="../chroma_storage", alias="CHROMA_DB_PATH")

    upload_folder: str = Field(default="uploads", alias="UPLOAD_FOLDER")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()