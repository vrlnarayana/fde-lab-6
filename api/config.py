from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_deployment: str = "gpt-4o-mini"
    azure_region: str = "westeurope"
    auth_mode: str = "key"                 # key | keyless
    azure_disable_local_auth: bool = False

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    default_provider: str = "mock"

    # Published blended $/1K tokens (indicative — see 6-D watch-out; verify before quoting).
    # Reasoning-model blends are a rough 50/50 of list input/output $/1M ÷ 1000.
    rate_per_1k_tokens: dict[str, float] = {
        "gpt-4o-mini": 0.0006,
        "gpt-4o": 0.0075,
        "o4-mini": 0.00275,   # ~$1.10 in / $4.40 out per 1M
        "gpt-5": 0.005625,    # ~$1.25 in / $10.00 out per 1M
        "mock-triage-1": 0.0,
    }


settings = Settings()
