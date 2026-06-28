from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Two-tier validation policy:
#   STRICT_IN — wire INPUT contracts: reject type coercion AND unknown fields (the
#               "Type it" boundary; e.g. fail_first_k="2" or an extra field -> 422).
#   FORBID    — internal + LLM-output contracts: reject unknown fields. DisputeTriage
#               is parsed from the model's JSON where enum values arrive as strings
#               ("high"), which pydantic strict mode rejects — so output stays FORBID
#               and its bool fields get an explicit non-coercion guard below.
STRICT_IN = ConfigDict(strict=True, extra="forbid")
FORBID = ConfigDict(extra="forbid")


class Urgency(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class DisputeTriage(BaseModel):
    """The typed contract the copilot must return (kit capstone shape)."""
    model_config = FORBID
    category: str = Field(description="card_fraud | duplicate_charge | subscription | atm | other")
    urgency: Urgency
    needs_human_review: bool
    suggested_next_action: str
    pii_detected: bool = Field(description="true if text holds PII to redact before logging")

    @field_validator("needs_human_review", "pii_detected", mode="before")
    @classmethod
    def validate_bools_strict(cls, v):
        if not isinstance(v, bool):
            raise ValueError(f"Expected bool, got {type(v).__name__}")
        return v


class Usage(BaseModel):
    model_config = FORBID
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class ProviderTriageRaw(BaseModel):
    """A provider's raw reply — content is JSON to be validated downstream ('Validate it')."""
    model_config = FORBID
    model: str
    content: str
    usage: Usage


class TriageRequest(BaseModel):
    model_config = STRICT_IN
    dispute_text: str = Field(min_length=1)
    provider: str | None = None
    fail_first_k: int = Field(default=0, ge=0, le=10)        # mock retry lever
    force_bad_output: bool = False                            # mock malformed-output lever


class TriageResponse(BaseModel):
    model_config = FORBID
    provider: str
    model: str
    auth_mode: str
    attempts: int
    latency_ms: float
    validated: bool
    triage: DisputeTriage | None = None
    error: str | None = None


class BenchmarkRequest(BaseModel):
    model_config = STRICT_IN
    providers: list[str] = Field(min_length=1)
    n: int = Field(default=20, ge=2, le=100)
    dispute_text: str = Field(min_length=1)


class BenchmarkRow(BaseModel):
    model_config = FORBID
    provider: str
    p50_ms: float
    p95_ms: float
    avg_tokens: float
    cost_per_1k_calls: float
    residency: str
    auth: str
    simulated: bool
