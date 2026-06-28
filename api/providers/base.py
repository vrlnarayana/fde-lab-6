from __future__ import annotations
from typing import Protocol
from api.models import TriageRequest, ProviderTriageRaw


class TriageProvider(Protocol):
    """The contract every adapter satisfies. Structural typing — no inheritance."""
    name: str
    is_mock: bool
    auth_mode: str   # "n/a" | "api-key" | "keyless"

    async def triage(self, request: TriageRequest) -> ProviderTriageRaw: ...
