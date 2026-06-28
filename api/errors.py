from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class ErrorEnvelope(BaseModel):
    """The single typed shape every failure is surfaced as."""
    model_config = ConfigDict(extra="forbid")
    error_type: str
    message: str
    retryable: bool
    attempts: int | None = None


class TransientError(Exception):
    """Retryable provider error (429 / 5xx). The client backs off and retries."""


class ProviderError(Exception):
    """Non-retryable provider error (bad request / auth). The client gives up."""
