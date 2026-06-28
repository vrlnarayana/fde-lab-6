from __future__ import annotations
import asyncio
import time
from pydantic import BaseModel, ConfigDict
from api.errors import TransientError
from api.models import TriageRequest, ProviderTriageRaw
from api.providers.base import TriageProvider


class CallOutcome(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", arbitrary_types_allowed=True)
    raw: ProviderTriageRaw
    attempts: int
    latency_ms: float


async def resilient_triage(
    provider: TriageProvider,
    request: TriageRequest,
    *,
    max_retries: int = 3,
    base_delay: float = 0.01,
    timeout: float = 30.0,   # reasoning models (o4-mini/gpt-5) run 5-10x slower than gpt-4o-mini
) -> CallOutcome:
    """Call a provider with a timeout and bounded exponential backoff on TransientError.

    Returns a CallOutcome stamped with attempts + wall-clock latency. Re-raises
    TransientError once retries are exhausted; asyncio.TimeoutError propagates.
    """
    attempt = 0
    start = time.perf_counter()
    while True:
        attempt += 1
        try:
            raw = await asyncio.wait_for(provider.triage(request), timeout=timeout)
        except TransientError:
            if attempt > max_retries:
                raise
            await asyncio.sleep(base_delay * (2 ** (attempt - 1)))
            continue
        latency_ms = (time.perf_counter() - start) * 1000.0
        return CallOutcome(raw=raw, attempts=attempt, latency_ms=latency_ms)
