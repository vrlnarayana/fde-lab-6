import pytest
from api.models import TriageRequest
from api.errors import TransientError
from api.providers.mock import MockProvider
from api.triage import parse_triage


async def test_mock_returns_valid_triage():
    raw = await MockProvider().triage(TriageRequest(dispute_text="I never authorised this charge"))
    triage, err = parse_triage(raw.content)
    assert err is None
    assert triage.category == "card_fraud"
    assert triage.needs_human_review is True


async def test_mock_detects_pii_from_digits():
    raw = await MockProvider().triage(TriageRequest(dispute_text="charged £89.99 on 3 June"))
    triage, _ = parse_triage(raw.content)
    assert triage.pii_detected is True


async def test_mock_no_pii_for_plain_text():
    raw = await MockProvider().triage(TriageRequest(dispute_text="my subscription renewed"))
    triage, _ = parse_triage(raw.content)
    assert triage.pii_detected is False
    assert triage.category == "subscription"


async def test_mock_fail_first_k_then_success():
    p = MockProvider(fail_first_k=2)
    req = TriageRequest(dispute_text="hi")
    for _ in range(2):
        with pytest.raises(TransientError):
            await p.triage(req)
    raw = await p.triage(req)
    assert raw.model == "mock-triage-1"


async def test_mock_force_bad_output_is_unparseable():
    raw = await MockProvider(force_bad_output=True).triage(TriageRequest(dispute_text="x"))
    triage, err = parse_triage(raw.content)
    assert triage is None and err is not None
