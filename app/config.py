"""Environment-backed settings. Secrets never live in code (spec 07 SEC-003)."""

from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg2://regimpact:regimpact@localhost:5432/regimpact"
    aws_region: str = "us-east-1"
    aws_endpoint_url: str = ""
    s3_document_bucket: str = "regimpact-documents"
    sqs_queue_url: str = ""
    demo_company_id: UUID | None = None
    demo_user_id: str = "demo_user"
    bedrock_llm_model: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    bedrock_embedding_model: str = "amazon.titan-embed-text-v2:0"
    llm_provider: str = "bedrock"
    embedding_provider: str = "bedrock"
    openai_api_key: str = ""
    openai_llm_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    presign_ttl_seconds: int = 300
    max_upload_bytes: int = 25 * 1024 * 1024
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    log_level: str = "INFO"

    @field_validator("demo_company_id", mode="before")
    @classmethod
    def empty_demo_company_id(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [part.strip() for part in self.cors_origins.split(",") if part.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
