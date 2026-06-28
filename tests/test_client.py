import asyncio
import pytest
from api.client import resilient_triage, CallOutcome
from api.models import TriageRequest
from api.errors import TransientError
from api.providers.mock import MockProvider

REQ = TriageRequest(dispute_text="I never authorised this")

async def test_succeeds_first_try():
    out = await resilient_triage(MockProvider(), REQ, base_delay=0.001)
    assert isinstance(out, CallOutcome)
    assert out.attempts == 1
    assert out.latency_ms >= 0.0

async def test_retries_then_succeeds():
    out = await resilient_triage(MockProvider(fail_first_k=2), REQ, base_delay=0.001)
    assert out.attempts == 3

async def test_raises_after_retries_exhausted():
    with pytest.raises(TransientError):
        await resilient_triage(MockProvider(fail_first_k=9), REQ, max_retries=2, base_delay=0.001)

async def test_timeout_propagates():
    class Slow(MockProvider):
        async def triage(self, request):
            await asyncio.sleep(0.2)
            return await super().triage(request)
    with pytest.raises(asyncio.TimeoutError):
        await resilient_triage(Slow(), REQ, timeout=0.01)
